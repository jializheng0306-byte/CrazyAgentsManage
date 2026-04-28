import { useEffect, useState } from "react";

const C = {
  bg: "#030A14",
  panel: "#071220",
  panelLight: "#0D1F38",
  border: "#152840",
  cyan: "#00E5FF",
  blue: "#2979FF",
  purple: "#AA00FF",
  green: "#00E676",
  orange: "#FF6D00",
  pink: "#F50057",
  teal: "#1DE9B6",
  yellow: "#FFD600",
  text: "#E3F2FD",
  dim: "#546E7A",
  dim2: "#37474F",
};

interface TechNode {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  label: string;
  tag?: string;
  color: string;
  icon?: string;
  badges?: string[];
}

interface TechEdge {
  from: string;
  to: string;
  color: string;
  label?: string;
  animated?: boolean;
  dashed?: boolean;
  thickness?: number;
}

const techNodes: TechNode[] = [
  // Layer 0 — Client Surfaces
  { id: "web", x: 30, y: 30, w: 140, h: 60, label: "Web UI", tag: "React 18 + Vite", color: C.purple, icon: "⚛️", badges: ["TypeScript", "Tailwind"] },
  { id: "cli", x: 185, y: 30, w: 110, h: 60, label: "CLI", tag: "Future Surface", color: C.dim, icon: "⌨️" },
  { id: "mobile", x: 310, y: 30, w: 130, h: 60, label: "Mobile", tag: "M4+ Next.js", color: C.dim, icon: "📱" },

  // External
  { id: "external_rt", x: 460, y: 30, w: 155, h: 60, label: "External Runtime", tag: "Claude Code / MCP", color: C.orange, icon: "🤖", badges: ["Bridge API"] },

  // Layer 1 — API Gateway
  { id: "express", x: 60, y: 145, w: 260, h: 55, label: "Express.js API Server", tag: "Node.js 22 · TypeScript strict", color: C.blue, icon: "🚀", badges: ["M4→Next.js"] },

  // Command / Query split
  { id: "cmd_surface", x: 30, y: 250, w: 165, h: 55, label: "Command Surface", tag: "POST /api/commands/", color: C.pink, icon: "⚡" },
  { id: "qry_surface", x: 210, y: 250, w: 160, h: 55, label: "Query Surface", tag: "GET /api/commitments/", color: C.teal, icon: "🔍" },

  // Bridge surface
  { id: "bridge_surface", x: 390, y: 145, w: 230, h: 55, label: "Integration Bridge Layer", tag: "4-Type Bridge Protocol", color: C.orange, icon: "🌉" },

  // Bridge types
  { id: "b1", x: 390, y: 250, w: 105, h: 48, label: "Bridge 1", tag: "Candidate Ingress", color: C.orange, icon: "📨" },
  { id: "b2", x: 502, y: 250, w: 105, h: 48, label: "Bridge 2", tag: "Truth Query", color: C.teal, icon: "🔎" },
  { id: "b3", x: 390, y: 307, w: 105, h: 48, label: "Bridge 3", tag: "Context Pack", color: C.yellow, icon: "📦" },
  { id: "b4", x: 502, y: 307, w: 105, h: 48, label: "Bridge 4", tag: "Truth Feedback", color: C.pink, icon: "🔔" },

  // WriteGate
  { id: "writegate", x: 30, y: 360, w: 340, h: 58, label: "WriteGate™ Governance Engine", tag: "Policy → Validation → Provenance → Confirmation", color: C.pink, icon: "🛡️" },

  // Domain Services
  { id: "inbox_svc", x: 30, y: 478, w: 110, h: 52, label: "InboxService", tag: "Capture", color: C.blue, icon: "📥" },
  { id: "clarify_svc", x: 148, y: 478, w: 110, h: 52, label: "ClarifyService", tag: "Clarification", color: C.cyan, icon: "❓" },
  { id: "commit_svc", x: 266, y: 478, w: 110, h: 52, label: "CommitService", tag: "Truth Mgmt", color: C.green, icon: "✅" },
  { id: "review_svc", x: 384, y: 478, w: 110, h: 52, label: "ReviewService", tag: "GTD Review", color: C.teal, icon: "📊" },
  { id: "memory_svc", x: 502, y: 478, w: 118, h: 52, label: "MemoryService", tag: "9-Layer FM", color: C.yellow, icon: "🧠" },

  // Persistence
  { id: "sqlite", x: 30, y: 590, w: 130, h: 52, label: "SQLite + Drizzle", tag: "MVP → PG M8", color: C.dim, icon: "🗄️" },
  { id: "qdrant", x: 170, y: 590, w: 130, h: 52, label: "Qdrant Vector", tag: "InMem → M3", color: C.dim, icon: "🔢" },
  { id: "fs", x: 310, y: 590, w: 110, h: 52, label: "File System", tag: "FM-L1/3/5/6", color: C.dim, icon: "📁" },
  { id: "audit", x: 428, y: 590, w: 110, h: 52, label: "Audit Log", tag: "Append-only", color: C.orange, icon: "📝" },
  { id: "zod", x: 546, y: 590, w: 74, h: 52, label: "Zod", tag: "Schema", color: C.dim, icon: "🔷" },
];

