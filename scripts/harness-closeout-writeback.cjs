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

const ROOT = process.env.HARNESS_REPO_ROOT
  ? path.resolve(process.env.HARNESS_REPO_ROOT)
  : path.resolve(__dirname, "..");
const CLOSEOUT_ROOT = process.env.HARNESS_CLOSEOUT_ROOT || path.join(ROOT, "harness", "closeouts");
const LANE_PREFIXES = new Set(["codex", "ops", "shared", "docs", "hotfix", "release", "feat", "fix", "chore"]);

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function safeBranch() {
  try {
    return cp.spawnSync("git", ["branch", "--show-current"], {
      cwd: ROOT,
      env: process.env,
      encoding: "utf8",
    }).stdout.trim() || "detached";
  } catch (_) {
    return "unknown";
  }
}

function nextCloseoutId() {
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  ensureDir(CLOSEOUT_ROOT);
  const existing = fs.readdirSync(CLOSEOUT_ROOT).filter((name) => {
    return name.startsWith("C-" + stamp + "-") && name.endsWith(".json");
  }).length;
  return "C-" + stamp + "-" + String(existing + 1).padStart(3, "0");
}

function readJsonIfExists(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return null;
    }
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_) {
    return null;
  }
}

function normalizePath(input) {
  return path.resolve(String(input || ROOT));
}

function readWorktreeContext(worktreePath) {
  const contextPath = path.join(worktreePath, ".omx", "worktree-context.json");
  const payload = readJsonIfExists(contextPath);
  if (!payload || typeof payload !== "object") {
    return null;
  }
  payload._contextPath = contextPath;
  return payload;
}

function inferLaneInfo(options, branch, worktreePath, worktreeContext) {
  if (options.lane) {
    return { lane: options.lane, source: "cli-arg", topic: options.topic || "" };
  }
  if (worktreeContext && worktreeContext.lane) {
    return {
      lane: String(worktreeContext.lane),
      source: "worktree-context",
      topic: String(worktreeContext.topic || options.topic || ""),
    };
  }
  if (branch && branch.includes("/")) {
    const prefix = branch.split("/")[0];
    if (LANE_PREFIXES.has(prefix)) {
      return { lane: prefix, source: "branch-prefix", topic: options.topic || "" };
    }
  }
  if (normalizePath(worktreePath) === ROOT) {
    return { lane: "primary", source: "primary-worktree", topic: options.topic || "" };
  }
  return { lane: "", source: "missing", topic: options.topic || "" };
}

function shouldAutoCriticWriteBack(status, criticResult) {
  if (status !== "failed" || !criticResult || !Array.isArray(criticResult.recommendations)) {
    return false;
  }
  return criticResult.recommendations.some((rec) => rec.priority && rec.priority !== "LOW");
}

function writeCloseoutArtifact(payload) {
  ensureDir(CLOSEOUT_ROOT);
  const filePath = path.join(CLOSEOUT_ROOT, payload.id + ".json");
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2) + "\n", "utf8");
  return filePath;
}

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
    lane: "",
    topic: "",
    trivial: false,
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
      case "--lane":
        out.lane = String(argv[++i] || "").trim();
        break;
      case "--topic":
        out.topic = String(argv[++i] || "").trim();
        break;
      case "--trivial":
        out.trivial = true;
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

  options.branch = options.branch || safeBranch();
  options.worktree = normalizePath(options.worktree || ROOT);
  const worktreeContext = readWorktreeContext(options.worktree);
  const laneInfo = inferLaneInfo(options, options.branch, options.worktree, worktreeContext);
  const nonTrivial = !options.trivial;
  if (nonTrivial && !laneInfo.lane) {
    throw new Error("non-trivial closeout requires traceable lane metadata: pass --lane or use a bootstrapped worktree");
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
      HARNESS_CLOSEOUT_CONTEXT: "true",
      HARNESS_TRACE_TRIVIAL: options.trivial ? "true" : "false",
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
      HARNESS_CLOSEOUT_CONTEXT: "true",
      HARNESS_TRACE_TRIVIAL: options.trivial ? "true" : "false",
      HARNESS_GOVERNANCE_REPORTS: JSON.stringify(governanceReports),
    });
    trace = { kind: "failure", id: result.stdout };
  }

  let critic = null;
  let criticWriteBackApplied = false;
  if (options.critic || options.status === "failed") {
    critic = maybeRunCritic(options.days, false);
    if (options.criticWriteBack || shouldAutoCriticWriteBack(options.status, critic)) {
      critic = maybeRunCritic(options.days, true);
      criticWriteBackApplied = true;
    }
  }

  const closeoutId = nextCloseoutId();
  const closeoutPayload = {
    id: closeoutId,
    timestamp: new Date().toISOString(),
    status: options.status,
    nonTrivial,
    message: options.message,
    trace,
    critic,
    criticWriteBackApplied,
    governance,
    governanceReports,
    context: {
      agent: options.agent,
      branch: options.branch,
      worktree: options.worktree,
      lane: laneInfo.lane,
      laneSource: laneInfo.source,
      topic: laneInfo.topic,
      worktreeContextPath: worktreeContext ? worktreeContext._contextPath : "",
      steps: options.steps ? options.steps.split(",").map((item) => item.trim()).filter(Boolean) : [],
      type: options.type,
      file: options.file,
      stage: options.stage,
      command: options.command,
      fatal: options.fatal,
    },
  };
  const closeoutFile = writeCloseoutArtifact(closeoutPayload);

  const payload = {
    status: options.status,
    trace,
    critic,
    criticWriteBackApplied,
    governance,
    governanceReports,
    closeout: {
      id: closeoutId,
      file: path.relative(ROOT, closeoutFile),
      lane: laneInfo.lane,
      laneSource: laneInfo.source,
      topic: laneInfo.topic,
    },
  };

  if (options.json) {
    process.stdout.write(JSON.stringify(payload, null, 2) + "\n");
    return;
  }

  process.stdout.write(`trace: ${trace.kind}:${trace.id}\n`);
  process.stdout.write(`closeout: ${closeoutId}\n`);
  if (critic) {
    process.stdout.write(`critic: ok${criticWriteBackApplied ? " (write-back)" : ""}\n`);
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
