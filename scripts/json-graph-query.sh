#!/bin/bash

# JSON Graph Query Tool - Demonstrates graph database queries on pure JSON
set -e

GRAPH_FILE="knowledge-map-cmd.json"

if [[ ! -f "$GRAPH_FILE" ]]; then
    echo "❌ Graph file not found: $GRAPH_FILE"
    exit 1
fi

show_help() {
    echo "JSON Graph Query Tool"
    echo ""
    echo "USAGE:"
    echo "  $0 <command> [options]"
    echo ""
    echo "COMMANDS:"
    echo "  traverse <entity_id> depends_on        - Show dependencies of entity"  
    echo "  reverse <entity_id> depends_on         - Find entities that depend on this entity"
    echo "  path <from_entity> <to_entity>         - Find dependency path between entities"
    echo "  deps <entity_id>                       - Show dependency chain"
    echo "  impact <entity_id>                     - Show impact analysis (what depends on this)"
    echo "  user <user_id>                         - Show dependencies for user"
    echo "  cycles                                 - Detect circular dependencies"
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
                name=$(jq -r --arg type "$target_type" --arg id "$target_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
                type=$(jq -r --arg type "$target_type" --arg id "$target_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
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
                name=$(jq -r --arg type "$source_type" --arg id "$source_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
                type=$(jq -r --arg type "$source_type" --arg id "$source_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
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
    
    # Simple BFS path finding using jq with depends_on relationships
    jq -r --arg from "$from" --arg to "$to" '
        def bfs($queue; $visited; $paths):
            if ($queue | length) == 0 then empty
            else 
                $queue[0] as $current |
                $queue[1:] as $rest_queue |
                $paths[$current] as $current_path |
                if $current == $to then 
                    $current_path + [$current]
                else
                    if $visited | has($current) then
                        bfs($rest_queue; $visited; $paths)
                    else
                        (.graph[$current].depends_on // []) as $neighbors |
                        $neighbors[] as $neighbor |
                        bfs(
                            $rest_queue + [$neighbor]; 
                            $visited + {($current): true}; 
                            $paths + {($neighbor): ($current_path + [$current])}
                        )
                    end
                end
            end;
        
        bfs([$from]; {}; {($from): []}) | .[0:5] | join(" → ")
    ' "$GRAPH_FILE"
}

show_dependencies() {
    local entity="$1"
    
    echo "📦 Dependency chain for '$entity':"
    
    # Simple approach: just get direct dependencies, limit output to prevent cycles
    local deps_found=()
    local depth=0
    
    _get_direct_deps() {
        local current_entity="$1"
        local current_depth="$2"
        
        # Depth limit to prevent infinite recursion
        if [[ $current_depth -gt 5 ]]; then
            echo "  ⚠️  MAX DEPTH REACHED (stopping at depth 5)"
            return
        fi
        
        # Check if already processed
        for found in "${deps_found[@]}"; do
            if [[ "$found" == "$current_entity" ]]; then
                echo "  🔄 CYCLE: $current_entity (already visited)"
                return
            fi
        done
        
        # Add to found list
        deps_found+=("$current_entity")
        
        # Display current entity
        local dep_type=$(echo "$current_entity" | cut -d':' -f1)
        local dep_id=$(echo "$current_entity" | cut -d':' -f2)
        local name=$(jq -r --arg type "$dep_type" --arg id "$dep_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE" 2>/dev/null || echo "Unknown")
        local type=$(jq -r --arg type "$dep_type" --arg id "$dep_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE" 2>/dev/null || echo "unknown")
        
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
    jq -r --arg entity "$entity" '
        def find_impact($e; $visited):
            if $visited | has($e) then empty
            else
                $e,
                ((.graph | to_entries[] | 
                  select(.value.depends_on[]? == $e) | .key) as $dependent |
                 find_impact($dependent; $visited + {($e): true}))
            end;
        
        find_impact($entity; {}) | select(. != $entity)
    ' "$GRAPH_FILE" | sort -u | while read -r impact; do
        if [[ -n "$impact" ]]; then
            # Parse impact type:id format
            impact_type=$(echo "$impact" | cut -d':' -f1)
            impact_id=$(echo "$impact" | cut -d':' -f2)
            name=$(jq -r --arg type "$impact_type" --arg id "$impact_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg type "$impact_type" --arg id "$impact_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
            echo "  ⚡ $impact ($type: $name)"
        fi
    done
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
            name=$(jq -r --arg type "$accessible_type" --arg id "$accessible_id" '.entities[$type][$id].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg type "$accessible_type" --arg id "$accessible_id" '.entities[$type][$id].type // "unknown"' "$GRAPH_FILE")
            echo "  ✅ $accessible ($type: $name)"
        fi
    done
}

detect_cycles() {
    echo "🔄 Checking for circular dependencies..."
    
    cycles=$(jq -r '
        def has_cycle($start; $current; $visited):
            if $visited | has($current) then
                if $current == $start then true else false end
            else
                (.graph[$current].depends_on[]? // empty) as $next |
                has_cycle($start; $next; $visited + {($current): true})
            end;
        
        .graph | keys[] as $entity |
        select(has_cycle($entity; $entity; {})) |
        $entity
    ' "$GRAPH_FILE")
    
    if [[ -n "$cycles" ]]; then
        echo "  ⚠️  Circular dependencies found:"
        echo "$cycles" | while read -r cycle; do
            if [[ -n "$cycle" ]]; then
                echo "    🔁 $cycle"
            fi
        done
    else
        echo "  ✅ No circular dependencies detected"
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
        if [[ $# -ne 2 ]]; then
            echo "Usage: $0 deps <entity_id>"
            exit 1
        fi
        show_dependencies "$2"
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