#!/bin/bash

# Interactive tool to fix disconnected entities in dependency graph
# Usage: ./scripts/fix-disconnects.sh [knowledge-map.json]

KNOWLEDGE_MAP="${1:-knowledge-map-cmd.json}"
BACKUP_FILE="${KNOWLEDGE_MAP}.backup"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    exit 1
fi

# Create backup
cp "$KNOWLEDGE_MAP" "$BACKUP_FILE"
echo "💾 Backup created: $BACKUP_FILE"
echo

# Colors for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_menu() {
    echo -e "${CYAN}🔧 DEPENDENCY GRAPH REPAIR TOOL${NC}"
    echo "=================================="
    echo
    echo "What would you like to fix?"
    echo "1. 🔴 Fix hanging references (remove invalid dependencies)"
    echo "2. 🟡 Connect orphaned entities (add them as dependencies)"
    echo "3. 🟠 Add missing graph entries (create dependency entries)"
    echo "4. 🔄 Break circular dependencies (interactive resolution)"
    echo "5. 📊 Show current health status"
    echo "6. 💾 Save and exit"
    echo "7. ❌ Restore backup and exit"
    echo
    echo -n "Choose option (1-7): "
}

get_health_status() {
    ./scripts/find-disconnects.sh "$KNOWLEDGE_MAP" | grep "Total issues found:" | grep -o '[0-9]\+' || echo "0"
}

show_health() {
    echo -e "${BLUE}📊 Current Health Status:${NC}"
    echo "=========================="
    ./scripts/find-disconnects.sh "$KNOWLEDGE_MAP" | tail -20
    echo
    read -p "Press Enter to continue..."
}

fix_hanging_references() {
    echo -e "${RED}🔴 FIXING HANGING REFERENCES${NC}"
    echo "=============================="
    
    HANGING=$(jq -r '
    ([.entities | .. | objects | select(has("id")) | .id] + [.graph | keys[]] | unique) as $all_entities |
    [.graph | .[] | .depends_on[]?] | unique[] |
    select(. as $ref | $all_entities | index($ref) | not)
    ' "$KNOWLEDGE_MAP" | sort)
    
    if [[ -z "$HANGING" ]]; then
        echo "✅ No hanging references found!"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Found hanging references:"
    echo "$HANGING" | nl -w2 -s'. '
    echo
    echo "Options:"
    echo "1. Remove ALL hanging references automatically"
    echo "2. Review each reference individually" 
    echo "3. Skip this step"
    echo
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "🗑️ Removing all hanging references..."
            # Create jq script to remove hanging references
            jq --argjson hanging_refs "$(echo "$HANGING" | jq -R -s 'split("\n")[:-1]')" '
            ([.entities | .. | objects | select(has("id")) | .id] + [.graph | keys[]] | unique) as $valid_entities |
            .graph |= with_entries(
                .value.depends_on = (
                    .value.depends_on | map(select(. as $ref | $valid_entities | index($ref)))
                )
            )
            ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
            echo "✅ All hanging references removed!"
            ;;
        2)
            echo "$HANGING" | while read -r ref; do
                echo
                echo -e "Reference: ${YELLOW}$ref${NC}"
                echo "Used by:"
                jq -r --arg ref "$ref" '
                .graph | to_entries[] | 
                select(.value.depends_on[]? == $ref) |
                "  - " + .key
                ' "$KNOWLEDGE_MAP"
                echo
                echo "1. Remove this reference"
                echo "2. Skip this reference"
                read -p "Choose (1-2): " ref_choice
                
                if [[ $ref_choice == "1" ]]; then
                    jq --arg ref "$ref" '
                    .graph |= with_entries(
                        .value.depends_on = (.value.depends_on | map(select(. != $ref)))
                    )
                    ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                    echo "✅ Removed reference: $ref"
                fi
            done
            ;;
        3)
            echo "⏭️ Skipping hanging references..."
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

