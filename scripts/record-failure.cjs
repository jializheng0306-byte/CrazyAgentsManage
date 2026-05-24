#!/usr/bin/env node
/**
 * record-failure.cjs — 写入结构化 Harness 失败记录
 *
 * 优先从环境变量读取，便于被 validate.js 等脚本调用。
 */

var fs = require('fs');
var path = require('path');
var execSync = require('child_process').execSync;

var ROOT = process.env.HARNESS_REPO_ROOT
  ? path.resolve(process.env.HARNESS_REPO_ROOT)
  : path.resolve(__dirname, '..');
var TRACE_ROOT = process.env.HARNESS_TRACE_ROOT || path.join(ROOT, 'harness', 'trace');
var FAILURES_DIR = path.join(TRACE_ROOT, 'failures');

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function boolFromEnv(name) {
  return String(process.env[name] || '').trim().toLowerCase() === 'true';
}

function parseArgs(argv) {
  var out = {
    allowTrivialDirect: false,
    probeReason: '',
    message: '',
    type: '',
    file: '',
    stage: '',
    command: '',
    agent: '',
    branch: '',
    worktree: '',
    fatal: false,
  };
  for (var i = 0; i < argv.length; i++) {
    var arg = argv[i];
    switch (arg) {
      case '--allow-trivial-direct':
        out.allowTrivialDirect = true;
        break;
      case '--probe-reason':
        out.probeReason = String(argv[++i] || '').trim();
        break;
      case '--message':
        out.message = String(argv[++i] || '').trim();
        break;
      case '--type':
        out.type = String(argv[++i] || '').trim();
        break;
      case '--file':
        out.file = String(argv[++i] || '').trim();
        break;
      case '--stage':
        out.stage = String(argv[++i] || '').trim();
        break;
      case '--command':
        out.command = String(argv[++i] || '').trim();
        break;
      case '--agent':
        out.agent = String(argv[++i] || '').trim();
        break;
      case '--branch':
        out.branch = String(argv[++i] || '').trim();
        break;
      case '--worktree':
        out.worktree = String(argv[++i] || '').trim();
        break;
      case '--fatal':
        out.fatal = true;
        break;
      default:
        break;
    }
  }
  return out;
}

function safeParentCommand() {
  var ppid = String(process.ppid || '').trim();
  if (!ppid) return '';
  try {
    return fs.readFileSync('/proc/' + ppid + '/cmdline', 'utf8').replace(/\u0000/g, ' ').trim();
  } catch (_) {}
  try {
    return execSync('ps -o command= -p ' + ppid, {
      cwd: ROOT,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
  } catch (_) {
    return '';
  }
}

function resolveInvocationMode(options) {
  var closeoutManaged = boolFromEnv('HARNESS_CLOSEOUT_CONTEXT');
  if (closeoutManaged) {
    if (safeParentCommand().indexOf('harness-closeout-writeback.cjs') === -1) {
      process.stderr.write(
        'HARNESS_CLOSEOUT_CONTEXT is reserved for a harness-closeout-writeback.cjs parent process\n'
      );
      process.exit(1);
    }
    return {
      closeoutManaged: true,
      trivial: false,
      source: 'closeout-writeback',
      probeReason: '',
    };
  }
  if (!options.allowTrivialDirect || !options.probeReason) {
    process.stderr.write(
      'record-failure.cjs only supports trivial direct traces via --allow-trivial-direct --probe-reason; non-trivial rounds must use node scripts/harness-closeout-writeback.cjs\n'
    );
    process.exit(1);
  }
  return {
    closeoutManaged: false,
    trivial: true,
    source: 'direct-trivial',
    probeReason: options.probeReason,
  };
}

function optionOrEnv(value, envName, fallback) {
  if (String(value || '').trim()) {
    return String(value).trim();
  }
  if (String(process.env[envName] || '').trim()) {
    return String(process.env[envName]).trim();
  }
  return fallback;
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
  ensureDir(FAILURES_DIR);
  var existing = fs.readdirSync(FAILURES_DIR).filter(function(name) {
    return name.indexOf('F-' + stamp + '-') === 0 && name.endsWith('.json');
  }).length;
  return 'F-' + stamp + '-' + String(existing + 1).padStart(3, '0');
}

function main() {
  var options = parseArgs(process.argv.slice(2));
  var invocation = resolveInvocationMode(options);
  var id = nextId();
  var governanceReports = [];
  if (process.env.HARNESS_GOVERNANCE_REPORTS) {
    try {
      governanceReports = JSON.parse(process.env.HARNESS_GOVERNANCE_REPORTS);
      if (!Array.isArray(governanceReports)) {
        governanceReports = [];
      }
    } catch (_) {
      governanceReports = [];
    }
  }
  var record = {
    id: id,
    timestamp: new Date().toISOString(),
    type: optionOrEnv(options.type, 'HARNESS_FAILURE_TYPE', optionOrEnv(options.stage, 'HARNESS_FAILURE_STAGE', 'unknown-failure')),
    file: optionOrEnv(options.file, 'HARNESS_FAILURE_FILE', ''),
    message: optionOrEnv(options.message, 'HARNESS_FAILURE_MESSAGE', 'Unknown failure'),
    context: {
      agent: optionOrEnv(options.agent, 'HARNESS_AGENT', 'unknown'),
      branch: optionOrEnv(options.branch, 'HARNESS_BRANCH', safeBranch()),
      worktree: optionOrEnv(options.worktree, 'HARNESS_WORKTREE', process.cwd()),
      verification_step: optionOrEnv(options.stage, 'HARNESS_FAILURE_STAGE', ''),
      command: optionOrEnv(options.command, 'HARNESS_FAILURE_COMMAND', ''),
      fatal: options.fatal || process.env.HARNESS_FAILURE_FATAL === 'true',
      traceSource: invocation.source,
      closeoutManaged: invocation.closeoutManaged,
      trivial: invocation.trivial,
      probeReason: invocation.probeReason,
      governanceReports: governanceReports,
    },
  };

  ensureDir(FAILURES_DIR);
  fs.writeFileSync(path.join(FAILURES_DIR, id + '.json'), JSON.stringify(record, null, 2) + '\n', 'utf8');
  process.stdout.write(id + '\n');
}

main();
