# Agent Observability Dashboard - Prototype

## 📋 Overview
Vercel Workflow style timeline dashboard for monitoring all agents and task execution.

---

## 🎨 Page Prototype (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  CrazyAgentsManage                                                  ┌──────────┐ ┌──────────┐ │
│  ⬡  Dashboard  Tasks  Team Memory  Cron  Skills                    │ Overview │ │ Settings │ │
│  ⬢  [Active]                                                        └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │  42         │  │  12          │  │  28         │  │  2          │                        │
│  │  Agents     │  │  Running     │  │  Completed  │  │  Failed     │                        │
│  └─────────────┘  └──────────────┘  └─────────────┘  └─────────────┘                        │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  generateBirthdayCard  wrun_01KP45XGBHRMT7H0JXXHKBEQS4  ● Completed  [View Logs] [...] │ │
│  ├────────────────────────────────────────────────────────────────────────────────────────┤ │
│  │  Created    Completed    Duration    Token Usage    Storage                            │ │
│  │  2d ago     2d ago       1m 48s      12,847        8 MB                               │ │
│  ├────────────────────────────────────────────────────────────────────────────────────────┤ │
│  │  [Trace]  [Events]                                                                     │ │
│  ├────────────────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                                        │ │
│  │  ── 0 ─── 10s ─── 20s ─── 30s ─── 40s ─── 50s ─── 1m ─── 1m10s ─── 1m20s ─── 1m30s   │ │
│  │                                                                                        │ │
│  │  generateBirthdayCard  [Queued 200.03ms · Executed 1m 48s] ─────────────────────── 1m48s│ │
│  │  ├─ generateImagePrompt ────────────────────────────────────────────────               │ │
│  │  │  [Research Agent]  Waiting 1m 6s · Received 29.5s               1m35s               │ │
│  │  │  ────────────────────────────────────────────────────────                          │ │
│  │  │     web_search  Searching 12.3s ─────────── 12.3s                                  │ │
│  │  │     read_file   Reading    8.7s  ────────── 8.7s                                   │ │
│  │  ├─ generateImage ────────────────────────────────────────                             │ │
│  │  │  [Code Agent]  Waiting 5s · Executed 22s                     27s                   │ │
│  │  │  ────────────────────────────────────────                                          │ │
│  │  │     terminal    Running    22s  ──────────────────── 22s                            │ │
│  │  └─ sendCard ────────────────────────────                                               │ │
│  │     [Ops Agent]  Waiting 2s · Executed 5s                        7s                    │ │
│  │                                                                                        │ │
│  │  [Search spans...]                                    [-] [+] [🔍]                    │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Components

### 1. Header Navigation
- Logo + App Name
- Navigation links: Dashboard, Tasks, Team Memory, Cron, Skills
- User profile / settings

### 2. Stats Cards
- Total Agents
- Running
- Completed
- Failed

### 3. Workflow Header
- Workflow name
- Workflow ID
- Status indicator (dot + text)
- Action buttons (View Logs, ...)

### 4. Metadata Row
- Created time
- Completed time
- Duration
- Token usage
- Storage

### 5. Tabs
- Trace (active)
- Events

### 6. Timeline View
- Horizontal time axis with markers
- Task bars with nested hierarchy
- Vertical connector lines
- Duration badges on right
- Tool spans (sub-tasks)

### 7. Controls
- Search bar
- Zoom controls (- / +)

---

## 🎨 Color Mapping

| Element | Color | Hex |
|---------|-------|-----|
| Page background | Pure black | `#000000` |
| Card background | Dark gray | `#111111` |
| Borders | Gray | `#1f2937` |
| Completed task | Blue | `#3b82f6` |
| Executing task | Green | `#10b981` |
| Queued task | Gray | `#4b5563` |
| Waiting task | Orange | `#f59e0b` |
| Failed task | Red | `#ef4444` |
| Tool span | Deep blue | `#1e3a5f` |
| Primary text | White | `#ffffff` |
| Secondary text | Gray | `#9ca3af` |