connect_orphaned_entities() {
    echo -e "${YELLOW}🟡 CONNECTING ORPHANED ENTITIES${NC}"
    echo "================================"
    
    ORPHANED=$(jq -r '
    (.graph | keys) as $graph_entities |
    [.graph | .[] | .depends_on[]?] as $referenced |
    $graph_entities[] |
    select(. as $entity | ($referenced | index($entity) | not))
    ' "$KNOWLEDGE_MAP" | sort)
    
    if [[ -z "$ORPHANED" ]]; then
        echo "✅ No orphaned entities found!"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Found orphaned entities (nothing depends on them):"
    echo "$ORPHANED" | nl -w2 -s'. '
    echo
    
    echo "$ORPHANED" | while read -r orphan; do
        echo
        echo -e "Orphaned entity: ${YELLOW}$orphan${NC}"
        echo "Current dependencies:"
        jq -r --arg entity "$orphan" '.graph[$entity].depends_on[]? // "  (no dependencies)"' "$KNOWLEDGE_MAP"
        echo
        echo "Potential candidates to depend on this entity:"
        
        # Suggest entities based on type similarity
        entity_type=$(echo "$orphan" | cut -d':' -f1)
        jq -r --arg type "$entity_type" --arg orphan "$orphan" '
        .graph | keys[] | 
        select(startswith($type + ":") and . != $orphan) |
        "  - " + .
        ' "$KNOWLEDGE_MAP" | head -5
        
        echo
        echo "1. Add this entity as dependency to another entity"
        echo "2. Remove this orphaned entity (if unused)"
        echo "3. Skip this entity"
        read -p "Choose (1-3): " orphan_choice
        
        case $orphan_choice in
            1)
                echo "Available entities to connect to:"
                jq -r '.graph | keys[]' "$KNOWLEDGE_MAP" | grep -v "^$orphan$" | nl -w2 -s'. '
                echo
                read -p "Enter entity number (or entity name): " target
                
                if [[ "$target" =~ ^[0-9]+$ ]]; then
                    target_entity=$(jq -r '.graph | keys[]' "$KNOWLEDGE_MAP" | sed -n "${target}p")
                else
                    target_entity="$target"
                fi
                
                if [[ -n "$target_entity" ]]; then
                    jq --arg target "$target_entity" --arg orphan "$orphan" '
                    .graph[$target].depends_on += [$orphan] |
                    .graph[$target].depends_on |= unique
                    ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                    echo "✅ Connected $orphan to $target_entity"
                else
                    echo "❌ Invalid target entity"
                fi
                ;;
            2)
                jq --arg orphan "$orphan" 'del(.graph[$orphan])' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                echo "✅ Removed orphaned entity: $orphan"
                ;;
            3)
                echo "⏭️ Skipping $orphan"
                ;;
        esac
    done
    
    read -p "Press Enter to continue..."
}

add_missing_graph_entries() {
    echo -e "${BLUE}🟠 ADDING MISSING GRAPH ENTRIES${NC}"
    echo "================================"
    
    MISSING=$(jq -r '
    [.entities | .. | objects | select(has("id")) | .id] as $entity_ids |
    (.graph | keys) as $graph_entities |
    $entity_ids[] |
    select(. as $entity | $graph_entities | index($entity) | not)
    ' "$KNOWLEDGE_MAP" | sort)
    
    if [[ -z "$MISSING" ]]; then
        echo "✅ All entities have graph entries!"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Found entities missing from graph:"
    echo "$MISSING" | nl -w2 -s'. '
    echo
    echo "Options:"
    echo "1. Add ALL missing entities with empty dependencies"
    echo "2. Add each entity individually with custom dependencies"
    echo "3. Skip this step"
    echo
    read -p "Choose option (1-3): " choice
    
    case $choice in
        1)
            echo "📝 Adding all missing entities with empty dependencies..."
            echo "$MISSING" | while read -r entity; do
                jq --arg entity "$entity" '.graph[$entity] = {"depends_on": []}' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
            done
            echo "✅ Added all missing entities!"
            ;;
        2)
            echo "$MISSING" | while read -r entity; do
                echo
                echo -e "Entity: ${BLUE}$entity${NC}"
                
                # Show entity details
                jq -r --arg entity "$entity" '
                [.entities | .. | objects | select(.id == $entity)] | 
                if length > 0 then 
                    .[0] | "Type: " + .type + "\nName: " + .name + "\nDescription: " + (.description_ref // "none")
                else 
                    "No entity details found"
                end
                ' "$KNOWLEDGE_MAP"
                
                echo
                echo "Available entities to depend on:"
                jq -r '.graph | keys[]' "$KNOWLEDGE_MAP" | head -10 | nl -w2 -s'. '
                echo "... (showing first 10, or type entity names directly)"
                echo
                echo "Enter dependencies (space-separated numbers or entity names, or 'none'):"
                read -r deps_input
                
                if [[ "$deps_input" == "none" ]]; then
                    deps_array="[]"
                else
                    deps_array="["
                    for dep in $deps_input; do
                        if [[ "$dep" =~ ^[0-9]+$ ]]; then
                            dep_entity=$(jq -r '.graph | keys[]' "$KNOWLEDGE_MAP" | sed -n "${dep}p")
                        else
                            dep_entity="$dep"
                        fi
                        if [[ -n "$dep_entity" ]]; then
                            deps_array="$deps_array\"$dep_entity\","
                        fi
                    done
                    deps_array="${deps_array%,}]"
                fi
                
                jq --arg entity "$entity" --argjson deps "$deps_array" '
                .graph[$entity] = {"depends_on": $deps}
                ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                
                echo "✅ Added $entity to graph"
            done
            ;;
        3)
            echo "⏭️ Skipping missing graph entries..."
            ;;
    esac
    
    read -p "Press Enter to continue..."
}

