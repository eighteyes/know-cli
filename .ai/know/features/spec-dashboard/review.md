# Quality Review: spec-dashboard

## Issues Found & Fixed

### Critical
1. **Path traversal in static file serving** — `file_path` was not validated against `WWW_DIR`. Fixed: added `.resolve()` + startswith check.

### High
2. **URL-encoded entity IDs not decoded** — Entity IDs from URL paths were used raw. Fixed: added `_extract_entity_id()` helper using `urllib.parse.unquote`.
3. **Stale graph after phase+status write** — `_read_graph()` was called before optional status write completed. Fixed: moved read after all mutations.
4. **Unhandled `json.JSONDecodeError` in `_read_body`** — Malformed JSON bodies would crash the thread. Fixed: wrapped in try/except, returns `{}`.
5. **`project_cwd` derived from path depth** — Fragile assumption. Fixed: `serve()` now accepts explicit `project_cwd` parameter, CLI passes `Path.cwd()`.

### Medium
6. **ANSI strip regex duplicated** — Same regex used in two places. Fixed: extracted `_strip_ansi()` helper.
7. **Dead `dragging` state** — `useState(null)` set but never read. Fixed: removed.
8. **Entity colors duplicated in CSS vars + JS** — CSS vars and JS objects had same values. Fixed: kept only the 3 CSS vars actually used in selectors, JS handles inline styles.
9. **`Content-Type` sent on GET requests** — api.js set header unconditionally. Fixed: only set when body exists.
10. **`BASE = ''` constant** — No-op constant removed.

### Acknowledged (not fixed)
- `allEntities` in LinkModal rebuilt every render — acceptable for local tool, graph is small
- Filter asymmetry (user = 2-hop, objective = 1-hop) — correct for the entity hierarchy
- Partial failure on add+link — entity created but link fails leaves stale UI until refresh. Acceptable: next re-fetch corrects it.