const techEdges: TechEdge[] = [
  // Client → Express
  { from: "web", to: "express", color: C.purple, animated: true, thickness: 2 },
  { from: "cli", to: "express", color: C.dim, dashed: true },
  { from: "mobile", to: "express", color: C.dim, dashed: true },

  // External → Bridge
  { from: "external_rt", to: "bridge_surface", color: C.orange, animated: true, thickness: 2 },

  // Express → surfaces
  { from: "express", to: "cmd_surface", color: C.pink, animated: true },
  { from: "express", to: "qry_surface", color: C.teal, animated: true },

  // Bridge surface → bridge types
  { from: "bridge_surface", to: "b1", color: C.orange, animated: true },
  { from: "bridge_surface", to: "b2", color: C.teal },
  { from: "bridge_surface", to: "b3", color: C.yellow },
  { from: "bridge_surface", to: "b4", color: C.pink },

  // Bridges → writegate or query
  { from: "b1", to: "writegate", color: C.orange, animated: true, dashed: true },
  { from: "b2", to: "qry_surface", color: C.teal, dashed: true },

  // cmd_surface → writegate
  { from: "cmd_surface", to: "writegate", color: C.pink, animated: true, thickness: 2 },

  // qry_surface → services
  { from: "qry_surface", to: "commit_svc", color: C.teal, dashed: true },
  { from: "qry_surface", to: "review_svc", color: C.teal, dashed: true },

  // writegate → domain services
  { from: "writegate", to: "inbox_svc", color: C.blue, animated: true },
  { from: "writegate", to: "clarify_svc", color: C.cyan, animated: true },
  { from: "writegate", to: "commit_svc", color: C.green, animated: true },
  { from: "writegate", to: "memory_svc", color: C.yellow },

  // Domain services → persistence
  { from: "commit_svc", to: "sqlite", color: C.green, animated: true },
  { from: "commit_svc", to: "qdrant", color: C.dim },
  { from: "commit_svc", to: "audit", color: C.orange, dashed: true },
  { from: "inbox_svc", to: "sqlite", color: C.blue },
  { from: "review_svc", to: "sqlite", color: C.teal },
  { from: "memory_svc", to: "fs", color: C.yellow },
  { from: "memory_svc", to: "qdrant", color: C.yellow },
  { from: "writegate", to: "audit", color: C.orange, animated: true },
  { from: "clarify_svc", to: "zod", color: C.dim, dashed: true },
  { from: "commit_svc", to: "zod", color: C.dim, dashed: true },
];

function getCenter(n: TechNode) {
  return { x: n.x + n.w / 2, y: n.y + n.h / 2 };
}

function buildPath(a: TechNode, b: TechNode) {
  const from = getCenter(a);
  const to = getCenter(b);
  const dy = to.y - from.y;
  const dx = to.x - from.x;
  if (Math.abs(dy) < 20) {
    return `M ${from.x} ${from.y} L ${to.x} ${to.y}`;
  }
  const midY = from.y + dy / 2;
  const curve = Math.min(Math.abs(dx) * 0.2, 30);
  return `M ${from.x} ${from.y} C ${from.x} ${midY + curve} ${to.x} ${midY - curve} ${to.x} ${to.y}`;
}

function Dot({ path, color, delay }: { path: string; color: string; delay: number }) {
  return (
    <circle r="3" fill={color} opacity="0.9">
      <animateMotion
        dur={`${1.6 + delay * 0.3}s`}
        repeatCount="indefinite"
        path={path}
        begin={`${delay * 0.25}s`}
      />
    </circle>
  );
}

