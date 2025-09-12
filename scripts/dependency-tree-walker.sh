#!/bin/bash

# Walk dependency trees and show detailed paths from any entity
# Usage: ./scripts/dependency-tree-walker.sh [knowledge-map.json] [entity] [direction] [max-depth]
# Direction: down (dependencies), up (dependents), both
# Max-depth: maximum levels to traverse (default: 10)

# Help function
show_help() {
    cat << 'EOF'
🌳 Dependency Tree Walker - Interactive Tree Navigation

USAGE:
    ./scripts/dependency-tree-walker.sh [knowledge-map.json] [entity] [direction] [max-depth]
    ./scripts/dependency-tree-walker.sh -h|--help

DESCRIPTION:
    Walks dependency trees and shows detailed paths from any entity:
    • Interactive tree exploration with multiple directions
    • Circular dependency detection and visualization
    • Path finding between entities
    • Leaf node path analysis
    • Comprehensive tree statistics
    • ASCII tree visualization with depth control

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)
    entity               Starting entity for tree walk (interactive if not provided)
    direction            Walk direction (default: down)
    max-depth            Maximum levels to traverse (default: 10)

DIRECTIONS:
    down     - Show what entity depends on (dependencies)
    up       - Show what depends on entity (dependents)
    both     - Show both dependency and dependent trees
    leaves   - Show all paths from entity to leaf nodes

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/dependency-tree-walker.sh                                    # Interactive mode
    ./scripts/dependency-tree-walker.sh knowledge-map.json                # Interactive with file
    ./scripts/dependency-tree-walker.sh knowledge-map.json MyEntity       # Walk down from MyEntity
    ./scripts/dependency-tree-walker.sh knowledge-map.json MyEntity up    # Walk up from MyEntity
    ./scripts/dependency-tree-walker.sh knowledge-map.json MyEntity both 5 # Both directions, max 5 levels

INTERACTIVE FEATURES:
    • Entity selection from available entities
    • Direction choice with clear explanations
    • Path finding between two specific entities
    • Configurable depth limits
    • Tree analysis summaries and statistics

OUTPUT:
    ASCII tree visualization with circular dependency detection and detailed analysis
EOF
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-knowledge-map-cmd.json}"
ENTITY="$2"
DIRECTION="${3:-down}"
MAX_DEPTH="${4:-10}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    exit 1
fi

echo "🌳 DEPENDENCY TREE WALKER: $KNOWLEDGE_MAP"
[[ -n "$ENTITY" ]] && echo "🎯 Starting entity: $ENTITY"
echo "📍 Direction: $DIRECTION"
echo "📏 Max depth: $MAX_DEPTH"
echo "=" | tr '=' '=' | head -c 60
echo

