#!/usr/bin/env node
/**
 * harness-closeout-writeback.cjs
 *
 * One entrypoint for repository-local harness write-back after a round / sprint closeout.
 *
 * Responsibilities:
 * - write success or failure trace
 * - optionally trigger critic
 * - optionally trigger critic write-back
 *
 * Usage examples:
 *   node scripts/harness-closeout-writeback.cjs --status success --message "Round completed" --agent codex --steps plan,verify
 *   node scripts/harness-closeout-writeback.cjs --status failed --message "Verification emitted no artifact" --agent codex --stage verification
 *   node scripts/harness-closeout-writeback.cjs --status success --message "Sprint batch completed" --agent codex --critic-write-back
 */

const cp = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");

function parseArgs(argv) {
  const out = {
    status: "",
    message: "",
    agent: "codex",
    branch: "",
    worktree: ROOT,
    steps: "",
    type: "",
    file: "",
    stage: "",
    command: "",
    fatal: false,
    critic: false,
    criticWriteBack: false,
    governanceCheck: false,
    skipGovernanceCheck: false,
    governanceReports: [],
    days: "7",
    json: false,
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "--status":
        out.status = String(argv[++i] || "").trim();
        break;
      case "--message":
        out.message = String(argv[++i] || "").trim();
        break;
      case "--agent":
        out.agent = String(argv[++i] || "").trim() || out.agent;
        break;
      case "--branch":
        out.branch = String(argv[++i] || "").trim();
        break;
      case "--worktree":
        out.worktree = String(argv[++i] || "").trim() || out.worktree;
        break;
      case "--steps":
        out.steps = String(argv[++i] || "").trim();
        break;
      case "--type":
        out.type = String(argv[++i] || "").trim();
        break;
      case "--file":
        out.file = String(argv[++i] || "").trim();
        break;
      case "--stage":
        out.stage = String(argv[++i] || "").trim();
        break;
      case "--command":
        out.command = String(argv[++i] || "").trim();
        break;
      case "--days":
        out.days = String(argv[++i] || "").trim() || out.days;
        break;
      case "--fatal":
        out.fatal = true;
        break;
      case "--critic":
        out.critic = true;
        break;
      case "--critic-write-back":
        out.critic = true;
        out.criticWriteBack = true;
        break;
      case "--governance-check":
        out.governanceCheck = true;
        break;
      case "--skip-governance-check":
        out.skipGovernanceCheck = true;
        break;
      case "--governance-report":
        out.governanceReports.push(String(argv[++i] || "").trim());
        break;
      case "--json":
        out.json = true;
        break;
      default:
        break;
    }
  }

  return out;
}

