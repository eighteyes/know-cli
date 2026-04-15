# Know-CLI Feature to Module Mapping

## Core Architecture

### Graph Management
**Feature**: Dual graph system (spec + code graphs) with dependency tracking
**Modules**:
- `/Users/god/projects/know-cli/know/src/graph.py` - GraphManager (load/save, NetworkX construction, cross-graph traversal, diff logging)
- `/Users/god/projects/know-cli/know/src/cache.py` - GraphCache (graph file caching)
- `/Users/god/projects/know-cli/know/src/async_graph.py` - AsyncGraphManager, AsyncGraphPool (async graph operations)

### Entity Management
**Feature**: CRUD operations for graph entities and references
**Modules**:
- `/Users/god/projects/know-cli/know/src/entities.py` - EntityManager (entity CRUD, type validation)
- `/Users/god/projects/know-cli/know/src/dependencies.py` - DependencyManager (dependency validation, cycle detection)
- `/Users/god/projects/know-cli/know/src/reference_tools.py` - ReferenceManager (reference operations)

### Validation
**Feature**: Multi-level graph validation (syntax, structure, semantics, health)
**Modules**:
- `/Users/god/projects/know-cli/know/src/validation.py` - GraphValidator, ContractValidator (structure, schema, references, completeness)
- `/Users/god/projects/know-cli/know/src/migration.py` - GraphConformanceChecker, RulesDiffAnalyzer (rules conformance, migration planning)

---

## CLI Command Groups

### Initialization Commands
**CLI**: `know init`
**Feature**: Project setup, rules installation, template deployment
**Implementation**: `/Users/god/projects/know-cli/know/know.py` (lines ~6108+)
**Templates**: `/Users/god/projects/know-cli/know/templates/`
- `agents/` - Feature effort estimator agent
- `commands/` - add, build, plan, prepare, review, bug, connect, done, list, schema
- `hooks/` - Git hooks integration

### Graph Commands (`know graph`)
**CLI Group**: `@cli.group()` named `graph`
**Commands** (13 total):
- `link` - Add dependency between entities
- `unlink` - Remove dependency
- `uses/down` - Show what entity uses (dependencies)
- `used-by/up` - Show what uses entity (dependents)
- `connect` - Suggest related entities
- `build-order` - Topological sort for build sequence
- `diff` - Compare two graph files
- `migrate` - Migrate graph format
- `migrate-rules` - Migrate to new rules
- `traverse` - Cross-graph traversal (spec↔code)
- `clean` - Remove unused references
- `coverage` - Show graph coverage metrics
- `suggest` - ML-based dependency suggestions

**Modules**:
- `/Users/god/projects/know-cli/know/src/graph.py` - GraphManager (traversal, build order)
- `/Users/god/projects/know-cli/know/src/dependencies.py` - DependencyManager (link/unlink, validation)
- `/Users/god/projects/know-cli/know/src/diff.py` - GraphDiff (graph comparison)
- `/Users/god/projects/know-cli/know/src/migration.py` - GraphConformanceChecker, RulesDiffAnalyzer
- `/Users/god/projects/know-cli/know/src/semantic_search.py` - SemanticSearcher (suggest command)

### Check Commands (`know check`)
**CLI Group**: `@cli.group()` named `check`
**Commands** (15 total):
- `syntax` - Validate JSON syntax
- `structure` - Validate graph structure
- `semantics` - Validate dependencies and references
- `full` - Run all validation checks
- `validate` - Alias for full validation
- `health` - Overall graph health report
- `stats` - Graph statistics
- `completeness` - Check entity completeness
- `cycles` - Detect circular dependencies
- `orphans` - Find orphaned entities
- `usage` - Link usage analysis
- `ref-types` - Reference type analysis
- `link-gap-analysis` - Missing dependency chains
- `link-gap-missing` - Missing dependencies
- `link-gap-summary` - Gap analysis summary

**Modules**:
- `/Users/god/projects/know-cli/know/src/validation.py` - GraphValidator
- `/Users/god/projects/know-cli/know/src/gap_analysis.py` - GapAnalyzer (completeness, chains)
- `/Users/god/projects/know-cli/know/src/utils.py` - get_graph_stats

