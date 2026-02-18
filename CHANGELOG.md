# Changelog

All notable changes to the Know Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-02-17

### Added

#### Layered Validation
- `know check syntax` — fast structural + format check (~ms)
- `know check structure` — schema, orphaned nodes, entity types, reference usage (~50ms)
- `know check semantics` — dependency rules, cycles, naming conventions (~200ms)
- `know check full` — all layers combined
- `know check validate` now aliases `check full` (backward compatible)
- `know check health` updated to use `validate_full()`

#### Semantic Search
- `know find "<query>"` — TF-IDF semantic search across entity names and descriptions
- `know related <entity>` — find entities with similar text to a given entity
- Search index cached at `{graph}-search-index.json`, stale-checked via SHA256 graph hash
- Pure Python TF-IDF, zero new dependencies

#### Spec Graph Diff Log
- Every write to `spec-graph.json` appends a structured diff entry to `.ai/know/diff-graph.jsonl`
- Each entry records: timestamp, entities added/removed/modified, graph links added/removed, references added/removed
- Skips empty diffs (no-op saves produce no entry)

### Fixed

#### Concurrent Write Safety
- Replaced polling lock file with `fcntl.flock(LOCK_EX)` — concurrent writers now queue instead of silently dropping writes
- Lock file co-located with graph file (`.{graph-stem}.lock`) instead of cwd

---

## [0.1.0] - 2026-01-25

### Added

#### Requirements-Driven System
- **requirements.py** - First-class requirement entities with status tracking
  - `know req add <feature> <key>` - Create requirements linked to features
  - `know req status <id> <status>` - Update requirement status (pending/in-progress/blocked/complete/verified)
  - `know req list <feature>` - List requirements with completion counts
  - `know req complete <id>` - Mark requirement as complete
  - `know req block <id>` - Mark requirement as blocked
  - Status tracked in `meta.requirements` with dates and metadata

#### Deprecation System
- **deprecation.py** - Soft deprecation with warnings and migration paths
  - `know deprecate <entity> --reason "..."` - Mark entity as deprecated
  - `know undeprecate <entity>` - Remove deprecation status
  - `know deprecated` - List all deprecated entities
  - `know deprecated --overdue` - List entities past removal date
  - Warnings shown when linking to deprecated entities
  - Tracked in `meta.deprecated` with replacement suggestions

#### Test Coverage Queries
- **coverage.py** - Coverage analysis via graph traversal
  - `know coverage <feature>` - Aggregate coverage from feature level
  - `know coverage <feature> --detail` - Per-component breakdown
  - Traverses: feature → components → modules → test-suites

### Changed

#### /know:add Command
- Added step 3b "Define Requirements" for breaking features into testable requirements
- Extension workflow uses `know req add` instead of todo.md
- Scaffold creates `notes.md` for freeform notes (replaces todo.md)
- Register step uses `know req add` commands
- Replaced config.json with contract.yaml for drift detection
- Expanded to populate full spec-graph from Clarify step
- Added experiments capture and validation before build
- Added reference materials tracking (research papers, specs, docs)
- Added duplicate detection step
- Added /know:connect step for graph coverage

#### /know:build Command
- Phase 6 tracks progress via `know req status` instead of todo.md
- Replace workflow uses `know deprecate <entity>` instead of todo.md
- Added contract.yaml tracking for observed files/entities
- Added Phase 5: Experiments - gates implementation on validation
- QA_STEPS are human-only (no automation)

#### /know:review Command
- Bug fixes and changes tracked as requirements in spec-graph
- Creates requirements for fixes instead of todo.md entries
- Added contract action verification section

#### /know:plan Command
- PM mode outputs requirements via spec-graph instead of todo.md
- Streamlined Discovery mode (delegates to /know:add for feature details)
- Renamed Mode 6 Prototyping→Experiments
- Added Graph Operations section with CLI examples

#### /know:done Command
- Completion check uses `know req list` instead of todo.md parsing

#### /know:list Command
- Task counts from spec-graph requirements instead of todo.md

#### /know:bug Command
- Bug fixes tracked as requirements via `know req add`

#### /know:prepare Command
- Added /know:connect step for graph coverage validation

### Removed
- **Beads task management system** - Replaced by requirements
  - Removed `know/src/tasks/` directory
  - Removed `.ai/tasks/tasks.jsonl`
  - Removed beads-integration feature
  - Cleaned spec-graph of beads-related entities

### Breaking Changes
- `todo.md` no longer used for progress tracking
- Use `know req list <feature>` to view feature requirements
- Use `know req status` to update progress

---

## [0.0.1] - 2025-10-08

### Added - Python Implementation

#### Core Modules
- **graph.py** - Fast graph file operations with caching (10-20x faster than bash)
- **entities.py** - Entity CRUD operations with validation
- **dependencies.py** - Dependency resolution, cycle detection, topological sorting
- **validation.py** - Comprehensive graph structure and schema validation
- **generators.py** - Spec generation for entities, features, interfaces, components
- **utils.py** - Helper functions for parsing, formatting, fuzzy matching
- **llm.py** - LLM provider integration with HTTP client support
- **async_graph.py** - Async wrapper for non-blocking web integration

#### CLI Enhancements
- `know health` - Comprehensive graph health check
- `know completeness <entity>` - Entity completeness scoring
- `know spec <entity>` - Generate entity specifications
- `know feature-spec <feature>` - Generate detailed feature specs
- `know sitemap` - Generate interface sitemap
- `know suggest <entity>` - AI-powered connection suggestions
- Enhanced `validate` with categorized errors/warnings/info
- Enhanced `stats` with detailed breakdowns

#### Testing
- Comprehensive test suite for dependencies
- Comprehensive test suite for validation
- Comprehensive test suite for LLM integration
- Comprehensive test suite for utilities
- Benchmark suite for performance testing

#### Infrastructure
- Setup.py for pip installation
- CI/CD workflows (GitHub Actions)
- Automated testing across Python 3.8-3.12
- Performance regression detection
- Automated PyPI releases

#### Documentation
- Complete README with examples
- Installation guide for all platforms
- Migration guide from bash to Python
- API documentation
- Benchmark results

### Changed
- Moved JSON configs to `config/` directory
- Updated all bash scripts to use new config paths
- Enhanced bash wrapper to call Python implementation
- Improved error messages and validation output

### Performance
- **10-20x faster** than bash/jq implementation
- **In-memory caching** provides near-instantaneous repeated access
- **Async support** for non-blocking operations
- Handles graphs up to 1000+ entities efficiently

### Backward Compatibility
- **100% compatible** with existing bash commands
- All CLI commands work identically
- No breaking changes to graph format
- Bash version still available if needed

## [0.0.0] - Bash Implementation

### Features
- Graph file operations via jq
- Entity management
- Dependency validation
- Spec generation via templates
- 44 bash utility scripts

### Known Limitations
- Performance degrades with large graphs (>200KB)
- Complex jq queries can be slow
- Shell escaping issues in some cases
- Limited caching capabilities

---

## Migration Path

### From Bash (0.0.0) to Python (0.0.1)

1. **Install Python version**: `./install-local.sh`
2. **Test compatibility**: Run both versions in parallel
3. **Switch default**: Update symlinks to Python version
4. **Remove bash version**: After confirming Python works

## Future Releases

- Full LLM HTTP integration (Anthropic, OpenAI)
- Automated graph optimization
- Natural language graph queries
