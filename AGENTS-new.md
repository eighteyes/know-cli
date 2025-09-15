# Repository Guidelines

## Project Structure & Module Organization
- **Knowledge graph core**: `.ai/spec-graph.json` is the single source of truth for all specifications
- **Knowledge graph assets**: Live in `.ai/` with subdirectories:
  - `ctx/` - Context and configuration files
  - `qa/` - QA notes and test scenarios
  - `requirements/` - Requirement briefs and specifications
  - `tmp/` - Temporary files and one-off scripts
- **CLI source**: Sits in `know/` with:
  - `lib/` - Reusable shell modules (e.g., `mod-graph.sh`, `query-graph.sh`, `jq-patterns.json`)
  - `generators/` - Template generators (6 specialized generators)
  - `templates/` - Output templates for specifications
- **Automation scripts**: Under `scripts/` (23+ analytics and utility scripts)
- **Experimental code**: Keep one-off experiments in `research/` or `old/`
- **Tests**: Reside in `tests/know/`, mirroring CLI feature areas with TAP-based testing
- **Backups**: Automatic backups stored in `.backup-temp/` during graph modifications

## Primary Tools & Interfaces

### Know CLI - Main Interface
The `know` command is the primary interface for working with the knowledge graph:

**Core Operations:**
- `know list [entity_type]` - List available entities
- `know search <term>` - Find entities by name or description
- `know check <type> <id>` - Validate entity completeness (70% threshold required)
- `know preview <type> <id>` - Preview specification before generation
- `know <type> <id>` - Generate specification (feature, component, screen, etc.)

**Analysis & Dependencies:**
- `know deps <entity>` - Show dependency chain
- `know impact <entity>` - Show reverse dependencies
- `know gaps <entity>` - Identify missing information
- `know path <from> <to>` - Find dependency path between entities

**Graph Management:**
- `know mod <cmd> [args]` - Modify graph (uses `mod-graph.sh`)
- `know query <cmd> [args]` - Query graph (uses `query-graph.sh`)
- `know jq <cmd>` - Access JQ pattern library:
  - `know jq list` - List pattern categories
  - `know jq exec <pattern> [vars]` - Execute patterns dynamically

### Graph Management Scripts
- **Primary interfaces**: Always prefer using these over direct file manipulation:
  - `know/lib/mod-graph.sh` - Graph modification operations
  - `know/lib/query-graph.sh` - Graph querying and analysis
- **Pattern library**: `know/lib/jq-patterns.json` - Reusable JQ queries
- **Validation**: 70% completeness threshold required for spec generation

## Build, Test, and Development Commands
- `npm run graph:list` - List all entities in the knowledge graph
- `npm run graph:validate` - Run structural validation and cycle detection
- `npm run graph:test` - Execute TAP-based CLI regression tests
- `npm run test:all` - Full validation suite (tests + validation)
- `./tests/know/run-tests.sh [-v|--pattern ...]` - Direct test runner with filtering

## Coding Style & Naming Conventions
- Shell scripts target Bash 5; start files with `#!/bin/bash` and `set -euo pipefail`
- Prefer lowercase, hyphenated filenames (`mod-graph.sh`, `query-graph.sh`)
- Use snake_case for function names
- Wrap jq filters in single quotes; indent pipelines by two spaces
- Update shared helpers in `know/lib/utils.sh` rather than duplicating logic
- Run `shellcheck` locally when touching non-trivial scripts
- String together multiple `jq` commands into a single BASH call for efficiency

## Testing Guidelines
- Tag new CLI scenarios in `tests/know/` using descriptive filenames (`test-discovery.sh`)
- Source `tests/know/lib/test-utils.sh` for TAP-compatible assertions
- Use `plan`/`ok` helpers from test utilities for consistent output
- Coverage expectations: exercise both happy paths and failure cases
- Test graph mutations including backup/restore flows
- For data changes, validate with `know check` before spec generation

## Graph Structure & Dependencies
Follow this hierarchy to avoid circular dependencies:
```
HOW: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Components
```

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`type(scope): summary`), e.g., `refactor(graph): reorganize tools`
- Keep commits focused: separate data updates (`spec-graph.json`) from tooling changes
- Pull requests should:
  - Describe impacted graph entities or commands
  - List validation commands run (`know check`, `know validate`)
  - Attach relevant output snippets or generated specs
  - Link to issue IDs or knowledge base references
  - Note any follow-up work required

## Important Project Rules
- **DO NOT add features without approval** - Check with maintainers first
- **Schema changes require review** - Be precise about graph structure modifications
- **Document learnings**: Save insights to `json-graph-learning.md`
- **Update documentation**: Keep knowledge-graph.md and json-graph-approach.md current
- **Use scripts for graph operations**: Prefer `mod-graph.sh` and `query-graph.sh` over direct manipulation
- **Completeness threshold**: Entities must reach 70% completeness before spec generation

## Quick Reference Commands
```bash
# Discovery workflow
know list features                    # Browse available features
know search telemetry                 # Find specific entities
know check feature real-time-telemetry # Validate before generating

# Implementation workflow
know gaps feature:analytics           # Find missing information
know deps feature:analytics           # Check dependencies
know feature analytics                # Generate specification

# Graph analysis
know query stats                      # Graph statistics
know query cycles                     # Detect circular dependencies
know jq exec entity_dependencies entity_id=user:owner  # Execute JQ patterns
```