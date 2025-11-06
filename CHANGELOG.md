# Changelog

All notable changes to the Know Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
