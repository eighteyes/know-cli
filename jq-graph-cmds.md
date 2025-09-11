# JQ Graph Query Commands

Comprehensive collection of jq commands for parsing and analyzing the knowledge graph.

## Basic Entity Queries

### Get all entities of a specific type
```bash
jq '.entities.screens' knowledge-map.json
jq '.entities.features' knowledge-map.json
jq '.entities.models' knowledge-map.json
```

### Extract specific entity by ID
```bash
jq '.entities.screens."fleet-dashboard"' knowledge-map.json
jq '.entities.features."real-time-telemetry"' knowledge-map.json
```

### List all entity IDs by type
```bash
jq '.entities.screens | keys[]' knowledge-map.json
jq '.entities.features | keys[]' knowledge-map.json
```

## Graph Relationship Queries

### Find outbound relationships from an entity
```bash
jq '.graph."user:owner".outbound' knowledge-map.json
jq '.graph."screen:fleet-dashboard".outbound.contains[]' knowledge-map.json
```

### Find inbound relationships to an entity
```bash
jq '.graph."platform:aws-infrastructure".inbound' knowledge-map.json
jq '.graph."feature:real-time-telemetry".inbound.used_by[]' knowledge-map.json
```

### Trace specific relationship types
```bash
# What does the owner access?
jq '.graph."user:owner".outbound.accesses[]' knowledge-map.json

# What features implement real-time telemetry?
jq '.graph."feature:real-time-telemetry".inbound.implemented_by[]' knowledge-map.json

# What components are contained by screens?
jq '.graph | to_entries[] | select(.value.outbound.contains?) | {entity: .key, contains: .value.outbound.contains}' knowledge-map.json
```

## Index-Based Queries

### Query by priority
```bash
jq '.indexes.by_priority.P0[]' knowledge-map.json
jq '.indexes.by_priority.P1[]' knowledge-map.json
```

### Query by type with counts
```bash
jq '.indexes.by_type | to_entries[] | {type: .key, count: (.value | length), entities: .value}' knowledge-map.json
```

### Query by user access
```bash
jq '.indexes.by_user_access.owner[]' knowledge-map.json
jq '.indexes.by_user_access | to_entries[] | {user: .key, accessible_screens: .value}' knowledge-map.json
```

## Project Management Queries

### Feature status analysis
```bash
# All blocked features
jq '.project.roadmap | to_entries[] | select(.value.blockers | length > 0) | {feature: .key, blockers: .value.blockers}' knowledge-map.json

# Features by status
jq '.project.roadmap | to_entries[] | {feature: .key, status: .value.status, priority: .value.priority}' knowledge-map.json

# P0 features that are not completed
jq '.project.roadmap | to_entries[] | select(.value.priority == "P0" and .value.status != "completed") | {feature: .key, status: .value.status}' knowledge-map.json
```

### Dependency analysis
```bash
# Technical dependencies
jq '.project.dependencies.technical' knowledge-map.json

# Find features with no dependencies (can start immediately)
jq '.project.roadmap | keys[] as $f | select([.project.dependencies.technical[$f]?, .project.roadmap[$f].dependencies[]?] | length == 0) | $f' knowledge-map.json

# Features blocked by other features
jq '.project.dependencies.technical | to_entries[] | {feature: .key, depends_on: .value}' knowledge-map.json
```

## Content Library Queries

### Search descriptions
```bash
jq '.content_library | to_entries[] | select(.value | test("real-time"; "i")) | {ref: .key, description: .value}' knowledge-map.json
```

### Find unused content references
```bash
# Get all description_ref values
jq '[.entities[][] | select(type == "object" and has("description_ref")) | .description_ref] | unique' knowledge-map.json

# Compare with content_library keys
jq '.content_library | keys' knowledge-map.json
```

## Advanced Graph Traversal

### Multi-hop relationship traversal
```bash
# Find all entities that depend on AWS infrastructure (2-hop)
jq '.graph."platform:aws-infrastructure".inbound.powered_by[] as $entity | .graph[$entity].inbound | to_entries[] | {relationship: .key, dependents: .value}' knowledge-map.json

# Find dependency chains for a feature
jq '
def deps(entity):
  .project.roadmap[entity].dependencies[]? as $dep |
  {entity: entity, depends_on: $dep} +
  if (.project.roadmap[$dep]) then deps($dep) else empty end;

deps("feature:parts-ordering-system")
' knowledge-map.json
```

### Impact analysis
```bash
# What would be affected if a platform went down?
jq '.graph."platform:aws-infrastructure".inbound | to_entries[] | {relationship: .key, impacted: .value}' knowledge-map.json

# Recursive impact analysis
jq '
def impacts(entity):
  (.graph[entity].inbound // {}) | to_entries[] | .value[] as $dependent |
  {impacted: $dependent, via: .key} +
  impacts($dependent);

impacts("platform:aws-infrastructure")
' knowledge-map.json
```

## Validation Queries

### Check for broken references
```bash
# Find entity references that don't exist
jq '
(.entities | keys) as $valid_ids |
.graph | to_entries[] |
(.value.outbound // {}) | to_entries[] |
.value[] | select(. as $ref | $valid_ids | index($ref) | not)
' knowledge-map.json
```

