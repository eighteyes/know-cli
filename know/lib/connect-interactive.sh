#!/bin/bash

# Interactive connection tool - review and approve connections

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Interactive connection finder
interactive_connect() {
    local threshold="${1:-40}"
    local max_suggestions="${2:-20}"

    echo -e "${BLUE}🔍 Interactive Connection Mode${NC}"
    echo -e "${CYAN}Finding connections with similarity > ${threshold}%${NC}"
    echo

    local connections_made=0
    local connections_reviewed=0

    # Find entities with few or no connections
    local entities=$(jq -r '
        .graph as $g |
        .entities | to_entries[] | .key as $type | .value | to_entries[] |
        "\($type):\(.key)" as $entity |
        select(($g[$entity].depends_on // []) | length < 2) |
        $entity
    ' "$KNOWLEDGE_MAP" 2>/dev/null | sort -u | head -"$max_suggestions")

    echo -e "${YELLOW}Found entities needing connections:${NC}"
    echo

    while IFS= read -r entity; do
        [[ -z "$entity" ]] && continue

        local entity_type="${entity%%:*}"
        local entity_name="${entity#*:}"

        # Get allowed dependencies for this type
        local allowed=$(jq -r ".allowed_dependencies.$entity_type[]?" "$SCRIPT_DIR/dependency-rules.json" 2>/dev/null)

        if [[ -z "$allowed" ]]; then
            continue
        fi

        echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}Entity: $entity${NC}"
        echo -e "${CYAN}Can connect to: $allowed${NC}"
        echo

        # Find potential matches
        local found_any=false
        for target_type in $allowed; do
            # Get entities of target type
            local targets=$(jq -r ".entities.$target_type | keys[]?" "$KNOWLEDGE_MAP" 2>/dev/null)

            for target_name in $targets; do
                local target="${target_type}:${target_name}"

                # Skip if already connected
                local exists=$(jq -r ".graph[\"$entity\"].depends_on[]? | select(. == \"$target\")" "$KNOWLEDGE_MAP" 2>/dev/null)
                [[ -n "$exists" ]] && continue

                # Calculate simple similarity
                local score=0

                # Check for keyword matches
                local entity_words=$(echo "$entity_name" | sed 's/[-_]/ /g')
                local target_words=$(echo "$target_name" | sed 's/[-_]/ /g')

                for e_word in $entity_words; do
                    for t_word in $target_words; do
                        if [[ ${#e_word} -gt 3 ]] && [[ ${#t_word} -gt 3 ]]; then
                            if [[ "${e_word:0:4}" == "${t_word:0:4}" ]]; then
                                score=50
                                # Boost score for longer matches
                                [[ "${e_word:0:6}" == "${t_word:0:6}" ]] && score=70
                                [[ "$e_word" == "$t_word" ]] && score=90
                                break 2
                            fi
                        fi
                    done
                done

                # Also check references
                if [[ "$target_type" == "acceptance_criteria" ]] || [[ "$target_type" == "business_logic" ]]; then
                    # Special handling for references
                    local ref_base=$(echo "$target_name" | sed 's/_/-/g')
                    local entity_base=$(echo "$entity_name" | sed 's/_/-/g')
                    if [[ "$ref_base" == *"$entity_base"* ]] || [[ "$entity_base" == *"$ref_base"* ]]; then
                        score=80
                    fi
                fi

                if [[ $score -ge $threshold ]]; then
                    found_any=true
                    echo -e "  ${YELLOW}→${NC} $target ${BLUE}(${score}% match)${NC}"
                    echo -n "     Connect? (y/n/q) "
                    read -n 1 -r answer
                    echo

                    ((connections_reviewed++))

                    case "$answer" in
                        y|Y)
                            # Apply connection
                            echo -e "     ${GREEN}✓ Connecting...${NC}"

                            # Ensure source exists in graph
                            if ! jq -e ".graph | has(\"$entity\")" "$KNOWLEDGE_MAP" > /dev/null 2>&1; then
                                jq --arg src "$entity" '.graph[$src] = {"depends_on": []}' \
                                   "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
                            fi

                            # Add connection
                            jq --arg src "$entity" --arg tgt "$target" \
                               '.graph[$src].depends_on = ((.graph[$src].depends_on // []) + [$tgt] | unique)' \
                               "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"

                            ((connections_made++))
                            echo -e "     ${GREEN}Connected!${NC}"
                            echo
                            break  # Move to next entity after making a connection
                            ;;
                        q|Q)
                            echo
                            echo -e "${YELLOW}Stopping interactive mode${NC}"
                            break 2
                            ;;
                        *)
                            echo -e "     ${RED}✗ Skipped${NC}"
                            ;;
                    esac
                fi
            done

            # If we made a connection, move to next entity
            [[ $connections_made -gt 0 ]] && break
        done

        if [[ "$found_any" != "true" ]]; then
            echo -e "  ${YELLOW}No matches found with > ${threshold}% similarity${NC}"
        fi

        echo

        # Ask if user wants to continue
        if [[ $connections_reviewed -gt 0 ]] && [[ $((connections_reviewed % 5)) -eq 0 ]]; then
            echo -n "Continue reviewing? (y/n) "
            read -n 1 -r continue_answer
            echo
            [[ ! "$continue_answer" =~ ^[Yy]$ ]] && break
        fi

    done <<< "$entities"

    # Summary
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Interactive Connection Summary:${NC}"
    echo -e "  Connections reviewed: $connections_reviewed"
    echo -e "  Connections made: $connections_made"

    local total_deps=$(jq '[.graph | to_entries[] | select(.value.depends_on | length > 0)] | length' "$KNOWLEDGE_MAP")
    echo -e "  Total graph connections: $total_deps"
}

# Run interactive mode
interactive_connect "$@"