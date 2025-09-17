#!/bin/bash

# Check that every reference key has at least one parent entity
# by traversing the depends_on graph backwards

set -e

# Source common functions if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/common.sh" ]; then
    source "$SCRIPT_DIR/common.sh"
fi

# Default spec graph (will be set properly after argument parsing)
SPEC_GRAPH=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_reference_keys() {
    local format="${1:-text}"

    # Get all references and their keys
    local all_reference_keys=$(jq -r '
        .references |
        to_entries |
        map(.key as $ref | .value | keys | map($ref + ":" + .)) |
        flatten[]
    ' "$SPEC_GRAPH" 2>/dev/null || echo "")

    if [ -z "$all_reference_keys" ]; then
        if [ "$format" == "json" ]; then
            echo '{"status": "warning", "message": "No reference keys found in graph"}'
        else
            echo -e "${YELLOW}Warning: No reference keys found in graph${NC}"
        fi
        return 0
    fi

    # Function to find parents of a node by traversing graph backwards
    find_parents() {
        local node="$1"
        local parents=""

        # The graph structure is an object where each entity has a depends_on array
        # We need to find all entities that have this node in their depends_on array
        parents=$(jq -r --arg node "$node" '
            .graph |
            to_entries[] |
            select(.value.depends_on? and (.value.depends_on | index($node))) |
            .key
        ' "$SPEC_GRAPH" 2>/dev/null | xargs)

        echo "$parents"
    }

    # Function to check if a reference is an entity
    is_entity() {
        local ref="$1"

        # Parse entity type and id from reference format (type:id)
        if [[ "$ref" == *":"* ]]; then
            local type="${ref%:*}"
            local id="${ref#*:}"

            # Handle singular to plural conversions
            local type_plural="$type"
            case "$type" in
                feature) type_plural="features" ;;
                component) type_plural="components" ;;
                screen) type_plural="screens" ;;
                interface) type_plural="interfaces" ;;
                requirement) type_plural="requirements" ;;
                user) type_plural="users" ;;
                objective) type_plural="objectives" ;;
                action) type_plural="actions" ;;
            esac

            # Check if this entity exists
            local exists=$(jq -r --arg type "$type_plural" --arg id "$id" \
                '.entities[$type] | has($id)' "$SPEC_GRAPH" 2>/dev/null)

            if [ "$exists" == "true" ]; then
                return 0
            fi
        fi

        return 1
    }


    # Check each reference key
    local orphan_count=0
    local orphan_keys=""
    local connected_count=0
    local json_results='[]'
    local total_keys=0

    # Process each reference key
    for ref_key in $all_reference_keys; do
        total_keys=$((total_keys + 1))

        # Split ref:key format
        local ref_name="${ref_key%:*}"
        local key_name="${ref_key#*:}"
        local full_key="${ref_name}:${key_name}"

        # Find what depends on this specific reference key
        local parents=$(find_parents "$full_key")

        if [ -z "$parents" ]; then
            orphan_count=$((orphan_count + 1))
            orphan_keys="$orphan_keys $full_key"

            if [ "$format" == "json" ]; then
                json_results=$(echo "$json_results" | jq \
                    --arg ref "$ref_name" \
                    --arg key "$key_name" \
                    --arg full "$full_key" \
                    '. + [{reference: $ref, key: $key, full_key: $full, status: "orphaned", parents: []}]')
            fi
        else
            # Check if at least one parent is an entity
            local has_entity_parent=false
            local entity_parents=""

            for parent in $parents; do
                if is_entity "$parent"; then
                    has_entity_parent=true
                    entity_parents="$entity_parents $parent"
                fi
            done

            if [ "$has_entity_parent" = true ]; then
                connected_count=$((connected_count + 1))

                if [ "$format" == "json" ]; then
                    json_results=$(echo "$json_results" | jq \
                        --arg ref "$ref_name" \
                        --arg key "$key_name" \
                        --arg full "$full_key" \
                        --arg parents "$entity_parents" \
                        '. + [{reference: $ref, key: $key, full_key: $full, status: "connected", entity_parents: ($parents | split(" ") | map(select(. != "")))}]')
                fi
            else
                orphan_count=$((orphan_count + 1))
                orphan_keys="$orphan_keys $full_key"

                if [ "$format" == "json" ]; then
                    json_results=$(echo "$json_results" | jq \
                        --arg ref "$ref_name" \
                        --arg key "$key_name" \
                        --arg full "$full_key" \
                        --arg parents "$parents" \
                        '. + [{reference: $ref, key: $key, full_key: $full, status: "orphaned", non_entity_parents: ($parents | split(" ") | map(select(. != "")))}]')
                fi
            fi
        fi
    done

    if [ "$format" == "json" ]; then
        jq -n \
            --argjson results "$json_results" \
            --arg total "$total_keys" \
            --arg connected "$connected_count" \
            --arg orphaned "$orphan_count" \
            --argjson orphan_list "$(echo "$orphan_keys" | xargs -n1 | jq -Rs 'split("\n") | map(select(. != ""))')" \
            '{
                timestamp: now | strftime("%Y-%m-%dT%H:%M:%SZ"),
                status: (if $orphaned == "0" then "pass" else "fail" end),
                summary: {
                    total_reference_keys: ($total | tonumber),
                    connected_to_entities: ($connected | tonumber),
                    orphaned_reference_keys: ($orphaned | tonumber)
                },
                orphaned_keys: $orphan_list,
                details: $results
            }'
    else
        echo "Checking reference key parent relationships..."
        echo "=============================================="
        echo ""
        echo "Total reference keys: $total_keys"
        echo -e "${GREEN}Connected to entities: $connected_count${NC}"
        echo -e "${RED}Orphaned reference keys: $orphan_count${NC}"

        if [ $orphan_count -gt 0 ]; then
            echo ""
            echo -e "${RED}❌ Check failed: Orphaned reference keys found${NC}"
            echo ""
            echo "Orphaned reference keys (need parent entities):"

            # Group by reference for better readability
            local current_ref=""
            for key in $orphan_keys; do
                local ref_name="${key%:*}"
                local key_name="${key#*:}"

                if [ "$ref_name" != "$current_ref" ]; then
                    echo ""
                    echo "  $ref_name:"
                    current_ref="$ref_name"
                fi
                echo "    - $key_name"
            done

            echo ""
            echo "Fix: Each reference key must be depended upon by at least one entity"
            echo "Example: entity depends_on 'reference_name:key_name'"
            return 1
        else
            echo ""
            echo -e "${GREEN}✅ All reference keys have parent entities!${NC}"
        fi
    fi

    return $([ $orphan_count -eq 0 ] && echo 0 || echo 1)
}

# Main execution
main() {
    local format="${FORMAT:-text}"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --json)
                format="json"
                shift
                ;;
            --file|-f)
                SPEC_GRAPH="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done

    # Set default graph file if not provided
    if [ -z "$SPEC_GRAPH" ]; then
        SPEC_GRAPH="${KNOWLEDGE_MAP:-.ai/spec-graph.json}"
    fi

    # Check if graph file exists
    if [ ! -f "$SPEC_GRAPH" ]; then
        echo "Error: Graph file not found: $SPEC_GRAPH" >&2
        exit 1
    fi

    check_reference_keys "$format"
}

# Only run main if not being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi