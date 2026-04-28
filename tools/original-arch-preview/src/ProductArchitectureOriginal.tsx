import { useEffect, useMemo, useState } from "react";

const COLORS = {
  bg: "#050B18",
  panel: "#0A1628",
  border: "#1A2E50",
  cyan: "#00D4FF",
  blue: "#0066FF",
  purple: "#7C3AED",
  green: "#00FF88",
  orange: "#FF6B35",
  pink: "#FF2D78",
  yellow: "#FFD700",
  text: "#E2E8F0",
  textDim: "#64748B",
  glow: "rgba(0,212,255,0.15)",
};

interface Node {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  sublabel?: string;
  color: string;
  glow?: string;
  icon?: string;
}

interface Edge {
  from: string;
  to: string;
  label?: string;
  color?: string;
  dashed?: boolean;
  animated?: boolean;
  bidirectional?: boolean;
}

interface FlowRecord {
  id: string;
  title: string;
  status: string;
  sourceAgent?: string;
  instanceId?: string;
  sessionId?: string;
  confidence?: number;
  createdAt?: string;
  updatedAt?: string;
  rawText?: string;
  replayMode?: "trace" | "derived";
}

interface DetailItem {
  label: string;
  value: string;
}

interface DetailSection {
  title: string;
  items: DetailItem[];
}

interface ModuleDetail {
  title: string;
  summary: string;
  sections: DetailSection[];
}

interface ReplayStep {
  key: string;
  moduleId: string;
  label: string;
  detail: string;
  timestamp?: string;
  kind: "trace" | "derived";
}

interface ReplayResponse {
  recordId: string;
  mode: "trace" | "derived";
  gaps: string[];
  steps: ReplayStep[];
  moduleDetails: Record<string, ModuleDetail>;
}

const nodes: Node[] = [
  { id: "chat", x: 60, y: 30, w: 130, h: 50, label: "Chat / NL Input", sublabel: "自然语言捕获", color: COLORS.purple, icon: "💬" },
  { id: "manual", x: 210, y: 30, w: 120, h: 50, label: "Manual Input", sublabel: "手动录入", color: COLORS.purple, icon: "✏️" },
  { id: "meeting", x: 345, y: 30, w: 120, h: 50, label: "Meeting Notes", sublabel: "会议纪要", color: COLORS.purple, icon: "📋" },
  { id: "agent", x: 480, y: 30, w: 130, h: 50, label: "External Agent", sublabel: "外部 Agent", color: COLORS.orange, icon: "🤖" },
  { id: "inbox", x: 160, y: 130, w: 150, h: 55, label: "Inbox Service", sublabel: "候选池收集", color: COLORS.blue, glow: COLORS.blue, icon: "📥" },
  { id: "classify", x: 330, y: 130, w: 150, h: 55, label: "Classification", sublabel: "语义分类引擎", color: COLORS.blue, icon: "🔍" },
  { id: "clarify", x: 240, y: 235, w: 180, h: 55, label: "Clarification Loop", sublabel: "Candidate → Confirmed", color: COLORS.cyan, glow: COLORS.cyan, icon: "🔄" },
  { id: "writegate", x: 195, y: 340, w: 270, h: 60, label: "WriteGate™ Governance", sublabel: "Policy · Validation · Provenance · Confirmation", color: COLORS.pink, glow: COLORS.pink, icon: "🛡️" },
  { id: "truth", x: 155, y: 455, w: 180, h: 65, label: "Canonical Truth", sublabel: "Commitment Objects", color: COLORS.green, glow: COLORS.green, icon: "💎" },
  { id: "review", x: 345, y: 455, w: 160, h: 65, label: "Review Sessions", sublabel: "Weekly GTD Review", color: COLORS.green, icon: "📊" },
  { id: "memory", x: 560, y: 235, w: 155, h: 55, label: "9-Layer Memory", sublabel: "FM-L1 ~ FM-L9", color: COLORS.yellow, glow: COLORS.yellow, icon: "🧠" },
  { id: "trust", x: 560, y: 340, w: 155, h: 55, label: "Trust Score", sublabel: "FM-L8 可靠性评分", color: COLORS.yellow, icon: "⭐" },
  { id: "sqlite", x: 60, y: 565, w: 135, h: 50, label: "SQLite / PG", sublabel: "Canonical Store", color: COLORS.textDim, icon: "🗄️" },
  { id: "vector", x: 210, y: 565, w: 135, h: 50, label: "Qdrant Vector", sublabel: "Semantic Store", color: COLORS.textDim, icon: "🔢" },
  { id: "files", x: 355, y: 565, w: 135, h: 50, label: "File System", sublabel: "Memory Substrate", color: COLORS.textDim, icon: "📁" },
  { id: "webui", x: 560, y: 130, w: 155, h: 55, label: "Web UI", sublabel: "React 18 + Vite", color: COLORS.purple, icon: "🖥️" },
  { id: "provenance", x: 510, y: 455, w: 155, h: 65, label: "Provenance", sublabel: "Audit Trail FM-L9", color: COLORS.orange, icon: "🔎" },
];

