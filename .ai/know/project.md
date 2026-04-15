# Project Context

## Purpose
Know-CLI is an opinionated graph knowledgebase for product-driven software development, designed primarily for automated LLM access. It solves the brittleness of traditional spec.md files by using interconnected graphs that map user intent to implementation through a unidirectional dependency model.

**Key Value**: Provides LLMs with structured project context without token-wasting repetitive analysis, enabling better planning and more intuitive understanding of how product features connect to code.

**Target Users**: AI assistants (`user:ai-assistant`), developers (`user:developer`), software architects (`user:software-architect`), product managers (`user:product-manager`), and tool integrators (`user:tool-integrator`).

**Core Objectives**: Query graph (`objective:query-graph`), manage specs (`objective:manage-specs`), analyze gaps (`objective:analyze-gaps`), generate docs (`objective:generate-docs`), manage tasks (`objective:manage-tasks`), architect system (`objective:architect-system`), track features (`objective:track-features`), integrate tools (`objective:integrate-tools`).

## Tech Stack
- **Language**: Python 3.8+
- **CLI Framework**: Click 8.0+ (`external-dep:click`) - command-line interface
- **Graph Engine**: NetworkX 3.0+ (`external-dep:networkx`) - graph algorithms, topological sorting
- **Data Validation**: Pydantic 2.0+ (`external-dep:pydantic`) - schema validation
- **CLI Rendering**: Rich 13.0+ (`external-dep:rich`) - beautiful terminal output
- **Testing**: Pytest 7.0+ (`external-dep:pytest`) - unit and integration tests
- **Async I/O**: aiofiles 0.8+ (`external-dep:aiofiles`) - async file operations
- **Config**: python-dotenv 0.19+ (`external-dep:python-dotenv`) - environment management

## Graph Architecture

### Spec Graph (.ai/know/spec-graph.json)
**Status**: ✓ Populated & Validated, **Coverage**: 100%
**Entities**: 121 total (5 users, 8 objectives, 9 features, 28 actions, 20 components, 51 operations)
**Dependencies**: 144 mapped relationships

Maps user intent to product features through dependency chains:

**Users** (5):
- `user:ai-assistant` - LLM-based coding assistant managing project specs
- `user:developer` - Software developer using know to manage product specs
- `user:software-architect` - System architect designing and planning architecture
- `user:product-manager` - Product manager tracking features and roadmap
- `user:tool-integrator` - Developer integrating know with other tools

**Objectives** (8):
- `objective:query-graph` - Query product and code structure efficiently
- `objective:manage-specs` - Create and update spec graphs
- `objective:analyze-gaps` - Identify implementation gaps
- `objective:generate-docs` - Generate spec documents from graph
- `objective:manage-tasks` - Track and organize development tasks
- `objective:architect-system` - Design and document system architecture
- `objective:track-features` - Monitor feature development progress
- `objective:integrate-tools` - Integrate with external tools and LLM workflows

**Features** (9):
- `feature:cli-operations` - Command-line graph management
- `feature:graph-validation` - Validate graph structure and dependencies
- `feature:gap-detection` - Detect missing implementations
- `feature:spec-generation` - Generate markdown specs from graph
- `feature:llm-workflows` - AI-assisted graph operations
- `feature:schema-agnostic-know` - Custom LLM-defined schemas
- `feature:graph-embeddings` - Semantic search using vector embeddings
- `feature:beads-integration` - Integration with Beads task management
- `feature:spec-generation-enrichment` - Rich spec generation with metadata

**Components** (20): Including `component:cli-commands`, `component:graph-operations`, `component:validation-engine`, `component:spec-templates`, `component:llm-integration`, `component:gap-analyzer`, `component:reference-analyzer`, `component:task-manager`, `component:task-sync`, `component:beads-bridge`, and more.

**Actions** (28): Including add-entity, query-dependencies, list-entities, manage-links, validate-structure, validate-dependencies, check-cycles, health-check, analyze-missing-connections, detect-orphaned-references, suggest-connections, generate-entity-spec, generate-feature-spec, execute-llm-chain, and more.

**Operations** (51): Low-level operations like add_entity_to_graph, get_entity_dependencies, create_dependency_link, validate_dag_structure, check_dependency_rules, detect_cycles, compute_health_score, find_missing_chains, compute_completeness, and more.

### Code Graph (.ai/know/code-graph.json)
**Status**: ✓ Populated & Validated
**Entities**: 31 total (26 modules, 5 packages)
**Dependencies**: 58 mapped relationships
**References**: 24 total (11 external-dep, 8+ product-component links)

Maps actual codebase structure:

**Packages** (5):
- `package:src` - Core library implementation with all graph operations
- `package:tests` - Comprehensive test suite with pytest
- `package:config` - Configuration files and dependency rules
- `package:templates` - Specification templates for generation
- `package:tasks` - Task management and Beads integration

**Modules** (26): Including `module:know-cli`, `module:graph`, `module:cache`, `module:entities`, `module:dependencies`, `module:validation`, `module:generators`, `module:llm`, `module:gap-analysis`, `module:reference-tools`, `module:async-graph`, `module:diff`, `module:utils`, `module:task-manager`, `module:task-sync`, `module:beads-bridge`, `module:task-interfaces`, plus test modules.

**Integration Points** - Product-component references link code modules to spec components:
- `module:know-cli` → `component:cli-commands` (`feature:cli-operations`)
- `module:graph` → `component:graph-operations` (`feature:cli-operations`)
- `module:validation` → `component:validation-engine` (`feature:graph-validation`)
- `module:generators` → `component:spec-templates` (`feature:spec-generation`)
- `module:llm` → `component:llm-integration` (`feature:llm-workflows`)
- `module:diff` → `component:gap-analyzer` (`feature:gap-detection`)
- `module:task-manager` → `component:task-manager` (`feature:beads-integration`)
- `module:task-sync` → `component:task-sync` (`feature:beads-integration`)
- `module:beads-bridge` → `component:beads-bridge` (`feature:beads-integration`)

