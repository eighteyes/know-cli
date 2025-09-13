# JQ Graph Query Commands - JSON Graph Database

Comprehensive collection of jq commands for parsing and analyzing the JSON graph database structure.

## Basic Entity Queries

### Get all entities of a specific type
```bash
jq '.entities.screens' spec-graph.json
jq '.entities.features' spec-graph.json
jq '.entities.users' spec-graph.json
jq '.entities.platforms' spec-graph.json
jq '.entities.ui_components' spec-graph.json
```

### Extract specific entity by ID
```bash
jq '.entities.screens."fleet-dashboard"' spec-graph.json
jq '.entities.features."real-time-telemetry"' spec-graph.json
```

### List all entity IDs by type
```bash
jq '.entities.screens | keys[]' spec-graph.json
jq '.entities.features | keys[]' spec-graph.json
```

## JSON Graph Database Queries

### Find what an entity depends on
```bash
jq '.graph."user:owner".depends_on[]' spec-graph.json
jq '.graph."screen:fleet-dashboard".depends_on[]' spec-graph.json
```

### Find what depends on an entity (reverse lookup)
```bash
# Who depends on web-platform?
jq -r '.graph | to_entries[] | select(.value.depends_on[]? == "platform:web-platform") | .key' spec-graph.json

# What depends on real-time-telemetry feature?
jq -r '.graph | to_entries[] | select(.value.depends_on[]? == "feature:real-time-telemetry") | .key' spec-graph.json

# What screens depend on status indicators?
jq -r '.graph | to_entries[] | select(.value.depends_on[]? == "ui_component:status-indicators") | .key' spec-graph.json
```

### Entity dependency counts
```bash
# Entities with most dependencies (most complex)
jq '.graph | to_entries | map({entity: .key, dep_count: (.value.depends_on | length)}) | sort_by(.dep_count) | reverse' spec-graph.json

# Most depended-upon entities (most critical)
jq '.graph | to_entries[] | .value.depends_on[]' spec-graph.json | sort | uniq -c | sort -nr

# User access analysis
jq '.graph | to_entries[] | select(.key | startswith("user:")) | {user: .key, access_count: (.value.depends_on | length)}' spec-graph.json
```

## Multi-Hop Dependency Analysis

### Find dependency chains
```bash
# Recursive dependency lookup
jq -r '
def find_deps($entity):
  (.graph[$entity].depends_on[]? // empty) as $dep |
  $dep, find_deps($dep);

find_deps("feature:real-time-telemetry")
' spec-graph.json
```

### Trace all paths to a dependency
```bash
# Find all paths that lead to AWS infrastructure
jq -r '
def find_paths_to($target; $current; $visited):
  if ($visited | has($current)) then empty
  elif $current == $target then [$current]
  else
    (.graph[$current].depends_on[]? // empty) as $dep |
    [$current] + find_paths_to($target; $dep; $visited + {($current): true})
  end;

.graph | keys[] as $entity |
find_paths_to("platform:aws-infrastructure"; $entity; {})
' spec-graph.json
```

## Impact Analysis Queries

### Find all dependents of an entity
```bash
# What would be impacted if AWS infrastructure failed?
jq -r '
def find_dependents($target):
  (.graph | to_entries[] | select(.value.depends_on[]? == $target) | .key) as $dependent |
  $dependent, find_dependents($dependent);

find_dependents("platform:aws-infrastructure") | unique
' spec-graph.json
```

### Circular dependency detection
```bash
# Find circular dependencies
jq -r '
def has_cycle($start; $current; $visited):
  if ($visited | has($current)) then
    if $current == $start then true else false end
  else
    (.graph[$current].depends_on[]? // empty) as $next |
    has_cycle($start; $next; $visited + {($current): true})
  end;

.graph | keys[] as $entity |
select(has_cycle($entity; $entity; {})) |
$entity
' spec-graph.json
```

## Type-Based Dependency Analysis

### Dependencies by entity type
```bash
# What do users depend on?
jq -r '.graph | to_entries[] | select(.key | startswith("user:")) | {user: .key, depends_on: .value.depends_on}' spec-graph.json

# What do screens depend on?
jq -r '.graph | to_entries[] | select(.key | startswith("screen:")) | {screen: .key, depends_on: .value.depends_on}' spec-graph.json

# What do features depend on?
jq -r '.graph | to_entries[] | select(.key | startswith("feature:")) | {feature: .key, depends_on: .value.depends_on}' spec-graph.json

# What do platforms depend on?
jq -r '.graph | to_entries[] | select(.key | startswith("platform:")) | {platform: .key, depends_on: .value.depends_on}' spec-graph.json
```

