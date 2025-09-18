#!/bin/bash

# Chain Validator - Validates individual dependency chains in the knowledge graph

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_FILE="${GRAPH_FILE:-$SCRIPT_DIR/../../.ai/spec-graph.json}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to validate a single chain
validate_chain() {
    local entity_id="$1"
    local visited="${2:-}"

    # Check for circular dependencies
    if [[ " $visited " == *" $entity_id "* ]]; then
        echo "CIRCULAR|Circular dependency detected at $entity_id"
        return 1
    fi

    visited="$visited $entity_id"

    # Get entity type and validate it exists
    local entity_type="${entity_id%%:*}"
    local entity_key="${entity_id#*:}"

    if ! jq -e ".entities.$entity_type[\"$entity_key\"] // false" "$GRAPH_FILE" > /dev/null 2>&1; then
        # Check if it's a reference
        if jq -e ".references.$entity_type // false" "$GRAPH_FILE" > /dev/null 2>&1; then
            echo "VALID|Reference node: $entity_id"
            return 0
        fi
        echo "INVALID|Entity not found: $entity_id"
        return 1
    fi

    # Get dependencies
    local deps=$(jq -r ".graph[\"$entity_id\"].depends_on[]? // empty" "$GRAPH_FILE" 2>/dev/null)

    if [[ -z "$deps" ]]; then
        # Terminal entity - check if it's a component
        if [[ "$entity_type" == "component" ]]; then
            # Check for behavior and data model
            echo "TERMINAL|Component without dependencies: $entity_id"
        else
            echo "TERMINAL|Entity without dependencies: $entity_id"
        fi
        return 0
    fi

    # Validate each dependency
    local all_valid=true
    for dep in $deps; do
        if ! validate_chain "$dep" "$visited"; then
            all_valid=false
        fi
    done

    if $all_valid; then
        echo "VALID|Chain valid for: $entity_id"
    else
        echo "INVALID|Invalid dependencies for: $entity_id"
    fi
}

# Function to get chain depth
get_chain_depth() {
    local entity_id="$1"
    local current_depth="${2:-0}"
    local max_depth=20

    if [[ $current_depth -gt $max_depth ]]; then
        echo "$max_depth"
        return
    fi

    local deps=$(jq -r ".graph[\"$entity_id\"].depends_on[]? // empty" "$GRAPH_FILE" 2>/dev/null)

    if [[ -z "$deps" ]]; then
        echo "$current_depth"
        return
    fi

    local deepest=$current_depth
    for dep in $deps; do
        local dep_depth=$(get_chain_depth "$dep" $((current_depth + 1)))
        if [[ $dep_depth -gt $deepest ]]; then
            deepest=$dep_depth
        fi
    done

    echo "$deepest"
}

# Main execution
if [[ $# -eq 0 ]]; then
    echo "Usage: $(basename "$0") <entity_id>"
    echo "Example: $(basename "$0") user:owner"
    exit 1
fi

ENTITY_ID="$1"

echo -e "${YELLOW}Validating chain for: $ENTITY_ID${NC}\n"

# Run validation
validation_result=$(validate_chain "$ENTITY_ID")

# Process results
while IFS='|' read -r status message; do
    case "$status" in
        VALID|TERMINAL)
            echo -e "${GREEN}✓${NC} $message"
            ;;
        INVALID)
            echo -e "${RED}✗${NC} $message"
            ;;
        CIRCULAR)
            echo -e "${RED}⚠${NC} $message"
            ;;
        *)
            echo "$message"
            ;;
    esac
done <<< "$validation_result"

# Get chain depth
depth=$(get_chain_depth "$ENTITY_ID")
echo -e "\n${YELLOW}Chain Depth:${NC} $depth levels"