## Project Conventions

### Code Style
- Python 3.8+ with type hints
- Black code formatting (88 character line length)
- MyPy type checking
- Rich library for CLI output (tables, trees, colored output)
- Click decorators for command definitions
- Import order: standard library, third-party, local imports

### Architecture Patterns
**Core Pattern**: Manager-based architecture with separation of concerns
- **GraphManager**: Core graph operations and NetworkX integration
- **EntityManager**: Entity CRUD operations
- **DependencyManager**: Dependency relationship management
- **GraphValidator**: Rule-based validation against dependency-rules.json
- **SpecGenerator**: Template-based document generation
- **LLMManager**: LLM provider integration (Anthropic, OpenAI)
- **GraphCache**: Thread-safe in-memory caching with atomic writes

**Dependency Flow**:
- CLI commands → Managers → GraphManager → GraphCache → JSON files
- All graph operations flow through GraphManager for consistency
- Validation and generation layers are independent

**Module Dependencies**:
- `module:graph` depends on: `module:entities`, `module:dependencies`, `module:cache`
- `module:validation` depends on: `module:graph`, `module:entities`
- `module:generators` depends on: `module:graph`, `module:entities`
- `module:task-manager` depends on: `module:graph`
- `module:task-sync` depends on: `module:task-manager`, `module:beads-bridge`

### Testing Strategy
- **Framework**: Pytest with pytest-asyncio for async tests, pytest-cov for coverage
- **Test Structure**: tests/ package mirrors src/ structure
- **Test Types**:
  - Unit tests for individual modules
  - Integration tests for command workflows
  - Property-based testing with Hypothesis
  - Bug fix regression tests (test_bug_fixes.py)
  - Fuzzing tests for robustness

### Git Workflow
- **Branch Naming**: `feature/feature-name`, `fix/bug-description`
- **Commit Style**: Conventional commits (feat, fix, docs, test, chore)
- **Horizon Management**: Features tracked in `meta.horizons` (pending, I, II, III, in-progress, review-ready, done)
- Main branch for stable releases
- Feature branches for development

## Domain Context
**Domain**: Developer tooling / Graph-based knowledge management

**Key Concepts**:
1. **Dual Graph System**:
   - Spec-graph maps user intent (WHAT users want)
   - Code-graph maps implementation (HOW it's built)
   - Product-component references link the two
   - Auto-detection based on filename (spec-graph vs code-graph)

2. **Dependency Rules**:
   - `config/dependency-rules.json` defines valid spec-graph relationships
   - `config/code-dependency-rules.json` defines valid code-graph relationships
   - Unidirectional "depends_on" relationship model (DAG structure)
   - Strict validation prevents cycles and invalid connections

3. **Graph Operations**:
   - Add/remove entities and dependencies
   - Validate graph structure (DAG, dependency rules)
   - Detect circular dependencies
   - Generate topological build order
   - Analyze implementation gaps (gap-missing, gap-summary, gap-analysis)
   - Manage orphaned references (ref-orphans, ref-usage, ref-suggest, ref-clean)
   - Coverage analysis (100% coverage achieved)

4. **Workflow System**:
   - `/know:add` creates feature directories with proposal/todo/plan/spec files
   - `/know:list` shows all features grouped by phase with task counts
   - `/know:done` archives completed features
   - `/know:build` 5-phase workflow (Discover, Clarify, Architect, Implement, Wrapup)
   - `/know:review` interactive QA walkthrough for acceptance testing

## Important Constraints
- **Graph Structure**: Must be valid DAG (Directed Acyclic Graph) - no cycles allowed
- **Single Graph File**: CLI operates on one graph at a time via `-g` flag
- **Python Dependency**: Requires Python 3.8+ runtime
- **File-based Storage**: Graphs stored as JSON files, no database backend
- **Thread Safety**: GraphCache uses file locks for concurrent access
- **Performance Target**: 10-20x faster than bash/jq implementation
- **Scalability**: Optimized for graphs up to 1000+ entities

## External Dependencies
From code-graph `external-dep` references:
- **click** (>=8.0): CLI framework for command-line interface
- **pydantic** (>=2.0): Data validation and settings management
- **networkx** (>=3.0): Graph algorithms and topological sorting
- **rich** (>=13.0): Beautiful CLI output with tables and formatting
- **pytest** (>=7.0): Testing framework for unit and integration tests
- **pytest-asyncio** (>=0.21): Async test support
- **pytest-cov** (>=4.0): Coverage reporting
- **aiofiles** (>=0.8): Async file operations
- **python-dotenv** (>=0.19): Environment variable management
- **black** (>=23.0): Code formatting
- **mypy** (>=1.0): Type checking

## Querying the Graphs

Query spec-graph:
```bash
know -g .ai/know/spec-graph.json list              # List all entities
know -g .ai/know/spec-graph.json uses feature:X    # Show feature dependencies
know -g .ai/know/spec-graph.json gap-summary       # Implementation status
know -g .ai/know/spec-graph.json coverage          # Coverage analysis
know -g .ai/know/spec-graph.json feature-spec X    # Rich feature spec
```

Query code-graph:
```bash
know -g .ai/know/code-graph.json list              # List all modules
know -g .ai/know/code-graph.json trace module:X    # Trace across boundary
know -g .ai/know/code-graph.json stats             # Graph statistics
```

For detailed graph operations and workflows, use the `/know-tool` skill or refer to `.claude/skills/know-tool/` documentation.

---

*Generated from spec-graph.json and code-graph.json via know CLI queries*