break_circular_dependencies() {
    echo -e "${RED}🔄 BREAKING CIRCULAR DEPENDENCIES${NC}"
    echo "=================================="
    
    CIRCULAR=$(jq -r '
    .graph as $g |
    $g | to_entries[] |
    .key as $entity |
    .value.depends_on[]? as $dep |
    select($g[$dep].depends_on[]? == $entity) |
    [$entity, $dep] | sort | join(" <-> ")
    ' "$KNOWLEDGE_MAP" | sort | uniq)
    
    if [[ -z "$CIRCULAR" ]]; then
        echo "✅ No circular dependencies found!"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Found circular dependencies:"
    echo "$CIRCULAR" | nl -w2 -s'. '
    echo
    
    echo "$CIRCULAR" | while read -r cycle; do
        entity1=$(echo "$cycle" | cut -d' ' -f1)
        entity2=$(echo "$cycle" | cut -d' ' -f3)
        
        echo
        echo -e "Circular dependency: ${RED}$entity1 <-> $entity2${NC}"
        echo
        echo -e "${entity1} depends on:"
        jq -r --arg e "$entity1" '.graph[$e].depends_on[]?' "$KNOWLEDGE_MAP" | sed 's/^/  - /'
        echo
        echo -e "${entity2} depends on:"
        jq -r --arg e "$entity2" '.graph[$e].depends_on[]?' "$KNOWLEDGE_MAP" | sed 's/^/  - /'
        echo
        echo "How to resolve?"
        echo "1. Remove $entity1 -> $entity2 dependency"
        echo "2. Remove $entity2 -> $entity1 dependency"
        echo "3. Remove both dependencies"
        echo "4. Skip this circular dependency"
        read -p "Choose (1-4): " cycle_choice
        
        case $cycle_choice in
            1)
                jq --arg e1 "$entity1" --arg e2 "$entity2" '
                .graph[$e1].depends_on = (.graph[$e1].depends_on | map(select(. != $e2)))
                ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                echo "✅ Removed $entity1 -> $entity2 dependency"
                ;;
            2)
                jq --arg e1 "$entity1" --arg e2 "$entity2" '
                .graph[$e2].depends_on = (.graph[$e2].depends_on | map(select(. != $e1)))
                ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                echo "✅ Removed $entity2 -> $entity1 dependency"
                ;;
            3)
                jq --arg e1 "$entity1" --arg e2 "$entity2" '
                .graph[$e1].depends_on = (.graph[$e1].depends_on | map(select(. != $e2))) |
                .graph[$e2].depends_on = (.graph[$e2].depends_on | map(select(. != $e1)))
                ' "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                echo "✅ Removed both circular dependencies"
                ;;
            4)
                echo "⏭️ Skipping circular dependency"
                ;;
        esac
    done
    
    read -p "Press Enter to continue..."
}

# Main interactive loop
echo -e "${GREEN}🔧 Welcome to the Dependency Graph Repair Tool!${NC}"
echo
echo "Initial health check:"
INITIAL_ISSUES=$(get_health_status)
echo "Found $INITIAL_ISSUES issues to fix."
echo

while true; do
    echo
    show_menu
    read -r choice
    echo
    
    case $choice in
        1)
            fix_hanging_references
            ;;
        2)
            connect_orphaned_entities
            ;;
        3)
            add_missing_graph_entries
            ;;
        4)
            break_circular_dependencies
            ;;
        5)
            show_health
            ;;
        6)
            echo -e "${GREEN}💾 Saving changes and exiting...${NC}"
            FINAL_ISSUES=$(get_health_status)
            echo "Fixed $((INITIAL_ISSUES - FINAL_ISSUES)) issues!"
            echo "Backup available at: $BACKUP_FILE"
            exit 0
            ;;
        7)
            echo -e "${YELLOW}❌ Restoring backup and exiting...${NC}"
            mv "$BACKUP_FILE" "$KNOWLEDGE_MAP"
            echo "Changes discarded, original file restored."
            exit 1
            ;;
        *)
            echo "❌ Invalid option. Please choose 1-7."
            ;;
    esac
done