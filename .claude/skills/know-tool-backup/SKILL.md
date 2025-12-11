---
name: know-tool
description: Master the know CLI tool for managing specification graphs. Use when working with spec-graph.json, understanding graph structure, querying entities/references/meta, managing dependencies, or learning graph architecture. Teaches dependency rules, entity types, and graph operations.
---

# Know Tool - Specification Graph Mastery

## What is the Specification Graph?

The specification graph (`.ai/spec-graph.json`) is a directed acyclic graph (DAG) representing software systems as interconnected nodes with explicit dependencies. Everything is a node, relationships are explicit, nothing is implied.

**Three node types:**

1. **Entities** - Structural nodes that participate in dependencies (user, feature, component, etc.)
2. **References** - Terminal nodes with implementation details (business_logic, data-models, etc.)
3. **Meta** - Project metadata (phases, assumptions, decisions, qa_sessions)

**Key principle:** The graph IS the source of truth. All relationships are explicit.

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

## Using know rules Commands

These commands expose the dependency structure for LLMs:

```bash
# Understand any type
know rules describe feature
know rules describe business_logic
know rules describe phases

# See dependency rules
know rules before component    # What can depend on component?
know rules after feature        # What can feature depend on?

# Visualize the structure
know rules graph                # See the full dependency map
```

**Always start with `know rules` commands before manipulating the graph.**

## Essential Commands

### Discovery & Exploration
```bash
know list                       # List all entities
know list-type feature          # List specific type
know get feature:real-time-telemetry
know deps feature:real-time-telemetry
know dependents component:websocket-manager
```

### Modification
```bash
know add feature new-feature '{"name":"...", "description":"..."}'
know add-dep feature:analytics action:export-report
know remove-dep feature:analytics action:export-report
```

### Validation
```bash
know validate                   # Must run after changes
know health                     # Comprehensive check
know cycles                     # Find circular dependencies
```

### Analysis
```bash
know gap-analysis feature:x     # Find missing dependencies
know gap-summary                # Overall implementation status
know ref-orphans                # Find unused references
know build-order                # Topological sort
```

## Reference Files

For detailed information, read these reference files:

- **[entity-types.md](references/entity-types.md)** - Deep dive on all entity types and their roles
- **[references-guide.md](references/references-guide.md)** - Understanding reference categories and when to use them
- **[meta-sections.md](references/meta-sections.md)** - Meta section structures and schemas
- **[commands-reference.md](references/commands-reference.md)** - Complete command listing with examples
- **[workflows.md](references/workflows.md)** - Common patterns: adding features, connecting actions, validation
- **[troubleshooting.md](references/troubleshooting.md)** - Debugging and fixing graph issues

## Quick Workflow Pattern

When adding a new feature:

```bash
# 1. Understand the type
know rules describe feature

# 2. Add the entity
know add feature new-feature '{"name":"...", "description":"..."}'

# 3. Check what it can depend on
know rules after feature

# 4. Connect dependencies
know add-dep feature:new-feature action:trigger-action

# 5. Validate
know validate
know deps feature:new-feature --recursive
```

## Critical Rules for LLMs

1. **Always validate after modifications** - Run `know validate`
2. **Respect entity vs reference distinction** - Entities participate in dependencies, references don't
3. **Follow dependency rules** - Use `know rules` to check before adding dependencies
4. **Maintain DAG properties** - No cycles allowed, check with `know cycles`
5. **Use full paths** - Always use `type:key` format (e.g., `feature:real-time-telemetry`)
6. **Never add dependencies to entity objects** - Only in the `graph` section
7. **Check completeness** - Use `know gap-analysis` to ensure full dependency chains

## When to Read Which Reference

- **Adding/modifying entities?** → Read [entity-types.md](references/entity-types.md) and [workflows.md](references/workflows.md)
- **Working with references?** → Read [references-guide.md](references/references-guide.md)
- **Updating meta sections?** → Read [meta-sections.md](references/meta-sections.md)
- **Need command details?** → Read [commands-reference.md](references/commands-reference.md)
- **Debugging issues?** → Read [troubleshooting.md](references/troubleshooting.md)

## Installation Note

If `know` command is not found, the tool is at `/Users/god/projects/know-cli/know/know`. See project INSTALL.md for setup.

---

**Remember:** The graph is dependency-driven. Use `know rules` to understand structure before making changes. Always validate after modifications.
