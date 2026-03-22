# Implementation Notes: spec-dashboard

## Files Created
- `know/src/server.py` (~200 lines) — HTTP server with static file serving + REST API
- `know/www/index.html` (~550 lines) — Full Preact+HTM dashboard, single file, no build step
- `know/www/api.js` (~50 lines) — Fetch wrappers for all REST endpoints

## Files Modified
- `know/know.py` — Added `serve` command (+18 lines), added 'serve' to section_commands

## Architecture
- stdlib `http.server.ThreadingHTTPServer` — zero new deps
- In-process graph reads (direct JSON file read, no subprocess)
- All mutations via `subprocess.run()` shelling out to know CLI
- Preact + HTM from CDN (esm.sh), no build step
- Entity colors ported from theme.py as CSS variables

## API Endpoints
- GET /api/graph — full graph JSON
- GET /api/rules — dependency rules
- POST /api/entity — create entity/reference
- PUT /api/entity/:id — update fields
- DELETE /api/entity/:id — delete
- POST /api/link — add dependency
- DELETE /api/link — remove dependency
- POST /api/phase — change phase assignment

## Smoke Test Results
- `know serve --help` ✓
- GET /api/graph returns full spec-graph.json ✓
- GET / serves index.html ✓
- POST /api/entity creates entity ✓
- DELETE /api/entity removes entity ✓
