# spec-dashboard

Interactive HTML dashboard for visualizing spec-graph data. Kanban-first design with drillable feature cards.

## Architecture

**Master Nav** (top bar): Users > Objectives as scope selectors/filters
**Kanban Board** (main view): Features as cards in columns derived from meta.phases
**Feature Cards**: Name, description snippet, pills for linked entity counts
**Sidecard** (right panel): Expands on feature click — shows parent context (user/objective), child entities (actions/components/operations) as accordion tree, linked references
**Validation**: Banner on load + inline badges on affected entities

## Hierarchy Model

```
master-nav:  project > user > objective  (tree/selector — scoping only)
kanban:      feature cards in phase columns  (THE view)
sidecard:    action / component / operation  (accordion expand)
terminal:    operation, references  (leaf display)
```

## CRUD Operations

Dashboard supports basic know actions via REST API proxy:
- **Change phase**: Drag feature cards between kanban columns (calls `know phases`/`know meta set`)
- **Add entities/refs**: Modal/inline form to create new entities and references (calls `know add`)
- **Edit entities/refs**: Inline editing of name/description fields (calls know CLI to update)
- **Link/unlink**: Add or remove dependencies between entities (calls `know link`/`know unlink`)

All writes go through `cli-proxy` component on the server, which shells out to know CLI commands.
Client uses `mutation-handler` component for optimistic updates and error handling.

## Data Flow

```
Browser → mutation-handler → POST /api/* → cli-proxy → know CLI → spec-graph.json
Browser ← re-render ← GET /api/graph ← know serve ← spec-graph.json
```

## Tech

Lightweight framework (Preact or Alpine) + D3 for any graph visualization. Minimal deps, small bundle.

## Constraints

- Local-only, single-user, no auth
- Kanban columns from meta.phases (not hardcoded)
- Follows dependency-rules.json for valid parent-child relationships
- All mutations go through know CLI (no direct file writes from server)
