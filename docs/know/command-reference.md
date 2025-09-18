# Know Tool Command Reference

## Overview
The `know` tool is a zero-LLM dependency shell + jq implementation for generating implementation specifications from a knowledge map (spec-graph.json).

## Core Concepts

### Entity Reference Format
- `<type>:<id>` - Full reference (e.g., `feature:real-time-telemetry`)
- `<id>` - Auto-detect type if unique (e.g., `real-time-telemetry`)

### Global Options
- `--format <md|json|yaml>` - Output format (default: md)
- `--output <file>` - Save output to file
- `--map <file>` - Use custom knowledge map file
- `--ai` - Generate Claude-optimized specification
- `--install-completion` - Install bash autocomplete
- `--completion-status` - Check autocomplete status
- `--help` - Show help

## Command Categories

### 1. Core Operations

#### `know list [entity_type]`
List available entities by type.
- **Parameters**: Optional entity_type (features, components, screens, functionality, requirements)
- **Example**: `know list features`
- **Logic**: Calls `list_entities()` → queries graph for entity type

#### `know search <term> [entity_type]`
Find entities by name or description.
- **Parameters**:
  - `term` - Search string (required)
  - `entity_type` - Optional filter
- **Example**: `know search telemetry`
- **Logic**: Calls `search_entities()` → filters entities by matching term

#### `know check <type> <entity_id>`
Validate entity completeness.
- **Parameters**:
  - `type` - Entity type
  - `entity_id` - Entity identifier
- **Example**: `know check feature real-time-telemetry`
- **Logic**: Resolves reference → calls `validate_entity_completeness()`

#### `know check references`
Check all reference keys have parent entities.
- **Logic**: Executes `check-reference-parents.sh` script

#### `know preview <type> <entity_id>`
Preview what will be generated for an entity.
- **Parameters**: Same as `check`
- **Example**: `know preview component fleet-status-map`
- **Logic**: Shows completeness score and preview without generating

### 2. Entity-Specific Commands

#### `know feature [entity_id]`
Generate feature specification or list features.
- **Parameters**: Optional entity_id
- **Example**: `know feature real-time-telemetry`
- **Logic**:
  1. Check completeness (minimum 70%)
  2. If passed, generate spec via `simple-feature-spec.sh`
  3. Without ID, lists all features

#### `know component [entity_id]`
Generate component specification or list components.
- **Logic**: Same as feature command

#### `know screen [entity_id]`
Generate screen/UI specification or list screens.
- **Logic**: Uses `simple-screen-spec.sh` generator

#### `know functionality [entity_id]`
Generate functionality specification or list functionality.

#### `know requirement [entity_id]`
Generate requirement specification or list requirements.

### 3. Analysis & Dependencies

#### `know deps <entity_ref>`
Show dependency chain for an entity.
- **Parameters**: entity_ref (required)
- **Example**: `know deps feature:user-auth`
- **Logic**: Resolves reference → calls `show_dependencies()`

#### `know impact <entity_ref>`
Show what depends on this entity (reverse dependencies).
- **Parameters**: entity_ref (required)
- **Example**: `know impact component:auth-manager`
- **Logic**: Resolves reference → calls `show_impact_analysis()`

#### `know validate <entity_ref> [--comprehensive] [--min-score N]`
Check reference integrity and completeness.
- **Parameters**:
  - `entity_ref` - Entity to validate
  - `--comprehensive` - Detailed validation
  - `--min-score` - Minimum acceptable score (default: 70)
- **Logic**: Comprehensive mode uses `validate_entity_comprehensive()`

#### `know validate-deps`
Validate dependency chains against rules.
- **Logic**: Executes `validate-dependencies.sh`

#### `know validate-graph`
Full graph structure and dependency validation.
- **Logic**: Executes `validate-spec-graph.sh` with dependency rules

#### `know order`
Show optimal implementation order based on dependencies.
- **Logic**: Calls `show_implementation_order()`

#### `know blockers`
Show entities blocking implementation (< 70% complete).
- **Logic**: Iterates entity types → calculates scores → identifies blockers

### 4. Gap Analysis

#### `know gaps <entity_ref>`
Show missing information for an entity.
- **Parameters**: entity_ref (required)
- **Example**: `know gaps feature:analytics`
- **Logic**: Runs comprehensive validation → extracts gap sections

#### `know gap-analyze <entity_id>`
Analyze implementation gaps for entity.
- **Logic**: Executes `gap-analysis.sh analyze`

#### `know gap-analyze-all`
Analyze all users and objectives.
- **Logic**: Executes `gap-analysis.sh analyze-all`

#### `know gap-summary`
Show gap analysis summary.
- **Logic**: Executes `gap-analysis.sh summary`

