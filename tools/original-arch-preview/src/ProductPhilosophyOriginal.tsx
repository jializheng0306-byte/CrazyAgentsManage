import React from "react";

const C = {
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
};

function Card({
  x,
  y,
  w,
  h,
  color,
  title,
  sub,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  title: string;
  sub: string;
}) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="10" fill={C.panel} stroke={color} strokeWidth="1.5" />
      <rect x={x + 10} y={y} width={w - 20} height={2} rx="1" fill={color} opacity="0.85" />
      <text x={x + w / 2} y={y + 22} textAnchor="middle" fontSize="10" fontWeight="700" fill={color} letterSpacing="0.3">
        {title}
      </text>
      <text x={x + w / 2} y={y + 39} textAnchor="middle" fontSize="8" fill={C.textDim}>
        {sub}
      </text>
    </g>
  );
}

export function ProductPhilosophyOriginal() {
  const W = 780;
  const H = 680;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: `radial-gradient(ellipse at 25% 18%, rgba(0,102,255,0.10) 0%, transparent 58%), radial-gradient(ellipse at 78% 80%, rgba(124,58,237,0.10) 0%, transparent 62%), ${C.bg}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "28px 20px 24px",
        fontFamily: "'Inter', -apple-system, sans-serif",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <div style={{ fontSize: 11, letterSpacing: 4, color: C.cyan, textTransform: "uppercase", marginBottom: 8, fontWeight: 600 }}>
          FlowMind Architecture V1
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: C.text, margin: 0, letterSpacing: -0.5 }}>
          Product Philosophy
        </h1>
        <p style={{ fontSize: 13, color: C.textDim, marginTop: 6 }}>
          HermesAgent Hosted FlowMind — 运营产品定位与治理边界
        </p>
      </div>

      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow: "visible" }}>
        <pattern id="pgrid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="0.5" />
        </pattern>
        <rect width={W} height={H} fill="url(#pgrid)" rx="16" />

        <rect x="58" y="20" width="660" height="80" rx="12" fill="rgba(124,58,237,0.06)" stroke="rgba(124,58,237,0.20)" strokeDasharray="4,4" />
        <text x="72" y="16" fontSize="9" fill="rgba(124,58,237,0.6)" letterSpacing="2">POSITIONING LAYER</text>
        <Card x={78} y={36} w={178} h={50} color={C.purple} title="HermesAgent Host" sub="运行时宿主 / 执行面" />
        <Card x={302} y={36} w={178} h={50} color={C.green} title="FlowMind Truth" sub="治理真相 / 规范层" />
        <Card x={526} y={36} w={172} h={50} color={C.cyan} title="Product Surface" sub="CrazyAgentsManage 产品层" />

        <rect x="146" y="140" width="488" height="74" rx="12" fill="rgba(0,212,255,0.05)" stroke="rgba(0,212,255,0.20)" strokeDasharray="4,4" />
        <text x="160" y="136" fontSize="9" fill="rgba(0,212,255,0.6)" letterSpacing="2">MISSION LAYER</text>
        <Card x={166} y={156} w={146} h={46} color={C.cyan} title="Readable Runtime" sub="让运行态可见" />
        <Card x={326} y={156} w={146} h={46} color={C.orange} title="Operable Objects" sub="让运营对象可管" />
        <Card x={486} y={156} w={128} h={46} color={C.pink} title="Governable Loop" sub="让治理闭环可执行" />

        <rect x="72" y="264" width="636" height="146" rx="12" fill="rgba(255,45,120,0.05)" stroke="rgba(255,45,120,0.18)" strokeDasharray="4,4" />
        <text x="86" y="260" fontSize="9" fill="rgba(255,45,120,0.58)" letterSpacing="2">PRINCIPLE MATRIX</text>
        <Card x={92} y={284} w={186} h={48} color={C.blue} title="Runtime First" sub="先看清系统正在发生什么" />
        <Card x={296} y={284} w={186} h={48} color={C.green} title="Truth Before Chat" sub="仓库事实高于聊天记录" />
        <Card x={500} y={284} w={188} h={48} color={C.orange} title="Clear Boundary" sub="宿主 / 真相层 / 产品层分工清晰" />
        <Card x={92} y={348} w={186} h={48} color={C.yellow} title="Manage the Objects" sub="会话 / 技能 / 记忆 / Handoff" />
        <Card x={296} y={348} w={186} h={48} color={C.purple} title="Architecture as Surface" sub="页面必须接实施动态" />
        <Card x={500} y={348} w={188} h={48} color={C.pink} title="Closed Governance" sub="Candidate → Truth → Review → Writeback" />

        <rect x="110" y="468" width="560" height="112" rx="12" fill="rgba(0,255,136,0.05)" stroke="rgba(0,255,136,0.20)" strokeDasharray="4,4" />
        <text x="124" y="464" fontSize="9" fill="rgba(0,255,136,0.6)" letterSpacing="2">PRODUCT LOOP</text>
        <Card x={130} y={492} w={122} h={50} color={C.purple} title="Intent Ingress" sub="CLI / Feishu / Webhook" />
        <Card x={266} y={492} w={122} h={50} color={C.orange} title="Hermes Runtime" sub="Session / Tool / State" />
        <Card x={402} y={492} w={122} h={50} color={C.cyan} title="Product Surface" sub="Overview / Runtime / Ops" />
        <Card x={538} y={492} w={112} h={50} color={C.green} title="Repo Facts" sub="PRD / Harness / Truth" />

        <g transform="translate(566, 602)">
          <rect x="0" y="0" width="150" height="62" rx="8" fill={C.panel} stroke={C.border} strokeWidth="1" />
          <text x="12" y="16" fontSize="8" fill={C.textDim} letterSpacing="2" fontWeight="600">LEGEND</text>
          {[
            [C.purple, "宿主 / 定位层"],
            [C.cyan, "产品表面 / 使命"],
            [C.orange, "运营对象 / 过程"],
            [C.green, "治理真相 / 回写"],
            [C.pink, "治理原则"],
          ].map((item, i) => (
            <g key={i} transform={`translate(12, ${26 + i * 11})`}>
              <rect width="10" height="6" rx="2" fill={item[0] as string} y="1" />
              <text x="16" y="8" fontSize="8" fill={C.textDim}>{item[1] as string}</text>
            </g>
          ))}
        </g>
      </svg>

      <div style={{ display: "flex", gap: 12, marginTop: 14, flexWrap: "wrap", justifyContent: "center" }}>
        {[
          { label: "定位", value: "HermesAgent Hosted FlowMind", color: C.cyan },
          { label: "产品职责", value: "Readable / Operable / Governable", color: C.green },
          { label: "对象", value: "Session · Skill · Memory · Handoff", color: C.yellow },
          { label: "原则", value: "Truth Before Chat", color: C.pink },
        ].map((item) => (
          <div
            key={item.label}
            style={{
              background: C.panel,
              border: `1px solid ${C.border}`,
              borderRadius: 8,
              padding: "8px 14px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 10, color: C.textDim, marginBottom: 2 }}>{item.label}</div>
            <div style={{ fontSize: 12, fontWeight: 700, color: item.color }}>{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
