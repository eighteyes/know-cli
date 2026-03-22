# Exploration: spec-dashboard

## Project Structure
- Python Click CLI: `know/know.py` (~6500+ lines, monolithic)
- Source modules: `know/src/` (graph.py, cache.py, entities.py, workflow.py, dependencies.py, validation.py)
- Visualizers: `know/src/visualizers/` (8 visualizers including D3 force-directed and D3 tree)
- Templates: `know/templates/commands/` (slash command templates)
- Node wrapper: `bin/know.js`
- No existing HTTP server or dashboard

## Key Architecture Insights

### Graph I/O Stack
```
CLI command (Click) → Manager class → GraphManager.save_graph() → GraphCache.write() (atomic with flock)
```
- `GraphCache` (cache.py): mtime-based caching, atomic writes via tempfile + os.replace, fcntl.flock
- `GraphManager` (graph.py): load/save, diff logging to diff-graph.jsonl, NetworkX graph
- `EntityManager` (entities.py): entity/reference CRUD, dependency add/remove
- All writes converge on `GraphManager.save_graph()` — single choke point

### Existing D3 Visualizers
- `D3Visualizer` (d3.py): ~525 lines HTML/JS template, force-directed graph, D3 v7 from CDN
- `D3TreeVisualizer` (d3_tree.py): collapsible tree, DAG-to-tree conversion
- Both generate standalone HTML with embedded data — good pattern reference
- `BaseVisualizer.extract()` pipeline: reads graph, filters, builds VisualizationData
- `theme.py`: shared ENTITY_COLORS dict with fill/stroke/rich_style per entity type

### AsyncGraphManager
- `know/src/async_graph.py` — described as "Async wrapper for graph operations to support web server integration"
- Already exists but unused — potential server foundation

### Graph Protect Hook
- `.claude/hooks/protect-graph-files.sh` blocks Edit/Write/jq/sed on *-graph.json
- Read-only ops (cat, grep, head, tail) allowed
- All dashboard mutations must go through know CLI

## Write Paths for HTTP Proxy

| Command | What it does | Saves |
|---|---|---|
| `know add <type> <key> <json>` | Creates entity or reference | 1 save |
| `know link <from> <to1> <to2>...` | Adds dependencies | N saves (1 per target) |
| `know unlink <from> <to>` | Removes dependency | 1 save |
| `know meta set <section> <key> <data>` | Updates meta | 1 save |
| `know phases add <phase> <entity>` | Adds entity to phase | 1 save |
| `know phases move <entity> <phase>` | Moves entity between phases | 1 save |
| `know phases status <entity> <status>` | Updates status in phase | 1 save |

## Server Strategy
- Shell out to know CLI for all mutations (honors all validation, hooks, diff logging)
- Serve static HTML/JS/CSS + GET /api/graph endpoint
- POST endpoints map 1:1 to know CLI commands
- `AsyncGraphManager` could be used for read caching but mutations still go through CLI
- flock-based locking handles concurrent access at file level

## Reusable Assets
- Entity color scheme from `theme.py`
- D3 patterns from existing visualizers
- Graph extraction pipeline from `BaseVisualizer`
- No existing frontend framework code — clean slate for Preact/Alpine
