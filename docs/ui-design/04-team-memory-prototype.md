# Team Memory Management Page - Prototype

## 📋 Overview
Manage team memories, role memories, and team documents.

---

## 🎨 Page Prototype (ASCII)

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

---

## 🎯 Key Components

### 1. Team Sidebar
- List of all teams
- Active team indicator
- "+ Team" button

### 2. Team Header
- Team name
- Action buttons

### 3. Team Memory Section
- Markdown editor/viewer
- Auto-updated content
- Edit button

### 4. Role Memories Section
- Tab navigation for each role
- Role memory editor/viewer
- Edit button for each

### 5. Team Documents Section
- List of documents
- Edit/Delete buttons
- "+ Add Document" button

---

## 🎨 Color Mapping

| Element | Color | Hex |
|---------|-------|-----|
| Page background | Dark blue | `#0F172A` |
| Sidebar background | Slate | `#1E293B` |
| Card background | Dark slate | `#272F42` |
| Active tab | Green | `#22C55E` |
| Inactive tab | Gray | `#9ca3af` |
| Border | Light slate | `#475569` |
| Text | White | `#F8FAFC` |
