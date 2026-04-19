---
name: "ui-ux-pro-max"
description: "UI/UX design intelligence with 67 styles, 161 color palettes, 57 font pairings, 99 UX guidelines, and 25 chart types. Invoke when designing UI pages, choosing styles/colors/fonts, reviewing UX, or implementing components for the CrazyAgentsManage WebUI dashboard."
---

# UI/UX Pro Max - Design Intelligence

Comprehensive design intelligence for building professional UI/UX. Contains searchable databases of styles, colors, fonts, and UX guidelines.

## How to Use This Skill

Use this skill when:
- **Designing new WebUI pages** — Dashboard, Timeline, Task pages for CrazyAgentsManage
- **Choosing styles/colors/fonts** — Need design system recommendations
- **Implementing components** — Need UX best practices for specific patterns
- **Reviewing existing UI** — Need UX audit or accessibility checks

## Design System Generator (REQUIRED - Start Here)

Always start with design system generation for comprehensive recommendations:

```bash
python3 skills/ui-ux-pro-max/scripts/search.py "<product_type> <industry> <keywords>" --design-system [-p "Project Name"]
```

For the CrazyAgentsManage project:
```bash
python3 skills/ui-ux-pro-max/scripts/search.py "developer tool dashboard dark mode workflow timeline" --design-system -p "CrazyAgentsManage"
```

**For documentation output:**
```bash
python3 skills/ui-ux-pro-max/scripts/search.py "developer tool dashboard dark mode workflow timeline" --design-system -p "CrazyAgentsManage" -f markdown
```

## Domain-Specific Searches

After design system, use domain searches for details:

| Domain | Use For | Example |
|--------|---------|---------|
| `product` | Product type patterns | `--domain product "developer tool"` |
| `style` | UI styles, effects | `--domain style "dark mode workflow"` |
| `color` | Color palettes | `--domain color "developer tool"` |
| `typography` | Font pairings | `--domain typography "modern dashboard"` |
| `ux` | UX best practices | `--domain ux "timeline accessibility"` |
| `landing` | Page structure | `--domain landing "dashboard hero"` |
| `chart` | Chart recommendations | `--domain chart "real-time timeline"` |
| `prompt` | CSS keywords | `--domain prompt "vercel dark"` |

## Vercel Workflow Dashboard Style Guide

For the CrazyAgentsManage Agent Observability Dashboard (inspired by Vercel Workflow SDK):

**Color Palette:**
- Background: `#000000` (pure black)
- Surface: `#111111` - `#1a1a1a`
- Border: `#1f2937` (dark gray)
- Primary (Executing): `#10b981` (green)
- Secondary (Completed): `#3b82f6` (blue)
- Queued: `#4b5563` (gray striped)
- Waiting: `#f59e0b` (orange)
- Failed: `#ef4444` (red)
- Tool spans: `#1e3a5f` (deep blue)
- Text: `#ffffff` (white)
- Secondary text: `#9ca3af` (gray)

**Key Design Patterns:**
- Horizontal timeline with timestamp markers
- Nested task hierarchy with vertical connector lines
- Duration badges on the right edge
- Tab navigation (Trace/Events)
- Expandable/collapsible task groups
- Search bar with filters
- Zoom controls (+/-)

**Typography:**
- Use system fonts or Inter/Geist Mono
- Monospace for IDs, timestamps, durations
- 14px base, 12px secondary, 16px headings

## Pre-Delivery Checklist

Before delivering UI code:

### Visual Quality
- [ ] No emojis as structural icons (use SVG/Lucide/Heroicons)
- [ ] Consistent icon family and style
- [ ] Semantic theme tokens (no hardcoded colors)
- [ ] Pressed-state visuals don't shift layout

### Dark Mode (Critical for Dashboard)
- [ ] Primary text contrast >=4.5:1 on dark background
- [ ] Secondary text contrast >=3:1 on dark surfaces
- [ ] Borders/separators visible in dark theme
- [ ] Modal/drawer scrim 40-60% black opacity

### Layout
- [ ] Horizontal scroll for wide timeline content
- [ ] Nested indentation for task hierarchy
- [ ] Duration badges aligned to right edge
- [ ] Tab navigation clearly indicates active state

### Accessibility
- [ ] All meaningful elements have aria labels
- [ ] Focus states visible for keyboard navigation
- [ ] Color not the only indicator (use icons too)
- [ ] prefers-reduced-motion respected
