# Clarification: spec-dashboard

## Resolved by Decision (no user input needed)

1. **Framework choice**: Preact over Alpine. Reason: component model maps well to our architecture (kanban-renderer, sidecard-renderer, etc.), JSX is more productive for complex UIs, and Preact is ~3KB.

2. **Server framework**: Python's built-in `http.server` + custom handler. Reason: know CLI is Python, no need to add Node/Express. Keep deps minimal. Use subprocess to shell out to know CLI for mutations.

3. **Build step**: None initially. Single HTML file with Preact from CDN (via HTM for JSX-like syntax without build). D3 from CDN. Can add a build step later if needed.

4. **Entity editing**: For v1, edit name/description only. No type/key changes (those are destructive — use `know nodes rename` via CLI).

5. **Graph refresh after mutation**: After any successful POST, client does GET /api/graph to reload the full graph. No WebSocket push for v1 — simple and sufficient for single-user.

6. **Concurrent edit handling**: flock at file level handles this. If user edits via CLI while dashboard is open, next GET /api/graph picks up changes. No conflict resolution needed for single-user.

7. **Large graph performance**: For v1, load entire graph into memory. spec-graphs are typically <500KB. If performance is an issue, add pagination/virtualization later.

## Assumptions
- Dashboard HTML/JS lives in `know/www/` directory, served as static files
- `know serve` is a new Click command in know.py
- Port defaults to 3000, configurable with --port flag
- Server opens browser automatically on start (like existing viz --open)
