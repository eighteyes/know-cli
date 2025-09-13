#!/bin/bash

# JSON Graph Query Tool - Demonstrates graph database queries on pure JSON
set -e

GRAPH_FILE="spec-graph.json"

# Convert singular entity type to plural for lookup
get_plural_type() {
    local entity_type="$1"
    case "$entity_type" in
        "functionality") echo "functionality" ;;
        *) echo "${entity_type}s" ;;
    esac
}

show_help() {
    echo "JSON Graph Query Tool"
    echo ""
    echo "USAGE:"
    echo "  $0 [--file|-f <graph-file>] <command> [options]"
    echo ""
    echo "OPTIONS:"
    echo "  --file, -f <file>    Use specified graph file (default: spec-graph.json)"
    echo ""
    echo "COMMANDS:"
    echo "  traverse <entity_id> depends_on        - Show dependencies of entity"  
    echo "  reverse <entity_id> depends_on         - Find entities that depend on this entity"
    echo "  path <from_entity> <to_entity>         - Find dependency path between entities"
    echo "  deps <entity_id>                       - Show dependency chain"
    echo "  impact <entity_id>                     - Show impact analysis (what depends on this)"
    echo "  user <user_id>                         - Show dependencies for user"
    echo "  cycles                                 - Detect circular dependencies"
    echo "  scan-all                               - Comprehensive scan of ALL entities for cycles"
    echo "  stats                                  - Show graph statistics"
    echo "  view <view_name>                       - Show pre-computed view"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 traverse user:owner depends_on"
    echo "  $0 reverse platform:aws-infrastructure depends_on"
    echo "  $0 path user:owner platform:aws-infrastructure"
    echo "  $0 deps feature:real-time-telemetry"
    echo "  $0 impact platform:aws-infrastructure"
    echo "  $0 user user:owner"
    echo "  $0 view dependency_chains"
}

