#!/usr/bin/env node
/**
 * harness-critic.cjs — Critic 回写版 (失败模式分析器)
 *
 * 定期分析 harness/trace/failures/ 中的结构化失败记录,
 * 找出反复出现的模式, 给出改进建议。
 *
 * 用法: node scripts/harness-critic.cjs [--days N] [--json]
 * 默认分析最近7天的记录
 *
 * CrazyAgentsManage Harness critic
 */

var fs = require('fs');
var path = require('path');

var ROOT = path.resolve(__dirname, '..');
var TRACE_ROOT = process.env.HARNESS_TRACE_ROOT || path.join(ROOT, 'harness', 'trace');
var MEMORY_ROOT = process.env.HARNESS_MEMORY_ROOT || path.join(ROOT, 'harness', 'memory');
var FAILURES_DIR = path.join(TRACE_ROOT, 'failures');
var MEMORY_FILE = path.join(MEMORY_ROOT, 'failure-patterns.md');
var PROCEDURAL_FILE = path.join(MEMORY_ROOT, 'procedural.md');

function findFailureFiles(dir, days) {
  if (!fs.existsSync(dir)) return [];
  var cutoff = Date.now() - days * 86400000;
  var files = fs.readdirSync(dir).filter(function(f) {
    return f !== 'TEMPLATE.json' && f.endsWith('.json') && fs.statSync(path.join(dir, f)).mtimeMs >= cutoff;
  });
  return files.map(function(f) { return JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8')); });
}

function analyzePatterns(failures, days) {
  if (failures.length === 0) {
    return { totalFailures: 0, patterns: [], recommendations: [] };
  }

  // 按错误类型分组
  var typeMap = {};
  for (var i = 0; i < failures.length; i++) {
    var f = failures[i];
    var key = f.type || f.errorType || 'unknown';
    if (!typeMap[key]) typeMap[key] = { count: 0, files: [], examples: [] };
    typeMap[key].count++;
    typeMap[key].files.push(f.file || 'unknown');
    if (typeMap[key].examples.length < 3) {
      typeMap[key].examples.push((f.message || f.error || '').substring(0, 100));
    }
  }

  // 按出现次数排序
  var sorted = Object.keys(typeMap).map(function(k) {
    return { type: k, count: typeMap[k].count, files: typeMap[k].files, examples: typeMap[k].examples };
  }).sort(function(a, b) { return b.count - a.count; });

  // 生成建议
  var recommendations = [];

  sorted.forEach(function(pattern) {
    if (pattern.count >= 3) {
      // 反复出现的问题 → 建议转为硬规则
      recommendations.push({
        priority: pattern.count >= 5 ? 'HIGH' : 'MEDIUM',
        pattern: pattern.type,
        count: pattern.count,
        suggestion: generateSuggestion(pattern),
        action: pattern.count >= 5 ? 'CONSIDER_LINT_RULE' : 'UPDATE_DOCUMENTATION'
      });
    } else if (pattern.count >= 2) {
      recommendations.push({
        priority: 'LOW',
        pattern: pattern.type,
        count: pattern.count,
        suggestion: 'Monitor this pattern. If it reaches 3 occurrences, consider adding a lint rule or updating documentation.',
        action: 'MONITOR'
      });
    }
  });

  return {
    totalFailures: failures.length,
    analysisPeriod: days + ' days',
    topPatterns: sorted.slice(0, 10),
    recommendations: recommendations
  };
}

function generateSuggestion(pattern) {
  var suggestions = {
    'layer-violation': 'UPDATE: 在当前仓库的分层规则、适配边界或 Harness 文档中补齐约束。',
    'typescript-error': 'UPDATE: 在相关实现文档、PRD 或故障排查文档中补齐该错误的处理规则。',
    'test-failure': 'UPDATE: 为该类缺陷补回归测试，并将经验回写到 harness/memory/procedural.md。',
    'eslint-error': 'UPDATE: 评估是否需要修正规则、代码风格，或在文档中补充约束。',
    'schema-validation': 'UPDATE: 在当前仓库的数据契约或适配层中修正校验边界。'
  };

  var key = Object.keys(suggestions).find(function(k) {
    return pattern.type.toLowerCase().indexOf(k) !== -1;
  });

  return key ? suggestions[key] : 'Analyze root cause and consider adding to lint rules or documentation.';
}

function appendUniqueSection(filePath, marker, section) {
  if (!fs.existsSync(filePath)) return false;
  var content = fs.readFileSync(filePath, 'utf-8');
  if (content.indexOf(marker) !== -1) return false;
  fs.writeFileSync(filePath, content.replace(/\s*$/, '\n\n') + section + '\n', 'utf-8');
  return true;
}

function updateFailurePatterns(result) {
  if (!fs.existsSync(MEMORY_FILE)) return 0;
  var updated = 0;
  for (var i = 0; i < result.recommendations.length; i++) {
    var rec = result.recommendations[i];
    if (rec.priority === 'LOW') continue;
    var marker = '### [AUTO-' + rec.pattern + ']';
    var section =
      '### [AUTO-' + rec.pattern + '] ' + rec.pattern + '\n' +
      '- **出现次数**: ' + rec.count + '\n' +
      '- **根因分析**: Critic 自动聚合到 `' + rec.pattern + '` 模式，说明该失败已出现重复趋势。\n' +
      '- **短期修复**: ' + rec.suggestion + '\n' +
      '- **长期修复**: 评估是否转化为 lint / 模板 / 文档规则。\n';
    if (appendUniqueSection(MEMORY_FILE, marker, section)) updated++;
  }
  return updated;
}

function updateProceduralMemory(result) {
  if (!fs.existsSync(PROCEDURAL_FILE)) return 0;
  var updated = 0;
  for (var i = 0; i < result.recommendations.length; i++) {
    var rec = result.recommendations[i];
    if (rec.action !== 'UPDATE_DOCUMENTATION' && rec.action !== 'CONSIDER_LINT_RULE') continue;
    var marker = '### Critic Follow-up: ' + rec.pattern;
    var section =
      '### Critic Follow-up: ' + rec.pattern + '\n' +
      '1. 复盘 `' + rec.pattern + '` 对应的失败样本\n' +
      '2. 决定是补规则、补模板，还是补验证\n' +
      '3. 若已修复，更新相关执行流程并保留验证证据\n';
    if (appendUniqueSection(PROCEDURAL_FILE, marker, section)) updated++;
  }
  return updated;
}

function writeBack(result) {
  return {
    failurePatternsUpdated: updateFailurePatterns(result),
    proceduralUpdated: updateProceduralMemory(result),
  };
}

function main() {
  var args = process.argv.slice(2);
  var days = 7;
  var jsonMode = false;
  var writeBackMode = false;

  for (var a = 0; a < args.length; a++) {
    if (args[a] === '--days' && a + 1 < args.length) days = parseInt(args[++a]);
    else if (args[a] === '--json') jsonMode = true;
    else if (args[a] === '--write-back') writeBackMode = true;
  }

  var failures = findFailureFiles(FAILURES_DIR, days);
  var result = analyzePatterns(failures, days);
  var writeBackResult = null;

  if (writeBackMode) {
    writeBackResult = writeBack(result);
    result.writeBack = writeBackResult;
  }

  if (jsonMode) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log('');
    console.log('╔══════════════════════════════════════╗');
    console.log('║ CrazyAgentsManage Critic Analysis Report ║');
    console.log('╠══════════════════════════════════════╣');
    console.log('║ Period: Last ' + days + ' days                 ║');
    console.log('║ Failures analyzed: ' + result.totalFailures + '               ║');

    if (result.totalFailures === 0) {
      console.log('║                                            ║');
      console.log('║  ✅ No failures found! System healthy.  ║');
      console.log('╚══════════════════════════════════════╝');
      process.exit(0);
    }

    console.log('║ Top patterns:                             ║');
    console.log('╠══════════════════════════════════════╣');

    if (result.topPatterns.length === 0) {
      console.log('║  (untyped failures - need better data)   ║');
    } else {
      for (var p = 0; p < result.topPatterns.length; p++) {
        var pat = result.topPatterns[p];
        var bar = '';
        for (var b = 0; b < Math.min(pat.count, 20); b++) bar += '█';
        console.log('║  #' + (p + 1) + ' [' + pat.type + '] x' + pat.count + ' ' + bar + '  ║');
      }
    }

    console.log('╠══════════════════════════════════════╣');
    console.log('║ Recommendations:                          ║');
    console.log('╚══════════════════════════════════════╝');

    if (result.recommendations.length === 0) {
      console.log('\nNo actionable patterns yet. Continue monitoring.\n');
    } else {
      for (var r = 0; r < result.recommendations.length; r++) {
        var rec = result.recommendations[r];
        console.log('\n[' + rec.priority + '] Pattern: "' + rec.pattern + '" (' + rec.count + 'x)');
        console.log('  Suggestion: ' + rec.suggestion);
        console.log('  Action:     ' + rec.action);
      }
      console.log('');
    }

    if (writeBackResult) {
      console.log('Write-back result:');
      console.log('  failure-patterns updated: ' + writeBackResult.failurePatternsUpdated);
      console.log('  procedural updated:       ' + writeBackResult.proceduralUpdated);
      console.log('');
    }
  }

  process.exit(0);
}

main();