# Function to walk down the dependency tree (what this entity depends on)
walk_dependencies_down() {
    local entity="$1"
    local max_depth="$2"
    
    jq -r --arg entity "$entity" --argjson max_depth "$max_depth" '
    def walk_down($node; $depth; $max_depth; $prefix; $visited; $path):
        if ($depth > $max_depth) then
            $prefix + "⚠️  ... (max depth " + ($max_depth | tostring) + " reached)"
        elif ($visited | index($node)) then
            $prefix + "🔄 " + $node + " (circular - see above)"
        else
            $prefix + "📦 " + $node + 
            (if ($path | index($node)) then " 🔄" else "" end) +
            "\n" +
            ((.graph[$node].depends_on // []) as $deps |
             if ($deps | length) == 0 then ""
             else
                 (range(0; $deps | length) as $i |
                  ($deps[$i]) as $dep |
                  ($prefix + (if $i == (($deps | length) - 1) then "└── " else "├── ")) as $new_prefix |
                  walk_down($dep; $depth + 1; $max_depth; $new_prefix; $visited + [$node]; $path + [$node])
                 ) | join("")
             end)
        end;
    
    if (.graph | has($entity)) then
        walk_down($entity; 0; $max_depth; ""; []; [])
    else
        "❌ Entity not found: " + $entity
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to walk up the dependency tree (what depends on this entity)
walk_dependencies_up() {
    local entity="$1"
    local max_depth="$2"
    
    jq -r --arg entity "$entity" --argjson max_depth "$max_depth" '
    def walk_up($node; $depth; $max_depth; $prefix; $visited; $path):
        if ($depth > $max_depth) then
            $prefix + "⚠️  ... (max depth " + ($max_depth | tostring) + " reached)"
        elif ($visited | index($node)) then
            $prefix + "🔄 " + $node + " (circular - see above)"
        else
            $prefix + "📦 " + $node + 
            (if ($path | index($node)) then " 🔄" else "" end) +
            "\n" +
            ([.graph | to_entries[] | 
              select(.value.depends_on // [] | index($node)) | .key] as $dependents |
             if ($dependents | length) == 0 then ""
             else
                 (range(0; $dependents | length) as $i |
                  ($dependents[$i]) as $dependent |
                  ($prefix + (if $i == (($dependents | length) - 1) then "└── " else "├── ")) as $new_prefix |
                  walk_up($dependent; $depth + 1; $max_depth; $new_prefix; $visited + [$node]; $path + [$node])
                 ) | join("")
             end)
        end;
    
    if (.graph | has($entity)) then
        walk_up($entity; 0; $max_depth; ""; []; [])
    else
        "❌ Entity not found: " + $entity
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to show all paths between two entities
show_all_paths() {
    local from="$1"
    local to="$2"
    local max_depth="${3:-5}"
    
    jq -r --arg from "$from" --arg to "$to" --argjson max_depth "$max_depth" '
    def find_all_paths($current; $target; $path; $max_depth):
        if ($path | length) > $max_depth then []
        elif ($current == $target) then [($path + [$current])]
        elif ($path | index($current)) then []
        else
            (.graph[$current].depends_on // []) as $deps |
            [$deps[] | find_all_paths(.; $target; $path + [$current]; $max_depth)] | 
            flatten(1)
        end;
    
    find_all_paths($from; $to; []; $max_depth) as $all_paths |
    
    if ($all_paths | length) == 0 then
        "❌ No paths found from " + $from + " to " + $to + " (within " + ($max_depth | tostring) + " levels)"
    else
        "🛤️  Found " + ($all_paths | length | tostring) + " path(s) from " + $from + " to " + $to + ":\n\n" +
        (($all_paths | to_entries[] |
          ((.key + 1) | tostring) + ". " + (.value | join(" → "))) | join("\n"))
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to find all leaf nodes (entities with no dependencies)
show_leaf_paths() {
    local entity="$1"
    local max_depth="$2"
    
    jq -r --arg entity "$entity" --argjson max_depth "$max_depth" '
    def find_leaf_paths($current; $path; $max_depth):
        if ($path | length) > $max_depth then []
        elif ($path | index($current)) then []
        else
            (.graph[$current].depends_on // []) as $deps |
            if ($deps | length) == 0 then [($path + [$current])]
            else
                [$deps[] | find_leaf_paths(.; $path + [$current]; $max_depth)] | 
                flatten(1)
            end
        end;
    
    if (.graph | has($entity)) then
        find_leaf_paths($entity; []; $max_depth) as $leaf_paths |
        
        if ($leaf_paths | length) == 0 then
            "❌ No leaf paths found from " + $entity + " (within " + ($max_depth | tostring) + " levels)"
        else
            "🍃 Found " + ($leaf_paths | length | tostring) + " path(s) to leaf nodes from " + $entity + ":\n\n" +
            (($leaf_paths | to_entries[] |
              ((.key + 1) | tostring) + ". " + (.value | join(" → "))) | join("\n"))
        end
    else
        "❌ Entity not found: " + $entity
    end
    ' "$KNOWLEDGE_MAP"
}

# Main execution logic
if [[ -n "$ENTITY" ]]; then
    # Specific entity provided
    case "$DIRECTION" in
        "down")
            echo "🔽 DEPENDENCY TREE (what $ENTITY depends on):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_down "$ENTITY" "$MAX_DEPTH"
            ;;
            
        "up")
            echo "🔼 DEPENDENT TREE (what depends on $ENTITY):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_up "$ENTITY" "$MAX_DEPTH"
            ;;
            
        "both")
            echo "🔽 DEPENDENCY TREE (what $ENTITY depends on):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_down "$ENTITY" "$MAX_DEPTH"
            echo
            echo "🔼 DEPENDENT TREE (what depends on $ENTITY):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_up "$ENTITY" "$MAX_DEPTH"
            ;;
            
        "leaves")
            echo "🍃 PATHS TO LEAF NODES from $ENTITY:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            show_leaf_paths "$ENTITY" "$MAX_DEPTH"
            ;;
            
        *)
            echo "❌ Invalid direction: $DIRECTION"
            echo "Valid directions: down, up, both, leaves"
            exit 1
            ;;
    esac
else
    # Interactive mode
    echo "🎯 Interactive mode - choose operation:"
    echo
    
    # Show available entities
    ENTITIES=$(jq -r '.graph | keys[]' "$KNOWLEDGE_MAP")
    ENTITY_COUNT=$(echo "$ENTITIES" | wc -l | tr -d ' ')
    
    echo "📦 Available entities ($ENTITY_COUNT total):"
    echo "$ENTITIES" | head -10 | while read -r entity; do
        echo "   - $entity"
    done
    
    if [[ $ENTITY_COUNT -gt 10 ]]; then
        echo "   ... and $((ENTITY_COUNT - 10)) more"
        echo
        echo "💡 Use: $0 $KNOWLEDGE_MAP <entity> <direction> [max-depth]"
        echo "   Directions: down, up, both, leaves"
        echo "   Example: $0 $KNOWLEDGE_MAP user.service down 5"
        exit 0
    fi
    
    echo
    printf "Enter entity name: "
    read -r selected_entity
    
    if [[ -z "$selected_entity" ]]; then
        echo "❌ No entity specified"
        exit 1
    fi
    
    echo "📍 Choose direction:"
    echo "   1. down - Show what $selected_entity depends on"
    echo "   2. up - Show what depends on $selected_entity"
    echo "   3. both - Show both directions"
    echo "   4. leaves - Show paths to leaf nodes"
    echo "   5. paths - Find paths between two entities"
    
    printf "Select (1-5): "
    read -r dir_choice
    
    case "$dir_choice" in
        "1") DIRECTION="down" ;;
        "2") DIRECTION="up" ;;
        "3") DIRECTION="both" ;;
        "4") DIRECTION="leaves" ;;
        "5") 
            printf "Target entity: "
            read -r target_entity
            echo "🛤️  PATHS from $selected_entity to $target_entity:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            show_all_paths "$selected_entity" "$target_entity" "$MAX_DEPTH"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice"
            exit 1
            ;;
    esac
    
    printf "Max depth (default $MAX_DEPTH): "
    read -r user_depth
    MAX_DEPTH=${user_depth:-$MAX_DEPTH}
    
    echo
    case "$DIRECTION" in
        "down")
            echo "🔽 DEPENDENCY TREE (what $selected_entity depends on):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_down "$selected_entity" "$MAX_DEPTH"
            ;;
        "up")
            echo "🔼 DEPENDENT TREE (what depends on $selected_entity):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_up "$selected_entity" "$MAX_DEPTH"
            ;;
        "both")
            echo "🔽 DEPENDENCY TREE (what $selected_entity depends on):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_down "$selected_entity" "$MAX_DEPTH"
            echo
            echo "🔼 DEPENDENT TREE (what depends on $selected_entity):"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            walk_dependencies_up "$selected_entity" "$MAX_DEPTH"
            ;;
        "leaves")
            echo "🍃 PATHS TO LEAF NODES from $selected_entity:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            show_leaf_paths "$selected_entity" "$MAX_DEPTH"
            ;;
    esac