#### `know gap-report [format]`
Generate comprehensive gap report.
- **Parameters**: format (text|json|html)
- **Logic**: Executes `gap-reporter.sh`

#### `know gap-qa` / `know chain-builder`
Interactive full chain builder.
- **Logic**: Executes `full-chain-qa.sh`

#### `know gap-score <entity_id>`
Get completeness score for entity.
- **Logic**: Executes `completeness-scorer.sh score`

### 5. Workflows & Automation

#### `know create-feature`
Interactive feature creation wizard.
- **Logic**: Calls `create_feature_interactive()`

#### `know complete <entity_ref>`
Interactive gap completion for an entity.
- **Logic**: Calls `complete_entity_interactive()`

#### `know implementation-chain <entity_ref>`
Create full implementation plan.
- **Logic**: Calls `create_implementation_chain()`

#### `know priorities`
Show implementation priorities.
- **Logic**: Calls `show_implementation_priorities()`

#### `know completeness [entity_type]`
Show completeness scores for entities.
- **Parameters**: Optional entity_type filter
- **Logic**: Calls `analyze_completeness_batch()`

#### `know ready-check <entity_ref>`
Implementation readiness check.
- **Logic**: Validates entity → reports ready/not ready status

#### `know todo`
Show next actions needed.
- **Logic**: Finds incomplete features → lists priority actions

#### `know package <entity_id>`
Complete implementation package.
- **Logic**: Calls `generate_package()`

#### `know test <entity_ref>`
Generate test scenarios.
- **Logic**: Calls `generate_test_scenarios()`

### 6. Graph Management

#### `know mod <command> [args...]`
Modify graph (add, edit, connect entities).
- **Subcommands**: add, edit, connect, remove, rename, etc.
- **Logic**: Forwards to `mod-graph.sh` or `mod-graph-enhanced.sh`

#### `know query <command> [args...]`
Query graph (traverse, stats, paths).
- **Subcommands**: traverse, stats, paths, cycles, etc.
- **Logic**: Forwards to `query-graph.sh`

#### `know component-map <cmd> [args...]`
Map components to interfaces.
- **Logic**: Forwards to `component-map.sh`

### 7. Maintenance & Health

#### `know health`
Comprehensive graph health check.
- **Logic**: Calls `check_graph_health()`

#### `know repair [mode]`
Fix graph issues.
- **Parameters**: mode (interactive|auto|hanging|orphans|missing|self-deps|cycles)
- **Logic**: Calls `repair_graph()`

### 8. Dependency Rules

#### `know rules`
Show allowed dependency patterns.
- **Logic**: Reads and displays `dependency-rules.json`

#### `know suggest <entity>`
Suggest valid connections for entity.
- **Logic**: Calls `suggest_connections()`

#### `know validate-connection <from> <to>`
Check if connection is allowed.
- **Logic**: Calls `validate_connection()`

#### `know connect-references [interactive|batch]`
Connect orphaned reference keys.
- **Modes**:
  - `interactive` - FZF tool for connections
  - `batch <ref> <entity>` - Batch connect
- **Logic**: Executes `connect-references.sh`

### 9. Navigation & Routing

#### `know sitemap`
Generate sitemap with page hierarchy.
- **Logic**: Executes `sitemap.sh`

#### `know routes`
Show all pages and API endpoints.
- **Logic**: Executes `routes.sh`

### 10. Phase Management

#### `know phases display`
Show current implementation phases.
- **Logic**: Forwards to `phase-manager.sh`

#### `know phases restructure`
Generate optimal phases from dependencies.

#### `know phases prioritize`
Interactively adjust entity priorities.

#### `know phases validate`
Check phase dependency validity.

#### `know phases stats`
Show phase statistics and metrics.

## Environment Variables

- `KNOWLEDGE_MAP` - Default knowledge map file path (default: `.ai/spec-graph.json`)
- `PROJECT_ROOT` - Project root directory
- `LIB_DIR` - Library directory path
- `TEMPLATE_DIR` - Templates directory path
- `GENERATOR_DIR` - Generators directory path

## Exit Codes

- `0` - Success
- `1` - General error
- Other codes defined by individual scripts

## Common Workflows

### Discovery Workflow
```bash
know list features                    # Browse available features
know search telemetry                 # Find specific entities
know check feature real-time-telemetry # Validate before generating
```

### Analysis Workflow
```bash
know gaps feature:user-auth           # Identify missing information
know deps feature:user-auth           # Understand dependencies
know implementation-chain feature:user-auth # Plan full implementation
```

### Generation Workflow
```bash
know component fleet-status-map       # Generate ready specifications
know package teleoperation-interface # Create complete implementation package
```