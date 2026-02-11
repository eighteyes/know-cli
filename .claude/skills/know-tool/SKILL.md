---
name: know-tool
description: Master the know CLI tool for managing specification graphs. Use when working with spec-graph.json, understanding graph structure, querying entities/references/meta, managing dependencies, or learning graph architecture. Teaches dependency rules, entity types, and graph operations.
---

# Know Tool - Specification Graph Mastery

## What is the Specification Graph?

The specification graph (`.ai/know/spec-graph.json`) is a directed acyclic graph (DAG) representing software systems as interconnected nodes with explicit dependencies. Everything is a node, relationships are explicit, nothing is implied.

**Three node types:**

1. **Entities** - Structural nodes that participate in dependencies (user, feature, component, etc.)
2. **References** - Terminal nodes with implementation details (business_logic, data-models, etc.)
3. **Meta** - Project metadata (phases, assumptions, decisions, qa_sessions)

**Key principle:** The graph IS the source of truth. All relationships are explicit.

## Phases in meta.phases

The `meta.phases` section tracks feature lifecycle and scheduling:

**Phase Types:**
- `I, II, III` - Scheduling phases (immediate, next, future)
- `pending` - Not yet scheduled
- `done` - Completed and archived

**Phase Status:**
- `incomplete` - Feature added but not started
- `in-progress` - Active development
- `review-ready` - Implementation complete, awaiting review
- `complete` - Finished (in done phase)

**Phase Lifecycle:**
```
/know:add    → pending phase, status: incomplete
/know:build  → status: in-progress → review-ready
/know:done   → done phase, status: complete
```

## Core Mental Model

### Two Chains

**WHAT Chain (User Intent):**
```
project → user → objective → action
```

**HOW Chain (Implementation):**
```
project → requirement → interface → feature → action → component → operation
```

Action connects both chains - what users DO and how the system implements it.

### Dependency Rules

Dependencies are strict and unidirectional:
- Only entities participate in dependencies
- References are terminal nodes (no dependencies)
- Graph must remain a DAG (no cycles)

## Command Groups

Know CLI uses a flat structure with auto-detection:

| Command | Purpose |
|---------|---------|
| `know get <type:key>` | Get entity or reference (auto-detects) |
| `know list [--type TYPE]` | List entities or references (auto-detects) |
| `know add <type> <key> <json>` | Add entity or reference (auto-detects) |
| `know nodes` | Node operations: deprecate, merge, rename, delete, cut, clone |
| `know meta get/set` | Get or set meta sections |
| `know graph` | Link, unlink, traverse dependencies |
| `know check` | Validate, health, stats, gaps, orphans |
| `know gen` | Generate specs, maps, traces, rules |
| `know feature` | Contracts, coverage, block, complete |
| `know phases` | Phase management |

## Using know gen rules Commands

These commands expose the dependency structure for LLMs:

```bash
# Understand any type
know gen rules describe feature
know gen rules describe business_logic
know gen rules describe phases

# See dependency rules
know gen rules before component    # What can depend on component?
know gen rules after feature        # What can feature depend on?

# Visualize the structure
know gen rules graph                # See the full dependency map
```

**Always start with `know gen rules` commands before manipulating the graph.**

## Essential Commands

### Discovery & Exploration
```bash
know list                           # List all entities
know list --type feature            # List entities of type (auto-detects entity vs reference)
know list --type business_logic     # List references of type (auto-detects)
know get feature:real-time-telemetry   # Get entity (auto-detects)
know get business_logic:login          # Get reference (auto-detects)

# Dependencies
know graph uses feature:real-time-telemetry          # What does this entity use? (dependencies)
know graph used-by component:websocket-manager       # What uses this entity? (dependents)
know graph up feature:x                              # Alias for 'uses' (go up dependency chain)
know graph down component:y                          # Alias for 'used-by' (go down chain)

# Statistics
know check stats                    # Graph statistics (entity counts, dependencies)
know check completeness feature:x   # Completeness score for an entity
```

### Modification
```bash
know add feature new-feature '{"name":"...", "description":"..."}'       # Add entity (auto-detects)
know add documentation new-doc '{"title":"...", "url":"..."}'            # Add reference (auto-detects)
know meta set project key '{"value":"..."}'                              # Set meta value
know meta get project                                                    # Get meta section
know graph link feature:analytics action:export-report     # Add dependency
know graph unlink feature:analytics action:export-report   # Remove dependency
```

### Validation
```bash
know check validate                 # Must run after changes (includes fix commands in errors)
know check health                   # Comprehensive check
know check cycles                   # Find circular dependencies
```

### Requirements Management
```bash
know feature block <requirement-id> --by "reason"   # Mark requirement blocked
know feature complete <requirement-id>              # Mark requirement complete
```

**Requirement status values:** pending, in-progress, blocked, complete, verified

Requirements are managed through `meta.requirements` in the graph. Use `know meta get requirements` to view all.

