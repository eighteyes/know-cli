# Summary: spec-dashboard

## What Was Built
Interactive HTML dashboard for the know spec-graph, served via `know serve`. Kanban-first design with CRUD, undo/history, AI chat, and live hot updates.

## Files
| File | Lines | Purpose |
|---|---|---|
| `know/src/server.py` | ~400 | HTTP server, REST API, CLI proxy, undo stack, file watcher, AI chat streaming |
| `know/www/index.html` | ~800 | Full Preact+HTM dashboard with Phosphor Observatory design |
| `know/www/api.js` | ~110 | API client with SSE streaming for chat and events |
| `know/know.py` | +18 | `know serve` command |

## Features
1. **Kanban board** — features as cards in phase columns (reversed: V→I, unphased at right)
2. **Master nav** — user/objective scope filtering
3. **Sidecard** — parent breadcrumb + child entity accordion tree
4. **CRUD** — add/edit/delete entities, link/unlink, drag-drop phase change
5. **Undo** — snapshot-based (max 30), undo button with badge count
6. **History** — reads diff-graph.jsonl, shows timestamped change log
7. **AI Chat** — claude CLI via execPath auth passthrough, stream-json SSE
8. **Hot Updates** — file watcher SSE, auto-refresh on external CLI changes
9. **Validation** — banner + inline badges for graph issues

## Architecture
- **Zero new Python deps** — stdlib http.server + subprocess
- **In-process reads** — direct JSON file read for graph data
- **CLI proxy writes** — all mutations via know CLI subprocess (honors hooks, validation, diff logging)
- **SSE streaming** — chat responses + file-watch events
- **Auth passthrough** — claude CLI handles auth, no API keys needed

## Graph
47 dependency nodes: 11 actions, 8 operations, 13 components, 15 references

## Design
Phosphor Observatory — DM Serif Text for names, IBM Plex Mono for system labels, luminous entity colors against deep void background, dot-grid texture, staggered animations.
