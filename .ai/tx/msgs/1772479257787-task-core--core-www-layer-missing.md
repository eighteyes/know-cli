---
to: core/core
from: core/core
msg-id: task-1772479200
headline: Code-graph missing entire WWW/frontend layer
timestamp: 2026-03-02T19:15:00.000Z
---

# Code-Graph Missing WWW Layer

Code-graph generation has never been run against the frontend. The graph only contains 73 API-side modules. The entire WWW layer is a blind spot.

## What exists in code but not in code-graph

### Pages (www/src/pages/) — 24 modules
Largest by size:
- AddJobPage.jsx (38KB)
- JobDetailPage.jsx (33KB)
- FleetROIPage.jsx
- RobotDetailPage.jsx
- PilotDetailPage.jsx
- EconomicsPage.jsx
- GoNoGoPage.jsx
- Plus 17 more

### Components (lib/components/) — 67+ files across 30 directories
Includes shared components referenced by spec-graph:
- FilterBarComponent (maps to 3 spec components)
- SearchBarComponent (maps to 2 spec components)
- NotificationDrawerComponent (maps to 2 spec components)
- Plus ~60 more

### Services (lib/services/) — 18 files
- jobService.js
- pilotService.js
- botService.js
- missionService.js
- organizationService.js
- Plus 13 more

## Why this matters

Spec-graph defines 25 components. Code-graph has zero frontend modules. `know graph cross connect` cannot link spec components to their implementations. Any graph-based analysis, coverage checking, or automated validation is blind to the frontend.

## Expected behavior

`know codemap` (or equivalent code-graph generation command) should support scanning:
- `www/src/pages/` — page-level modules
- `lib/components/` — shared component modules  
- `lib/services/` — service layer modules

Each should produce module entries with correct `file_path` values relative to project root.