traverse() {
    local entity="$1"
    local relationship="$2"
    
    if [[ "$relationship" == "depends_on" ]]; then
        echo "🔍 Dependencies of '$entity':"
        jq -r --arg entity "$entity" '
            .graph[$entity].depends_on[]? // empty
        ' "$GRAPH_FILE" | while read -r target; do
            if [[ -n "$target" ]]; then
                # Parse target type:id format
                target_type=$(echo "$target" | cut -d':' -f1)
                target_id=$(echo "$target" | cut -d':' -f2)
                # Convert singular to plural for entity lookup
                plural_type=$(get_plural_type "$target_type")
                name=$(jq -r --arg type "$plural_type" --arg id "$target_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
                type=$(jq -r --arg type "$plural_type" --arg id "$target_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
                echo "  → $target ($type: $name)"
            fi
        done
    else
        echo "❌ Only 'depends_on' relationship is supported in current graph format"
        echo "   Available relationship: depends_on"
    fi
}

reverse() {
    local entity="$1"
    local relationship="$2"
    
    if [[ "$relationship" == "depends_on" ]]; then
        echo "🔄 Entities that depend on '$entity':"
        jq -r --arg entity "$entity" '
            .graph | to_entries[] | 
            select(.value.depends_on[]? == $entity) | 
            .key
        ' "$GRAPH_FILE" | while read -r source; do
            if [[ -n "$source" ]]; then
                # Parse source type:id format
                source_type=$(echo "$source" | cut -d':' -f1)
                source_id=$(echo "$source" | cut -d':' -f2)
                # Convert singular to plural for entity lookup
                plural_type=$(get_plural_type "$source_type")
                name=$(jq -r --arg type "$plural_type" --arg id "$source_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
                type=$(jq -r --arg type "$plural_type" --arg id "$source_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
                echo "  ← $source ($type: $name)"
            fi
        done
    else
        echo "❌ Only 'depends_on' relationship is supported in current graph format"
        echo "   Available relationship: depends_on"
    fi
}

find_path() {
    local from="$1"
    local to="$2"
    
    echo "🛤️  Finding dependency path from '$from' to '$to':"
    
    # Find shortest path using BFS, return only first result
    local result
    result=$(jq -r --arg from "$from" --arg to "$to" '
        def find_shortest_path($start; $target; $visited; $path; $depth):
            if $depth > 8 then 
                empty
            elif $start == $target then 
                $path + [$start] | join(" → ")
            elif ($visited | has($start)) then 
                empty
            else
                (.graph[$start].depends_on // [])[] as $next |
                find_shortest_path($next; $target; $visited + {($start): true}; $path + [$start]; $depth + 1)
            end;
        
        first(find_shortest_path($from; $to; {}; []; 0))
    ' "$GRAPH_FILE" 2>/dev/null)
    
    if [[ -z "$result" || "$result" == "null" ]]; then
        echo "  ❌ No path found from '$from' to '$to'"
    else
        echo "  📍 $result"
    fi
}

show_dependencies() {
    local entity="$1"
    local auto_resolve="${2:-false}"
    
    echo "📦 Dependency chain for '$entity':"
    
    # Simple approach: just get direct dependencies, limit output to prevent cycles
    local deps_found=()
    local depth=0
    
    _get_direct_deps() {
        local current_entity="$1"
        local current_depth="$2"
        
        # Depth limit to prevent infinite recursion
        if [[ $current_depth -gt 3 ]]; then
            echo "  ⚠️  MAX DEPTH REACHED (stopping at depth 3)"
            return
        fi
        
        # Check if already processed
        for found in "${deps_found[@]}"; do
            if [[ "$found" == "$current_entity" ]]; then
                echo "  🔄 CYCLE DETECTED: $current_entity (already visited)"
                if [[ "$auto_resolve" == "true" ]]; then
                    echo "  🔧 Auto-resolving circular dependencies..."
                    ./know/know mod resolve-cycles
                    echo "  ✅ Circular dependencies resolved. Re-run query to see clean results."
                    exit 0
                else
                    echo "  💡 Run './know/know query deps $current_entity --resolve' to auto-fix cycles"
                fi
                return
            fi
        done
        
        # Add to found list
        deps_found+=("$current_entity")
        
        # Display current entity
        local dep_type=$(echo "$current_entity" | cut -d':' -f1)
        local dep_id=$(echo "$current_entity" | cut -d':' -f2)
        # Convert singular to plural for entity lookup
        local plural_type=$(get_plural_type "$dep_type")
        local name=$(jq -r --arg type "$plural_type" --arg id "$dep_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE" 2>/dev/null || echo "Unknown")
        local type=$(jq -r --arg type "$plural_type" --arg id "$dep_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE" 2>/dev/null || echo "unknown")
        
        if [[ $current_depth -eq 0 ]]; then
            echo "  🎯 $current_entity ($type: $name) [ROOT]"
        else
            echo "  📋 $current_entity ($type: $name)"
        fi
        
        # Get direct dependencies
        local direct_deps
        direct_deps=$(jq -r --arg entity "$current_entity" '.graph[$entity].depends_on[]? // empty' "$GRAPH_FILE" 2>/dev/null)
        
        while IFS= read -r dep; do
            if [[ -n "$dep" ]]; then
                _get_direct_deps "$dep" $((current_depth + 1))
            fi
        done <<< "$direct_deps"
    }
    
    _get_direct_deps "$entity" 0
}

show_impact() {
    local entity="$1"
    
    echo "💥 Impact analysis for '$entity' (what depends on this):"
    
    # Find all entities that depend on the target entity (direct and indirect)
    local impacts_found=()
    local depth=0
    
    _get_impact_chain() {
        local target_entity="$1"
        local current_depth="$2"
        
        # Depth limit to prevent infinite recursion
        if [[ $current_depth -gt 3 ]]; then
            return
        fi
        
        # Find direct dependents
        local direct_dependents
        direct_dependents=$(jq -r --arg entity "$target_entity" '
            .graph | to_entries[] | 
            select(.value.depends_on[]? == $entity) | 
            .key
        ' "$GRAPH_FILE" 2>/dev/null)
        
        while IFS= read -r dependent; do
            if [[ -n "$dependent" ]]; then
                # Check if already processed
                local already_found=false
                for found in "${impacts_found[@]}"; do
                    if [[ "$found" == "$dependent" ]]; then
                        already_found=true
                        break
                    fi
                done
                
                if [[ "$already_found" == false ]]; then
                    impacts_found+=("$dependent")
                    
                    # Display this dependent
                    local dep_type=$(echo "$dependent" | cut -d':' -f1)
                    local dep_id=$(echo "$dependent" | cut -d':' -f2)
                    # Convert singular to plural for entity lookup
                    local plural_type=$(get_plural_type "$dep_type")
                    local name=$(jq -r --arg type "$plural_type" --arg id "$dep_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE" 2>/dev/null || echo "Unknown")
                    local type=$(jq -r --arg type "$plural_type" --arg id "$dep_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE" 2>/dev/null || echo "unknown")
                    
                    local indent=""
                    for ((i=0; i<current_depth; i++)); do
                        indent="  $indent"
                    done
                    
                    echo "  ${indent}⚡ $dependent ($type: $name)"
                    
                    # Recursively find what depends on this dependent
                    _get_impact_chain "$dependent" $((current_depth + 1))
                fi
            fi
        done <<< "$direct_dependents"
    }
    
    _get_impact_chain "$entity" 0
    
    if [[ ${#impacts_found[@]} -eq 0 ]]; then
        echo "  ℹ️  No entities depend on '$entity'"
    fi
}

show_user_access() {
    local user="$1"
    
    echo "👤 Dependencies for user '$user':"
    jq -r --arg user "$user" '
        .graph[$user].depends_on[]? // empty
    ' "$GRAPH_FILE" | while read -r accessible; do
        if [[ -n "$accessible" ]]; then
            # Parse accessible type:id format
            accessible_type=$(echo "$accessible" | cut -d':' -f1)
            accessible_id=$(echo "$accessible" | cut -d':' -f2)
            # Convert singular to plural for entity lookup
            plural_type=$(get_plural_type "$accessible_type")
            name=$(jq -r --arg type "$plural_type" --arg id "$accessible_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg type "$plural_type" --arg id "$accessible_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
            echo "  ✅ $accessible ($type: $name)"
        fi
    done
}

detect_cycles() {
    echo "🔄 Checking for circular dependencies..."
    
    # Enhanced cycle detection with path tracking
    cycles_with_paths=$(jq -r '
        def find_cycle_path($start; $current; $path; $visited):
            if $visited | has($current) then
                if $current == $start then
                    ($path + [$current] | join(" → "))
                else empty end
            else
                (.graph[$current].depends_on[]? // empty) as $next |
                if $next then
                    find_cycle_path($start; $next; $path + [$current]; $visited + {($current): true})
                else empty end
            end;
        
        .graph | keys[] as $entity |
        find_cycle_path($entity; $entity; []; {}) // empty
    ' "$GRAPH_FILE")
    
    if [[ -n "$cycles_with_paths" ]]; then
        echo "  ⚠️  Circular dependencies found:"
        echo "$cycles_with_paths" | sort -u | while IFS= read -r cycle_path; do
            if [[ -n "$cycle_path" ]]; then
                echo "    🔁 $cycle_path"
            fi
        done
        echo ""
        echo "  💡 Run './know/know mod resolve-cycles' to auto-fix all cycles"
    else
        echo "  ✅ No circular dependencies detected"
    fi
}

scan_all_cycles() {
    echo "🔍 Comprehensive scan: Testing ALL entities for cycles and hierarchy violations..."
    echo "📏 HOW: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models"
    echo "📏 WHAT: Project → User → Functionality → Implementation"
    echo "🔗 Integration: User → Requirements, Functionality → Features, Implementation → Action/Component"
    echo ""
    
    local total_entities=0
    local entities_with_cycles=0
    local hierarchy_violations=0
    local cycle_patterns=()
    local violation_patterns=()
    
    # Canonical hierarchy levels
    get_hierarchy_level() {
        local entity_type="$1"
        case "$entity_type" in
            "project") echo "1" ;;
            "platform") echo "2" ;;
            "requirement") echo "3" ;;
            "user") echo "35" ;;          # 3.5 - Parallel to requirements, feeds into interface
            "screen") echo "4" ;;         # Interface layer
            "interface") echo "4" ;;      # Interface layer (same as screen)
            "functionality") echo "45" ;; # 4.5 - Between interface and features
            "feature") echo "5" ;;
            "action") echo "6" ;;         # Actions come after features
            "component") echo "7" ;;
            "ui_component") echo "8" ;;
            "ui") echo "8" ;;             # Same as ui_component
            "model") echo "9" ;;          # Data models at the bottom
            "data_model") echo "9" ;;     # Same as model
            "implementation") echo "75" ;; # 7.5 - Between component and UI
            *) echo "999" ;;
        esac
    }
    
    # Get all entities from the graph
    local all_entities
    all_entities=$(jq -r '.graph | keys[]' "$GRAPH_FILE")
    
    while IFS= read -r entity; do
        if [[ -n "$entity" ]]; then
            ((total_entities++))
            
            # Check hierarchy violations
            local entity_type=$(echo "$entity" | cut -d':' -f1)
            local entity_level=$(get_hierarchy_level "$entity_type")
            
            # Check each dependency for hierarchy violations
            local direct_deps
            direct_deps=$(jq -r --arg entity "$entity" '.graph[$entity].depends_on[]? // empty' "$GRAPH_FILE" 2>/dev/null)
            
            while IFS= read -r dep; do
                if [[ -n "$dep" ]]; then
                    local dep_type=$(echo "$dep" | cut -d':' -f1)
                    local dep_level=$(get_hierarchy_level "$dep_type")
                    
                    # Check if dependency violates hierarchy (higher level depending on lower level)
                    if [[ $entity_level -lt $dep_level ]]; then
                        ((hierarchy_violations++))
                        violation_patterns+=("$entity → $dep (level $entity_level → $dep_level)")
                    fi
                fi
            done <<< "$direct_deps"
            
            # Test dependency traversal for cycles
            local cycle_detected=false
            local deps_found=()
            
            _scan_entity_cycles() {
                local current_entity="$1"
                local depth="$2"
                
                # Depth limit
                if [[ $depth -gt 5 ]]; then
                    return
                fi
                
                # Check if already visited
                for found in "${deps_found[@]}"; do
                    if [[ "$found" == "$current_entity" ]]; then
                        cycle_detected=true
                        cycle_patterns+=("$entity (contains cycle at depth $depth)")
                        return
                    fi
                done
                
                deps_found+=("$current_entity")
                
                # Get dependencies and recurse
                local direct_deps
                direct_deps=$(jq -r --arg entity "$current_entity" '.graph[$entity].depends_on[]? // empty' "$GRAPH_FILE" 2>/dev/null)
                
                while IFS= read -r dep; do
                    if [[ -n "$dep" ]]; then
                        _scan_entity_cycles "$dep" $((depth + 1))
                    fi
                done <<< "$direct_deps"
            }
            
            _scan_entity_cycles "$entity" 0
            
            if [[ "$cycle_detected" == "true" ]]; then
                ((entities_with_cycles++))
            fi
        fi
    done <<< "$all_entities"
    
    echo "📊 Comprehensive Scan Results:"
    echo "  📈 Total entities scanned: $total_entities"
    echo "  🔁 Entities with cycles: $entities_with_cycles"
    echo "  ⚠️  Hierarchy violations: $hierarchy_violations"
    
    if [[ $entities_with_cycles -gt 0 ]]; then
        echo ""
        echo "  🔴 Entities with circular dependency patterns:"
        for pattern in "${cycle_patterns[@]}"; do
            echo "    🔁 $pattern"
        done
    fi
    
    if [[ $hierarchy_violations -gt 0 ]]; then
        echo ""
        echo "  🔴 Canonical hierarchy violations:"
        for violation in "${violation_patterns[@]}"; do
            echo "    ⬆️  $violation"
        done
    fi
    
    if [[ $entities_with_cycles -gt 0 || $hierarchy_violations -gt 0 ]]; then
        echo ""
        echo "  💡 Run './know/know query cycles' for detailed cycle paths"
        echo "  🔧 Run './know/know mod resolve-cycles' to auto-fix all issues"
    else
        echo "  ✅ No cycles or hierarchy violations detected"
    fi
}

