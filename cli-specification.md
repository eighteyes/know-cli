# Knowledge Map CLI Specification

## Overview

The Knowledge Map CLI provides comprehensive project analysis, entity extraction, and development workflow integration for structured project specifications.

## Installation & Setup

```bash
npm install -g knowledge-map-cli
# or
cargo install knowledge-map-cli

# Initialize in project directory
km init --format lucid-commander
```

## Core Commands

### Entity Extraction Commands

#### `km get <entity_type> <entity_id>`
Extract specific entity with full context for Claude development.

```bash
# Basic entity extraction
km get screen dashboard
km get component fleet-status-map
km get feature real-time-status
km get user owner
km get model robot

# With context depth control
km get screen dashboard --depth 2          # Include 2 levels of dependencies
km get component fleet-map --minimal       # Just the entity, no relations
km get feature auth --full-context         # Everything related to this feature
```

**Output Format:**
```json
{
  "requested_entity": { /* full entity with resolved content_refs */ },
  "related_entities": {
    "dependencies": [ /* entities this depends on */ ],
    "dependents": [ /* entities that depend on this */ ],
    "components": [ /* related components */ ],
    "screens": [ /* related screens */ ],
    "features": [ /* related features */ ],
    "models": [ /* related data models */ ]
  },
  "development_context": {
    "files_to_create": [ /* suggested file paths */ ],
    "existing_patterns": [ /* similar components in codebase */ ],
    "design_tokens": { /* relevant design system values */ },
    "api_endpoints": [ /* related API routes */ ]
  },
  "implementation_notes": [
    "Component depends on websocket-client for real-time updates",
    "Requires react-leaflet for map functionality",
    "Must implement responsive design for mobile compatibility"
  ]
}
```

### Validation Commands

#### `km validate [type]`
Comprehensive system consistency checking.

```bash
km validate                    # Full system validation
km validate links             # Check all entity references
km validate dependencies      # Analyze dependency chains  
km validate permissions       # Verify user access patterns
km validate data-flow        # Check model→component→screen flow
km validate duplicates       # Find duplicate content
km validate --fix           # Auto-fix simple issues where possible
```

### Analysis Commands  

#### `km analyze <analysis_type>`
Deep system analysis for planning and optimization.

```bash
km analyze coverage          # Feature/requirement coverage analysis
km analyze deps             # Dependency mapping for implementation
km analyze orphans          # Find unreferenced entities
km analyze complexity       # Identify overly complex chains
km analyze bottlenecks      # Find implementation blocking points
km analyze parallel         # Identify parallelizable work
```

**Dependency Analysis Output:**
```json
{
  "implementation_phases": {
    "phase_1": { "entities": [...], "estimated_effort": "2-3 sprints" },
    "phase_2": { "entities": [...], "estimated_effort": "3-4 sprints" },
    "phase_3": { "entities": [...], "estimated_effort": "4-5 sprints" }
  },
  "critical_path": ["model:user", "model:robot", "feature:real-time-status"],
  "parallel_tracks": {
    "backend": ["models", "integrations", "apis"],
    "frontend": ["components", "screens", "flows"],
    "ai": ["capabilities", "ml-models", "edge-processing"]
  },
  "blockers": [
    {
      "entity": "integration:ros-pipeline",
      "blocks": ["feature:real-time-status", "component:fleet-map"],
      "risk": "high",
      "mitigation": "Prototype integration early"
    }
  ],
  "quick_wins": [
    {
      "entity": "component:status-indicator", 
      "effort": "1-2 days",
      "impact": "enables multiple screens",
      "dependencies": []
    }
  ]
}
```

### Statistics Commands

#### `km stats [--detailed]`
System metrics and health overview.

```bash
km stats                     # Basic entity counts
km stats --detailed         # Full metrics with relationships
km stats --format json      # Machine readable output
```

**Output:**
```json
{
  "entity_counts": {
    "users": 7,
    "screens": 12, 
    "components": 24,
    "features": 18,
    "models": 8,
    "requirements": 15
  },
  "relationship_health": {
    "total_relationships": 156,
    "orphaned_entities": 2,
    "circular_dependencies": 0,
    "broken_references": 0
  },
  "coverage_metrics": {
    "requirements_covered": "94%",
    "features_implemented": "87%", 
    "components_tested": "76%"
  },
  "complexity_metrics": {
    "max_dependency_depth": 6,
    "average_entity_connections": 4.2,
    "most_connected_entity": "model:robot"
  }
}
```

## Integration with Claude

### Piped Development Workflow

```bash
# Start development on specific entity
km get screen dashboard | claude

# Validate before committing  
km validate --json | claude --prompt "Review these validation issues and suggest fixes"

# Implementation planning
km analyze deps --feature user-auth | claude --prompt "Create implementation plan for user authentication"

# Coverage analysis
km analyze coverage | claude --prompt "Prioritize uncovered requirements by business impact"
```

### Context Injection

```bash
# Include related entities automatically
km get component fleet-map --claude-context | claude

# Add design system context
km get screen dashboard --include design-system | claude  

# Include similar patterns for reference
km get component data-grid --include-patterns | claude
```

## Configuration

### `.kmrc.json`
```json
{
  "knowledge_map": "./knowledge-map.json",
  "format_version": "1.0.0",
  "validation": {
    "strict_references": true,
    "require_descriptions": true,
    "enforce_naming_convention": true
  },
  "claude_integration": {
    "include_design_system": true,
    "include_similar_patterns": true,
    "context_depth": 2
  },
  "output_format": "json",
  "mcp_sync": {
    "notion_database": "knowledge-map-sync",
    "auto_sync": false
  }
}
```

## Advanced Features

### Watch Mode
```bash
km watch --entity screen:dashboard  # Watch specific entity changes
km watch --validate                 # Continuous validation
```

### Export & Import
```bash
km export --format notion          # Export to Notion-compatible format
km export --entity-type screens --format markdown
km import --from ./legacy-specs.json --merge
```

### Diff & Compare
```bash
km diff v1.0.0 v1.1.0              # Compare versions
km diff --entity feature:real-time-status  # Show entity changes
```

### MCP Integration
```bash
km mcp sync notion                  # Sync with Notion database
km mcp status                      # Check sync status  
km mcp configure --database "Project Knowledge Map"
```

## Validation Rules Engine

### Built-in Validators
- **reference_integrity**: All entity references must exist
- **circular_dependencies**: Detect and prevent dependency loops  
- **naming_convention**: Enforce kebab-case IDs, Title Case names
- **required_fields**: Validate required entity fields
- **content_uniqueness**: Detect duplicate descriptions
- **permission_consistency**: User access patterns must be coherent

### Custom Validators
```bash
km validate --config ./custom-rules.json
```

### Auto-fix Capabilities
```bash
km validate --fix-naming           # Fix naming convention issues
km validate --fix-references       # Update broken references  
km validate --deduplicate         # Consolidate duplicate content
```

## Performance Optimization

### Caching
- Entity resolution caching for faster repeated queries
- Validation result caching
- Dependency graph caching

### Parallel Processing
- Multi-threaded validation
- Parallel dependency analysis
- Concurrent entity extraction

## Error Handling

### Exit Codes
- 0: Success
- 1: Validation errors found
- 2: Missing required files
- 3: Invalid configuration
- 4: Network/MCP sync errors

### Verbose Output
```bash
km validate --verbose              # Detailed error messages
km get screen dashboard --debug    # Debug entity resolution
```

This CLI transforms the knowledge map from a static document into a dynamic development tool that integrates seamlessly with Claude for AI-assisted development workflows.