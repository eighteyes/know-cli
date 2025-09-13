#!/bin/bash

# Check external dependencies in knowledge graph
# Usage: ./scripts/check-externals.sh [knowledge-map.json]

KNOWLEDGE_MAP="${1:-spec-graph.json}"

echo "🔍 External Dependencies Analysis"
echo "================================="

# Find all external dependencies
EXTERNALS=$(jq -r '
[.graph | .[] | .depends_on[]?] | 
unique[] | 
select(startswith("external:"))
' "$KNOWLEDGE_MAP" | sort)

if [[ -z "$EXTERNALS" ]]; then
    echo "✅ No external dependencies found"
    exit 0
fi

echo "Found external dependencies:"
echo "$EXTERNALS" | nl -w2 -s'. '
echo

# Analyze usage
echo "📊 External Dependency Usage:"
echo "$EXTERNALS" | while read -r ext; do
    count=$(jq -r --arg ext "$ext" '
    [.graph | .[] | .depends_on[]? | select(. == $ext)] | length
    ' "$KNOWLEDGE_MAP")
    
    users=$(jq -r --arg ext "$ext" '
    .graph | to_entries[] | 
    select(.value.depends_on[]? == $ext) | 
    .key
    ' "$KNOWLEDGE_MAP" | tr '\n' ', ' | sed 's/,$//')
    
    echo "  $ext: used by $count entities ($users)"
done

echo
echo "🔧 Recommendations:"
echo "- Document version requirements for external:* dependencies"  
echo "- Monitor external service availability"
echo "- Consider fallback strategies for critical externals"