const edges: Edge[] = [
  { from: "chat", to: "inbox", color: COLORS.purple, animated: true },
  { from: "manual", to: "inbox", color: COLORS.purple, animated: true },
  { from: "meeting", to: "inbox", color: COLORS.purple, animated: true },
  { from: "agent", to: "classify", color: COLORS.orange, animated: true },
  { from: "inbox", to: "classify", color: COLORS.blue, animated: true },
  { from: "classify", to: "clarify", color: COLORS.cyan, animated: true },
  { from: "inbox", to: "clarify", color: COLORS.cyan },
  { from: "clarify", to: "writegate", color: COLORS.pink, animated: true },
  { from: "writegate", to: "truth", color: COLORS.green, animated: true },
  { from: "writegate", to: "review", color: COLORS.green, animated: true },
  { from: "truth", to: "review", color: COLORS.green, bidirectional: true },
  { from: "truth", to: "sqlite", color: COLORS.textDim },
  { from: "truth", to: "vector", color: COLORS.textDim },
  { from: "memory", to: "files", color: COLORS.textDim },
  { from: "truth", to: "trust", color: COLORS.yellow, animated: true },
  { from: "clarify", to: "memory", color: COLORS.yellow, dashed: true },
  { from: "memory", to: "trust", color: COLORS.yellow },
  { from: "writegate", to: "provenance", color: COLORS.orange, dashed: true },
  { from: "truth", to: "provenance", color: COLORS.orange, dashed: true },
  { from: "webui", to: "truth", color: COLORS.cyan, dashed: true, bidirectional: true },
  { from: "webui", to: "review", color: COLORS.cyan, dashed: true },
  { from: "webui", to: "provenance", color: COLORS.cyan, dashed: true },
];

function getNodeCenter(node: Node) {
  return { x: node.x + node.w / 2, y: node.y + node.h / 2 };
}

function getEdgePath(fromNode: Node, toNode: Node): string {
  const from = getNodeCenter(fromNode);
  const to = getNodeCenter(toNode);
  const mx = (from.x + to.x) / 2;
  const my = (from.y + to.y) / 2;
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const curve = Math.min(Math.abs(dy) * 0.3, 60);
  const cpx = mx + (Math.abs(dx) > 80 ? 0 : curve * (dx > 0 ? 1 : -1));
  const cpy = my;
  return `M ${from.x} ${from.y} Q ${cpx} ${cpy} ${to.x} ${to.y}`;
}

function AnimatedDot({ path, color, duration }: { path: string; color: string; duration: number }) {
  return (
    <circle r="4" fill={color}>
      <animateMotion dur={`${duration}s`} repeatCount="1" path={path} />
    </circle>
  );
}

function getApiBase() {
  const path = window.location.pathname;
  return path.indexOf("/manage/") === 0 ? "/manage" : "";
}

function fetchJson<T>(path: string): Promise<T> {
  return fetch(`${getApiBase()}${path}`).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json() as Promise<T>;
  });
}

