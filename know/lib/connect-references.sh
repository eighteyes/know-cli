#!/bin/bash

# Interactive tool to connect orphaned reference keys to entities using FZF

set -e

# Source common functions if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/common.sh" ]; then
    source "$SCRIPT_DIR/common.sh"
fi

# Set up paths
SPEC_GRAPH="${KNOWLEDGE_MAP:-.ai/spec-graph.json}"
MOD_GRAPH="${MOD_GRAPH:-$SCRIPT_DIR/mod-graph.sh}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check dependencies
check_dependencies() {
    if ! command -v fzf &> /dev/null; then
        echo -e "${RED}Error: fzf is required but not installed${NC}" >&2
        echo "Install with: brew install fzf" >&2
        exit 1
    fi

    if [ ! -f "$SPEC_GRAPH" ]; then
        echo -e "${RED}Error: Graph file not found: $SPEC_GRAPH${NC}" >&2
        exit 1
    fi

    if [ ! -f "$MOD_GRAPH" ]; then
        echo -e "${RED}Error: mod-graph.sh not found: $MOD_GRAPH${NC}" >&2
        exit 1
    fi
}

# Get orphaned reference keys
get_orphaned_keys() {
    # Get all reference keys
    local all_keys=$(jq -r '
        .references |
        to_entries |
        map(.key as $ref | .value | keys | map($ref + ":" + .)) |
        flatten[]
    ' "$SPEC_GRAPH" 2>/dev/null)

    # Check each key for parents
    local orphaned=""
    for key in $all_keys; do
        # Check if this key has any parents in the graph
        local has_parent=$(jq --arg key "$key" '
            .graph | map(select(.target == $key)) | length
        ' "$SPEC_GRAPH")

        if [ "$has_parent" -eq 0 ]; then
            orphaned="$orphaned$key\n"
        fi
    done

    echo -e "$orphaned" | grep -v '^$' | sort
}

# Get all individual entities with their types
get_all_entities() {
    # Get all entities from all entity types
    jq -r '
        .entities |
        to_entries[] |
        .key as $type |
        .value |
        to_entries[] |
        "\($type):\(.key)"
    ' "$SPEC_GRAPH" | sort
}

# Get entity description
get_entity_description() {
    local entity_ref="$1"

    # Parse entity type and id
    if [[ "$entity_ref" == *":"* ]]; then
        local entity_type="${entity_ref%:*}"
        local entity_id="${entity_ref#*:}"

        jq -r --arg type "$entity_type" --arg id "$entity_id" \
            '.entities[$type][$id].description // "No description"' "$SPEC_GRAPH"
    else
        echo "No description"
    fi
}

# Get entity dependencies
get_entity_dependencies() {
    local entity_ref="$1"

    # Get dependencies from the graph
    jq -r --arg ref "$entity_ref" '
        .graph[$ref].depends_on[]? // empty
    ' "$SPEC_GRAPH" 2>/dev/null | head -10
}

# Get reference key value
get_reference_value() {
    local ref_key="$1"
    local ref="${ref_key%:*}"
    local key="${ref_key#*:}"

    jq -r --arg r "$ref" --arg k "$key" '.references[$r][$k] // "No value"' "$SPEC_GRAPH"
}

# Connect a reference key to entities
connect_reference_key() {
    local ref_key="$1"
    shift
    local entities=("$@")

    echo -e "\n${CYAN}Connecting: $ref_key${NC}"

    for entity in "${entities[@]}"; do
        echo -e "  ${GREEN}→${NC} $entity"

        # Use mod-graph to create the connection
        "$MOD_GRAPH" connect "$entity" "$ref_key" >/dev/null 2>&1

        if [ $? -eq 0 ]; then
            echo -e "    ${GREEN}✓ Connected${NC}"
        else
            echo -e "    ${RED}✗ Failed to connect${NC}"
        fi
    done
}

# Interactive mode with FZF
interactive_mode() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}        Interactive Reference Connection Tool${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"

    # Get orphaned keys
    local orphaned_keys=$(get_orphaned_keys)

    if [ -z "$orphaned_keys" ]; then
        echo -e "${GREEN}✓ All reference keys are connected!${NC}"
        return 0
    fi

    local orphan_count=$(echo "$orphaned_keys" | wc -l | xargs)
    echo -e "${YELLOW}Found $orphan_count orphaned reference keys${NC}\n"

    while true; do
        # Select reference key with preview
        local selected_key=$(echo "$orphaned_keys" | \
            fzf --prompt="Select reference key to connect (ESC to quit): " \
                --header="↓/↑ navigate, Enter to select, ESC to quit" \
                --preview="echo '${CYAN}Reference Key:${NC} {}' && \
                          echo '${CYAN}Value:${NC}' && \
                          echo '{}' | awk -F: '{print \$1, \$2}' | \
                          xargs -I% sh -c 'jq -r --arg r \"\$(echo % | cut -d\" \" -f1)\" --arg k \"\$(echo % | cut -d\" \" -f2)\" \".references[\\\$r][\\\$k] // \\\"No value\\\"\" \"$SPEC_GRAPH\"' | \
                          sed 's/^/  /' && \
                          echo '' && \
                          echo '${YELLOW}This key is not connected to any entities${NC}'" \
                --preview-window=up:40%:wrap \
                --height=80%)

        if [ -z "$selected_key" ]; then
            break
        fi

        echo -e "\n${CYAN}══════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}    Connecting Reference: $selected_key${NC}"
        echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"

        # Show reference value
        local value=$(get_reference_value "$selected_key")
        echo -e "\n${BLUE}Reference Value:${NC}"
        echo "$value" | fold -w 70 | sed 's/^/  /'
        echo

        # Get all individual entities for selection
        local entities=$(get_all_entities)

        # Multi-select entities with preview showing reference context
        echo -e "${YELLOW}Select entities to connect this reference to:${NC}"
        echo -e "${YELLOW}(Use '/' to search, Tab to multi-select, Enter to confirm)${NC}\n"

        local selected_entities=$(echo "$entities" | \
            fzf --multi \
                --prompt="Search entities to connect '$selected_key' to: " \
                --header="Reference: $selected_key | ↓/↑ navigate, / search, Tab select, Enter confirm" \
                --preview="echo '${MAGENTA}═══ REFERENCE BEING CONNECTED ═══${NC}' && \
                          echo '${CYAN}$selected_key${NC}' && \
                          echo '$(get_reference_value \"$selected_key\" | head -3)' | sed 's/^/  /' && \
                          echo '' && \
                          echo '${MAGENTA}═══ TARGET ENTITY ═══${NC}' && \
                          echo '${CYAN}Entity:${NC} {}' && \
                          echo '${BLUE}Description:${NC}' && \
                          ref='{}' && \
                          type=\${ref%:*} && \
                          id=\${ref#*:} && \
                          jq -r --arg t \"\$type\" --arg i \"\$id\" '.entities[\$t][\$i].description // \"No description\"' \"$SPEC_GRAPH\" | \
                          fold -w 60 | sed 's/^/  /' && \
                          echo '' && \
                          echo '${BLUE}Current dependencies:${NC}' && \
                          jq -r --arg ref '{}' '.graph[\$ref].depends_on[]? // empty' \"$SPEC_GRAPH\" 2>/dev/null | head -5 | sed 's/^/  • /'" \
                --preview-window=up:60%:wrap \
                --height=90% \
                --bind='tab:toggle+down' \
                --marker='✓' \
                --border=rounded)

        if [ -n "$selected_entities" ]; then
            # Convert to array
            local entity_array=()
            while IFS= read -r entity; do
                entity_array+=("$entity")
            done <<< "$selected_entities"

            # Confirm connection
            echo -e "\n${YELLOW}Will create connections:${NC}"
            for entity in "${entity_array[@]}"; do
                echo -e "  ${entity} → ${selected_key}"
            done

            echo -e "\n${YELLOW}Confirm? (y/n):${NC} "
            read -r confirm

            if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
                connect_reference_key "$selected_key" "${entity_array[@]}"

                # Update orphaned keys list
                orphaned_keys=$(get_orphaned_keys)

                if [ -z "$orphaned_keys" ]; then
                    echo -e "\n${GREEN}✓ All reference keys are now connected!${NC}"
                    break
                fi

                orphan_count=$(echo "$orphaned_keys" | wc -l | xargs)
                echo -e "\n${YELLOW}$orphan_count reference keys remaining${NC}"
            else
                echo -e "${RED}Cancelled${NC}"
            fi
        fi

        echo -e "\n${CYAN}Continue with another key? (y/n):${NC} "
        read -r continue_choice
        if [[ "$continue_choice" != "y" && "$continue_choice" != "Y" ]]; then
            break
        fi
    done
}

# Batch mode - connect all keys of a reference to an entity
batch_mode() {
    local reference="$1"
    local entity="$2"

    echo -e "${CYAN}Batch connecting all keys from '$reference' to '$entity'${NC}\n"

    # Get all keys for this reference
    local keys=$(jq -r --arg ref "$reference" '
        .references[$ref] | keys[]
    ' "$SPEC_GRAPH" 2>/dev/null)

    if [ -z "$keys" ]; then
        echo -e "${RED}Error: Reference '$reference' not found or has no keys${NC}"
        exit 1
    fi

    # Parse entity reference (could be type:id or just id)
    local entity_ref="$entity"
    if [[ ! "$entity_ref" == *":"* ]]; then
        # Try to auto-detect entity type
        for entity_type in features components screens interfaces behavior actions objectives requirements users; do
            local exists=$(jq -r --arg type "$entity_type" --arg id "$entity" '.entities[$type] | has($id)' "$SPEC_GRAPH")
            if [ "$exists" == "true" ]; then
                entity_ref="${entity_type%s}:${entity}"
                break
            fi
        done
    fi

    # Verify entity exists using the reference format
    local entity_type="${entity_ref%:*}"
    local entity_id="${entity_ref#*:}"

    # Handle plural forms
    local entity_type_plural="$entity_type"
    case "$entity_type" in
        feature) entity_type_plural="features" ;;
        component) entity_type_plural="components" ;;
        screen) entity_type_plural="screens" ;;
        interface) entity_type_plural="interfaces" ;;
        requirement) entity_type_plural="requirements" ;;
        user) entity_type_plural="users" ;;
        objective) entity_type_plural="objectives" ;;
        action) entity_type_plural="actions" ;;
    esac

    local entity_exists=$(jq -r --arg type "$entity_type_plural" --arg id "$entity_id" '.entities[$type] | has($id)' "$SPEC_GRAPH")
    if [ "$entity_exists" != "true" ]; then
        echo -e "${RED}Error: Entity '$entity' not found${NC}"
        echo "Tried: $entity_type_plural:$entity_id"
        exit 1
    fi

    # Use the properly formatted entity reference
    entity="$entity_ref"

    # Connect each key
    local connected=0
    local failed=0

    for key in $keys; do
        local ref_key="${reference}:${key}"
        echo -e "Connecting ${BLUE}$ref_key${NC} to ${GREEN}$entity${NC}"

        "$MOD_GRAPH" connect "$entity" "$ref_key" >/dev/null 2>&1

        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓ Connected${NC}"
            connected=$((connected + 1))
        else
            echo -e "  ${RED}✗ Failed${NC}"
            failed=$((failed + 1))
        fi
    done

    echo -e "\n${CYAN}Summary:${NC}"
    echo -e "  ${GREEN}Connected: $connected${NC}"
    echo -e "  ${RED}Failed: $failed${NC}"
}