show_stats() {
    echo "📊 Graph Statistics:"
    
    echo "  📋 By entity type:"
    jq -r '.entities | to_entries[] | "    \(.key): \(.value | length)"' "$GRAPH_FILE"
    
    total_entities=$(jq '[.entities[] | length] | add' "$GRAPH_FILE")
    echo "  📦 Total entities: $total_entities"
    
    total_relationships=$(jq '[.graph[] | .depends_on | length] | add' "$GRAPH_FILE")
    echo "  🔗 Total dependencies: $total_relationships"
    
    echo "  📊 Most dependent entities:"
    jq -r '
        .graph | to_entries[] | 
        {
            entity: .key, 
            dependencies: (.value.depends_on | length)
        } | 
        select(.dependencies > 0)
    ' "$GRAPH_FILE" | jq -s -r 'sort_by(.dependencies) | reverse | .[0:5][] | "    \(.entity): \(.dependencies) deps"'
    
    echo "  🎯 Most depended-upon entities:"
    # Count dependencies for each entity
    jq -r '
        [.graph | to_entries[].value.depends_on // []] | 
        flatten | 
        group_by(.) | 
        map({entity: .[0], count: length}) | 
        sort_by(.count) | reverse | 
        .[0:5][] | 
        "    \(.entity): \(.count) dependents"
    ' "$GRAPH_FILE"
}

show_view() {
    local view_name="$1"
    
    echo "👁️  Pre-computed view: '$view_name'"
    jq -r --arg view "$view_name" '.views[$view]' "$GRAPH_FILE" | jq '.'
}

# Parse file option
while [[ $# -gt 0 ]]; do
    case $1 in
        --file|-f)
            GRAPH_FILE="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

# Check if file exists
if [[ ! -f "$GRAPH_FILE" ]]; then
    echo "❌ Graph file not found: $GRAPH_FILE"
    exit 1
fi

# Main command processing
case "$1" in
    "traverse")
        if [[ $# -ne 3 ]]; then
            echo "Usage: $0 traverse <entity_id> <relationship>"
            exit 1
        fi
        traverse "$2" "$3"
        ;;
    "reverse")
        if [[ $# -ne 3 ]]; then
            echo "Usage: $0 reverse <entity_id> <relationship>"
            exit 1
        fi
        reverse "$2" "$3"
        ;;
    "path")
        if [[ $# -ne 3 ]]; then
            echo "Usage: $0 path <from_entity> <to_entity>"
            exit 1
        fi
        find_path "$2" "$3"
        ;;
    "deps")
        if [[ $# -lt 2 ]]; then
            echo "Usage: $0 deps <entity_id> [--resolve]"
            exit 1
        fi
        auto_resolve="false"
        if [[ "${3:-}" == "--resolve" ]]; then
            auto_resolve="true"
        fi
        show_dependencies "$2" "$auto_resolve"
        ;;
    "impact")
        if [[ $# -ne 2 ]]; then
            echo "Usage: $0 impact <entity_id>"
            exit 1
        fi
        show_impact "$2"
        ;;
    "user")
        if [[ $# -ne 2 ]]; then
            echo "Usage: $0 user <user_id>"
            exit 1
        fi
        show_user_access "$2"
        ;;
    "cycles")
        detect_cycles
        ;;
    "scan-all")
        scan_all_cycles
        ;;
    "stats")
        show_stats
        ;;
    "view")
        if [[ $# -ne 2 ]]; then
            echo "Usage: $0 view <view_name>"
            exit 1
        fi
        show_view "$2"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac