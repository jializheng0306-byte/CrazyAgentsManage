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

function resolveInvocationMode() {
  var closeoutManaged = boolFromEnv('HARNESS_CLOSEOUT_CONTEXT');
  var trivial = boolFromEnv('HARNESS_TRACE_TRIVIAL');
  if (!closeoutManaged && !trivial) {
    process.stderr.write(
      'record-failure.cjs only supports trivial direct traces; non-trivial rounds must use node scripts/harness-closeout-writeback.cjs\n'
    );
    process.exit(1);
  }
  return {
    closeoutManaged: closeoutManaged,
    trivial: trivial,
    source: closeoutManaged ? 'closeout-writeback' : 'direct-trivial',
  };
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
  var invocation = resolveInvocationMode();
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
    type: process.env.HARNESS_FAILURE_TYPE || process.env.HARNESS_FAILURE_STAGE || 'unknown-failure',
    file: process.env.HARNESS_FAILURE_FILE || '',
    message: process.env.HARNESS_FAILURE_MESSAGE || 'Unknown failure',
    context: {
      agent: process.env.HARNESS_AGENT || 'unknown',
      branch: process.env.HARNESS_BRANCH || safeBranch(),
      worktree: process.env.HARNESS_WORKTREE || process.cwd(),
      verification_step: process.env.HARNESS_FAILURE_STAGE || '',
      command: process.env.HARNESS_FAILURE_COMMAND || '',
      fatal: process.env.HARNESS_FAILURE_FATAL === 'true',
      traceSource: invocation.source,
      closeoutManaged: invocation.closeoutManaged,
      trivial: invocation.trivial,
      governanceReports: governanceReports,
    },
  };

  ensureDir(FAILURES_DIR);
  fs.writeFileSync(path.join(FAILURES_DIR, id + '.json'), JSON.stringify(record, null, 2) + '\n', 'utf8');
  process.stdout.write(id + '\n');
}

main();