### Gen Commands (`know gen`)
**CLI Group**: `@cli.group()` named `gen`
**Commands** (8 total):
- `spec` - Generate spec from entity
- `feature-spec` - Generate feature specification
- `docs` - Generate feature documentation
- `sitemap` - Generate project sitemap
- `code-graph` - Generate code graph from codemap
- `codemap` - Generate codemap from source code
- `trace` - Trace entity across graphs
- `trace-matrix` - Generate traceability matrix

**Modules**:
- `/Users/god/projects/know-cli/know/src/generators.py` - SpecGenerator (spec, docs generation)
- `/Users/god/projects/know-cli/know/src/codemap_to_graph.py` - CodeGraphGenerator (codemap→graph conversion)
- `/Users/god/projects/know-cli/know/src/graph.py` - GraphManager (cross-graph tracing)

### Feature Commands (`know feature`)
**CLI Group**: `@cli.group()` named `feature`
**Commands** (12 total):
- `status` - Feature status and progress
- `contract` - Feature contract management
- `validate-contracts` - Validate all contracts
- `validate` - Validate feature completeness
- `tag` - Tag git commits to feature
- `review` - Feature review checklist
- `connect` - Connect feature to code entities
- `done` - Mark feature as complete
- `impact` - Feature impact analysis
- `coverage` - Feature test coverage
- `block` - Block requirement
- `complete` - Complete requirement

**Modules**:
- `/Users/god/projects/know-cli/know/src/feature_tracker.py` - FeatureTracker (git integration, baselines, commit tagging)
- `/Users/god/projects/know-cli/know/src/contract_manager.py` - ContractManager (contract validation)
- `/Users/god/projects/know-cli/know/src/impact_analyzer.py` - ImpactAnalyzer (cross-feature dependencies)
- `/Users/god/projects/know-cli/know/src/coverage.py` - CoverageAnalyzer (test coverage via spec→code)
- `/Users/god/projects/know-cli/know/src/requirements.py` - RequirementManager (requirement tracking)

### Nodes Commands (`know nodes`)
**CLI Group**: `@cli.group()` named `nodes`
**Commands** (9 total):
- `deprecate` - Mark entity as deprecated
- `undeprecate` - Remove deprecation
- `deprecated` - List deprecated entities
- `merge` - Merge two entities
- `rename` - Rename entity key
- `delete` - Delete entities (batch support)
- `cut` - Cut entity and move to clipboard
- `update` - Update entity properties
- `clone` - Clone entity with new key

**Modules**:
- `/Users/god/projects/know-cli/know/src/deprecation.py` - DeprecationManager (deprecation lifecycle)
- `/Users/god/projects/know-cli/know/src/entities.py` - EntityManager (CRUD operations)

### Operation Commands (`know op`)
**CLI Group**: `@cli.group()` named `op`
**Commands** (5 total):
- `start` - Start operation execution
- `done` - Complete operation
- `status` - Operation status
- `next` - Get next pending operation
- `reset` - Reset operation state

**Modules**:
- `/Users/god/projects/know-cli/know/src/op_manager.py` - OpManager (operation state tracking)

### Horizon Commands (`know horizons`)
**CLI Group**: `@cli.group()` named `horizons`
**Commands** (5 total):
- `list` - List all horizons
- `add` - Add entity to horizon
- `move` - Move entity to different horizon
- `status` - Set horizon status
- `remove` - Remove entity from horizon

**Modules**:
- `/Users/god/projects/know-cli/know/know.py` - Direct meta manipulation (horizons stored in meta.horizons)

### Requirement Commands (`know req`)
**CLI Group**: `@cli.group()` named `req`
**Commands** (5 total):
- `add` - Add requirement to feature
- `status` - Set requirement status
- `list` - List feature requirements
- `complete` - Complete requirement
- `block` - Block requirement

**Modules**:
- `/Users/god/projects/know-cli/know/src/requirements.py` - RequirementManager (requirement lifecycle)

### Meta Commands (`know meta`)
**CLI Group**: `@cli.group()` named `meta`
**Commands** (3 total):
- `get` - Get meta value
- `set` - Set meta value
- `delete` - Delete meta key

**Modules**:
- `/Users/god/projects/know-cli/know/know.py` - Direct graph meta manipulation

### Visualization Commands (`know viz`)
**CLI Group**: `@cli.group()` named `viz`
**Commands** (5 total):
- `tree` - ASCII tree visualization
- `mermaid` - Mermaid diagram generation
- `dot` - GraphViz dot format
- `html` - Interactive HTML visualization
- `fzf` - Interactive fuzzy picker

