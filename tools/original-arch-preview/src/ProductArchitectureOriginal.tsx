import { useEffect, useRef, useState } from "react";

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

const nodes: Node[] = [
  // Top: User Inputs
  { id: "chat", x: 60, y: 30, w: 130, h: 50, label: "Chat / NL Input", sublabel: "自然语言捕获", color: COLORS.purple, icon: "💬" },
  { id: "manual", x: 210, y: 30, w: 120, h: 50, label: "Manual Input", sublabel: "手动录入", color: COLORS.purple, icon: "✏️" },
  { id: "meeting", x: 345, y: 30, w: 120, h: 50, label: "Meeting Notes", sublabel: "会议纪要", color: COLORS.purple, icon: "📋" },
  { id: "agent", x: 480, y: 30, w: 130, h: 50, label: "External Agent", sublabel: "外部 Agent", color: COLORS.orange, icon: "🤖" },

  // Candidate Layer
  { id: "inbox", x: 160, y: 130, w: 150, h: 55, label: "Inbox Service", sublabel: "候选池收集", color: COLORS.blue, glow: COLORS.blue, icon: "📥" },
  { id: "classify", x: 330, y: 130, w: 150, h: 55, label: "Classification", sublabel: "语义分类引擎", color: COLORS.blue, icon: "🔍" },

  // Clarification
  { id: "clarify", x: 240, y: 235, w: 180, h: 55, label: "Clarification Loop", sublabel: "Candidate → Confirmed", color: COLORS.cyan, glow: COLORS.cyan, icon: "🔄" },

  // WriteGate
  { id: "writegate", x: 195, y: 340, w: 270, h: 60, label: "WriteGate™ Governance", sublabel: "Policy · Validation · Provenance · Confirmation", color: COLORS.pink, glow: COLORS.pink, icon: "🛡️" },

  // Core Truth Domain
  { id: "truth", x: 155, y: 455, w: 180, h: 65, label: "Canonical Truth", sublabel: "Commitment Objects", color: COLORS.green, glow: COLORS.green, icon: "💎" },
  { id: "review", x: 345, y: 455, w: 160, h: 65, label: "Review Sessions", sublabel: "Weekly GTD Review", color: COLORS.green, icon: "📊" },

  // Memory Architecture
  { id: "memory", x: 560, y: 235, w: 155, h: 55, label: "9-Layer Memory", sublabel: "FM-L1 ~ FM-L9", color: COLORS.yellow, glow: COLORS.yellow, icon: "🧠" },
  { id: "trust", x: 560, y: 340, w: 155, h: 55, label: "Trust Score", sublabel: "FM-L8 可靠性评分", color: COLORS.yellow, icon: "⭐" },

  // Storage
  { id: "sqlite", x: 60, y: 565, w: 135, h: 50, label: "SQLite / PG", sublabel: "Canonical Store", color: COLORS.textDim, icon: "🗄️" },
  { id: "vector", x: 210, y: 565, w: 135, h: 50, label: "Qdrant Vector", sublabel: "Semantic Store", color: COLORS.textDim, icon: "🔢" },
  { id: "files", x: 355, y: 565, w: 135, h: 50, label: "File System", sublabel: "Memory Substrate", color: COLORS.textDim, icon: "📁" },

  // UI / Consumer
  { id: "webui", x: 560, y: 130, w: 155, h: 55, label: "Web UI", sublabel: "React 18 + Vite", color: COLORS.purple, icon: "🖥️" },
  { id: "provenance", x: 510, y: 455, w: 155, h: 65, label: "Provenance", sublabel: "Audit Trail FM-L9", color: COLORS.orange, icon: "🔎" },
];

