#!/usr/bin/env node
/**
 * record-success.cjs — 写入结构化 Harness 成功记录
 */

var fs = require('fs');
var path = require('path');
var execSync = require('child_process').execSync;

var ROOT = path.resolve(__dirname, '..');
var TRACE_ROOT = process.env.HARNESS_TRACE_ROOT || path.join(ROOT, 'harness', 'trace');
var SUCCESSES_DIR = path.join(TRACE_ROOT, 'successes');

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function safeBranch() {
  try {
    return execSync('git branch --show-current', {
      cwd: ROOT,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim() || 'detached';
  } catch (_) {
    return 'unknown';
  }
}

function nextId() {
  var now = new Date();
  var stamp = now.toISOString().slice(0, 10).replace(/-/g, '');
  ensureDir(SUCCESSES_DIR);
  var existing = fs.readdirSync(SUCCESSES_DIR).filter(function(name) {
    return name.indexOf('S-' + stamp + '-') === 0 && name.endsWith('.json');
  }).length;
  return 'S-' + stamp + '-' + String(existing + 1).padStart(3, '0');
}

function parseSteps(raw) {
  if (!raw) return [];
  return raw.split(',').map(function(x) { return x.trim(); }).filter(Boolean);
}

function main() {
  var id = nextId();
  var record = {
    id: id,
    timestamp: new Date().toISOString(),
    type: process.env.HARNESS_SUCCESS_TYPE || 'pipeline-success',
    message: process.env.HARNESS_SUCCESS_MESSAGE || 'Pipeline completed successfully',
    context: {
      agent: process.env.HARNESS_AGENT || 'unknown',
      branch: process.env.HARNESS_BRANCH || safeBranch(),
      worktree: process.env.HARNESS_WORKTREE || process.cwd(),
      steps: parseSteps(process.env.HARNESS_SUCCESS_STEPS),
    },
  };

  ensureDir(SUCCESSES_DIR);
  fs.writeFileSync(path.join(SUCCESSES_DIR, id + '.json'), JSON.stringify(record, null, 2) + '\n', 'utf8');
  process.stdout.write(id + '\n');
}

main();
