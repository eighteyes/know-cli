#!/bin/bash

# Interactive dependency graph explorer with search and filtering
# Usage: ./scripts/dependency-explorer.sh [knowledge-map.json]

# Help function
show_help() {
    cat << 'EOF'
🔍 Dependency Explorer - Interactive Graph Navigation

USAGE:
    ./scripts/dependency-explorer.sh [knowledge-map.json]
    ./scripts/dependency-explorer.sh -h|--help

DESCRIPTION:
    Interactive CLI tool for exploring dependency graphs with fuzzy search

FEATURES:
    • Browse all entities with fuzzy search (fzf)
    • Show detailed entity information
    • Find dependency paths between entities
    • Explore entity neighborhoods
    • Search entities by pattern
    • Quick statistics and critical entity analysis
    • Detect circular dependencies
    • Complexity ranking

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: spec-graph.json)

OPTIONS:
    -h, --help           Show this help message

DEPENDENCIES:
    fzf                  Fuzzy finder (brew install fzf)

EXAMPLES:
    ./scripts/dependency-explorer.sh                          # Interactive mode
    ./scripts/dependency-explorer.sh my-knowledge-map.json    # Custom map file

INTERACTIVE MENU:
    1. Browse all entities    - Fuzzy search through entities
    2. Show entity details    - Detailed dependency information
    3. Find dependency path   - Path between two entities
    4. Explore neighborhood   - Show related entities
    5. Search entities        - Pattern-based search
    6. Quick stats           - Graph statistics
    7. Find critical entities - High-impact analysis
    8. Find circular deps    - Cycle detection
    9. Complexity ranking    - Sorted by complexity

OUTPUT:
    Interactive exploration with real-time search and navigation
EOF
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-spec-graph.json}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    echo "💡 Use -h for help"
    exit 1
fi

# Check for required tools
if ! command -v fzf &> /dev/null; then
    echo "❌ fzf not found. Install with:"
    echo "   macOS: brew install fzf"
    echo "   Ubuntu: sudo apt-get install fzf"
    echo "   Manual: https://github.com/junegunn/fzf#installation"
    exit 1
fi

echo "🔍 INTERACTIVE DEPENDENCY EXPLORER: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 60
echo

