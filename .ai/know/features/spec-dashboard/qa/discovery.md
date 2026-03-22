# Discovery: spec-dashboard

## Success Criteria
- Kanban board renders features in phase-derived columns from spec-graph.json
- Master nav scopes by user > objective
- Feature card click opens sidecard with parent context + child entity tree
- CRUD: change phase, add/edit entities+refs, link/unlink — all via know CLI proxy
- Validation banner + inline badges on structural issues
- `know serve` starts local server, opens browser

## Constraints
- Local-only, single-user, no auth
- All mutations proxy through know CLI (no direct JSON writes)
- Kanban columns from meta.phases (not hardcoded)
- Lightweight framework (Preact/Alpine) + D3

## Out of Scope
- Multi-user / auth
- Code-graph visualization (spec-graph only for v1)
- Drag-to-reorder within a column (drag between columns = phase change only)
- Complex graph editing (bulk operations, merge, rename — use CLI for those)

## Users
- `developer` — primary user, uses dashboard for visual spec-graph exploration and quick edits

## Edge Cases
- Empty graph (no features, no phases)
- Feature with no phase assignment
- Circular dependencies in graph
- Very large graphs (100+ entities)
- CLI command failures (validation errors, missing entities)
- Concurrent edits (user edits graph via CLI while dashboard is open)

## Graph Context
- Parent: objective:enhance-graph-model → user:developer
- 33 dependency nodes (8 actions, 5 operations, 9 components, 11 references)