const LAYERS = [
  { label: "CLIENT SURFACES", y: 18, color: C.purple },
  { label: "API GATEWAY", y: 132, color: C.blue },
  { label: "COMMAND / QUERY / BRIDGE", y: 237, color: C.pink },
  { label: "GOVERNANCE ENGINE", y: 348, color: C.pink },
  { label: "DOMAIN SERVICES", y: 464, color: C.green },
  { label: "PERSISTENCE", y: 577, color: C.dim },
];

export function TechArchitecture() {
  const [hovered, setHovered] = useState<string | null>(null);
  const SVG_W = 640;
  const SVG_H = 665;
  const nodeMap = Object.fromEntries(techNodes.map((n) => [n.id, n]));

  return (
    <div
      style={{
        minHeight: "100vh",
        background: `radial-gradient(ellipse at 20% 30%, rgba(41,121,255,0.1) 0%, transparent 55%), radial-gradient(ellipse at 85% 75%, rgba(170,0,255,0.08) 0%, transparent 55%), ${C.bg}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "32px 20px 24px",
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}
    >
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 28 }}>
        <div style={{ fontSize: 11, letterSpacing: 4, color: C.teal, textTransform: "uppercase", marginBottom: 8, fontWeight: 600 }}>
          FlowMind Architecture V1
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: C.text, margin: 0, letterSpacing: -0.5 }}>
          Technical Architecture
        </h1>
        <p style={{ fontSize: 13, color: C.dim, marginTop: 6 }}>
          Node.js 22 · TypeScript · SQLite→PG · Express→Next.js · MCP Bridge
        </p>
      </div>

      <div style={{ position: "relative" }}>
        <svg
          width={SVG_W}
          height={SVG_H}
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          style={{ overflow: "visible" }}
        >
          <defs>
            {["cyan", "pink", "green", "orange", "yellow", "teal"].map((name) => {
              const colorMap: Record<string, string> = {
                cyan: C.cyan, pink: C.pink, green: C.green,
                orange: C.orange, yellow: C.yellow, teal: C.teal,
              };
              return (
                <marker
                  key={name}
                  id={`arr-${name}`}
                  markerWidth="6"
                  markerHeight="6"
                  refX="5"
                  refY="3"
                  orient="auto"
                >
                  <path d="M0,0 L6,3 L0,6 Z" fill={colorMap[name]} opacity="0.8" />
                </marker>
              );
            })}
            <marker id="arr-blue" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill={C.blue} opacity="0.8" />
            </marker>
            <marker id="arr-purple" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill={C.purple} opacity="0.8" />
            </marker>
            <marker id="arr-dim" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill={C.dim} opacity="0.5" />
            </marker>
            <filter id="glow-b">
              <feGaussianBlur stdDeviation="3" result="b" />
              <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Grid */}
          <pattern id="tgrid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(255,255,255,0.018)" strokeWidth="0.5" />
          </pattern>
          <rect width={SVG_W} height={SVG_H} fill="url(#tgrid)" rx="16" />

          {/* Layer backgrounds */}
          {LAYERS.map((layer) => (
            <g key={layer.label}>
              <text x="8" y={layer.y + 2} fontSize="7.5" fill={layer.color} opacity="0.5" letterSpacing="2" fontWeight="600">
                {layer.label}
              </text>
            </g>
          ))}

          {/* Layer separator lines */}
          {LAYERS.slice(1).map((layer) => (
            <line
              key={`sep-${layer.y}`}
              x1="0"
              y1={layer.y + 4}
              x2={SVG_W}
              y2={layer.y + 4}
              stroke={C.border}
              strokeWidth="1"
              strokeDasharray="3,6"
              opacity="0.6"
            />
          ))}

          {/* Edges */}
          {techEdges.map((edge, i) => {
            const a = nodeMap[edge.from];
            const b = nodeMap[edge.to];
            if (!a || !b) return null;
            const path = buildPath(a, b);
            const col = edge.color;
            const markerName =
              col === C.pink ? "pink"
              : col === C.teal ? "teal"
              : col === C.green ? "green"
              : col === C.orange ? "orange"
              : col === C.yellow ? "yellow"
              : col === C.blue ? "blue"
              : col === C.cyan ? "cyan"
              : col === C.purple ? "purple"
              : "dim";

            return (
              <g key={i}>
                <path
                  d={path}
                  fill="none"
                  stroke={col}
                  strokeWidth={edge.thickness || 1.2}
                  strokeOpacity={0.38}
                  strokeDasharray={edge.dashed ? "5,4" : undefined}
                  markerEnd={`url(#arr-${markerName})`}
                />
                {edge.animated && (
                  <Dot path={path} color={col} delay={i % 6} />
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {techNodes.map((node) => {
            const isH = hovered === node.id;
            return (
              <g
                key={node.id}
                onMouseEnter={() => setHovered(node.id)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: "pointer" }}
              >
                {/* Hovered glow */}
                {isH && (
                  <rect
                    x={node.x - 3}
                    y={node.y - 3}
                    width={node.w + 6}
                    height={node.h + 6}
                    rx="11"
                    fill={node.color}
                    opacity="0.08"
                    filter="url(#glow-b)"
                  />
                )}
                {/* Card */}
                <rect
                  x={node.x}
                  y={node.y}
                  width={node.w}
                  height={node.h}
                  rx="9"
                  fill={C.panel}
                  stroke={node.color}
                  strokeWidth={isH ? 1.8 : 1.2}
                />
                {/* Accent bar */}
                <rect
                  x={node.x + 8}
                  y={node.y}
                  width={node.w - 16}
                  height={2}
                  rx="1"
                  fill={node.color}
                  opacity="0.9"
                />
                {/* Label */}
                <text
                  x={node.x + node.w / 2}
                  y={node.y + (node.tag ? 18 : 24)}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="700"
                  fill={node.color}
                  letterSpacing="0.3"
                >
                  {node.icon} {node.label}
                </text>
                {node.tag && (
                  <text
                    x={node.x + node.w / 2}
                    y={node.y + 30}
                    textAnchor="middle"
                    fontSize="7.5"
                    fill={C.dim}
                  >
                    {node.tag}
                  </text>
                )}
                {/* Badges */}
                {node.badges && node.badges.map((b, bi) => (
                  <g key={bi}>
                    <rect
                      x={node.x + 5 + bi * 52}
                      y={node.y + node.h - 14}
                      width={48}
                      height={10}
                      rx="3"
                      fill={node.color}
                      opacity="0.12"
                    />
                    <text
                      x={node.x + 29 + bi * 52}
                      y={node.y + node.h - 6}
                      textAnchor="middle"
                      fontSize="6.5"
                      fill={node.color}
                      opacity="0.8"
                    >
                      {b}
                    </text>
                  </g>
                ))}
              </g>
            );
          })}

          {/* Migration annotation */}
          <g transform="translate(540, 145)">
            <rect x="0" y="0" width="90" height="62" rx="7" fill={C.panel} stroke={C.border} strokeWidth="1" />
            <text x="8" y="13" fontSize="7.5" fill={C.dim} letterSpacing="1.5" fontWeight="600">ROADMAP</text>
            {[
              { color: C.blue, label: "M1-M3: SQLite" },
              { color: C.teal, label: "M4: Next.js" },
              { color: C.green, label: "M6: AI/LLM" },
              { color: C.purple, label: "M8: PG+Qdrant" },
            ].map((r, i) => (
              <g key={i} transform={`translate(8, ${22 + i * 11})`}>
                <circle cx="3" cy="4" r="3" fill={r.color} opacity="0.7" />
                <text x="10" y="8" fontSize="7.5" fill={C.dim}>{r.label}</text>
              </g>
            ))}
          </g>
        </svg>
      </div>

      {/* Stack tags */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16, justifyContent: "center" }}>
        {[
          ["Node.js 22", C.green],
          ["TypeScript strict", C.blue],
          ["React 18 + Vite", C.purple],
          ["Express 4.x", C.blue],
          ["SQLite + Drizzle", C.teal],
          ["Zod v4", C.cyan],
          ["pnpm workspace", C.dim],
          ["Vitest 448 tests", C.green],
          ["MCP Server", C.orange],
          ["Qdrant M3+", C.yellow],
        ].map(([label, color]) => (
          <span
            key={label as string}
            style={{
              background: C.panel,
              border: `1px solid ${color as string}`,
              borderRadius: 20,
              padding: "4px 12px",
              fontSize: 11,
              color: color as string,
              fontWeight: 600,
              letterSpacing: 0.3,
            }}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