### Bidirectional consistency check
```bash
# Check if outbound relationships have matching inbound
jq '
.graph | to_entries[] | .key as $entity |
(.value.outbound // {}) | to_entries[] | .key as $rel_type |
.value[] as $target |
{
  entity: $entity,
  target: $target, 
  relationship: $rel_type,
  has_reverse: ((.graph[$target].inbound // {}) | has($rel_type))
}
' knowledge-map.json
```

## Duplicity Detection Queries

### Find duplicate entity names
```bash
# Detect entities with identical names across types
jq '
[.entities[][] | select(type == "object" and has("name")) | {id: .id, name: .name, type: .type}] |
group_by(.name) |
map(select(length > 1)) |
map({name: .[0].name, duplicates: [.[].id], types: [.[].type]})
' knowledge-map.json
```

### Find duplicate descriptions in content library
```bash
# Detect identical descriptions (potential content duplication)
jq '
.content_library | to_entries |
group_by(.value) |
map(select(length > 1)) |
map({description: .[0].value, duplicate_refs: [.[].key]})
' knowledge-map.json
```

### Find redundant relationships
```bash
# Detect duplicate relationship entries
jq '
.graph | to_entries[] |
.key as $entity |
(.value.outbound // {}) | to_entries[] |
.key as $rel_type |
.value | group_by(.) | 
map(select(length > 1)) |
map({entity: $entity, relationship: $rel_type, target: .[0], count: length})
' knowledge-map.json
```

### Find similar entity descriptions
```bash
# Find entities with very similar description references (potential consolidation opportunities)
jq '
[.entities[][] | select(type == "object" and has("description_ref")) | 
{id: .id, desc_ref: .description_ref, desc_text: .content_library[.description_ref]}] |
group_by(.desc_text) |
map(select(length > 1)) |
map({description: .[0].desc_text, entities: [.[].id]})
' knowledge-map.json
```

### Find duplicate feature requirements
```bash
# Detect features with identical requirements (potential consolidation)
jq '
.entities.features | to_entries |
map({feature: .key, requirements: (.value.requirements // [])}) |
group_by(.requirements) |
map(select(length > 1 and .[0].requirements | length > 0)) |
map({requirements: .[0].requirements, features: [.[].feature]})
' knowledge-map.json
```

### Find duplicate model attributes
```bash
# Detect models with identical attribute sets
jq '
.entities.schema // {} | to_entries |
map({model: .key, attributes: (.value.attributes | keys)}) |
group_by(.attributes) |
map(select(length > 1)) |
map({attributes: .[0].attributes, models: [.[].model]})
' knowledge-map.json
```

### Comprehensive duplicity report
```bash
# Generate complete duplicity analysis report
jq '
{
  duplicate_names: (
    [.entities[][] | select(type == "object" and has("name")) | {id: .id, name: .name}] |
    group_by(.name) | map(select(length > 1)) |
    map({name: .[0].name, count: length, entities: [.[].id]})
  ),
  duplicate_descriptions: (
    .content_library | to_entries |
    group_by(.value) | map(select(length > 1)) |
    map({description: .[0].value, count: length, refs: [.[].key]})
  ),
  redundant_relationships: (
    [.graph | to_entries[] | .key as $entity |
     (.value.outbound // {}) | to_entries[] | .key as $rel |
     .value[] as $target | {entity: $entity, rel: $rel, target: $target}] |
    group_by([.entity, .rel, .target]) |
    map(select(length > 1)) |
    map({relationship: .[0], count: length})
  ),
  summary: {
    total_entities: [.entities[][]] | length,
    total_descriptions: .content_library | keys | length,
    total_relationships: [.graph | .[] | .outbound // {} | .[]] | length
  }
}
' knowledge-map.json
```

## Reporting Queries

### Generate entity summary
```bash
jq '{
  total_entities: (.entities | [.[][]] | length),
  by_type: (.entities | to_entries | map({type: .key, count: (.value | length)})),
  total_relationships: (.graph | [.[][].outbound // {} | .[]] | length),
  features_by_status: (.project.roadmap | group_by(.status) | map({status: .[0].status, count: length}))
}' knowledge-map.json
```

### Critical path analysis
```bash
# Features with the most dependencies
jq '.project.roadmap | to_entries | map({feature: .key, dep_count: (.value.dependencies | length)}) | sort_by(.dep_count) | reverse' knowledge-map.json

# Most connected entities in graph
jq '.graph | to_entries | map({
  entity: .key, 
  connections: ((.value.outbound // {}) | [.[]] | length) + ((.value.inbound // {}) | [.[]] | length)
}) | sort_by(.connections) | reverse | .[0:5]' knowledge-map.json
```

## Meta Queries

### Schema analysis
```bash
# All relationship types used
jq '[.graph | .[] | (.outbound // {}, .inbound // {}) | keys[]] | unique' knowledge-map.json

# Entity type distribution
jq '.entities | to_entries | map({type: .key, entities: (.value | length)})' knowledge-map.json

# Content library usage
jq '[.entities[][] | select(type == "object" and has("description_ref")) | .description_ref] | group_by(.) | map({ref: .[0], usage_count: length}) | sort_by(.usage_count) | reverse' knowledge-map.json
```