# spec-dashboard — Todo

## Setup
- [x] Add `know serve` command to know.py
- [x] Create know/src/server.py (HTTP handler + CLI proxy)
- [x] Create know/www/index.html (Preact + HTM dashboard)
- [x] Create know/www/api.js (fetch wrappers)

## Core
- [x] Graph parser — reads spec-graph.json directly via file read
- [x] Kanban renderer — phase columns + feature cards
- [x] Master nav — user/objective scope selector
- [x] Sidecard — parent context + child accordion tree
- [x] Entity pills/badges on feature cards
- [x] Column ordering — reversed roman numerals (V→I), unphased at right

## CRUD
- [x] Add entity modal — type, key, name, description
- [x] Edit entity inline — name, description via contenteditable
- [x] Link entity modal — search + click to link
- [x] Unlink entity — button in sidecard
- [x] Change phase — drag and drop between columns
- [x] Delete entity — via CLI proxy endpoint

## Undo & History
- [x] Undo stack — snapshot-based, max 30, thread-safe
- [x] Undo button in nav with badge count
- [x] History panel — reads diff-graph.jsonl, shows timestamped entries
- [x] Change pills — color-coded added/removed/modified

## AI Chat
- [x] Chat panel — bottom-right floating, toggle with ◈ button
- [x] Claude CLI integration — execPath auth passthrough, stream-json output
- [x] System prompt with graph context (features, actions, components, phases)
- [x] SSE streaming — real-time response rendering
- [x] Chat status check — indicates if claude CLI available

## Hot Updates
- [x] File watcher — background thread, 500ms mtime polling
- [x] SSE endpoint — GET /api/events, pushes graph-updated events
- [x] Auto-refresh — browser re-fetches graph on SSE event
- [x] Heartbeat — 15s keepalive for SSE connections

## Validation
- [x] Client-side validation — orphans, dangling refs, missing deps
- [x] Banner display for graph issues
- [x] Inline badges on affected entities (via pills)

## Design
- [x] Phosphor Observatory aesthetic — DM Serif Text + IBM Plex Mono
- [x] Luminous entity colors against deep void backgrounds
- [x] Dot-grid texture overlay
- [x] Staggered column animations, spring-eased sidecard, modal backdrop blur

## Remaining
- [ ] URL hash state persistence
- [ ] Responsive layout for narrow screens
- [ ] Keyboard navigation (Esc to close, arrows to navigate)
