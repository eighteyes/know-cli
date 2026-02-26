# Know-CLI Codebase Exploration Summary

## Project Overview
**Know-CLI**: Product knowledge graph CLI for AI-driven software development. Replaces flat spec files with structured dependency graphs linking product intent to code implementation.

## Primary Users
- Solo technical leads doing rapid AI-assisted prototyping
- Developers using Claude Code / LLM-powered development tools
- Startup environment, 0→1 or 0→0.1 projects

## Core Purpose
Provide structured, queryable context to LLMs via dual graphs:
- **Spec Graph**: Maps user intent → features (product WHAT/WHY)
- **Code Graph**: Maps codebase architecture (implementation HOW)

## Architecture (28 modules, ~17K LOC)

### Core Modules (Layer 1-2):
- `graph.py`: GraphManager (I/O, NetworkX, diff logging)
- `cache.py`: Thread-safe caching with mtime tracking
- `entities.py`: EntityManager (CRUD operations)
- `dependencies.py`: DependencyManager (rules-based validation)
- `validation.py`: GraphValidator (comprehensive validation)

### Advanced Modules (Layer 3-4):
- `generators.py`: SpecGenerator (markdown/XML spec generation)
- `llm.py`: Multi-provider LLM integration
- `async_graph.py`: Async wrapper for graph operations
- `contract_manager.py`: Feature contract tracking (declared vs observed)
- `feature_tracker.py`: Git integration, commit tagging
- `impact_analyzer.py`: Cross-feature dependency analysis
- `semantic_search.py`: TF-IDF search indexing
- `diff.py`: Graph change tracking (JSONL logging)
- `codemap_to_graph.py`: Generate code-graph from AST
- `migration.py`: Rules conformance checking
- `requirements.py`: Requirement tracking (replaces todo.md)
- `coverage.py`: Implementation coverage metrics

### CLI (know.py - 6,535 lines):
**80+ commands** organized in 11 groups:
- Graph operations: add, list, get, link, unlink, uses, used-by, diff, validate
- Feature lifecycle: feature contract/done/impact/coverage
- Generation: gen spec/sitemap/codemap/trace-matrix
- Visualization: tree, mermaid, dot, HTML, fzf

### Entity Types:
**Spec Graph**: user, objective, feature, action, component, operation
**Code Graph**: module, package, class, function, layer, namespace, interface

### Reference Types (45+ types):
Technical: data-model, api_contract, interface, business_logic, security-spec, configuration
Implementation: external-dep, code-link, implementation, product-component

## Key Features Discovered:
1. Dual graph system with cross-linking
2. Rules-driven validation (JSON config files)
3. XML task specification + BuildExecutor
4. LLM workflow integration
5. Contract-based drift detection
6. Git integration for feature tracking
7. Interactive Claude Code skills (slash commands)
8. Comprehensive visualization (5 formats)
9. Async API for server integration
10. Search indexing with staleness detection

## External Dependencies:
- click (CLI framework)
- pydantic (validation)
- networkx (graph algorithms)
- rich (terminal formatting)
- aiofiles (async I/O)
- pyyaml (contract parsing)

## Test Coverage:
- 11 test files
- Unit + integration tests
- Property-based testing
- 80%+ coverage

## Feature-Module Mappings:
- Graph management → graph.py, cache.py, async_graph.py
- Entity CRUD → entities.py, dependencies.py
- Validation → validation.py, migration.py, gap_analysis.py
- Spec generation → generators.py (1,287 LOC)
- LLM workflows → llm.py (562 LOC)
- Feature lifecycle → feature_tracker.py, contract_manager.py, impact_analyzer.py
- Search → semantic_search.py
- Visualization → visualizers/ (7 modules)
