- IMPORTANT: Keep ~/ai/commands/lb/knowledge-graph.md and json-graph-approach.md updated with the latest evolution of the structure in `knowledge-map-cmd.json` approach
- IMPORTANT: When we improve the approach, save a learning entry to `json-graph-learning.md`
- string together multiple `jq` commands into a single BASH call

# GRAPH SCRIPTS
All in `scripts/`
- `json-graph-query.sh`
```
JSON Graph Query Tool

USAGE:
  ./scripts/json-graph-query.sh <command> [options]

COMMANDS:
  traverse <entity_id> <relationship>    - Follow relationships from entity
  reverse <entity_id> <relationship>     - Find entities that relate TO this entity
  path <from_entity> <to_entity>         - Find connection path between entities
  deps <entity_id>                       - Show dependency chain
  impact <entity_id>                     - Show impact analysis (what depends on this)
  user <user_id>                         - Show all entities accessible to user
  cycles                                 - Detect circular dependencies
  stats                                  - Show graph statistics
  view <view_name>                       - Show pre-computed view

EXAMPLES:
  ./scripts/json-graph-query.sh traverse screen:dashboard contains
  ./scripts/json-graph-query.sh reverse component:fleet-map contained_by
  ./scripts/json-graph-query.sh path screen:dashboard model:robot
  ./scripts/json-graph-query.sh deps feature:real-time-status
  ./scripts/json-graph-query.sh impact model:robot
  ./scripts/json-graph-query.sh user user:owner
  ./scripts/json-graph-query.sh view user_owner_context
```

- `mod-graph.sh`
```
Knowledge Graph Modifier
Fast CLI for managing knowledge-map-cmd.json

Usage:
  ./scripts/mod-graph.sh <command> [args...]

Entity Commands:
  list [type]              List entities (optionally by type)
  add <type> <id> <name>   Add new entity
  edit <type> <id>         Edit entity (interactive)
  remove <type> <id>       Remove entity
  show <type> <id>         Show entity details

Graph Commands:
  connect <from> <to>      Add dependency: from -> to
  disconnect <from> <to>   Remove dependency
  deps <entity>            Show dependencies for entity
  dependents <entity>      Show what depends on entity
  validate                 Validate graph structure

Utility Commands:
  stats                    Show statistics
  backup                   Create backup
  types                    List entity types
  search <term>            Search entities by name/id

Examples:
  ./scripts/mod-graph.sh add features new-telemetry "Real-time Telemetry v2"
  ./scripts/mod-graph.sh connect feature:new-telemetry platform:aws-infrastructure
  ./scripts/mod-graph.sh deps user:owner
  ./scripts/mod-graph.sh search telemetry
❯ ./scripts/json-graph-query.sh
```
