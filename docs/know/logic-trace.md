# Know Tool Logic Trace

## System Architecture

### Core Components

```
know (main script)
├── Library Files (know/lib/)
│   ├── utils.sh          - Common utility functions
│   ├── resolve.sh        - Entity/reference resolution
│   ├── query.sh          - Graph traversal functions
│   ├── backend.sh        - Backend processing
│   ├── render.sh         - Rendering functions
│   ├── autocomplete.sh   - Bash completion support
│   ├── validate-simple.sh - Basic validation
│   ├── validation-comprehensive.sh - Deep validation
│   ├── workflows.sh      - Workflow automation
│   ├── health.sh         - Graph health checks
│   ├── dynamic-commands.sh - Dynamic command support
│   ├── mod-graph.sh      - Graph modification
│   ├── query-graph.sh    - Graph queries
│   └── ...more specialized scripts
├── Generators (know/generators/)
│   ├── simple-feature-spec.sh
│   ├── simple-screen-spec.sh
│   ├── component-spec.sh
│   ├── full-chain-qa.sh
│   └── ...more generators
└── Templates (know/templates/)
    └── Various markdown templates
```

### Initialization Flow

```
1. Script Start
   ↓
2. Set environment (set -euo pipefail)
   ↓
3. Determine directories
   - SCRIPT_DIR: Script location
   - PROJECT_ROOT: Project root
   - Handle /usr/local/bin installation
   ↓
4. Set paths
   - KNOWLEDGE_MAP: .ai/spec-graph.json
   - LIB_DIR, TEMPLATE_DIR, GENERATOR_DIR
   ↓
5. Source library files
   - Load all .sh files from lib/
   ↓
6. Parse global options
   - --format, --output, --map, --ai
   ↓
7. Check dependencies (jq, knowledge map)
   ↓
8. Main command dispatcher
```

## Command Logic Traces

### 1. Entity Generation Commands (feature/component/screen)

**Command**: `know feature real-time-telemetry`

```
main()
├── Parse command: "feature"
├── Check if entity_id provided
│   ├── YES: Generate spec
│   │   ├── resolve_entity_reference("real-time-telemetry", "feature")
│   │   │   ├── Check if already in type:id format
│   │   │   └── Return: "feature:real-time-telemetry"
│   │   ├── get_completeness_score("feature:real-time-telemetry")
│   │   │   └── Calculate score from dependencies/references
│   │   ├── Check if score >= 70%
│   │   │   ├── NO: error() with guidance
│   │   │   └── YES: Continue
│   │   ├── generate_spec("feature", entity_ref, format, output)
│   │   │   ├── Determine generator script
│   │   │   │   └── simple-feature-spec.sh
│   │   │   ├── Export environment variables
│   │   │   ├── Change to project directory
│   │   │   ├── Execute generator script
│   │   │   └── Restore directory
│   │   └── Output result
│   └── NO: List entities
│       └── list_entities("features")
│           └── Query graph for all features
```

### 2. Dependency Analysis

**Command**: `know deps feature:user-auth`

```
main()
├── Parse command: "deps"
├── resolve_entity_reference("feature:user-auth")
│   └── Return: "feature:user-auth"
├── show_dependencies("feature:user-auth")
│   ├── get_dependencies(entity_ref)
│   │   └── jq query: .graph[entity].depends_on[]
│   ├── Display direct dependencies
│   │   └── For each dep: get_entity_name()
│   ├── Calculate transitive dependencies
│   │   └── Recursive traversal of dependency graph
│   └── Display dependency tree
```

### 3. Validation Commands

**Command**: `know validate feature:analytics --comprehensive`

```
main()
├── Parse command: "validate"
├── Check if entity_ref provided
│   ├── YES: Entity validation
│   │   ├── resolve_entity_reference("feature:analytics")
│   │   ├── Parse options (--comprehensive, --min-score)
│   │   ├── Check comprehensive flag
│   │   │   ├── TRUE: validate_entity_comprehensive()
│   │   │   │   ├── Check entity existence
│   │   │   │   ├── Get entity data
│   │   │   │   ├── Check dependencies
│   │   │   │   ├── Check references
│   │   │   │   ├── Calculate completeness score
│   │   │   │   ├── Identify gaps
│   │   │   │   └── Generate report
│   │   │   └── FALSE: validate_entity_completeness()
│   │   └── Return validation result
│   └── NO: Graph validation
│       └── validate_knowledge_map()
│           ├── Check JSON syntax
│           ├── Validate structure
│           └── Check reference integrity
```

### 4. Gap Analysis

**Command**: `know gaps feature:real-time-telemetry`

```
main()
├── Parse command: "gaps"
├── resolve_entity_reference("feature:real-time-telemetry")
├── validate_entity_comprehensive(entity_ref, 70)
│   ├── Load entity data
│   ├── Check required fields
│   ├── Analyze dependencies
│   │   ├── Missing dependencies
│   │   ├── Circular dependencies
│   │   └── Invalid references
│   ├── Check references
│   │   ├── Missing references
│   │   └── Orphaned references
│   ├── Calculate completeness
│   └── Generate gap report
├── Extract gap sections (grep)
└── Display identified gaps and recommendations
```

### 5. Graph Modification

**Command**: `know mod connect feature:auth component:login-form`

```
main()
├── Parse command: "mod"
├── Check subcommand: "connect"
│   └── Forward to mod-graph-enhanced.sh
├── mod-graph-enhanced.sh connect
│   ├── Validate connection allowed (dependency rules)
│   │   ├── Load dependency-rules.json
│   │   ├── Check if connection type allowed
│   │   └── Validate direction
│   ├── Add to graph section
│   │   └── jq update: .graph[from].depends_on += [to]
│   ├── Update bidirectional references
│   └── Save updated graph
```

