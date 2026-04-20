# Cron Tasks Management Page - Prototype

## 📋 Overview
Manage scheduled tasks with team and role binding.

---

## 🎨 Page Prototype (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  CrazyAgentsManage                                                  ┌──────────┐ ┌──────────┐ │
│  ⬡  Dashboard  Tasks  Team Memory  ⬢  Cron  Skills             │ + Task   │ │ Settings │ │
│  ⬡  [Active]                                                        └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                                    │
│  │  8       │  │  6       │  │  1       │  │  1       │                                    │
│  │  Total    │  │  Active   │  │  Paused   │  │  Failed   │                                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                                    │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Scheduled Tasks                                                                       │ │
│  ├────────────────────────────────────────────────────────────────────────────────────────┤ │
│  │                                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │  [●] Daily Report Generator          [Cron Agent]  [Default Team]       [Active] │ │ │
│  │  ├──────────────────────────────────────────────────────────────────────────────────┤ │ │
│  │  │  Schedule: 0 9 * * *  (Every day at 9:00 AM)                                     │ │ │
│  │  │  Last Run: 2026-04-19 09:00:12  ✓ Success  (12,450 tokens)                      │ │ │
│  │  │  Next Run: 2026-04-20 09:00:00                                                    │ │ │
│  │  │  Output: Auto-precipitate to team memory                                          │ │ │
│  │  │  [Edit] [Pause] [Run Now] [View Logs]                                             │ │ │
│  │  └──────────────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │  [●] Weekly Backup                 [Ops Agent]   [DevOps Team]        [Active] │ │ │
│  │  ├──────────────────────────────────────────────────────────────────────────────────┤ │ │
│  │  │  Schedule: 0 2 * * 0  (Every Sunday at 2:00 AM)                                   │ │ │
│  │  │  Last Run: 2026-04-13 02:00:45  ✓ Success  (8,230 tokens)                        │ │ │
│  │  │  Next Run: 2026-04-20 02:00:00                                                    │ │ │
│  │  │  Output: Auto-precipitate to team memory                                          │ │ │
│  │  │  [Edit] [Pause] [Run Now] [View Logs]                                             │ │ │
│  │  └──────────────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │  [○] Data Sync                     [Research]    [AI Research Team]    [Paused] │ │ │
│  │  ├──────────────────────────────────────────────────────────────────────────────────┤ │ │
│  │  │  Schedule: 0 */6 * * *  (Every 6 hours)                                           │ │ │
│  │  │  Last Run: 2026-04-18 18:00:22  ✗ Failed  (Error: API rate limit exceeded)      │ │ │
│  │  │  Next Run: -- (Paused)                                                            │ │ │
│  │  │  Output: Auto-precipitate to team memory                                          │ │ │
│  │  │  [Edit] [Resume] [Run Now] [View Logs]                                            │ │ │
│  │  └──────────────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                                        │ │
│  │  [+ Add New Task]                                                                     │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Components

### 1. Stats Cards
- Total Tasks
- Active
- Paused
- Failed

### 2. Task Cards
Each task card shows:
- Status indicator
- Task name
- Role
- Team
- Schedule (cron expression)
- Last run info
- Next run time
- Output destination
- Action buttons

### 3. Action Buttons
- Edit
- Pause/Resume
- Run Now
- View Logs

### 4. Add Task
- "+ Add New Task" button

---

## 🎨 Color Mapping

| Element | Color | Hex |
|---------|-------|-----|
| Page background | Dark blue | `#0F172A` |
| Card background | Slate | `#1E293B` |
| Active status | Green | `#22C55E` |
| Paused status | Orange | `#f59e0b` |
| Failed status | Red | `#ef4444` |
| Success indicator | Green | `#10b981` |
| Error indicator | Red | `#ef4444` |
| Border | Light slate | `#475569` |
| Text | White | `#F8FAFC` |
