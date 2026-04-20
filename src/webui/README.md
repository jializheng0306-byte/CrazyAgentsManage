# CrazyAgentsManage WebUI

## Overview

This is the WebUI for CrazyAgentsManage, a multi-agent collaboration platform. The UI is designed with inspiration from Vercel's Workflow SDK dashboard.

## Pages

1. **Dashboard** - Agent Observability Dashboard (Vercel Workflow style)
2. **Tasks** - Task Orchestration with DAG visualization
3. **Team Memory** - Team and role memory management
4. **Cron** - Scheduled tasks management
5. **Skills** - Skills management

## Design System

### Colors

- **Backgrounds**: Pure black (dashboard), dark blue (other pages)
- **Status Colors**:
  - Completed: Blue (#3b82f6)
  - Executing: Green (#10b981)
  - Queued/Pending: Gray (#4b5563)
  - Waiting/Paused: Orange (#f59e0b)
  - Failed/Error: Red (#ef4444)
- **Text**: White (#ffffff)
- **Secondary Text**: Gray (#9ca3af)

### Typography

- **Font**: Inter (from Google Fonts)
- **Monospace**: System monospace or Geist Mono

## Running the Application

### Prerequisites

- Python 3.11+
- Flask

### Installation

```bash
cd src/webui
pip install flask
```

### Running

```bash
python app.py
```

Then open your browser and navigate to: http://localhost:5000

## File Structure

```
src/webui/
├── app.py                      # Flask application
├── README.md                   # This file
├── static/
│   ├── css/
│   │   ├── design-system.css   # Design system styles
│   │   ├── dashboard.css       # Dashboard specific styles
│   │   └── pages.css           # Other pages styles
│   └── js/
│       └── dashboard.js        # Dashboard JavaScript
└── templates/
    ├── dashboard.html          # Dashboard page
    ├── tasks.html              # Tasks page
    ├── team-memory.html        # Team memory page
    ├── cron.html               # Cron page
    └── skills.html             # Skills page
```

## Features Implemented

### Dashboard
- ✅ Vercel Workflow style timeline
- ✅ Status indicators with color coding
- ✅ Nested task hierarchy
- ✅ Tool spans visualization
- ✅ Search and zoom controls
- ✅ Metadata row (Created, Completed, Duration, etc.)

### Tasks
- ✅ DAG graph visualization
- ✅ Task list with status badges
- ✅ Stats grid

### Team Memory
- ✅ Team sidebar navigation
- ✅ Team memory editor
- ✅ Role memory tabs
- ✅ Document management

### Cron
- ✅ Scheduled tasks cards
- ✅ Status badges
- ✅ Action buttons (Edit, Pause, Run Now, etc.)

## Responsive Design

The UI is responsive with breakpoints at:
- 480px (Mobile)
- 768px (Tablet)
- 1024px (Desktop)
- 1440px (Large Desktop)

## Accessibility

- All interactive elements have appropriate labels
- Visible focus states
- Color is not the only indicator (icons used as well)
- `prefers-reduced-motion` is respected

## Browser Support

Modern browsers with ES6+ support:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Next Steps

1. Connect to real backend APIs
2. Add real-time data updates (WebSocket/SSE)
3. Implement user authentication
4. Add more interactive features