function runNodeScript(scriptPath, extraEnv, args) {
  const result = cp.spawnSync(process.execPath, [scriptPath].concat(args || []), {
    cwd: ROOT,
    env: Object.assign({}, process.env, extraEnv || {}),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    const stderr = String(result.stderr || "").trim();
    const stdout = String(result.stdout || "").trim();
    const detail = stderr || stdout || `exit ${result.status}`;
    throw new Error(`${path.basename(scriptPath)} failed: ${detail}`);
  }
  return {
    stdout: String(result.stdout || "").trim(),
    stderr: String(result.stderr || "").trim(),
  };
}

function maybeRunCritic(days, writeBack) {
  const args = ["scripts/harness-critic.cjs", "--days", String(days || "7"), "--json"];
  if (writeBack) {
    args.splice(args.length - 1, 0, "--write-back");
  }
  const result = cp.spawnSync(process.execPath, args, {
    cwd: ROOT,
    env: process.env,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    const stderr = String(result.stderr || "").trim();
    const stdout = String(result.stdout || "").trim();
    const detail = stderr || stdout || `exit ${result.status}`;
    throw new Error(`harness-critic failed: ${detail}`);
  }
  const raw = String(result.stdout || "").trim();
  return raw ? JSON.parse(raw) : null;
}

function maybeRunGovernanceCheck(enabled) {
  if (!enabled) {
    return null;
  }
  const result = cp.spawnSync(path.join(ROOT, "scripts", "check_harness_governance_all.sh"), [], {
    cwd: ROOT,
    env: process.env,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    const stderr = String(result.stderr || "").trim();
    const stdout = String(result.stdout || "").trim();
    const detail = stderr || stdout || `exit ${result.status}`;
    throw new Error(`harness governance check failed: ${detail}`);
  }
  return {
    stdout: String(result.stdout || "").trim(),
  };
}

function defaultGovernanceReportPaths() {
  return [
    path.join(ROOT, "docs", "02-engineering", "harness", "harness-governance-report.md"),
    path.resolve(ROOT, "..", "FlowMindDeploy", "docs", "05-version-control", "architecture-drift-report.md"),
  ];
}

function summarizeGovernanceReport(reportPath) {
  const resolved = path.resolve(ROOT, reportPath);
  if (!fs.existsSync(resolved)) {
    return null;
  }
  const raw = fs.readFileSync(resolved, "utf8");
  const statusMatch = raw.match(/^- Status:\s*(.+)$/m);
  const repoMatch = raw.match(/^- Repo:\s*(.+)$/m);
  const titleMatch = raw.match(/^#\s+(.+)$/m);
  const passCount = (raw.match(/^\-\s+\[PASS\]/gm) || []).length;
  const failCount = (raw.match(/^\-\s+\[(FAIL|ERROR)\]/gm) || []).length;
  const scopedSection =
    raw.match(/^## Drift Findings\s+([\s\S]*?)(?:\n## |\s*$)/m)?.[1] ||
    raw.match(/^## Findings\s+([\s\S]*?)(?:\n## |\s*$)/m)?.[1] ||
    "";
  const findingLines = scopedSection
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => /^- /.test(line) && !/^- (Date|Status|Repo):/.test(line));
  return {
    path: path.relative(ROOT, resolved),
    absolutePath: resolved,
    title: titleMatch ? titleMatch[1].trim() : path.basename(resolved),
    repo: repoMatch ? repoMatch[1].trim() : "",
    status: statusMatch ? statusMatch[1].trim() : "UNKNOWN",
    passCount,
    failCount,
    summary: findingLines[0] ? findingLines[0].replace(/^- /, "").trim() : "",
  };
}

function collectGovernanceReports(options) {
  const requested = options.governanceReports.length > 0
    ? options.governanceReports
    : defaultGovernanceReportPaths();
  const seen = new Set();
  return requested
    .map((reportPath) => String(reportPath || "").trim())
    .filter(Boolean)
    .map((reportPath) => path.resolve(ROOT, reportPath))
    .filter((resolved) => {
      if (seen.has(resolved)) {
        return false;
      }
      seen.add(resolved);
      return true;
    })
    .map((resolved) => summarizeGovernanceReport(resolved))
    .filter(Boolean);
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.status !== "success" && options.status !== "failed") {
    throw new Error("--status must be success or failed");
  }
  if (!options.message) {
    throw new Error("--message is required");
  }

  const shouldRunGovernanceCheck =
    !options.skipGovernanceCheck && (options.governanceCheck || options.status === "success");

  const governance = maybeRunGovernanceCheck(shouldRunGovernanceCheck);
  const governanceReports = collectGovernanceReports(options);

  let trace = null;
  if (options.status === "success") {
    const result = runNodeScript(path.join(ROOT, "scripts", "record-success.cjs"), {
      HARNESS_SUCCESS_TYPE: options.type || "round-success",
      HARNESS_SUCCESS_MESSAGE: options.message,
      HARNESS_AGENT: options.agent,
      HARNESS_BRANCH: options.branch,
      HARNESS_WORKTREE: options.worktree,
      HARNESS_SUCCESS_STEPS: options.steps,
      HARNESS_GOVERNANCE_REPORTS: JSON.stringify(governanceReports),
    });
    trace = { kind: "success", id: result.stdout };
  } else {
    const result = runNodeScript(path.join(ROOT, "scripts", "record-failure.cjs"), {
      HARNESS_FAILURE_TYPE: options.type || options.stage || "round-failure",
      HARNESS_FAILURE_FILE: options.file,
      HARNESS_FAILURE_MESSAGE: options.message,
      HARNESS_AGENT: options.agent,
      HARNESS_BRANCH: options.branch,
      HARNESS_WORKTREE: options.worktree,
      HARNESS_FAILURE_STAGE: options.stage,
      HARNESS_FAILURE_COMMAND: options.command,
      HARNESS_FAILURE_FATAL: options.fatal ? "true" : "false",
      HARNESS_GOVERNANCE_REPORTS: JSON.stringify(governanceReports),
    });
    trace = { kind: "failure", id: result.stdout };
  }

  let critic = null;
  if (options.critic || options.status === "failed") {
    critic = maybeRunCritic(options.days, options.criticWriteBack);
  }

  const payload = {
    status: options.status,
    trace,
    critic,
    governance,
    governanceReports,
  };

  if (options.json) {
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return;
  }

  process.stdout.write(`trace: ${trace.kind}:${trace.id}\n`);
  if (critic) {
    process.stdout.write(`critic: ok${options.criticWriteBack ? " (write-back)" : ""}\n`);
  }
  if (governance) {
    process.stdout.write("governance: ok\n");
  }
  if (governanceReports.length > 0) {
    process.stdout.write(`governance-reports: ${governanceReports.length}\n`);
  }
}

try {
  main();
} catch (err) {
  const message = err && err.message ? err.message : String(err);
  process.stderr.write(message + "\n");
  process.exit(1);
}