# Function to show entity details
show_entity_details() {
    local entity="$1"
    
    jq -r --arg entity "$entity" '
    if (.graph | has($entity)) then
        (.graph[$entity].depends_on // []) as $dependencies |
        ([.graph | .[] | .depends_on[]?] | map(select(. == $entity))) as $dependents |
        
        "📦 ENTITY: " + $entity + "\n" +
        "=" + ("=" * ($entity | length + 10)) + "\n" +
        "\n📤 DEPENDENCIES (" + ($dependencies | length | tostring) + "):\n" +
        (if ($dependencies | length) > 0 then
            ($dependencies[] | "  - " + .) | join("\n")
        else
            "  (no dependencies)"
        end) + 
        "\n\n📥 DEPENDENTS (" + ($dependents | length | tostring) + "):\n" +
        (if ($dependents | length) > 0 then
            ($dependents[] | "  - " + .) | join("\n")
        else
            "  (no dependents)"
        end) + "\n"
    else
        "❌ Entity not found: " + $entity
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to show dependency path
show_dependency_path() {
    local from="$1"
    local to="$2"
    
    jq -r --arg from "$from" --arg to "$to" '
    def find_path($current; $target; $path; $visited):
        if ($current == $target) then [$path + [$current]]
        elif ($visited | index($current)) then []
        else
            (.graph[$current].depends_on // []) as $deps |
            [$deps[] | find_path(.; $target; $path + [$current]; $visited + [$current])] | 
            flatten | 
            if length > 0 then . else [] end
        end;
    
    find_path($from; $to; []; []) as $paths |
    if ($paths | length) > 0 then
        "🛤️  Path from " + $from + " to " + $to + ":\n" +
        ($paths | join(" → "))
    else
        "❌ No path found from " + $from + " to " + $to
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to show entity neighborhood
show_neighborhood() {
    local entity="$1"
    local depth="${2:-2}"
    
    jq -r --arg entity "$entity" --argjson depth "$depth" '
    def get_neighbors($node; $current_depth; $max_depth; $visited):
        if ($current_depth > $max_depth or ($visited | index($node))) then []
        else
            [$node] + 
            ((.graph[$node].depends_on // [])[] | 
             get_neighbors(.; $current_depth + 1; $max_depth; $visited + [$node])) +
            ([.graph | to_entries[] | 
              select(.value.depends_on // [] | index($node)) | .key][] |
             get_neighbors(.; $current_depth + 1; $max_depth; $visited + [$node]))
        end;
    
    get_neighbors($entity; 0; $depth; []) | 
    unique | 
    sort[] |
    if . == $entity then "📦 " + . + " (center)"
    else "📦 " + .
    end
    ' "$KNOWLEDGE_MAP"
}

# Function to find entities matching pattern
find_entities() {
    local pattern="$1"
    
    jq -r --arg pattern "$pattern" '
    [.graph | keys[] | select(test($pattern; "i"))] |
    if length > 0 then
        "🔍 Entities matching \"" + $pattern + "\":\n" +
        (.[] | "  - " + .) | join("\n")
    else
        "❌ No entities found matching: " + $pattern
    end
    ' "$KNOWLEDGE_MAP"
}

# Main interactive loop
while true; do
    echo
    echo "🎛️  DEPENDENCY EXPLORER MENU"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. 🔍 Browse all entities"
    echo "2. 📦 Show entity details"
    echo "3. 🛤️  Find dependency path"
    echo "4. 🌐 Explore neighborhood"
    echo "5. 🔎 Search entities"
    echo "6. 📊 Quick stats"
    echo "7. 🚨 Find critical entities"
    echo "8. 🔄 Find circular dependencies"
    echo "9. 📈 Show complexity ranking"
    echo "q. ❌ Quit"
    echo

    printf "Select option: "
    read -r choice

    case "$choice" in
        "1")
            echo "🔍 All entities (use arrow keys, Enter to select, Esc to cancel):"
            SELECTED_ENTITY=$(jq -r '.graph | keys[]' "$KNOWLEDGE_MAP" | fzf --height 40% --preview "$(realpath "$0") show-details {} '$KNOWLEDGE_MAP'")
            
            if [[ -n "$SELECTED_ENTITY" ]]; then
                echo
                show_entity_details "$SELECTED_ENTITY"
                echo
                printf "Press Enter to continue..."
                read -r
            fi
            ;;
            
        "2")
            printf "Enter entity name: "
            read -r entity_name
            if [[ -n "$entity_name" ]]; then
                echo
                show_entity_details "$entity_name"
                echo
                printf "Press Enter to continue..."
                read -r
            fi
            ;;
            
        "3")
            printf "From entity: "
            read -r from_entity
            printf "To entity: "
            read -r to_entity
            
            if [[ -n "$from_entity" && -n "$to_entity" ]]; then
                echo
                show_dependency_path "$from_entity" "$to_entity"
                echo
                printf "Press Enter to continue..."
                read -r
            fi
            ;;
            
        "4")
            printf "Entity name: "
            read -r entity_name
            printf "Depth (default 2): "
            read -r depth
            depth=${depth:-2}
            
            if [[ -n "$entity_name" ]]; then
                echo
                echo "🌐 Neighborhood of $entity_name (depth $depth):"
                show_neighborhood "$entity_name" "$depth"
                echo
                printf "Press Enter to continue..."
                read -r
            fi
            ;;
            
        "5")
            printf "Search pattern (regex): "
            read -r pattern
            
            if [[ -n "$pattern" ]]; then
                echo
                find_entities "$pattern"
                echo
                printf "Press Enter to continue..."
                read -r
            fi
            ;;
            
        "6")
            echo
            jq -r '
            (.graph | keys | length) as $total_entities |
            [.graph | .[] | .depends_on[]?] as $all_deps |
            
            "📊 QUICK STATISTICS:\n" +
            "   Entities: " + ($total_entities | tostring) + "\n" +
            "   Dependencies: " + ($all_deps | length | tostring) + "\n" +
            "   Avg deps per entity: " + (($all_deps | length) / $total_entities | . * 100 | round / 100 | tostring) + "\n" +
            "   Root entities: " + (
                (.graph | keys) as $entities |
                [$entities[] as $entity | 
                 select($all_deps | index($entity) | not)] | length | tostring
            ) + "\n" +
            "   Leaf entities: " + (
                [.graph | .[] | select((.depends_on // []) | length == 0)] | length | tostring
            )
            ' "$KNOWLEDGE_MAP"
            echo
            printf "Press Enter to continue..."
            read -r
            ;;
            
        "7")
            echo
            echo "🚨 Critical entities (high impact):"
            jq -r '
            [.graph | .[] | .depends_on[]?] as $all_deps |
            (.graph | keys) as $entities |
            
            [$entities[] as $entity |
             {entity: $entity, dependents: ($all_deps | map(select(. == $entity)) | length)}] |
            sort_by(-.dependents) |
            .[0:10][] |
            select(.dependents > 0) |
            "  - " + .entity + " (" + (.dependents | tostring) + " dependents)"
            ' "$KNOWLEDGE_MAP"
            echo
            printf "Press Enter to continue..."
            read -r
            ;;
            
        "8")
            echo
            echo "🔄 Circular dependencies:"
            CIRCULAR=$(jq -r '
            .graph as $g |
            [$g | to_entries[] |
             .key as $entity |
             (.value.depends_on // [])[] as $dep |
             select($g[$dep].depends_on // [] | index($entity)) |
             if $entity < $dep then [$entity, $dep] else [$dep, $entity] end] |
            unique[] |
            join(" <-> ")
            ' "$KNOWLEDGE_MAP")
            
            if [[ -z "$CIRCULAR" ]]; then
                echo "   ✅ No circular dependencies found"
            else
                echo "$CIRCULAR" | while read -r cycle; do
                    echo "   - $cycle"
                done
            fi
            echo
            printf "Press Enter to continue..."
            read -r
            ;;
            
        "9")
            echo
            echo "📈 Complexity ranking (top 10):"
            jq -r '
            def max_depth($entity; $visited):
                if ($visited | index($entity)) then 0
                else
                    (.graph[$entity].depends_on // []) as $deps |
                    if ($deps | length) == 0 then 0
                    else
                        [$deps[] | max_depth(.; $visited + [$entity])] |
                        (max // 0) + 1
                    end
                end;

            [.graph | .[] | .depends_on[]?] as $all_deps |

            [.graph | keys[] as $entity |
             {
                 entity: $entity,
                 dependencies: (.graph[$entity].depends_on // [] | length),
                 dependents: ($all_deps | map(select(. == $entity)) | length),
                 depth: max_depth($entity; []),
                 score: ((.graph[$entity].depends_on // [] | length) * 2 + 
                        ($all_deps | map(select(. == $entity)) | length) * 1.5 + 
                        max_depth($entity; []) * 3)
             }] |

            sort_by(-.score) |
            .[0:10][] |
            "  " + (.score | . * 10 | round / 10 | tostring) + " - " + .entity + 
            " (deps:" + (.dependencies | tostring) + " dependents:" + (.dependents | tostring) + " depth:" + (.depth | tostring) + ")"
            ' "$KNOWLEDGE_MAP"
            echo
            printf "Press Enter to continue..."
            read -r
            ;;
            
        "q"|"Q"|"quit"|"exit")
            echo "👋 Goodbye!"
            exit 0
            ;;
            
        *)
            echo "❌ Invalid option. Please try again."
            ;;
    esac
done