const edges: Edge[] = [
  // inputs → inbox
  { from: "chat", to: "inbox", color: COLORS.purple, animated: true },
  { from: "manual", to: "inbox", color: COLORS.purple, animated: true },
  { from: "meeting", to: "inbox", color: COLORS.purple, animated: true },
  { from: "agent", to: "classify", color: COLORS.orange, animated: true },

  // inbox → classify
  { from: "inbox", to: "classify", color: COLORS.blue, animated: true },

  // classify → clarify
  { from: "classify", to: "clarify", color: COLORS.cyan, animated: true },
  { from: "inbox", to: "clarify", color: COLORS.cyan },

  // clarify → writegate
  { from: "clarify", to: "writegate", color: COLORS.pink, animated: true },

  // writegate → truth
  { from: "writegate", to: "truth", color: COLORS.green, animated: true },
  { from: "writegate", to: "review", color: COLORS.green, animated: true },

  // truth ↔ review
  { from: "truth", to: "review", color: COLORS.green, bidirectional: true },

  // truth → storage
  { from: "truth", to: "sqlite", color: COLORS.textDim },
  { from: "truth", to: "vector", color: COLORS.textDim },
  { from: "memory", to: "files", color: COLORS.textDim },

  // truth → trust
  { from: "truth", to: "trust", color: COLORS.yellow, animated: true },

  // memory layer
  { from: "clarify", to: "memory", color: COLORS.yellow, dashed: true },
  { from: "memory", to: "trust", color: COLORS.yellow },

  // provenance
  { from: "writegate", to: "provenance", color: COLORS.orange, dashed: true },
  { from: "truth", to: "provenance", color: COLORS.orange, dashed: true },

  // webui consumes
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
    <circle r="3.5" fill={color}>
      <animateMotion dur={`${duration}s`} repeatCount="indefinite" path={path} />
    </circle>
  );
}

