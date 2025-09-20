#!/bin/bash

# Simple iterative connector - finds a few good connections quickly

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh" 2>/dev/null || true

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

simple_connect() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local max_connections="${2:-5}"
    local threshold="${3:-40}"
    local auto_approve="${4:-false}"

    echo -e "${BLUE}🔍 Quick connection finder${NC}"
    echo -e "${CYAN}Finding up to $max_connections connections...${NC}"

    # Store proposed connections
    local proposed_connections=""
    local found=0

    # Connect features to actions
    echo -e "${YELLOW}Checking features → actions...${NC}"
    for feature in $(jq -r '.entities.features | keys[]?' "$graph_file" 2>/dev/null | head -5); do
        for action in $(jq -r '.entities.actions | keys[]?' "$graph_file" 2>/dev/null); do
            # Check if connection already exists
            local exists=$(jq -r ".graph[\"features:$feature\"].depends_on[]? | select(. == \"actions:$action\")" "$graph_file" 2>/dev/null)
            [[ -n "$exists" ]] && continue

            # Simple keyword match
            if [[ "$action" == *"${feature:0:8}"* ]] || [[ "$feature" == *"${action:0:8}"* ]]; then
                proposed_connections="${proposed_connections}features:$feature|actions:$action\n"
                echo -e "  ${CYAN}◆${NC} features:$feature → actions:$action"
                ((found++))
                [[ $found -ge $max_connections ]] && break 2
            fi
        done
    done

    # Connect actions to components
    echo -e "${YELLOW}Checking actions → components...${NC}"
    for action in $(jq -r '.entities.actions | keys[]?' "$graph_file" 2>/dev/null | head -5); do
        for comp in $(jq -r '.entities.components | keys[]?' "$graph_file" 2>/dev/null); do
            # Check if connection already exists
            local exists=$(jq -r ".graph[\"actions:$action\"].depends_on[]? | select(. == \"components:$comp\")" "$graph_file" 2>/dev/null)
            [[ -n "$exists" ]] && continue

            # Simple keyword match
            if [[ "$comp" == *"${action:0:6}"* ]] || [[ "$action" == *"${comp:0:6}"* ]]; then
                proposed_connections="${proposed_connections}actions:$action|components:$comp\n"
                echo -e "  ${CYAN}◆${NC} actions:$action → components:$comp"
                ((found++))
                [[ $found -ge $max_connections ]] && break 2
            fi
        done
    done

    # Connect interfaces to features
    echo -e "${YELLOW}Checking interfaces → features...${NC}"
    for iface in $(jq -r '.entities.interfaces | keys[]?' "$graph_file" 2>/dev/null | head -5); do
        for feature in $(jq -r '.entities.features | keys[]?' "$graph_file" 2>/dev/null); do
            # Check if connection already exists
            local exists=$(jq -r ".graph[\"interfaces:$iface\"].depends_on[]? | select(. == \"features:$feature\")" "$graph_file" 2>/dev/null)
            [[ -n "$exists" ]] && continue

            if [[ "$feature" == *"${iface:0:6}"* ]] || [[ "$iface" == *"${feature:0:6}"* ]]; then
                proposed_connections="${proposed_connections}interfaces:$iface|features:$feature\n"
                echo -e "  ${CYAN}◆${NC} interfaces:$iface → features:$feature"
                ((found++))
                [[ $found -ge $max_connections ]] && break 2
            fi
        done
    done

    echo

    if [[ $found -eq 0 ]]; then
        echo -e "${YELLOW}No new connections found${NC}"
        return 0
    fi

    # Show summary
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Found $found potential connections${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check for auto-approval
    local apply_changes=false
    if [[ "$auto_approve" == "true" ]] || [[ "$auto_approve" == "-y" ]]; then
        apply_changes=true
        echo -e "${CYAN}Auto-applying connections...${NC}"
    else
        echo
        echo -n "Apply these connections? (y/n) "
        read -n 1 -r answer
        echo
        [[ "$answer" =~ ^[Yy]$ ]] && apply_changes=true
    fi

    if [[ "$apply_changes" == "true" ]]; then
        echo -e "${CYAN}Applying connections...${NC}"

        # Apply each connection
        local applied=0
        while IFS='|' read -r src tgt; do
            [[ -z "$src" || -z "$tgt" ]] && continue

            # Ensure source exists in graph
            if ! jq -e ".graph | has(\"$src\")" "$graph_file" > /dev/null 2>&1; then
                jq --arg s "$src" '.graph[$s] = {"depends_on": []}' \
                   "$graph_file" > "${graph_file}.tmp" && mv "${graph_file}.tmp" "$graph_file"
            fi

            # Add connection
            jq --arg s "$src" --arg t "$tgt" \
               '.graph[$s].depends_on = ((.graph[$s].depends_on // []) + [$t] | unique)' \
               "$graph_file" > "${graph_file}.tmp" && mv "${graph_file}.tmp" "$graph_file"

            echo -e "  ${GREEN}✓${NC} Connected: $src → $tgt"
            ((applied++))
        done <<< "$(echo -e "$proposed_connections")"

        echo
        echo -e "${GREEN}✅ Applied $applied connections${NC}"

        # Show graph stats
        local nodes_with_deps=$(jq '[.graph | to_entries[] | select(.value.depends_on | length > 0)] | length' "$graph_file")
        echo -e "${GREEN}Graph now has $nodes_with_deps nodes with dependencies${NC}"
    else
        echo -e "${YELLOW}Cancelled - no changes made${NC}"
    fi
}

# Check for -y flag
auto_approve=false
for arg in "$@"; do
    [[ "$arg" == "-y" ]] && auto_approve=true
done

# Run it with lower threshold for more matches
simple_connect "$KNOWLEDGE_MAP" 5 30 "$auto_approve"