### 6. Health Check

**Command**: `know health`

```
main()
├── Parse command: "health"
├── check_graph_health(KNOWLEDGE_MAP)
│   ├── Structural checks
│   │   ├── JSON validity
│   │   ├── Required sections (meta, entities, graph)
│   │   └── Schema compliance
│   ├── Dependency checks
│   │   ├── Circular dependencies
│   │   ├── Missing dependencies
│   │   └── Invalid references
│   ├── Reference checks
│   │   ├── Orphaned references
│   │   ├── Missing parent entities
│   │   └── Invalid reference keys
│   ├── Entity checks
│   │   ├── Missing required fields
│   │   ├── Completeness scores
│   │   └── Naming conventions
│   └── Generate health report
│       ├── Summary statistics
│       ├── Issues found
│       └── Recommendations
```

### 7. Interactive Workflows

**Command**: `know complete feature:analytics`

```
main()
├── Parse command: "complete"
├── resolve_entity_reference("feature:analytics")
├── complete_entity_interactive(entity_ref)
│   ├── Load current entity data
│   ├── identify_gaps()
│   │   └── Find missing fields/dependencies
│   ├── For each gap:
│   │   ├── Present gap to user
│   │   ├── Get user input (fzf/read)
│   │   ├── Validate input
│   │   └── Update entity
│   ├── Recalculate completeness
│   └── Save updated graph
```

### 8. Query Operations

**Command**: `know query traverse feature:auth --depth 3`

```
main()
├── Parse command: "query"
├── Forward to query-graph.sh
├── query-graph.sh traverse
│   ├── Parse arguments (entity, depth)
│   ├── Initialize queue with start entity
│   ├── BFS traversal
│   │   ├── For each entity in queue:
│   │   │   ├── Get dependencies
│   │   │   ├── Get dependents
│   │   │   ├── Add to visited set
│   │   │   └── Add neighbors to queue
│   │   └── Continue until depth reached
│   └── Output traversal result
│       ├── Visited entities
│       ├── Dependency paths
│       └── Statistics
```

## Data Flow Patterns

### Entity Resolution Flow
```
User Input → resolve_entity_reference()
           → Check format (type:id or just id)
           → If just id, search across types
           → Return normalized type:id
           → Pass to processing functions
```

### Dependency Chain Resolution
```
Entity → get_dependencies()
      → For each dependency
         → Recursive get_dependencies()
         → Build dependency tree
      → Detect cycles
      → Return ordered list
```

### Completeness Calculation
```
Entity → Load entity data
      → Check required fields (30%)
      → Check dependencies exist (30%)
      → Check references valid (20%)
      → Check descriptions/acceptance (20%)
      → Return weighted score
```

### Graph Modification Flow
```
Modification Request → Validate against rules
                    → Load current graph
                    → Apply modification (jq)
                    → Validate result
                    → Create backup
                    → Save new graph
```

## Error Handling Patterns

### Validation Errors
```
1. Entity not found
   → Suggest similar entities
   → Show search command

2. Low completeness
   → Show current score
   → Show required score
   → Suggest gap analysis

3. Invalid connection
   → Show allowed patterns
   → Suggest alternatives
```

### Recovery Mechanisms
```
1. Graph corruption
   → Automatic backup detection
   → Rollback option
   → Repair tools

2. Missing dependencies
   → Interactive resolution
   → Batch fix options
   → Validation after fix
```

## Performance Optimizations

### Caching Strategies
```
1. Entity resolution cache
   - Cache resolved references
   - Invalidate on graph change

2. Dependency cache
   - Cache traversal results
   - Update incrementally

3. Completeness cache
   - Store calculated scores
   - Recalculate on entity change
```

### Query Optimizations
```
1. Use jq streaming for large graphs
2. Parallelize independent queries
3. Early termination for depth searches
4. Index frequently accessed paths
```

## Integration Points

### External Scripts
```
know → mod-graph.sh
    → query-graph.sh
    → validate-spec-graph.sh
    → gap-analysis.sh
    → generators/*.sh
```

### Environment Variables
```
KNOWLEDGE_MAP → Graph file location
PROJECT_ROOT → Project base directory
LIB_DIR → Library scripts
DEBUG → Enable debug output
```

### File System Operations
```
1. Read operations
   - Load knowledge map (JSON)
   - Read templates
   - Load dependency rules

2. Write operations
   - Update knowledge map
   - Create backups
   - Generate output files
```

## Command Composition

Commands can be composed for complex workflows:

```bash
# Full implementation workflow
know gaps $entity | know complete $entity | know validate $entity

# Batch processing
for entity in $(know list features); do
    know validate feature:$entity
done

# Pipeline analysis
know deps $entity | know impact | know priorities
```

## Debug Tracing

Enable debug mode: `DEBUG=true know [command]`

Debug output includes:
- Function entry/exit
- Variable values
- jq queries executed
- File operations
- Validation results

## Common Execution Paths

### Most Frequent Paths
1. List → Search → Check → Generate
2. Gaps → Complete → Validate → Generate
3. Health → Repair → Validate
4. Dependencies → Impact → Priorities

### Critical Paths
1. Graph modification (requires validation)
2. Entity generation (requires 70% completeness)
3. Repair operations (requires backup)
4. Batch operations (requires transaction support)