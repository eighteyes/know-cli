# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lucid Commander (LC) - A knowledge graph-driven robotics fleet management platform for commercial operations. The system uses a JSON-based knowledge graph (`spec-graph.json`) to define and track all system entities, dependencies, and relationships.

Current deployment: 1000 Window Washing Drones with painting capabilities and pressure washing rovers in development.

## Key Architecture

### Knowledge Graph System
The codebase is organized around a JSON knowledge graph stored in `.ai/spec-graph.json` that defines:
- **Entities**: features, components, screens, functionality, requirements, users, objectives, actions, platforms, models, interfaces
- **Graph**: dependency relationships between entities
- **References**: shared descriptions, technical architecture, acceptance criteria

### Tool Architecture
Three-layer architecture for graph operations:
1. **User Interface**: `know` CLI - primary command interface for developers
2. **Core Operations**: Backend scripts in `scripts/` and `know/lib/` for graph queries and modifications
3. **Data Layer**: JSON graph file at `.ai/spec-graph.json`

## Essential Commands

### Build and Test
```bash
# Run all tests
npm run test:all

# Run graph-specific tests
npm run graph:test
./tests/know/run-tests.sh

# Validate graph integrity
npm run graph:validate
./know/know validate

# List available commands
npm run help
```

### Know CLI - Primary Interface
```bash
# Discovery
./know/know list features           # List all features
./know/know search telemetry       # Search across entities
./know/know show feature real-time-telemetry

# Dependencies
./know/know deps feature:real-time-telemetry    # Show dependencies
./know/know impact platform:aws-infrastructure  # Show what depends on this
./know/know path user:owner feature:real-time-telemetry

# Specification Generation
./know/know feature real-time-telemetry         # Generate feature spec
./know/know component telemetry-processor       # Generate component spec
./know/know package feature:real-time-telemetry # Complete implementation package

# Validation
./know/know check feature real-time-telemetry   # Check completeness
./know/know preview feature real-time-telemetry # Preview before generation
./know/know cycles                              # Detect circular dependencies
```

### Perspective Profiles
```bash
./know/know profiles list            # Show available dependency perspectives
./know/know profiles show default    # Inspect ordering for a profile
./know/know --profile product_lead deps feature:real-time-telemetry
```
Profiles reorder dependency output without touching the underlying `depends_on` data, letting different teams reason in their preferred sequence. Omit `--profile` (or select `default`) to retain the original Lucid Commander flow.

### Graph Query Operations
```bash
# Using query-graph.sh directly
./know/lib/query-graph.sh deps feature:real-time-telemetry
./know/lib/query-graph.sh impact platform:aws-infrastructure
./know/lib/query-graph.sh cycles
./know/lib/query-graph.sh stats

# Using mod-graph.sh for modifications
./know/lib/mod-graph.sh list features
./know/lib/mod-graph.sh search telemetry
./know/lib/mod-graph.sh validate
./know/lib/mod-graph.sh connect feature:fleet-status depends_on component:telemetry-aggregator
```

## Working with the Knowledge Graph

### Entity Reference Format
All entities use the format: `<type>:<id>`
- Example: `feature:real-time-telemetry`
- Example: `user:owner`
- Example: `platform:aws-infrastructure`

### Graph Structure
```json
{
  "entities": {
    "features": { "feature-id": { "name": "...", "type": "feature" } },
    "components": { "component-id": { ... } }
  },
  "graph": {
    "feature:feature-id": {
      "depends_on": ["component:some-component"],
      "required_by": ["user:owner"]
    }
  },
  "references": {
    "descriptions": { "desc-ref": "Description content" }
  }
}
```

### Dependency Resolution Order
When resolving dependencies, follow this hierarchy:
```
HOW: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models
WHAT: Project → User → Objectives → Actions
Integration: User → Requirements, Objectives → Features, Actions → Components
```

## Important Files and Locations

- **Knowledge Graph**: `.ai/spec-graph.json` - The central knowledge graph
- **Know CLI**: `know/know` - Primary command interface
- **Query Tool**: `know/lib/query-graph.sh` - Graph database queries
- **Modify Tool**: `know/lib/mod-graph.sh` - Graph modifications
- **Profiles**: `.ai/profiles/` - Perspective definitions for dependency traversal
- **Scripts**: `scripts/` - Analysis and utility scripts
- **Tests**: `tests/know/` - Test suites for validation
- **Templates**: `know/templates/` - Specification generation templates
- **Generators**: `know/generators/` - Code generation tools

## Development Workflow

1. **Before making changes**: Query the graph to understand dependencies
   ```bash
   ./know/know deps <entity>
   ./know/know impact <entity>
   ```

2. **Validate changes**: Always validate after modifications
   ```bash
   ./know/know validate
   ./know/know cycles
   ```

3. **Generate specifications**: Use know CLI for consistent specs
   ```bash
   ./know/know feature <feature-id>
   ./know/know package <entity-id>
   ```

4. **Test thoroughly**: Run tests after changes
   ```bash
   npm run test:all
   ```

## Key Principles

1. **Graph-First Development**: All system entities and relationships are defined in the knowledge graph
2. **Dependency Awareness**: Always check dependencies before modifications
3. **Tool Delegation**: Use `know` CLI which delegates to proven backend scripts
4. **Validation Required**: Run validation after any graph modifications
5. **Specification Generation**: Use generators for consistent documentation
6. **Perspective Awareness**: Choose a profile that matches your mental model before traversing dependencies; create a new file in `.ai/profiles/` if an existing view does not fit.

## User Roles (from graph)

- **owner**: Fleet owners who manage operators and robots
- **operator**: Robot operators assigned by owners
- **teleoperator**: Skilled remote pilots for 1:1 control
- **fleet-teleoperator**: Coordinate multiple autonomous systems
- **customer-service**: LB support staff with diagnostic access
- **operations-manager**: LB internal fleet oversight
- **executive**: Strategic oversight and business intelligence

## Notes

- The system supports 1000+ deployed window washing drones
- Painting and pressure washing capabilities are in development
- All graph operations maintain referential integrity automatically
- The `know` CLI provides AI-optimized output with the `--ai` flag
