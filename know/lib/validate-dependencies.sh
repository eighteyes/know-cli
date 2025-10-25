#!/bin/bash

# Dependency chain validation for spec-graph
# Based on CLAUDE.md dependency map

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FILE="${SCRIPT_DIR}/../config/dependency-rules.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default graph file
GRAPH_FILE="${1:-.ai/spec-graph.json}"

# Check if files exist
if [[ ! -f "$GRAPH_FILE" ]]; then
    echo -e "${RED}[ERROR]${NC} Graph file not found: $GRAPH_FILE" >&2
    exit 1
fi

if [[ ! -f "$RULES_FILE" ]]; then
    echo -e "${RED}[ERROR]${NC} Dependency rules file not found: $RULES_FILE" >&2
    exit 1
fi

echo "Validating dependency chains in $GRAPH_FILE"
echo "Using rules from: $RULES_FILE"
echo ""

violations=0
total_edges=0

# Process each edge in the graph
while IFS='|' read -r from_node to_node; do
    # Skip empty lines
    [[ -z "$from_node" || -z "$to_node" ]] && continue

    ((total_edges++))

    # Extract type from node (e.g., "user:owner" -> "user")
    from_type=$(echo "$from_node" | cut -d: -f1)
    to_type=$(echo "$to_node" | cut -d: -f1)

    # Normalize plural to singular
    from_type=${from_type%s}
    to_type=${to_type%s}

    # Map entity types to dependency rule types
    case "$from_type" in
        screen|ui_component) from_type="interface" ;;
        data_model) from_type="data_models" ;;
        platform) from_type="platforms" ;;
    esac

    case "$to_type" in
        screen|ui_component) to_type="interface" ;;
        data_model) to_type="data_models" ;;
        platform) to_type="platforms" ;;
    esac

    # Check if from_type has dependency rules
    if jq -e ".allowed_dependencies.\"$from_type\"" "$RULES_FILE" >/dev/null 2>&1; then
        # Check if the dependency is allowed
        if ! jq -e ".allowed_dependencies.\"$from_type\" | index(\"$to_type\")" "$RULES_FILE" >/dev/null 2>&1; then
            echo -e "${RED}[VIOLATION]${NC} $from_node -> $to_node"
            echo "  └─ $from_type cannot depend on $to_type"
            ((violations++))
        fi
    fi
done < <(jq -r '.graph | to_entries[] | .key as $from | .value.depends_on[]? | $from + "|" + .' "$GRAPH_FILE" 2>/dev/null)

# Summary
echo ""
echo "========================================="
echo "Dependency Validation Summary"
echo "========================================="
if [[ $violations -eq 0 ]]; then
    echo -e "${GREEN}✓ All $total_edges dependencies follow allowed patterns${NC}"
else
    echo -e "${RED}✗ Found $violations violations out of $total_edges dependencies${NC}"
    echo ""
    echo "Fix violations by reversing dependencies or updating the graph structure"
    echo "according to the dependency map in CLAUDE.md:"
    echo ""
    echo "  HOW: Project → Requirements → Interface → Feature → Action → Component → (UI + Data Models)"
    echo "  WHAT: Project → User → Objectives → Actions"
    echo "  Integration: User → Requirements, Objectives → Features, Actions → Components"
fi

exit $violations