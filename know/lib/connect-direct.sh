#!/bin/bash

# Direct connection tool - simple and fast

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Connect two entities directly
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <source> <target>"
    echo "Example: $0 features:real-time-telemetry acceptance_criteria:real_time_telemetry"
    exit 1
fi

source="$1"
target="$2"

echo -e "${GREEN}Connecting: $source → $target${NC}"

# Ensure source node exists in graph
if ! jq -e ".graph | has(\"$source\")" "$KNOWLEDGE_MAP" > /dev/null; then
    echo "Creating graph node for $source"
    jq --arg src "$source" '.graph[$src] = {"depends_on": []}' \
        "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
fi

# Add the connection
jq --arg src "$source" --arg tgt "$target" \
   '.graph[$src].depends_on = ((.graph[$src].depends_on // []) + [$tgt] | unique)' \
   "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp" && mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"

echo -e "${GREEN}✓ Connected${NC}"

# Verify
deps=$(jq -r ".graph[\"$source\"].depends_on[]?" "$KNOWLEDGE_MAP" 2>/dev/null | wc -l)
echo -e "${GREEN}$source now has $deps dependencies${NC}"