### Node Operations (`know nodes`)
```bash
# Deprecation
know nodes deprecate entity:id --reason "..." [--replacement entity:new]
know nodes undeprecate entity:id
know nodes deprecated             # List all deprecated entities
know nodes deprecated --overdue   # Only entities past removal date

# Modification
know nodes update entity:id '{"name":"New Name"}'  # Update properties
know nodes rename entity:id new-key                # Rename entity key
know nodes clone entity:id new-key                 # Clone with all dependencies
know nodes clone entity:id new-key --no-upstream  # Clone without incoming deps

# Removal
know nodes delete entity:id       # Remove entity and clean up dependencies
know nodes cut entity:id          # Remove entity only, leave deps orphaned

# Merging
know nodes merge from:entity into:entity      # Merge entities, transfer deps
know nodes merge from:entity into:entity --keep  # Keep source after merge
```

### Test Coverage
```bash
know feature coverage feature           # Aggregate coverage from feature level
know feature coverage feature --detail  # Per-component breakdown
```

**Note:** Validation errors now include example fix commands. For example:
```
✗ Invalid dependency: feature:x → component:y. feature can only depend on: action
  Fix: know graph unlink feature:x component:y
```

### Analysis
```bash
know check gap-analysis feature:x  # Find missing dependencies
know check gap-missing             # List missing connections in chains
know check gap-summary             # Overall implementation status
know check orphans                 # Find unused references
know check usage                   # Reference usage statistics
know check suggest                 # Suggest connections for orphaned references
know check clean                   # Clean up unused references
know graph build-order             # Topological sort
know gen trace entity:x            # Trace entity across product-code boundary
know graph connect entity:x        # Suggest valid connections for an entity
```

### Specification Generation
```bash
know gen spec entity:x              # Generate complete spec deterministically
know gen trace-matrix               # Show requirement traceability matrix
know gen trace-matrix -t component  # Trace specific entity type
know gen sitemap                    # Generate sitemap of all interfaces
```

**`know gen spec` produces comprehensive output:**
- Phase and status information
- Auto-generated user story (As a [user], I want to [action] so that [objective])
- Full traceability chain (user → objective → feature → component)
- Dependencies grouped by type with descriptions
- Requirements list with status icons
- Related references (data-models, business_logic, etc.)

### Advanced
```bash
know graph diff graph1.json graph2.json  # Compare two graph files
know init                                # Initialize know workflow in a project
```

## Reference Files

For detailed information, read these reference files:

- **[creating.md](references/creating.md)** - Guide to creating entities and references
- **[generating.md](references/generating.md)** - Specification generation patterns
- **[validating.md](references/validating.md)** - Graph validation and health checks
- **[qa-steps.md](references/qa-steps.md)** - QA testing patterns

## Quick Workflow Pattern

When adding a new feature:

```bash
# 1. Understand the type
know gen rules describe feature

# 2. Add the entity
know add feature new-feature '{"name":"...", "description":"..."}'

# 3. Check what it can depend on
know gen rules after feature

# 4. Connect dependencies
know graph link feature:new-feature action:trigger-action

# 5. Validate
know check validate
know graph uses feature:new-feature --recursive
```

## Phase Management

**Phase** = Roman numerals (I, II, III) - WHEN to do this feature (planning waves)
**Status** = in-progress, complete, planned - current state of the work

Phase is the plan, status is the territory. A feature can be `phase: III` (planned for wave 3) but `status: in-progress` (started early).

```bash
know phases                          # Alias for phases list
know phases list                     # Show all features organized by phase
know phases add <phase> <entity>     # Add feature to phase (e.g., know phases add I feature:auth)
know phases move <entity> <phase>    # Move feature to different phase
know phases status <entity> <status> # Update status (planned, in-progress, complete)
know phases remove <entity>          # Remove entity from all phases
```

**Output includes:**
- Phase metadata (shortname, name, description) from `meta.phases_metadata`
- Features within each phase
- Requirement completion counts (from `meta.requirements`)
- Status icons (✅ complete, 🔄 in-progress, 📋 planned)
- Summary totals

**Example output:**
```
Phase I (Foundation)
  🔄 feature:auth (3/5) - Authentication system

Phase II (Features)
  📋 feature:api-gateway (0/4) - API routing

Phase III (Polish)
  📋 feature:dark-mode (--) - No requirements yet
```

**Note:** "--" indicates no requirements exist yet for that feature.

## Requirements vs Todo.md

**Requirements replace todo.md** for progress tracking:
- Requirements are stored in `meta.requirements`
- Each feature links to requirement entities via depends_on
- Status tracked in `meta.requirements[key].status`
- Query requirements: `know meta get requirements`
- Update status: `know feature complete <req-id>` or `know feature block <req-id> --by "reason"`

## Critical Rules for LLMs

1. **Always validate after modifications** - Run `know check validate`
2. **Respect entity vs reference distinction** - Entities participate in dependencies, references don't
3. **Follow dependency rules** - Use `know gen rules` to check before adding dependencies
4. **Maintain DAG properties** - No cycles allowed, check with `know check cycles`
5. **Use full paths** - Always use `type:key` format (e.g., `feature:real-time-telemetry`)
6. **Never add dependencies to entity objects** - Only in the `graph` section
7. **Check completeness** - Use `know check gap-analysis` to ensure full dependency chains

## Installation Note

If `know` command is not found, run `python3 know/know.py` from the project root. See project INSTALL.md for setup.

---

**Remember:** The graph is dependency-driven. Use `know gen rules` to understand structure before making changes. Always validate after modifications.
