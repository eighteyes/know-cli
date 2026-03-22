# QA: spec-dashboard
_Each answer maps to a graph entity or reference. See type hints per section._

## Actions & Operations  [-> action:*, operation:*]
1. **Navigation sequence**: User lands on kanban view with features as cards in phase-derived columns. Master nav at top shows Users > Objectives for scoping/filtering. Click a feature card to expand it into a sidecard showing parent context (user, objective) and child entities (actions, components, operations). Sub-drill via accordion expand in the sidecard.
2. **Drill-down responses**: Clicking a feature card opens a sidecard overlay/panel. System reads the feature's graph dependencies, resolves parent chain (objective, user), and renders the sidecard. URL updates to reflect selected feature. Pills on the kanban card show entity counts.
3. **View transitions**: Kanban is the primary view (no view change). Feature expand = sidecard panel (split view). Sub-drill into actions/components/operations = accordion expand within sidecard. Breadcrumb not needed — kanban remains visible behind/beside sidecard.
4. **Empty/error states**: Both — validation banner on load summarizing structural issues + inline badges on affected entities (e.g. "no actions linked" on a feature card, "dangling ref" badge, orphaned node indicator).

## Components & Responsibilities  [-> component:*]
6. **Core responsibilities**: Graph parser (JSON -> traversable structure), kanban renderer (phase columns + feature cards), sidecard renderer (parent context + child entities), entity pill/badge renderer, master nav (user/objective filter), validation engine (structural checks), URL state manager.
8. **Component I/O**: Graph parser: raw JSON in -> typed entity map + dependency index out. Kanban renderer: entity map + phases in -> column layout with cards out. Sidecard: feature key in -> resolved parent chain + child tree out. Validation engine: graph in -> issue list out.
9. **Reusable vs specific**: Entity card renderer, pill/badge components, accordion tree — reusable. Kanban layout, sidecard composition, master nav — dashboard-specific.
10. **Side effects**: `know serve` reads graph JSON from disk. URL hash/query for state persistence. No localStorage writes. No file writes from the dashboard itself.

## Data Models & Interfaces  [-> data-model:*, interface:*, api-contract:*]
11. **Graph data fields**: Reads meta (phases, project name), entities (all types with name/description), graph (depends_on, depends_on_ordered), references (all types). Key display fields per entity: name, description, type, dependency count.
12. **UI layout**: Full-width kanban as main view. Master nav bar at top (Users > Objectives as scope selectors). Feature cards in phase columns. Sidecard slides out on feature click (right panel or overlay). Sidecard has: header (feature name), parent section (user/objective), child tree (accordion), reference list.
13. **Kanban design**: Columns derived from meta.phases in spec-graph. Feature cards show: name, description snippet, pills for linked entity counts (actions, components, refs). Status transitions happen in the graph (read-only display). Optional: drag to reorder within column.
14. **Validation & errors**: Catch on load: missing dependency targets, orphaned nodes (no parent in graph), entities with no references or dependents, invalid type relationships per dependency-rules.json. Show: dismissible banner + inline badges.
Custom: Hierarchy boundary is at feature level. Above feature (project/user/objective) = master nav/tree. Feature = kanban cards. Below feature = sidecard accordion.

## Rules, Config & Constraints  [-> business-logic:*, configuration:*, constraint:*, acceptance-criterion:*]
16. **Drill vs expand logic**: Feature is the drill boundary. Above feature = master nav (nested tree/selector). Feature = kanban card (click to expand sidecard). Below feature = accordion expand within sidecard. Terminal nodes = operations and references (no further drill). Both depends_on and depends_on_ordered are followed; ordered renders in array sequence.
17. **Startup config**: `know serve` command resolves graph path (default .ai/know/spec-graph.json, overridable with -g flag). Initial view = kanban. Kanban columns derived from meta.phases at runtime.
18. **Access**: Local-only, single-user, no auth. Kanban is read-only display (status comes from graph phases, not user interaction). Dashboard does not write back to graph files.
20. **Acceptance criteria**: (a) Click feature card -> sidecard shows correct parent objective/user + all linked actions/components/operations. (b) All features appear in correct phase column based on meta.phases. (c) Validation banner shows on load if graph has issues, inline badges mark affected entities.
