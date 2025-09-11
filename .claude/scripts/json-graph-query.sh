#!/bin/bash

# JSON Graph Query Tool - Demonstrates graph database queries on pure JSON
set -e

GRAPH_FILE="json-graph-example.json"

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
    echo "  traverse <entity_id> <relationship>    - Follow relationships from entity"  
    echo "  reverse <entity_id> <relationship>     - Find entities that relate TO this entity"
    echo "  path <from_entity> <to_entity>         - Find connection path between entities"
    echo "  deps <entity_id>                       - Show dependency chain"
    echo "  impact <entity_id>                     - Show impact analysis (what depends on this)"
    echo "  user <user_id>                         - Show all entities accessible to user"
    echo "  cycles                                 - Detect circular dependencies"
    echo "  stats                                  - Show graph statistics"
    echo "  view <view_name>                       - Show pre-computed view"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 traverse screen:dashboard contains"
    echo "  $0 reverse component:fleet-map contained_by"
    echo "  $0 path screen:dashboard model:robot"
    echo "  $0 deps feature:real-time-status"
    echo "  $0 impact model:robot"
    echo "  $0 user user:owner"
    echo "  $0 view user_owner_context"
}

traverse() {
    local entity="$1"
    local relationship="$2"
    
    echo "🔍 Following '$relationship' from '$entity':"
    jq -r --arg entity "$entity" --arg rel "$relationship" '
        .graph[$entity].outbound[$rel][]? // empty
    ' "$GRAPH_FILE" | while read -r target; do
        if [[ -n "$target" ]]; then
            name=$(jq -r --arg target "$target" '.entities[$target].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg target "$target" '.entities[$target].type // "unknown"' "$GRAPH_FILE")
            echo "  → $target ($type: $name)"
        fi
    done
}

reverse() {
    local entity="$1"
    local relationship="$2"
    
    echo "🔄 Finding entities with '$relationship' TO '$entity':"
    jq -r --arg entity "$entity" --arg rel "$relationship" '
        .graph | to_entries[] | 
        select(.value.outbound[$rel][]? == $entity) | 
        .key
    ' "$GRAPH_FILE" | while read -r source; do
        if [[ -n "$source" ]]; then
            name=$(jq -r --arg source "$source" '.entities[$source].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg source "$source" '.entities[$source].type // "unknown"' "$GRAPH_FILE")
            echo "  ← $source ($type: $name)"
        fi
    done
}

find_path() {
    local from="$1"
    local to="$2"
    
    echo "🛤️  Finding path from '$from' to '$to':"
    
    # Simple BFS path finding using jq
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
                        (.graph[$current].outbound // {} | to_entries[] | .value[]) as $neighbors |
                        $neighbors[] as $neighbor |
                        bfs(
                            $rest_queue + [$neighbor]; 
                            $visited + {($current): true}; 
                            $paths + {($neighbor): ($current_path + [$current])}
                        )
                    end
                end
            end;
        
        bfs([$from]; {}; {($from): []}) | .[0:3] | join(" → ")
    ' "$GRAPH_FILE"
}

show_dependencies() {
    local entity="$1"
    
    echo "📦 Dependency chain for '$entity':"
    jq -r --arg entity "$entity" '
        def find_deps($e; $visited):
            if $visited | has($e) then empty
            else
                $e,
                ((.graph[$e].outbound.depends_on[]? // empty) as $dep | 
                 find_deps($dep; $visited + {($e): true}))
            end;
        
        find_deps($entity; {})
    ' "$GRAPH_FILE" | while read -r dep; do
        if [[ -n "$dep" ]]; then
            name=$(jq -r --arg dep "$dep" '.entities[$dep].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg dep "$dep" '.entities[$dep].type // "unknown"' "$GRAPH_FILE")
            if [[ "$dep" == "$entity" ]]; then
                echo "  🎯 $dep ($type: $name) [ROOT]"
            else
                echo "  📋 $dep ($type: $name)"
            fi
        fi
    done
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
                  select(.value.outbound | to_entries[] | .value[] == $e) | .key) as $dependent |
                 find_impact($dependent; $visited + {($e): true}))
            end;
        
        find_impact($entity; {}) | select(. != $entity)
    ' "$GRAPH_FILE" | sort -u | while read -r impact; do
        if [[ -n "$impact" ]]; then
            name=$(jq -r --arg impact "$impact" '.entities[$impact].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg impact "$impact" '.entities[$impact].type // "unknown"' "$GRAPH_FILE")
            echo "  ⚡ $impact ($type: $name)"
        fi
    done
}

show_user_access() {
    local user="$1"
    
    echo "👤 Entities accessible to '$user':"
    jq -r --arg user "$user" '
        .graph | to_entries[] | 
        select(.value.inbound.accessed_by[]? == $user) | 
        .key
    ' "$GRAPH_FILE" | while read -r accessible; do
        if [[ -n "$accessible" ]]; then
            name=$(jq -r --arg accessible "$accessible" '.entities[$accessible].name // "Unknown"' "$GRAPH_FILE")
            type=$(jq -r --arg accessible "$accessible" '.entities[$accessible].type // "unknown"' "$GRAPH_FILE")
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
                (.graph[$current].outbound.depends_on[]? // empty) as $next |
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
    
    total_entities=$(jq '.entities | length' "$GRAPH_FILE")
    echo "  📦 Total entities: $total_entities"
    
    echo "  📋 By type:"
    jq -r '.indexes.by_type | to_entries[] | "    \(.key): \(.value | length)"' "$GRAPH_FILE"
    
    total_relationships=$(jq '.graph | to_entries[] | .value.outbound | to_entries[] | .value | length' "$GRAPH_FILE" | paste -sd+ | bc)
    echo "  🔗 Total relationships: $total_relationships"
    
    echo "  📊 Most connected entities:"
    jq -r '
        .graph | to_entries[] | 
        {
            entity: .key, 
            connections: ((.value.outbound | to_entries[] | .value | length) + (.value.inbound | to_entries[] | .value | length))
        } | 
        select(.connections > 0)
    ' "$GRAPH_FILE" | jq -s 'sort_by(.connections) | reverse | .[0:3][] | "    \(.entity): \(.connections) connections"'
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