export function ProductArchitecture() {
  const [hovered, setHovered] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setTick((p) => p + 1), 50);
    return () => clearInterval(t);
  }, []);

  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  const SVG_W = 740;
  const SVG_H = 650;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: `radial-gradient(ellipse at 30% 20%, rgba(0,102,255,0.08) 0%, transparent 60%), radial-gradient(ellipse at 80% 80%, rgba(124,58,237,0.08) 0%, transparent 60%), ${COLORS.bg}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        padding: "32px 20px 20px",
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <div style={{ fontSize: 11, letterSpacing: 4, color: COLORS.cyan, textTransform: "uppercase", marginBottom: 8, fontWeight: 600 }}>
          FlowMind Architecture V1
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: COLORS.text, margin: 0, letterSpacing: -0.5 }}>
          Product Architecture
        </h1>
        <p style={{ fontSize: 13, color: COLORS.textDim, marginTop: 6 }}>
          Commitment Control Plane — 承诺治理控制面
        </p>
      </div>

      {/* SVG Diagram */}
      <div style={{ position: "relative", width: SVG_W, maxWidth: "100%" }}>
        <svg
          width={SVG_W}
          height={SVG_H}
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          style={{ overflow: "visible" }}
        >
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

          {/* Background grid */}
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="0.5" />
          </pattern>
          <rect width={SVG_W} height={SVG_H} fill="url(#grid)" rx="16" />

          {/* Section backgrounds */}
          {/* Input zone */}
          <rect x="40" y="15" width="590" height="70" rx="10" fill="rgba(124,58,237,0.06)" stroke="rgba(124,58,237,0.2)" strokeWidth="1" strokeDasharray="4,4" />
          <text x="52" y="12" fontSize="9" fill="rgba(124,58,237,0.6)" letterSpacing="2">INPUT LAYER</text>

          {/* Governance zone */}
          <rect x="155" y="320" width="335" height="100" rx="10" fill="rgba(255,45,120,0.05)" stroke="rgba(255,45,120,0.2)" strokeWidth="1" strokeDasharray="4,4" />
          <text x="165" y="318" fontSize="9" fill="rgba(255,45,120,0.6)" letterSpacing="2">GOVERNANCE LAYER</text>

          {/* Truth zone */}
          <rect x="135" y="437" width="400" height="100" rx="10" fill="rgba(0,255,136,0.05)" stroke="rgba(0,255,136,0.2)" strokeWidth="1" strokeDasharray="4,4" />
          <text x="148" y="434" fontSize="9" fill="rgba(0,255,136,0.6)" letterSpacing="2">CANONICAL TRUTH DOMAIN</text>

          {/* Storage zone */}
          <rect x="40" y="548" width="470" height="70" rx="10" fill="rgba(100,116,139,0.08)" stroke="rgba(100,116,139,0.2)" strokeWidth="1" strokeDasharray="4,4" />
          <text x="52" y="545" fontSize="9" fill="rgba(100,116,139,0.6)" letterSpacing="2">PERSISTENCE LAYER</text>

          {/* Edges */}
          {edges.map((edge, i) => {
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
            return (
              <g key={i}>
                <path
                  d={path}
                  fill="none"
                  stroke={color}
                  strokeWidth={edge.animated ? 1.8 : 1}
                  strokeOpacity={0.4}
                  strokeDasharray={edge.dashed ? "5,4" : undefined}
                  markerEnd={`url(#arrow-${markerColor})`}
                  markerStart={edge.bidirectional ? `url(#arrow-${markerColor})` : undefined}
                />
                {edge.animated && (
                  <AnimatedDot path={path} color={color} duration={1.8 + (i % 5) * 0.4} />
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const isHovered = hovered === node.id;
            const filterMap: Record<string, string> = {
              [COLORS.cyan]: "url(#glow-cyan)",
              [COLORS.green]: "url(#glow-green)",
              [COLORS.pink]: "url(#glow-pink)",
            };
            const glowFilter = node.glow ? filterMap[node.glow] || "none" : "none";

            return (
              <g
                key={node.id}
                onMouseEnter={() => setHovered(node.id)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: "pointer" }}
                filter={isHovered ? glowFilter : "none"}
              >
                {/* Glow aura */}
                {node.glow && (
                  <rect
                    x={node.x - 4}
                    y={node.y - 4}
                    width={node.w + 8}
                    height={node.h + 8}
                    rx="12"
                    fill={node.glow}
                    opacity={0.15}
                  />
                )}
                {/* Card */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={node.w}
                  height={node.h}
                  rx="10"
                  fill={COLORS.panel}
                  stroke={node.color}
                  strokeWidth={isHovered ? 2 : 1.5}
                  opacity={isHovered ? 1 : 0.9}
                />
                {/* Top accent bar */}
                <rect x={node.x + 10} y={node.y} width={node.w - 20} height={2} rx="1" fill={node.color} opacity="0.8" />

                {/* Icon + Label */}
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
                {node.sublabel && (
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
                )}
              </g>
            );
          })}

          {/* Legend */}
          <g transform="translate(555, 548)">
            <rect x="0" y="0" width="160" height="88" rx="8" fill={COLORS.panel} stroke={COLORS.border} strokeWidth="1" />
            <text x="10" y="16" fontSize="8" fill={COLORS.textDim} letterSpacing="2" fontWeight="600">LEGEND</text>
            {[
              { color: COLORS.purple, label: "User Input" },
              { color: COLORS.cyan, label: "Clarification Loop" },
              { color: COLORS.pink, label: "Governance (WriteGate)" },
              { color: COLORS.green, label: "Canonical Truth" },
              { color: COLORS.yellow, label: "Memory / Trust Layer" },
              { color: COLORS.textDim, label: "Persistence" },
            ].map((item, i) => (
              <g key={i} transform={`translate(10, ${26 + i * 11})`}>
                <rect width="10" height="6" rx="2" fill={item.color} y="1" />
                <text x="16" y="8" fontSize="8.5" fill={COLORS.textDim}>{item.label}</text>
              </g>
            ))}
          </g>
        </svg>
      </div>

      {/* Status labels */}
      <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap", justifyContent: "center" }}>
        {[
          { label: "Commitment States", value: "5-Stage Lifecycle", color: COLORS.green },
          { label: "Memory Layers", value: "FM-L1 ~ FM-L9", color: COLORS.yellow },
          { label: "Governance", value: "WriteGate™ Policy", color: COLORS.pink },
          { label: "Storage", value: "SQLite → PostgreSQL", color: COLORS.textDim },
        ].map((item) => (
          <div
            key={item.label}
            style={{
              background: COLORS.panel,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 8,
              padding: "8px 16px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 10, color: COLORS.textDim, marginBottom: 2 }}>{item.label}</div>
            <div style={{ fontSize: 12, fontWeight: 700, color: item.color }}>{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