fi

echo
echo "🔧 TREE ANALYSIS SUMMARY:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -n "$ENTITY" ]]; then
    jq -r --arg entity "$ENTITY" '
    def count_dependencies($node; $visited):
        if ($visited | index($node)) then 0
        else
            (.graph[$node].depends_on // []) as $deps |
            ($deps | length) + ([$deps[] | count_dependencies(.; $visited + [$node])] | add // 0)
        end;
    
    def count_dependents($node; $visited):
        if ($visited | index($node)) then 0
        else
            ([.graph | to_entries[] | 
              select(.value.depends_on // [] | index($node)) | .key]) as $deps |
            ($deps | length) + ([$deps[] | count_dependents(.; $visited + [$node])] | add // 0)
        end;
    
    def max_depth($node; $visited):
        if ($visited | index($node)) then 0
        else
            (.graph[$node].depends_on // []) as $deps |
            if ($deps | length) == 0 then 0
            else
                [$deps[] | max_depth(.; $visited + [$node])] | (max // 0) + 1
            end
        end;
    
    if (.graph | has($entity)) then
        {
            direct_dependencies: (.graph[$entity].depends_on // [] | length),
            total_dependencies: count_dependencies($entity; []),
            direct_dependents: ([.graph | to_entries[] | 
                               select(.value.depends_on // [] | index($entity)) | .key] | length),
            total_dependents: count_dependents($entity; []),
            max_dependency_depth: max_depth($entity; [])
        } |
        
        "📊 " + $entity + " analysis:" + "\n" +
        "   Direct dependencies: " + (.direct_dependencies | tostring) + "\n" +
        "   Total dependencies (transitive): " + (.total_dependencies | tostring) + "\n" +
        "   Direct dependents: " + (.direct_dependents | tostring) + "\n" +
        "   Total dependents (transitive): " + (.total_dependents | tostring) + "\n" +
        "   Maximum dependency depth: " + (.max_dependency_depth | tostring) + " levels"
    else
        "❌ Entity analysis not available - entity not found"
    end
    ' "$KNOWLEDGE_MAP"
else
    echo "💡 Run with entity name for detailed analysis"
fi

echo
echo "🔍 Legend:"
echo "   📦 Entity"
echo "   ├── Has more dependencies below"
echo "   └── Last dependency at this level"
echo "   🔄 Circular dependency detected"
echo "   ⚠️  Maximum depth reached (use higher --max-depth)"

echo