### Cross-type dependency patterns
```bash
# Which users depend on which screens?
jq -r '.graph | to_entries[] | select(.key | startswith("user:")) | 
{user: .key, screens: [.value.depends_on[] | select(startswith("screen:"))]}' spec-graph.json

# Which screens depend on which features?
jq -r '.graph | to_entries[] | select(.key | startswith("screen:")) |
{screen: .key, features: [.value.depends_on[] | select(startswith("feature:"))]}' spec-graph.json

# Which features depend on which platforms?
jq -r '.graph | to_entries[] | select(.key | startswith("feature:")) |
{feature: .key, platforms: [.value.depends_on[] | select(startswith("platform:"))]}' spec-graph.json
```

## Validation Queries

### Find missing dependencies
```bash
# Entity references that don't exist
jq -r '
(.graph | keys) as $valid_entities |
.graph | to_entries[] | .value.depends_on[]? |
select(. as $ref | $valid_entities | index($ref) | not)
' spec-graph.json
```

### Orphaned entities
```bash
# Entities that nothing depends on
jq -r '
(.graph | [.[] | .depends_on[]?]) as $referenced |
.graph | keys[] |
select(. as $entity | $referenced | index($entity) | not)
' spec-graph.json
```

### Self-dependencies
```bash
# Entities that depend on themselves
jq -r '.graph | to_entries[] | select(.value.depends_on[]? == .key) | .key' spec-graph.json
```

## Reporting Queries

### Dependency summary report
```bash
jq '{
  total_entities: (.graph | keys | length),
  total_dependencies: (.graph | [.[] | .depends_on[]?] | length),
  entities_by_dependency_count: (.graph | to_entries | 
    map({entity: .key, dep_count: (.value.depends_on | length)}) | 
    group_by(.dep_count) | 
    map({dependency_count: .[0].dep_count, entity_count: length})),
  most_critical_dependencies: (
    [.graph | .[] | .depends_on[]?] |
    group_by(.) | map({entity: .[0], dependent_count: length}) |
    sort_by(.dependent_count) | reverse | .[0:10]
  )
}' spec-graph.json
```

### Complexity analysis
```bash
# Entities with highest complexity (most dependencies)
jq '.graph | to_entries | map({
  entity: .key,
  complexity: (.value.depends_on | length),
  dependencies: .value.depends_on
}) | sort_by(.complexity) | reverse | .[0:5]' spec-graph.json

# System bottlenecks (most depended upon)
jq '[.graph | .[] | .depends_on[]?] | 
group_by(.) | map({dependency: .[0], usage_count: length}) |
sort_by(.usage_count) | reverse | .[0:5]' spec-graph.json
```

## Advanced Analysis

### Dependency layers
```bash
# Group entities by dependency depth
jq -r '
def depth($entity; $visited):
  if ($visited | has($entity)) then 0
  else
    [(.graph[$entity].depends_on[]? // empty) | depth(.; $visited + {($entity): true})] |
    if length == 0 then 0 else (max + 1) end
  end;

.graph | to_entries | map({entity: .key, depth: depth(.key; {})}) |
group_by(.depth) | map({layer: .[0].depth, entities: [.[].entity]})
' spec-graph.json
```

### Dependency strength analysis
```bash
# Calculate dependency strength (how many entities depend on each entity)
jq '[.graph | .[] | .depends_on[]?] |
group_by(.) | map({
  entity: .[0], 
  strength: length,
  critical: (if length > 5 then true else false end)
}) | sort_by(.strength) | reverse' spec-graph.json

## Content Reference Queries

### Access shared content references
```bash
# List all content references
jq '.references.descriptions | keys[]' spec-graph.json

# Get specific description reference
jq '.references.descriptions."real-time-telemetry-desc"' spec-graph.json

# Find entities using a specific reference
jq -r '.entities | to_entries[] | .value | to_entries[] | select(.value.description_ref? == "real-time-telemetry-desc") | .key' spec-graph.json
```

### Component implementation queries
```bash
# List all component implementations
jq '.references.component_implementations | keys[]' spec-graph.json

# Get specific component configuration
jq '.references.component_implementations."status-indicators"' spec-graph.json

# Find components with specializations
jq '.references.component_implementations | to_entries[] | select(.value.specialized_for?) | {component: .key, specializations: .value.specialized_for}' spec-graph.json
```
```