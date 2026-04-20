# Task Orchestration Page - Prototype

## 📋 Overview
DAG-based task orchestration view showing task dependencies and execution status.

---

## 🎨 Page Prototype (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  CrazyAgentsManage                                                  ┌──────────┐ ┌──────────┐ │
│  ⬡  Dashboard  ⬢  Tasks  Team Memory  Cron  Skills               │ + New    │ │ Settings │ │
│  ⬡  [Active]                                                        └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                                    │
│  │  15      │  │  4       │  │  8       │  │  3       │                                    │
│  │  Total    │  │  Pending  │  │  Running  │  │  Done    │                                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                                    │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Project: "Website Redesign"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │ │
│  ├────────────────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                                        │ │
│  │                    ┌───────────────────┐                                               │ │
│  │                    │  Task 1: Research │                                               │ │
│  │                    │  [Research]       │                                               │ │
│  │                    │  ● Done           │                                               │ │
│  │                    └───────────────────┘                                               │ │
│  │                           │                                                            │ │
│  │              ┌────────────┴────────────┐                                               │ │
│  │              │                         │                                               │ │
│  │  ┌───────────┴───────────┐  ┌──────────┴───────────┐                                  │ │
│  │  │  Task 2: Design       │  │  Task 3: Content      │                                  │ │
│  │  │  [Expert]             │  │  [Research]           │                                  │ │
│  │  │  ● Running            │  │  ● Done               │                                  │ │
│  │  └───────────────────────┘  └──────────────────────┘                                  │ │
│  │              │                         │                                               │ │
│  │              └────────────┬────────────┘                                               │ │
│  │                           │                                                            │ │
│  │                    ┌──────┴──────┐                                                    │ │
│  │                    │  Task 4:    │                                                    │ │
│  │                    │  Develop    │                                                    │ │
│  │                    │  [Code]     │                                                    │ │
│  │                    │  ○ Pending  │                                                    │ │
│  │                    └─────────────┘                                                    │ │
│  │                                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Task List                                                                             │ │
│  ├────────────────────────────────────────────────────────────────────────────────────────┤ │
│  │  [●] Task 1: Research  [Research]  Done     2m 30s  [View] [Edit]                     │ │
│  │  [●] Task 2: Design    [Expert]    Running  1m 15s  [View] [Edit]                     │ │
│  │  [●] Task 3: Content   [Research]  Done     45s     [View] [Edit]                     │ │
│  │  [○] Task 4: Develop   [Code]      Pending  --      [View] [Edit]                     │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Components

### 1. Stats Cards
- Total Tasks
- Pending
- Running
- Done

### 2. Project Selector
- Dropdown to switch between projects

### 3. DAG Visualization
- Nodes = Tasks
- Edges = Dependencies
- Status indicators (dots)
- Role labels

### 4. Task List
- Table of all tasks
- Status, role, duration
- Action buttons (View, Edit)

### 5. Controls
- "+ New" button to create task
- Filter options

---

## 🎨 Color Mapping

| Element | Color | Hex |
|---------|-------|-----|
| Page background | Dark blue | `#0F172A` |
| Card background | Slate | `#1E293B` |
| Done task | Green | `#22C55E` |
| Running task | Blue | `#3b82f6` |
| Pending task | Gray | `#4b5563` |
| Failed task | Red | `#ef4444` |
| Node border | Light slate | `#475569` |
| Edge line | Gray | `#64748b` |
