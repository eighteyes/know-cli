# Know CLI - Primary Interface for Knowledge Graph Operations

The `know` CLI is the **primary user-friendly interface** for working with knowledge graphs and generating implementation specifications. It provides a clean, intuitive command set while leveraging the robust graph database operations in the core backend scripts.

## Architecture

`know` acts as the **orchestration layer** that delegates to proven backend scripts:

- **`scripts/json-graph-query.sh`** - Core graph database queries (deps, impact, cycles, stats)
- **`scripts/mod-graph.sh`** - Graph modification operations (list, search, validate, connect)
- **`know`** - User-friendly interface + specification generation

This architecture ensures:
- ✅ **Single source of truth** for graph operations
- ✅ **Consistent behavior** across all tools  
- ✅ **Easy maintenance** - improvements go in core scripts
- ✅ **Better tested** - core operations are proven and reliable

## Quick Start

```bash
# List entities
./know list features

# Search across all entity types
./know search telemetry

# Show dependencies (delegates to json-graph-query.sh)
./know deps feature:real-time-telemetry

# Generate implementation specifications
./know feature real-time-telemetry

# Generate complete implementation package
./know package feature:real-time-telemetry
```

## Core Commands

### Entity Discovery
```bash
know list [entity_type]                 # List entities (delegates to mod-graph.sh)
know search <term> [entity_type]       # Fuzzy search entities
know show <type> <id>                   # Show entity details
```

### Graph Analysis
```bash
know deps <entity_ref>                  # Dependency analysis (json-graph-query.sh)
know impact <entity_ref>                # Impact analysis (json-graph-query.sh)  
know cycles                             # Detect circular dependencies
know path <from> <to>                   # Find dependency path
know stats                              # Graph statistics
```

### Specification Generation  
```bash
know feature <entity_id>                # Feature spec with acceptance criteria
know component <entity_id>              # Component implementation spec
know screen <entity_id>                 # Screen/UI specification  
know functionality <entity_id>          # Technical functionality spec
know requirement <entity_id>            # Requirement with acceptance criteria
know api <entity_id>                    # API specification from schema
```

### Implementation Planning
```bash
know package <entity_id>                # Complete implementation package
know test <entity_ref>                  # Test scenarios from acceptance criteria
know order                              # Optimal implementation order
know validate                           # Reference integrity checking
```

### Preview & Validation
```bash
know preview <type> <entity_id>         # Preview spec sections before generation
know check <type> <entity_id>           # Validate completeness before generation
```

## Command Options

```bash
--format <md|json|yaml>                 # Output format (default: md)
--output <file>                         # Output to file instead of stdout
--map <file>                            # Path to knowledge map JSON file
--ai                                    # Generate Claude-optimized specification
```

## Examples

### Basic Usage
```bash
# Find telemetry-related entities
./know search telemetry

# See what depends on real-time telemetry
./know deps feature:real-time-telemetry

# Generate a feature specification
./know feature real-time-telemetry

# Create complete implementation package
./know package feature:real-time-telemetry --output implementation.md
```

### Advanced Analysis
```bash
# Find implementation path between entities  
./know path user:owner feature:real-time-telemetry

# Check for circular dependencies
./know cycles

# Show system statistics
./know stats

# Validate entire knowledge graph
./know validate
```

### AI-Optimized Specifications
```bash
# Generate Claude-optimized specs
./know --ai feature user-authentication --output spec.md

# Use with Claude
cat spec.md | claude "implement this feature following the specification"
```

## Backend Integration

The `know` tool delegates core operations to backend scripts:

### json-graph-query.sh Operations
- `know deps` → `./scripts/json-graph-query.sh deps`
- `know impact` → `./scripts/json-graph-query.sh impact`  
- `know cycles` → `./scripts/json-graph-query.sh cycles`
- `know stats` → `./scripts/json-graph-query.sh stats`
- `know path` → `./scripts/json-graph-query.sh path`

### mod-graph.sh Operations  
- `know list` → `./scripts/mod-graph.sh list`
- `know search` → `./scripts/mod-graph.sh search`
- `know validate` → `./scripts/mod-graph.sh validate`
- `know show` → `./scripts/mod-graph.sh show`

### Specification Generation
Uses the internal generator system with templates and rendering pipeline for:
- Feature specifications with acceptance criteria
- Component implementation specs
- Screen/UI specifications with design system integration
- API documentation from schema entities
- Complete implementation packages

## Knowledge Map Format

Works with the current `spec-graph.json` structure:

```json
{
  "entities": {
    "features": { "feature-id": { "name": "...", "type": "feature" } },
    "components": { "component-id": { ... } },
    "screens": { "screen-id": { ... } }
  },
  "graph": {
    "feature:feature-id": { "depends_on": ["component:some-component"] }
  },
  "references": {
    "descriptions": { "desc-ref": "Description content" },
    "technical_architecture": { ... }
  }
}
```

## Improving the System

To enhance functionality:

1. **Graph queries** → Improve `scripts/json-graph-query.sh`
2. **Entity operations** → Improve `scripts/mod-graph.sh` 
3. **User experience** → Improve `know` interface layer
4. **Specifications** → Update templates and generators

Changes to backend scripts automatically benefit the `know` interface.

## Testing

```bash
# Run all tests
./tests/know/run-tests.sh

# Run specific test suite
./tests/know/run-tests.sh --pattern discovery

# Run with verbose output
./tests/know/run-tests.sh -v
```

Tests validate both the `know` interface and its integration with backend scripts.

## Requirements

- `jq` - JSON processor
- `bash` 4.0+
- Backend scripts: `scripts/json-graph-query.sh`, `scripts/mod-graph.sh`

## Philosophy

The `know` CLI embodies the principle of **"do one thing well"** while orchestrating specialized tools. It provides the user-friendly interface developers want while leveraging the robust, tested graph operations in the backend scripts. This creates a maintainable, reliable system where improvements cascade throughout the entire toolchain.