**Modules**:
- `/Users/god/projects/know-cli/know/src/visualizers/base.py` - BaseVisualizer (shared extraction logic)
- `/Users/god/projects/know-cli/know/src/visualizers/tree.py` - TreeVisualizer
- `/Users/god/projects/know-cli/know/src/visualizers/mermaid.py` - MermaidVisualizer
- `/Users/god/projects/know-cli/know/src/visualizers/dot.py` - DotVisualizer
- `/Users/god/projects/know-cli/know/src/visualizers/html.py` - HtmlVisualizer
- `/Users/god/projects/know-cli/know/src/visualizers/fzf.py` - FzfPicker
- `/Users/god/projects/know-cli/know/src/visualizers/theme.py` - Color theming

### Basic CRUD Commands
**CLI**: `@cli.command()`
**Commands** (9 total):
- `add` - Add entity/reference
- `get` - Get entity/reference details
- `list` - List entities/references
- `search` - Pattern-based search
- `find` - Semantic search
- `related` - Find related entities
- `link` - Create dependency (alias)
- `unlink` - Remove dependency (alias)
- `init` - Initialize project

**Modules**:
- `/Users/god/projects/know-cli/know/src/entities.py` - EntityManager
- `/Users/god/projects/know-cli/know/src/semantic_search.py` - SearchIndex, SemanticSearcher

---

## Supporting Infrastructure

### Build System
**Feature**: Build execution and orchestration
**Modules**:
- `/Users/god/projects/know-cli/know/src/build_executor.py` - BuildExecutor (build order execution)

### LLM Integration
**Feature**: LLM provider abstraction and prompting
**Modules**:
- `/Users/god/projects/know-cli/know/src/llm.py` - LLMManager, LLMProvider, MockProvider

### Search & Discovery
**Feature**: Semantic search and entity discovery
**Modules**:
- `/Users/god/projects/know-cli/know/src/semantic_search.py` - SearchIndex, SemanticSearcher (TF-IDF, embeddings)

### Utilities
**Feature**: Shared utilities and helpers
**Modules**:
- `/Users/god/projects/know-cli/know/src/utils.py` - parse_entity_id, format_entity_id, normalize_entity_type, validate_name_format, get_graph_stats

---

## Graph Types & Rules

### Spec Graph
**File**: `.ai/know/spec-graph.json`
**Rules**: `know/config/dependency-rules.json`
**Entity Hierarchy**: `Project → User → Objective → Feature → Action → Component → Operation`
**Entities**: project, user, objective, feature, action, component, operation
**References**: requirement, interface, data-model, business_logic, etc.

### Code Graph
**File**: `.ai/know/code-graph.json`
**Rules**: `know/config/code-dependency-rules.json`
**Entity Types**: module, package, class, function, layer, namespace, interface, external-dep
**Cross-linking**:
- spec→code: `implementation` reference
- code→spec: `graph-link` reference

---

## Integration Points

### Git Integration
- **Module**: `feature_tracker.py`
- **Features**: Commit tagging (git notes), baseline tracking, file change detection

### Cross-Graph Operations
- **Modules**: `graph.py`, `coverage.py`, `impact_analyzer.py`
- **Features**: spec↔code traversal, traceability matrix, impact analysis

### Validation Pipeline
- **Modules**: `validation.py`, `migration.py`, `gap_analysis.py`
- **Levels**: syntax → structure → semantics → health → completeness

### Code Generation
- **Modules**: `generators.py`, `codemap_to_graph.py`
- **Input**: `codemap.json` (from tree-sitter or ast-grep)
- **Output**: code-graph.json, spec documents, traceability matrices

---

## Command Count Summary
- **Initialization**: 1 command
- **Graph**: 13 commands (+ 2 subgroups)
- **Check**: 15 commands
- **Gen**: 8 commands (+ 1 subgroup)
- **Feature**: 12 commands
- **Nodes**: 9 commands
- **Op**: 5 commands
- **Phases**: 5 commands
- **Req**: 5 commands
- **Meta**: 3 commands
- **Viz**: 5 commands
- **Basic CRUD**: 9 commands

**Total**: ~100+ CLI commands across 11 command groups
