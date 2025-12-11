# Project Context

## Purpose
Know-CLI is an opinionated graph knowledgebase for product-driven software development, designed primarily for automated LLM access. It solves the brittleness of traditional spec.md files by using interconnected graphs that map user intent to implementation through a unidirectional dependency model.

**Key Value**: Provides LLMs with structured project context without token-wasting repetitive analysis, enabling better planning and more intuitive understanding of how product features connect to code.

## Tech Stack
- **Language**: Python 3.8+
- **CLI Framework**: Click 8.0+ (command-line interface)
- **Graph Engine**: NetworkX 3.0+ (graph algorithms, topological sorting)
- **Data Validation**: Pydantic 2.0+ (schema validation)
- **CLI Rendering**: Rich 13.0+ (beautiful terminal output)
- **Testing**: Pytest 7.0+ (unit and integration tests)
- **Async I/O**: aiofiles 0.8+ (async file operations)
- **Config**: python-dotenv 0.19+ (environment management)

## Graph Architecture

### Spec Graph (.ai/spec-graph.json)
**Status**: ✓ Populated
**Entities**: 16 total (2 users, 4 objectives, 5 features, 5 components)
**Dependencies**: 15 mapped relationships

Maps user intent to product features:
- **Users**:
  - `ai-assistant`: LLM-based coding assistant managing project specs
  - `developer`: Software developer using know to manage product specs

- **Objectives**:
  - `query-graph`: Query product and code structure efficiently
  - `manage-specs`: Create and update spec graphs
  - `analyze-gaps`: Identify implementation gaps
  - `generate-docs`: Generate spec documents from graph

- **Features**:
  - `cli-operations`: Command-line graph management
  - `graph-validation`: Validate graph structure and dependencies
  - `gap-detection`: Detect missing implementations
  - `spec-generation`: Generate markdown specs from graph
  - `llm-workflows`: AI-assisted graph operations

- **Components**:
  - `cli-commands`: Command handlers for all CLI operations
  - `graph-operations`: Core graph CRUD and query operations
  - `validation-engine`: Rule-based graph validation
  - `spec-templates`: Template-based spec generation
  - `llm-integration`: LLM provider and workflow management

**Top User Journeys**:
- AI Assistant → Query Graph → CLI Operations → CLI Commands
- AI Assistant → Analyze Gaps → Gap Detection → Graph Operations
- Developer → Manage Specs → Graph Validation → Validation Engine
- Developer → Generate Docs → Spec Generation → Spec Templates

### Code Graph (.ai/code-graph.json)
**Status**: ✓ Populated & Validated
**Entities**: 25 total (21 modules, 4 packages)
**Dependencies**: 43 mapped relationships
**References**: 19 total (11 external-dep, 8 product-component links)

Maps actual codebase structure:
- **Modules** (21): know-cli, benchmark, graph, cache, entities, dependencies, validation, generators, llm, gap-analysis, reference-tools, async-graph, utils, test-graph, test-entities, test-dependencies, test-validation, test-commands, test-llm, test-utils, test-bug-fixes
- **Packages** (4): src, tests, templates, config
- **External Dependencies** (11): click, pydantic, networkx, rich, pytest, aiofiles, python-dotenv, pytest-asyncio, pytest-cov, black, mypy
- **Architecture**: CLI tool with core graph operations library and comprehensive test suite

**Integration Points**:
8 product-component references link code modules to spec components:
- `module:cli-main` → `component:cli-commands`
- `module:graph-manager` → `component:graph-operations`
- `module:graph-validator` → `component:validation-engine`
- `module:spec-generator` → `component:spec-templates`
- `module:llm-manager` → `component:llm-integration`
- `module:gap-analysis` → `component:graph-operations`
- (+ entity-manager, dependency-manager)

## Project Conventions

### Code Style
- Python 3.8+ with type hints
- Black code formatting
- MyPy type checking
- Rich library for CLI output (tables, trees, colored output)
- Click decorators for command definitions

### Architecture Patterns
**Core Pattern**: Separation of concerns with manager classes
- **GraphManager**: Core graph operations and NetworkX integration
- **EntityManager**: Entity CRUD operations
- **DependencyManager**: Dependency relationship management
- **GraphValidator**: Rule-based validation against dependency-rules.json
- **SpecGenerator**: Template-based document generation
- **LLMManager**: LLM provider integration

**Dependency Flow**:
- CLI commands → Managers → GraphManager → GraphCache → JSON files
- All graph operations flow through GraphManager for consistency
- GraphCache provides thread-safe in-memory caching with atomic writes

**Module Dependencies**:
- Most modules depend on GraphManager as central coordinator
- CLI main depends on all manager modules
- Validation and generation layers are independent

### Testing Strategy
- **Framework**: Pytest with pytest-asyncio for async tests
- **Coverage**: pytest-cov for coverage reporting
- **Test Structure**: tests/ package mirrors src/ structure
- **Test Types**:
  - Unit tests for individual modules
  - Integration tests for command workflows
  - Bug fix regression tests (test_bug_fixes.py)

### Git Workflow
- Main branch for stable releases
- Feature branches for development
- Conventional commits encouraged
- No specific PR process defined yet

## Domain Context
**Domain**: Developer tooling / Graph-based knowledge management

**Key Concepts**:
1. **Dual Graph System**:
   - Spec-graph maps user intent (WHAT users want)
   - Code-graph maps implementation (HOW it's built)
   - Product-component references link the two

2. **Dependency Rules**:
   - `config/dependency-rules.json` defines valid spec-graph relationships
   - `config/code-dependency-rules.json` defines valid code-graph relationships
   - Unidirectional "depends_on" relationship model

3. **Graph Operations**:
   - Add/remove entities and dependencies
   - Validate graph structure
   - Detect circular dependencies
   - Generate topological build order
   - Analyze implementation gaps
   - Manage orphaned references

4. **Workflow System**:
   - `/know-add` creates feature directories with proposal/todo/plan/spec files
   - `/know-list` shows all features (planned, in-progress, completed)
   - `/know-done` archives completed features
   - Graph entities created immediately when features are added

## Important Constraints
- **Graph Validation**: Currently uses spec-graph rules only; code-graph validation needs separate rules path support (known limitation)
- **Single Graph File**: CLI operates on one graph at a time via `-g` flag
- **Python Dependency**: Requires Python 3.8+ runtime
- **File-based Storage**: Graphs stored as JSON files, no database backend
- **Thread Safety**: GraphCache uses file locks for concurrent access

## External Dependencies
From code-graph external-dep references:
- **click** (^8.0): CLI framework for command-line interface
- **pydantic** (^2.0): Data validation and settings management
- **networkx** (^3.0): Graph algorithms and topological sorting
- **rich** (^13.0): Beautiful CLI output with tables and formatting
- **pytest** (^7.0): Testing framework for unit and integration tests
- **aiofiles** (^0.8): Async file operations
- **python-dotenv** (^0.19): Environment variable management

## Implementation Status
**Overall Completion**: Graphs populated, implementation complete

**Spec Graph**:
- 2 users defined
- 4 objectives mapped
- 5 features identified
- 5 components specified
- 15 dependency relationships

**Code Graph**:
- 21 modules implemented (11 src + 2 main + 8 test modules)
- 4 packages organized
- 11 external dependencies
- 8 product-component links
- 43 dependency relationships

**Next Steps**:
- Continue using `/know-add` for new features
- Maintain graph-code alignment via product-component references
- Run `know validate` before commits to ensure graph integrity