function formatTime(value?: string) {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatRelativeTime(value?: string) {
  if (!value) return "无时间";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const diff = Date.now() - date.getTime();
  const minutes = Math.round(diff / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes} 分钟前`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} 小时前`;
  const days = Math.round(hours / 24);
  return `${days} 天前`;
}

function statusColor(status: string) {
  switch (status) {
    case "approved":
    case "committed":
      return COLORS.green;
    case "rejected":
      return COLORS.orange;
    case "submitted":
      return COLORS.cyan;
    default:
      return COLORS.blue;
  }
}

function buildTransitionKey(from: string, to: string) {
  return `${from}->${to}`;
}

export function ProductArchitecture() {
  const [hovered, setHovered] = useState<string | null>(null);
  const [records, setRecords] = useState<FlowRecord[]>([]);
  const [recordsError, setRecordsError] = useState<string | null>(null);
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null);
  const [replay, setReplay] = useState<ReplayResponse | null>(null);
  const [replayError, setReplayError] = useState<string | null>(null);
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null);
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  useEffect(() => {
    let alive = true;
    fetchJson<{ records: FlowRecord[] }>("/api/flowmind/records")
      .then((data) => {
        if (!alive) return;
        const items = data.records || [];
        setRecords(items);
        setSelectedRecordId((current) => current || items[0]?.id || null);
      })
      .catch((error) => {
        if (!alive) return;
        setRecordsError(error instanceof Error ? error.message : "记录加载失败");
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedRecordId) return;
    let alive = true;
    setReplay(null);
    setReplayError(null);
    setActiveStepIndex(0);
    fetchJson<ReplayResponse>(`/api/flowmind/records/${selectedRecordId}/replay`)
      .then((data) => {
        if (!alive) return;
        setReplay(data);
        const firstModule = data.steps[0]?.moduleId || "agent";
        setSelectedModuleId(firstModule);
      })
      .catch((error) => {
        if (!alive) return;
        setReplayError(error instanceof Error ? error.message : "流程回放加载失败");
      });
    return () => {
      alive = false;
    };
  }, [selectedRecordId]);

  useEffect(() => {
    if (!replay || replay.steps.length <= 1) return;
    const timer = window.setInterval(() => {
      setActiveStepIndex((current) => {
        const next = current + 1;
        return next >= replay.steps.length ? 0 : next;
      });
    }, 1800);
    return () => window.clearInterval(timer);
  }, [replay]);

  const nodeMap = useMemo(() => Object.fromEntries(nodes.map((node) => [node.id, node])), []);
  const selectedRecord = records.find((item) => item.id === selectedRecordId) || null;
  const replaySteps = replay?.steps || [];
  const currentStep = replaySteps[activeStepIndex] || null;
  const currentModuleId = currentStep?.moduleId || selectedModuleId;
  const detailModuleId = selectedModuleId || currentModuleId || "agent";

  const completedModuleIds = useMemo(() => {
    const result = new Set<string>();
    replaySteps.slice(0, activeStepIndex + 1).forEach((step) => result.add(step.moduleId));
    return result;
  }, [activeStepIndex, replaySteps]);

  const transitionKeys = useMemo(() => {
    const result = new Set<string>();
    for (let i = 1; i <= activeStepIndex && i < replaySteps.length; i += 1) {
      const previous = replaySteps[i - 1];
      const current = replaySteps[i];
      result.add(buildTransitionKey(previous.moduleId, current.moduleId));
    }
    return result;
  }, [activeStepIndex, replaySteps]);

  const detail = replay?.moduleDetails[detailModuleId];
  const SVG_W = 740;
  const SVG_H = 650;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: `radial-gradient(ellipse at 30% 20%, rgba(0,102,255,0.08) 0%, transparent 60%), radial-gradient(ellipse at 80% 80%, rgba(124,58,237,0.08) 0%, transparent 60%), ${COLORS.bg}`,
        color: COLORS.text,
        fontFamily: "'Inter', -apple-system, sans-serif",
        padding: "24px 20px 20px",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <div style={{ fontSize: 11, letterSpacing: 4, color: COLORS.cyan, textTransform: "uppercase", marginBottom: 8, fontWeight: 600 }}>
          FlowMind Architecture V1
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: COLORS.text, margin: 0, letterSpacing: -0.5 }}>
          Product Architecture
        </h1>
        <p style={{ fontSize: 13, color: COLORS.textDim, marginTop: 6 }}>
          以 HermesAgent 发送到 FlowMind 的真实记录为驱动，展示记录进入治理控制面的实际处理路径
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "280px minmax(760px, 1fr) 300px",
          gap: 18,
          alignItems: "start",
          maxWidth: 1400,
          margin: "0 auto",
        }}
      >
        <aside
          style={{
            background: "rgba(10,22,40,0.94)",
            border: `1px solid ${COLORS.border}`,
            borderRadius: 16,
            padding: 16,
            minHeight: 760,
            boxShadow: "0 20px 60px rgba(2,6,23,0.28)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <div>
              <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", color: COLORS.orange }}>Hermes → FlowMind</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>记录列表</div>
            </div>
            <div style={{ fontSize: 12, color: COLORS.textDim }}>{records.length} 条</div>
          </div>

          {recordsError ? (
            <div style={{ padding: 14, borderRadius: 12, background: "rgba(255,107,53,0.12)", color: "#fed7aa", fontSize: 13 }}>
              {recordsError}
            </div>
          ) : null}

          {!recordsError && records.length === 0 ? (
            <div style={{ padding: 14, borderRadius: 12, background: "rgba(255,255,255,0.03)", color: COLORS.textDim, fontSize: 13 }}>
              当前还没有可供回放的 HermesAgent 记录。
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 10 }}>
            {records.map((record) => {
              const selected = record.id === selectedRecordId;
              const accent = statusColor(record.status);
              return (
                <button
                  key={record.id}
                  type="button"
                  onClick={() => setSelectedRecordId(record.id)}
                  style={{
                    textAlign: "left",
                    width: "100%",
                    borderRadius: 14,
                    border: `1px solid ${selected ? accent : "rgba(26,46,80,0.9)"}`,
                    background: selected ? "rgba(0,212,255,0.08)" : "rgba(255,255,255,0.02)",
                    padding: "12px 12px 11px",
                    color: COLORS.text,
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, lineHeight: 1.4 }}>{record.title || "未命名记录"}</div>
                    <span
                      style={{
                        fontSize: 10,
                        color: accent,
                        border: `1px solid ${accent}`,
                        borderRadius: 999,
                        padding: "2px 8px",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {record.status}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: COLORS.textDim, marginBottom: 8 }}>
                    {record.sourceAgent || "unknown"} · {formatRelativeTime(record.createdAt)}
                  </div>
                  <div style={{ fontSize: 11, color: "#cbd5e1", lineHeight: 1.5 }}>
                    会话 {record.sessionId ? record.sessionId.slice(0, 8) : "--"} · 置信度 {record.confidence ?? "--"}
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        <main
          style={{
            background: "rgba(5,11,24,0.72)",
            border: `1px solid ${COLORS.border}`,
            borderRadius: 18,
            padding: 18,
            minHeight: 760,
            boxShadow: "0 20px 60px rgba(2,6,23,0.28)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12, color: COLORS.textDim, textTransform: "uppercase", letterSpacing: 2 }}>Selected Record</div>
              <div style={{ fontSize: 19, fontWeight: 700, marginTop: 4 }}>{selectedRecord?.title || "等待选择记录"}</div>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
              <span style={{ fontSize: 11, color: COLORS.textDim, border: `1px solid ${COLORS.border}`, borderRadius: 999, padding: "5px 10px" }}>
                回放模式 {replay?.mode || "--"}
              </span>
              <span style={{ fontSize: 11, color: COLORS.textDim, border: `1px solid ${COLORS.border}`, borderRadius: 999, padding: "5px 10px" }}>
                当前阶段 {currentStep ? activeStepIndex + 1 : 0}/{replaySteps.length}
              </span>
            </div>
          </div>

          {replayError ? (
            <div style={{ marginBottom: 14, padding: 14, borderRadius: 12, background: "rgba(255,107,53,0.12)", color: "#fed7aa", fontSize: 13 }}>
              {replayError}
            </div>
          ) : null}

          {replay?.gaps?.length ? (
            <div style={{ marginBottom: 14, padding: 14, borderRadius: 12, background: "rgba(255,215,0,0.12)", color: "#fef08a", fontSize: 13, lineHeight: 1.6 }}>
              {replay.gaps.join("；")}
            </div>
          ) : null}

          <div style={{ position: "relative", width: SVG_W, maxWidth: "100%", margin: "0 auto" }}>
            <svg width={SVG_W} height={SVG_H} viewBox={`0 0 ${SVG_W} ${SVG_H}`} style={{ overflow: "visible" }}>
              <defs>
                <filter id="glow-cyan">
                  <feGaussianBlur stdDeviation="4" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
                <filter id="glow-green">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
                <filter id="glow-pink">
                  <feGaussianBlur stdDeviation="6" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
                <marker id="arrow-cyan" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.cyan} opacity="0.8" />
                </marker>
                <marker id="arrow-green" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.green} opacity="0.8" />
                </marker>
                <marker id="arrow-pink" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.pink} opacity="0.9" />
                </marker>
                <marker id="arrow-purple" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.purple} opacity="0.8" />
                </marker>
                <marker id="arrow-orange" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.orange} opacity="0.8" />
                </marker>
                <marker id="arrow-yellow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.yellow} opacity="0.8" />
                </marker>
                <marker id="arrow-dim" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                  <path d="M0,0 L6,3 L0,6 Z" fill={COLORS.textDim} opacity="0.6" />
                </marker>
              </defs>

              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="0.5" />
              </pattern>
              <rect width={SVG_W} height={SVG_H} fill="url(#grid)" rx="16" />

              <rect x="40" y="15" width="590" height="70" rx="10" fill="rgba(124,58,237,0.06)" stroke="rgba(124,58,237,0.2)" strokeWidth="1" strokeDasharray="4,4" />
              <text x="52" y="12" fontSize="9" fill="rgba(124,58,237,0.6)" letterSpacing="2">INPUT LAYER</text>
              <rect x="155" y="320" width="335" height="100" rx="10" fill="rgba(255,45,120,0.05)" stroke="rgba(255,45,120,0.2)" strokeWidth="1" strokeDasharray="4,4" />
              <text x="165" y="318" fontSize="9" fill="rgba(255,45,120,0.6)" letterSpacing="2">GOVERNANCE LAYER</text>
              <rect x="135" y="437" width="400" height="100" rx="10" fill="rgba(0,255,136,0.05)" stroke="rgba(0,255,136,0.2)" strokeWidth="1" strokeDasharray="4,4" />
              <text x="148" y="434" fontSize="9" fill="rgba(0,255,136,0.6)" letterSpacing="2">CANONICAL TRUTH DOMAIN</text>
              <rect x="40" y="548" width="470" height="70" rx="10" fill="rgba(100,116,139,0.08)" stroke="rgba(100,116,139,0.2)" strokeWidth="1" strokeDasharray="4,4" />
              <text x="52" y="545" fontSize="9" fill="rgba(100,116,139,0.6)" letterSpacing="2">PERSISTENCE LAYER</text>

              {edges.map((edge, index) => {
                const fromNode = nodeMap[edge.from];
                const toNode = nodeMap[edge.to];
                if (!fromNode || !toNode) return null;
                const path = getEdgePath(fromNode, toNode);
                const color = edge.color || COLORS.cyan;
                const markerColor = color === COLORS.green ? "green"
                  : color === COLORS.pink ? "pink"
                    : color === COLORS.purple ? "purple"
                      : color === COLORS.orange ? "orange"
                        : color === COLORS.yellow ? "yellow"
                          : color === COLORS.textDim ? "dim"
                            : "cyan";
                const isTransition = transitionKeys.has(buildTransitionKey(edge.from, edge.to));
                const isReverseTransition = transitionKeys.has(buildTransitionKey(edge.to, edge.from));
                const highlighted = isTransition || isReverseTransition;
                return (
                  <g key={`${edge.from}-${edge.to}-${index}`}>
                    <path
                      d={path}
                      fill="none"
                      stroke={color}
                      strokeWidth={highlighted ? 2.6 : edge.animated ? 1.8 : 1}
                      strokeOpacity={highlighted ? 0.95 : 0.25}
                      strokeDasharray={edge.dashed ? "5,4" : undefined}
                      markerEnd={`url(#arrow-${markerColor})`}
                      markerStart={edge.bidirectional ? `url(#arrow-${markerColor})` : undefined}
                    />
                    {highlighted ? (
                      <AnimatedDot path={path} color={color} duration={1.4 + (index % 4) * 0.25} />
                    ) : null}
                  </g>
                );
              })}

              {nodes.map((node) => {
                const isHovered = hovered === node.id;
                const isCompleted = completedModuleIds.has(node.id);
                const isCurrent = currentModuleId === node.id;
                const isSelected = detailModuleId === node.id;
                const filterMap: Record<string, string> = {
                  [COLORS.cyan]: "url(#glow-cyan)",
                  [COLORS.green]: "url(#glow-green)",
                  [COLORS.pink]: "url(#glow-pink)",
                };
                const glowFilter = node.glow ? filterMap[node.glow] || "none" : "none";
                const strokeWidth = isCurrent ? 3 : isSelected ? 2.3 : isHovered ? 2 : 1.5;
                const opacity = isCompleted || isCurrent || isSelected ? 1 : 0.88;
                const fill = isCurrent ? "rgba(255,255,255,0.06)" : COLORS.panel;

                return (
                  <g
                    key={node.id}
                    onMouseEnter={() => setHovered(node.id)}
                    onMouseLeave={() => setHovered(null)}
                    onClick={() => setSelectedModuleId(node.id)}
                    style={{ cursor: "pointer" }}
                    filter={isHovered || isCurrent ? glowFilter : "none"}
                  >
                    {(isCompleted || isCurrent) && node.glow ? (
                      <rect
                        x={node.x - 4}
                        y={node.y - 4}
                        width={node.w + 8}
                        height={node.h + 8}
                        rx="12"
                        fill={node.glow}
                        opacity={isCurrent ? 0.22 : 0.14}
                      />
                    ) : null}
                    <rect
                      x={node.x}
                      y={node.y}
                      width={node.w}
                      height={node.h}
                      rx="10"
                      fill={fill}
                      stroke={node.color}
                      strokeWidth={strokeWidth}
                      opacity={opacity}
                    />
                    <rect x={node.x + 10} y={node.y} width={node.w - 20} height={2} rx="1" fill={node.color} opacity="0.86" />
                    <text
                      x={node.x + node.w / 2}
                      y={node.y + (node.sublabel ? 18 : 22)}
                      textAnchor="middle"
                      fontSize="9.5"
                      fontWeight="700"
                      fill={node.color}
                      letterSpacing="0.5"
                    >
                      {node.icon} {node.label}
                    </text>
                    {node.sublabel ? (
                      <text
                        x={node.x + node.w / 2}
                        y={node.y + 33}
                        textAnchor="middle"
                        fontSize="8"
                        fill={COLORS.textDim}
                        letterSpacing="0.3"
                      >
                        {node.sublabel}
                      </text>
                    ) : null}
                  </g>
                );
              })}

              <g transform="translate(555, 548)">
                <rect x="0" y="0" width="160" height="88" rx="8" fill={COLORS.panel} stroke={COLORS.border} strokeWidth="1" />
                <text x="10" y="16" fontSize="8" fill={COLORS.textDim} letterSpacing="2" fontWeight="600">LEGEND</text>
                {[
                  { color: COLORS.orange, label: "HermesAgent Ingress" },
                  { color: COLORS.blue, label: "Candidate Intake" },
                  { color: COLORS.cyan, label: "Clarification Loop" },
                  { color: COLORS.pink, label: "Governance (WriteGate)" },
                  { color: COLORS.green, label: "Canonical Truth" },
                  { color: COLORS.yellow, label: "Memory / Trust Layer" },
                ].map((item, index) => (
                  <g key={item.label} transform={`translate(10, ${26 + index * 11})`}>
                    <rect width="10" height="6" rx="2" fill={item.color} y="1" />
                    <text x="16" y="8" fontSize="8.5" fill={COLORS.textDim}>{item.label}</text>
                  </g>
                ))}
              </g>
            </svg>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 14, marginTop: 16 }}>
            <div style={{ borderRadius: 12, border: `1px solid ${COLORS.border}`, background: "rgba(10,22,40,0.78)", padding: 14 }}>
              <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 2, color: COLORS.textDim, marginBottom: 10 }}>Replay Timeline</div>
              <div style={{ display: "grid", gap: 10 }}>
                {replaySteps.length === 0 ? (
                  <div style={{ fontSize: 13, color: COLORS.textDim }}>等待回放数据。</div>
                ) : replaySteps.map((step, index) => {
                  const active = index === activeStepIndex;
                  const done = index < activeStepIndex;
                  const color = nodeMap[step.moduleId]?.color || COLORS.cyan;
                  return (
                    <button
                      key={step.key}
                      type="button"
                      onClick={() => {
                        setActiveStepIndex(index);
                        setSelectedModuleId(step.moduleId);
                      }}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "16px 1fr",
                        gap: 12,
                        alignItems: "start",
                        textAlign: "left",
                        padding: "10px 10px 10px 8px",
                        borderRadius: 12,
                        border: `1px solid ${active ? color : "rgba(26,46,80,0.9)"}`,
                        background: active ? "rgba(255,255,255,0.04)" : "transparent",
                        color: COLORS.text,
                        cursor: "pointer",
                      }}
                    >
                      <div
                        style={{
                          width: 10,
                          height: 10,
                          borderRadius: 999,
                          background: color,
                          marginTop: 5,
                          boxShadow: active ? `0 0 14px ${color}` : "none",
                          opacity: done || active ? 1 : 0.42,
                        }}
                      />
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 700 }}>{step.label}</div>
                        <div style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.6, marginTop: 4 }}>{step.detail}</div>
                        <div style={{ fontSize: 11, color: COLORS.textDim, marginTop: 6 }}>
                          {formatTime(step.timestamp)} · {step.kind === "trace" ? "真实 trace" : "基于真实状态推导"}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div style={{ borderRadius: 12, border: `1px solid ${COLORS.border}`, background: "rgba(10,22,40,0.78)", padding: 14 }}>
              <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 2, color: COLORS.textDim, marginBottom: 10 }}>Record Snapshot</div>
              {selectedRecord ? (
                <div style={{ display: "grid", gap: 8, fontSize: 12 }}>
                  <div><span style={{ color: COLORS.textDim }}>记录 ID</span><div style={{ marginTop: 2 }}>{selectedRecord.id}</div></div>
                  <div><span style={{ color: COLORS.textDim }}>来源</span><div style={{ marginTop: 2 }}>{selectedRecord.sourceAgent || "--"} / {selectedRecord.instanceId || "--"}</div></div>
                  <div><span style={{ color: COLORS.textDim }}>会话</span><div style={{ marginTop: 2 }}>{selectedRecord.sessionId || "--"}</div></div>
                  <div><span style={{ color: COLORS.textDim }}>创建</span><div style={{ marginTop: 2 }}>{formatTime(selectedRecord.createdAt)}</div></div>
                  <div><span style={{ color: COLORS.textDim }}>状态</span><div style={{ marginTop: 2 }}>{selectedRecord.status}</div></div>
                </div>
              ) : (
                <div style={{ fontSize: 13, color: COLORS.textDim }}>暂无选中记录。</div>
              )}
            </div>
          </div>
        </main>

        <aside
          style={{
            background: "rgba(10,22,40,0.94)",
            border: `1px solid ${COLORS.border}`,
            borderRadius: 16,
            padding: 16,
            minHeight: 760,
            boxShadow: "0 20px 60px rgba(2,6,23,0.28)",
          }}
        >
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", color: COLORS.cyan }}>Module Detail</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>{detail?.title || "选择模块"}</div>
          </div>

          <div style={{ fontSize: 13, color: "#cbd5e1", lineHeight: 1.7, marginBottom: 14 }}>
            {detail?.summary || "点击中间架构图中的任意模块，查看当前选中记录在该模块里的具体处理细节。"}
          </div>

          {detail?.sections?.length ? (
            <div style={{ display: "grid", gap: 12 }}>
              {detail.sections.map((section) => (
                <div key={section.title} style={{ borderRadius: 12, border: `1px solid ${COLORS.border}`, background: "rgba(255,255,255,0.02)", padding: 12 }}>
                  <div style={{ fontSize: 12, color: COLORS.textDim, textTransform: "uppercase", letterSpacing: 1.6, marginBottom: 8 }}>
                    {section.title}
                  </div>
                  <div style={{ display: "grid", gap: 8 }}>
                    {section.items.map((item) => (
                      <div key={`${section.title}-${item.label}`} style={{ display: "grid", gap: 4 }}>
                        <div style={{ fontSize: 11, color: COLORS.textDim }}>{item.label}</div>
                        <div style={{ fontSize: 12, color: COLORS.text, lineHeight: 1.5, wordBreak: "break-word" }}>{item.value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}
