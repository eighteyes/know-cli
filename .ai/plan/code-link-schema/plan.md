# Plan: code-link Cross-Graph Schema

## Problem

Cross-graph linking (spec ↔ code) is:
- Broken: `implementation` type used in skills but not in spec-graph rules
- Redundant: `graph-link` + `product-component` both exist in code-graph, doing the same job
- Optional: `/know:build` Phase 5 explicitly calls linking optional → AI skips it
- Incomplete: only features linked, not components
- Unnamed: `graph-link` is ambiguous — a link to what?

## Decision

**Single reference type: `code-link`** — used in both graphs, schema differs by context.

| Graph | Type | Shape | Replaces |
|-------|------|-------|----------|
| spec-graph | `code-link` | `{ modules, classes, packages, status }` | `code-module` + `implementation` |
| code-graph | `code-link` | `{ feature, component, status }` | `graph-link` + `product-component` |

Both apply at: **feature AND component** level (spec-graph), **module AND class** level (code-graph).

Old types (`graph-link`, `product-component`, `code-module`) kept in rules for backward compat — marked deprecated in description.

---

## Tasks

### 1. Schema — dependency-rules.json (spec-graph)
- Add `code-link` to `reference_types` array
- Add `code-link` to `reference_description`: "Cross-graph link from a spec entity (feature/component) to implementing code entities. Shape: `{ modules: [...], classes: [...], packages: [...], status: 'planned|in-progress|complete' }`"
- Mark `code-module` as deprecated in description

### 2. Schema — code-dependency-rules.json (code-graph)
- Add `code-link` to `reference_types` array
- Add `code-link` to `reference_description`: "Cross-graph link from a code entity (module/class) to the spec entities it implements. Shape: `{ feature: 'feature:x', component: 'component:y', status: 'planned|in-progress|complete' }`"
- Mark `graph-link` and `product-component` as deprecated in their descriptions

### 3. New command — `know graph cross connect [feature]`
In `know.py`, add `cross` group under `graph`, with `connect` subcommand:
- Auto mode by default (no confirmation). `--dry-run` to preview.
- If `[feature]` omitted: connects ALL features missing code-links
- For each feature + its components:
  - Tokenize key (split on `-`, strip type prefix)
  - Search code-graph modules/classes for token overlap ≥ 1 (fuzzy match)
  - Score matches by token overlap count, take top match per entity
  - Creates `code-link` ref in spec-graph: `{ modules: [...], classes: [...], status: "in-progress" }`
  - Creates `code-link` ref in code-graph for each matched entity: `{ feature: "...", component: "...", status: "in-progress" }`
  - Links both directions in the graph section
- Validates both graphs after all links created
- Reports table: "feature:X → module:Y (score:2), module:Z (score:1)"
- Reports unmatched: "No match found for: component:sidebar-filter"

### 4. know:plan — add placeholder scaffolding
After feature entity creation, add:
```bash
# Create placeholder code-link (planned — fill in during build)
know -g .ai/know/spec-graph.json add code-link <feature>-code '{"modules":[],"classes":[],"status":"planned"}'
know -g .ai/know/spec-graph.json link feature:<name> code-link:<feature>-code
```
Repeat for each component scaffolded in the plan.

### 5. know:prepare — add code-link creation during analysis
After mapping existing code to spec entities:
```bash
# Create code-links from discovered mappings
know -g .ai/know/spec-graph.json add code-link <feature>-code '{"modules":["module:x"],"status":"complete"}'
know -g .ai/know/spec-graph.json link feature:<name> code-link:<feature>-code
know -g .ai/know/code-graph.json add code-link <module> '{"feature":"feature:<name>","status":"complete"}'
know -g .ai/know/code-graph.json link module:<name> code-link:<module>
```

### 6. know:prebuild — add code-link validation gate
Add Phase 0 check before spec comparison:
```bash
# Verify code-links exist (planned is ok, missing is a warning)
know -g .ai/know/spec-graph.json graph uses feature:<name> | grep code-link
```
If no `code-link` refs found: warn "No code-link placeholders. Run `/know:plan` or `know feature connect`."

### 7. know:build — make cross-graph linking mandatory
Phase 5, Step 7:
- Remove "NOTE: ...optional during implementation" language entirely
- Replace with: "REQUIRED: Create code-link refs for every new module/class written"
- Add named checkpoint task: `{ type: "checkpoint:human-verify", name: "Cross-graph links" }`
- Phase 7 Step 6b: If `feature status` shows `Implemented: No` → BLOCK phase completion, require `know feature connect <feature>`

### 8. New command — `know graph coverage` (restore) + `know graph cross coverage`

#### `know graph coverage`
Referenced in `know:connect` as `know -g spec-graph.json coverage` but never implemented.
Add to `graph` group in `know.py`:
- Counts entities reachable from root users via dependency chain
- Shows % coverage and lists disconnected entities
- Matches what `know:connect` already documents/expects

#### `know graph cross coverage`
Add `cross` group under `graph`, with `coverage` subcommand:

Reads both graphs, outputs a coverage table:

```
Cross-Graph Coverage
─────────────────────────────────────────────
Spec → Code
  Features:    12 / 20  (60%)   ← has code-link
  Components:   4 / 35  (11%)   ← has code-link

Code → Spec
  Modules:     18 / 30  (60%)   ← has code-link
  Classes:      2 / 12  (17%)   ← has code-link

Missing code-link (spec side):
  feature:export-pipeline
  feature:user-auth
  component:sidebar-filter
  ...

Missing code-link (code side):
  module:graph-validator
  class:DependencyResolver
  ...
```

- `--spec-only` — show only spec side
- `--code-only` — show only code side
- `--json` — machine-readable output for AI agents

This becomes the metric AI builds toward: 100% cross-graph coverage = every spec entity has a code counterpart and vice versa.

### 9. Update know:connect skill
- Fix `know -g .ai/know/spec-graph.json coverage` → `know graph coverage`
- Replace `implementation`/`graph-link` commands with `code-link` commands in cross-graph section
- Replace `know feature connect` references with `know graph cross connect`

### 10. know-tool SKILL.md — update reference type docs
Add `code-link` to reference types table, mark old types as deprecated.

---

## File Targets

| File | Change |
|------|--------|
| `know/config/dependency-rules.json` | Add `code-link` type + schema |
| `know/config/code-dependency-rules.json` | Add `code-link` type + schema, deprecate `graph-link`/`product-component` |
| `know/know.py` | Add `know graph coverage`, `know graph cross connect`, `know graph cross coverage` |
| `.claude/commands/know/plan.md` | Add placeholder `code-link` scaffolding steps |
| `.claude/commands/know/prepare.md` | Add `code-link` creation during code analysis |
| `.claude/commands/know/prebuild.md` | Add `code-link` existence check as Phase 0 gate |
| `.claude/commands/know/build.md` | Make Phase 5 cross-graph linking mandatory, gate Phase 7 |
| `.claude/commands/know/connect.md` | Update cross-graph section to use `code-link` |
| `.claude/skills/know-tool/SKILL.md` | Update reference type docs |

## Out of Scope
- Migrating existing graph data (no existing cross-graph links to migrate)
- Removing old types from rules (backward compat — deprecate only)
- Changing `know gen code-graph` behavior

## Grade: A