# List orphaned keys (non-interactive)
list_orphaned() {
    local orphaned_keys=$(get_orphaned_keys)

    if [ -z "$orphaned_keys" ]; then
        echo -e "${GREEN}✓ All reference keys are connected!${NC}"
        return 0
    fi

    local orphan_count=$(echo "$orphaned_keys" | wc -l | xargs)
    echo -e "${YELLOW}Found $orphan_count orphaned reference keys:${NC}\n"

    # Group by reference for better readability
    local current_ref=""
    for key in $orphaned_keys; do
        local ref_name="${key%:*}"
        local key_name="${key#*:}"

        if [ "$ref_name" != "$current_ref" ]; then
            echo -e "\n${CYAN}$ref_name:${NC}"
            current_ref="$ref_name"
        fi
        echo "  - $key_name"
    done

    echo -e "\n${YELLOW}To connect these keys:${NC}"
    echo "  Interactive mode: know connect-references interactive"
    echo "  Batch mode: know connect-references batch <reference> <entity>"
    echo "  Example: know connect-references batch design ui_component_fleet_map"
}

# Main function
main() {
    case "${1:-list}" in
        batch)
            check_dependencies
            if [ $# -lt 3 ]; then
                echo "Usage: $0 batch <reference> <entity>"
                echo "Example: $0 batch design ui_component_fleet_map"
                exit 1
            fi
            batch_mode "$2" "$3"
            ;;
        interactive)
            check_dependencies
            # Check if we're in an interactive terminal
            if [ ! -t 0 ] || [ ! -t 1 ]; then
                echo -e "${RED}Error: Interactive mode requires a terminal${NC}"
                echo "Use 'know connect-references list' to see orphaned keys"
                echo "Use 'know connect-references batch <ref> <entity>' for non-interactive connection"
                exit 1
            fi
            interactive_mode
            ;;
        list|*)
            # Don't check FZF dependency for list mode
            if [ ! -f "$SPEC_GRAPH" ]; then
                echo -e "${RED}Error: Graph file not found: $SPEC_GRAPH${NC}" >&2
                exit 1
            fi
            list_orphaned
            ;;
    esac
}

# Run main function
main "$@"