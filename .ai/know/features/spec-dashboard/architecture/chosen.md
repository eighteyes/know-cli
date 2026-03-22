# Chosen Architecture: spec-dashboard

**Grade: A** — Minimal approach with pragmatic structure. ~1,200 lines new code, zero new Python deps.

## Decision: Minimal + Pragmatic Hybrid

Take the minimal approach's simplicity (stdlib http.server, single HTML file, fewest new files) but borrow the pragmatic approach's server structure (separate cli_proxy, in-process reads via GraphManager).

## File Structure (5 new files, 1 modified)

```
know/
├── www/                           # NEW directory
│   ├── index.html                 # ~700 lines — full Preact+HTM app, inline CSS
│   └── api.js                     # ~100 lines — fetch wrappers for REST endpoints
├── src/
│   └── server.py                  # ~300 lines — HTTP handler, routing, CLI proxy
└── know.py                        # +30 lines — `know serve` Click command
```

**Total: ~1,130 lines new code.**

## Server (know/src/server.py)

- Python stdlib `http.server.BaseHTTPRequestHandler` + `ThreadingHTTPServer`
- Zero new pip dependencies
- In-process reads via `GraphManager.get_graph()` (uses existing GraphCache mtime-checking)
- All writes shell out via `subprocess.run(['python', know_py, '-g', graph_path, ...])`
- Single `run_know(args)` function for all CLI proxying

## REST API

| Method | Endpoint | CLI Command | Purpose |
|---|---|---|---|
| GET | /api/graph | (in-process read) | Full graph JSON for initial load + refresh |
| POST | /api/entity | `know add <type> <key> '<json>'` | Create entity or reference |
| PUT | /api/entity/:id | `know nodes update <id> '<json>'` | Update name/description |
| DELETE | /api/entity/:id | `know nodes delete <id> -y` | Remove entity |
| POST | /api/link | `know link <from> <to1> <to2>...` | Add dependencies |
| DELETE | /api/link | `know unlink <from> <to> -y` | Remove dependency |
| POST | /api/phase | `know phases move/add <entity> <phase>` | Change phase assignment |
| GET | / | (static files) | Serve index.html |
| GET | /api.js | (static files) | Serve api.js |

All mutation responses: `{ok: true}` or `{ok: false, error: "stderr message"}`.
After successful mutation, client re-fetches GET /api/graph to refresh state.

## Frontend (know/www/index.html)

Single HTML file with Preact + HTM from CDN. No build step.

**CDN imports:**
- Preact 10.x (~4KB)
- HTM 3.x (~1KB) — tagged template JSX alternative
- D3 v7 (only if mini-graph viz needed, deferred to v2)

**Component tree:**
```
App (useState: graph, selected, filter, toast)
├── MasterNav (user > objective filter pills)
├── ValidationBanner (dismissible, from graph validation)
├── KanbanBoard (CSS grid columns from meta.phases)
│   └── PhaseColumn[]
│       └── FeatureCard[] (draggable, pills, click to expand)
├── Sidecard (slide-in panel)
│   ├── ParentBreadcrumb (user > objective)
│   ├── EntityAccordion (actions, components, operations)
│   ├── RefsPanel
│   ├── AddEntityForm
│   └── LinkForm
└── Toast (mutation feedback)
```

**State: single useState at App level.** Re-fetch /api/graph after every mutation. No optimistic updates — local latency is <50ms, simpler to always show authoritative state.

**Drag-drop:** Native HTML5 draggable on FeatureCard + drop on PhaseColumn. On drop → POST /api/phase → re-fetch.

**Theme:** Port ENTITY_COLORS from theme.py directly into CSS variables in index.html.

## Key Decisions

1. **stdlib http.server over Flask/aiohttp** — zero deps, sufficient for single-user local tool
2. **Single HTML file over component files** — no build step, easy to ship via `know init`
3. **Re-fetch after mutation over optimistic updates** — simpler, no rollback bugs, fast enough locally
4. **In-process reads, subprocess writes** — reads are instant via GraphCache, writes honor all CLI validation/hooks/diff-logging
5. **No D3 for kanban** — CSS grid is simpler and better suited. D3 only if mini-graph viz is added later
6. **No WebSocket/SSE** — poll-free design, client controls refresh timing
