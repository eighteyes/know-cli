#!/bin/bash

# Mac-compatible connection script
# Works with Bash 3.2+ and BSD utilities

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}"

# Simple colors that work on Mac
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
NC=$'\033[0m'

# Load dependency rules without associative arrays (Bash 3.2 compatible)
load_rules() {
    if [[ ! -f "$SCRIPT_DIR/dependency-rules.json" ]]; then
        echo "${RED}Error: dependency-rules.json not found${NC}" >&2
        return 1
    fi

    # Just check the file exists, we'll use jq for lookups
    return 0
}

# Check if connection is valid
is_valid_connection() {
    local source_type="$1"
    local target_type="$2"

    # Use jq to check allowed dependencies
    local allowed=$(jq -r ".allowed_dependencies.$source_type[]?" "$SCRIPT_DIR/dependency-rules.json" 2>/dev/null)

    for allowed_type in $allowed; do
        [[ "$allowed_type" == "$target_type" ]] && return 0
    done

    return 1
}

# Find connections for an entity
find_connections() {
    local entity="$1"
    local threshold="${2:-40}"

    local entity_type="${entity%%:*}"
    local entity_name="${entity#*:}"

    echo "${BLUE}Finding connections for: $entity${NC}"

    # Get allowed target types
    local allowed_types=$(jq -r ".allowed_dependencies.$entity_type[]?" "$SCRIPT_DIR/dependency-rules.json" 2>/dev/null)

    if [[ -z "$allowed_types" ]]; then
        echo "${YELLOW}No dependencies defined for $entity_type${NC}"
        return
    fi

    echo "${CYAN}Can connect to: $allowed_types${NC}"

    # Check each allowed type
    for target_type in $allowed_types; do
        # Get all entities of this type
        local targets=$(jq -r ".entities.$target_type | keys[]?" "$KNOWLEDGE_MAP" 2>/dev/null)

        for target_name in $targets; do
            # Simple similarity check - look for common words
            local entity_words=$(echo "$entity_name" | sed 's/[-_]/ /g')
            local target_words=$(echo "$target_name" | sed 's/[-_]/ /g')

            local match=false
            for e_word in $entity_words; do
                for t_word in $target_words; do
                    if [[ "${e_word:0:4}" == "${t_word:0:4}" ]] && [[ ${#e_word} -gt 3 ]]; then
                        match=true
                        break 2
                    fi
                done
            done

            if [[ "$match" == "true" ]]; then
                echo "  ${GREEN}→${NC} $target_type:$target_name"
            fi
        done
    done
}

# Connect two entities
connect_entities() {
    local source="$1"
    local target="$2"

    local source_type="${source%%:*}"
    local target_type="${target%%:*}"

    # Check if valid
    if ! is_valid_connection "$source_type" "$target_type"; then
        echo "${RED}Invalid: $source_type cannot connect to $target_type${NC}"
        return 1
    fi

    echo "${GREEN}Connecting: $source → $target${NC}"

    # Ensure source exists in graph
    if ! jq -e ".graph | has(\"$source\")" "$KNOWLEDGE_MAP" > /dev/null 2>&1; then
        jq --arg src "$source" '.graph[$src] = {"depends_on": []}' \
            "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
    fi

    # Add connection
    jq --arg src "$source" --arg tgt "$target" \
       '.graph[$src].depends_on = ((.graph[$src].depends_on // []) + [$tgt] | unique)' \
       "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"

    echo "${GREEN}✓ Connected${NC}"
}

# Simple auto-connect
auto_connect() {
    local max="${1:-5}"
    local found=0

    echo "${BLUE}Auto-connecting (up to $max connections)...${NC}"

    # Features to actions
    for feature in $(jq -r '.entities.features | keys[]?' "$KNOWLEDGE_MAP" 2>/dev/null | head -5); do
        for action in $(jq -r '.entities.actions | keys[]?' "$KNOWLEDGE_MAP" 2>/dev/null); do
            # Check if already connected
            local exists=$(jq -r ".graph[\"features:$feature\"].depends_on[]? | select(. == \"actions:$action\")" "$KNOWLEDGE_MAP" 2>/dev/null)
            [[ -n "$exists" ]] && continue

            # Simple match
            if [[ "$action" == *"${feature:0:6}"* ]] || [[ "$feature" == *"${action:0:6}"* ]]; then
                connect_entities "features:$feature" "actions:$action"
                ((found++))
                [[ $found -ge $max ]] && break 2
            fi
        done
    done

    echo "${GREEN}Created $found connections${NC}"
}

# Main command handler
main() {
    load_rules || exit 1

    case "${1:-help}" in
        --auto)
            auto_connect "${2:-5}"
            ;;
        --find)
            [[ -n "${2:-}" ]] || { echo "Usage: $0 --find <entity>"; exit 1; }
            find_connections "$2" "${3:-40}"
            ;;
        --connect)
            [[ -n "${2:-}" && -n "${3:-}" ]] || { echo "Usage: $0 --connect <source> <target>"; exit 1; }
            connect_entities "$2" "$3"
            ;;
        *)
            echo "Mac-compatible connection tool"
            echo "Usage:"
            echo "  $0 --auto [max]        # Auto-connect entities"
            echo "  $0 --find <entity>     # Find connections for entity"
            echo "  $0 --connect <src> <tgt> # Connect two entities"
            ;;
    esac
}

main "$@"