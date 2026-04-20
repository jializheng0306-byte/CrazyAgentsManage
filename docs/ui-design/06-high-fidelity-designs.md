# High-Fidelity Interface Designs

## Overview
Complete high-fidelity designs with detailed specifications for all pages.

---

## 1. Agent Observability Dashboard (Vercel Workflow Style)

### Detailed Specifications

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

### CSS Variables (Dashboard)

```css
:root {
  --bg: #000000;
  --surface: #111111;
  --border: #1f2937;
  --text: #ffffff;
  --text-muted: #9ca3af;
  --completed: #3b82f6;
  --executing: #10b981;
  --queued: #4b5563;
  --waiting: #f59e0b;
  --failed: #ef4444;
  --tool-span: #1e3a5f;
}
```

### Typography

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.5;
}

h1, h2, h3 { font-weight: 600; }

.mono { font-family: 'Geist Mono', monospace; }
```

### Spacing

```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
```

---

## 2. Task Orchestration Page

### Detailed Specifications

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

### CSS Variables (Tasks)

```css
:root {
  --bg: #0F172A;
  --surface: #1E293B;
  --muted: #272F42;
  --border: #475569;
  --text: #F8FAFC;
  --accent: #22C55E;
  --done: #10b981;
  --running: #3b82f6;
  --pending: #4b5563;
  --failed: #ef4444;
}
```

---

## 3. Team Memory Management Page

### Detailed Specifications

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  CrazyAgentsManage                                                  ┌──────────┐ ┌──────────┐ │
│  ⬡  Dashboard  Tasks  ⬢  Team Memory  Cron  Skills            │ + Team   │ │ Settings │ │
│  ⬡  [Active]                                                        └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌──────────────────┐  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Teams           │  │  Team: "Default Team"                                              │ │
│  │                  │  ├───────────────────────────────────────────────────────────────────┤ │
│  │  ● Default Team  │  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │  ○ AI Research   │  │  │ Team Memory                                                  │ │ │
│  │  ○ DevOps Team   │  │  ├─────────────────────────────────────────────────────────────┤ │ │
│  │                  │  │  │ # Default Team Memory                                      │ │ │
│  │                  │  │  │ Created: 2026-04-19                                        │ │ │
│  │                  │  │  │                                                           │ │ │
│  │                  │  │  │ ## Overview                                                │ │ │
│  │                  │  │  │ This team's shared memory is automatically updated        │ │ │
│  │                  │  │  │ after each session.                                       │ │ │
│  │                  │  │  │                                                           │ │ │
│  │                  │  │  │ ## Recent Updates                                         │ │ │
│  │                  │  │  │                                                           │ │ │
│  │                  │  │  │ ### 2026-04-19 14:30:00                                   │ │ │
│  │                  │  │  │ Completed research task for market analysis               │ │ │
│  │                  │  │  └─────────────────────────────────────────────────────────────┘ │ │
│  │                  │  │                                                                   │ │
│  │                  │  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │                  │  │  │ Role Memories                                              │ │ │
│  │                  │  │  ├─────────────────────────────────────────────────────────────┤ │ │
│  │                  │  │  │  [Expert]  [Research]  [Code]  [Ops]  [Cron]  [Team]      │ │ │
│  │                  │  │  │                                                           │ │ │
│  │                  │  │  │  [Expert Role Memory]                                      │ │ │
│  │                  │  │  │  ┌─────────────────────────────────────────────────────┐  │ │ │
│  │                  │  │  │  │ # Expert Role Memory                              │  │ │ │
│  │                  │  │  │  │ Team: Default Team                                │  │ │ │
│  │                  │  │  │  │ Created: 2026-04-19                              │  │ │ │
│  │                  │  │  │  │                                                     │  │ │ │
│  │                  │  │  │  │ ## Responsibilities                                │  │ │ │
│  │                  │  │  │  │ - Complex reasoning and analysis                  │  │ │ │
│  │                  │  │  │  │ - Code review and debugging                        │  │ │ │
│  │                  │  │  │  │                                                     │  │ │ │
│  │                  │  │  │  │ ## Skills                                          │  │ │ │
│  │                  │  │  │  │ - Terminal, File, Web, MCP                         │  │ │ │
│  │                  │  │  │  └─────────────────────────────────────────────────────┘  │ │ │
│  │                  │  │  │                                                           │ │ │
│  │                  │  │  └─────────────────────────────────────────────────────────────┘ │ │
│  │                  │  │                                                                   │ │
│  │                  │  │  ┌─────────────────────────────────────────────────────────────┐ │ │
│  │                  │  │  │ Team Documents                                              │ │ │
│  │                  │  │  ├─────────────────────────────────────────────────────────────┤ │ │
│  │                  │  │  │  📄 coding-standards.md  [Edit] [Delete]                   │ │ │
│  │                  │  │  │  📄 deployment-guide.md    [Edit] [Delete]                   │ │ │
│  │                  │  │  │  📄 api-reference.md       [Edit] [Delete]                   │ │ │
│  │                  │  │  │  [+ Add Document]                                           │ │ │
│  │                  │  │  └─────────────────────────────────────────────────────────────┘ │ │
│  └──────────────────┘  └───────────────────────────────────────────────────────────────────┘ │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### CSS Variables (Team Memory)

```css
:root {
  --bg: #0F172A;
  --sidebar: #1E293B;
  --surface: #272F42;
  --border: #475569;
  --text: #F8FAFC;
  --accent: #22C55E;
  --accent-muted: #9ca3af;
}
```

---

## 4. Cron Tasks Management Page

### Detailed Specifications

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

### CSS Variables (Cron)

```css
:root {
  --bg: #0F172A;
  --surface: #1E293B;
  --border: #475569;
  --text: #F8FAFC;
  --accent: #22C55E;
  --active: #10b981;
  --paused: #f59e0b;
  --failed: #ef4444;
  --success: #10b981;
  --error: #ef4444;
}
```

---

## Common Components

### Button Styles

```css
.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
}

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
```

### Card Styles

```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: var(--spacing-lg);
}
```

### Status Indicators

```css
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.active { background: var(--active); }
.status-dot.paused { background: var(--paused); }
.status-dot.failed { background: var(--failed); }
```

---

## Responsive Breakpoints

```css
/* Mobile: 375px */
/* Tablet: 768px */
/* Desktop: 1024px */
/* Large Desktop: 1440px */
```

## Accessibility

- All interactive elements have `aria-label`
- Visible focus states
- Color is not the only indicator (icons too)
- `prefers-reduced-motion` is respected
