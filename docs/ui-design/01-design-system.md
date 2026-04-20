# CrazyAgentsManage - Design System

## 📋 Overview

**Design System for CrazyAgentsManage WebUI

## 🎨 Pattern
- **Pattern:** Real-Time / Operations Landing
- **Conversion Focus:** For ops/security/iot products. Demo or sandbox link. Trust signals.
- **CTA Placement:** Primary CTA in nav + After metrics
- **Color Strategy:** Dark or neutral. Status colors (green/amber/red). Data-dense but scannable.
- **Sections:** 1. Hero (product + live preview or status), 2. Key metrics/indicators, 3. How it works, 4. CTA (Start trial / Contact)

## 🎭 Style
- **Name:** Dark Mode (OLED)
- **Mode Support:** Light ✗ No | Dark ✓ Only
- **Keywords:** Dark theme, low light, high contrast, deep black, midnight blue, eye-friendly, OLED, night mode, power efficient
- **Best For:** Night-mode apps, coding platforms, entertainment, eye-strain prevention, OLED devices, low-light
- **Performance:** ⚡ Excellent | **Accessibility:** ✓ WCAG AAA

## 🎨 Color Palette

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#1E293B` | `--color-primary` |
| On Primary | `#FFFFFF` | `--color-on-primary` |
| Secondary | `#334155` | `--color-secondary` |
| Accent/CTA | `#22C55E` | `--color-accent` |
| Background | `#0F172A` | `--color-background` |
| Foreground | `#F8FAFC` | `--color-foreground` |
| Muted | `#272F42` | `--color-muted` |
| Border | `#475569` | `--color-border` |
| Destructive | `#EF4444` | `--color-destructive` |
| Ring | `#1E293B` | `--color-ring` |

### Vercel Workflow Dashboard Colors (for Timeline)

| State | Color | Hex | Purpose |
|-------|-------|-----|---------|
| Completed / Done | Blue | `#3b82f6` | Task completion |
| Executing / Running | Green | `#10b981` | Task in progress |
| Queued / Pending | Gray Striped | `#4b5563` | Task queued |
| Waiting | Orange | `#f59e0b` | Waiting for dependencies |
| Failed / Error | Red | `#ef4444` | Task failed |
| Background | Pure Black | `#000000` | Main background |
| Surface | Dark Gray | `#111111` | Card/panel background |
| Border | Gray | `#1f2937` | Border/separator |
| Text | White | `#ffffff` | Main text |
| Secondary Text | Gray | `#9ca3af` | Secondary info |
| Tool Span | Deep Blue | `#1e3a5f` | Tool execution span |

## 🖋️ Typography

- **Heading:** Inter
- **Body:** Inter
- **Mood:** dark, cinematic, technical, precision, clean, premium, developer, professional, high-end utility
- **Best For:** Developer tools, fintech/trading, AI dashboards, streaming platforms, high-end productivity apps
- **Google Fonts:** https://fonts.google.com/share?selection.family=Inter:wght@300;400;500;600;700
- **CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
```

## ✨ Key Effects
Minimal glow (text-shadow: 0 0 10px), dark-to-light transitions, low white emission, high readability, visible focus

## ❌ Avoid (Anti-patterns)
- Light mode default
- Slow performance

## ✅ Pre-Delivery Checklist
- [ ] No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] cursor-pointer on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard nav
- [ ] prefers-reduced-motion respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px

## 📄 Pages to Design

1. **Dashboard - Agent Observability (Vercel Workflow style)
2. **Tasks - Task Orchestration (DAG view)
3. **Team Memory - Team & Role Memory Management
4. **Cron - Scheduled Tasks Management
5. **Skills - Team & Role Skills
