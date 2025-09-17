#!/bin/bash

# Simple Reference Usage Analysis
GRAPH_FILE="${KNOWLEDGE_MAP:-./.ai/spec-graph.json}"

echo "🔍 Reference Usage Analysis:"
echo ""

# Get all graph dependencies into a temp file
TEMP_DEPS="/tmp/deps_$$.txt"
jq -r '.graph | to_entries | map(.value.depends_on[]?) | .[]' "$GRAPH_FILE" > "$TEMP_DEPS"

# Process each reference category
for category in $(jq -r '.references | keys[]' "$GRAPH_FILE"); do
    echo "📂 $category:"

    # Check if it's an object
    if [[ $(jq --arg cat "$category" '.references[$cat] | type' "$GRAPH_FILE") == '"object"' ]]; then
        total=0
        used=0

        # Get keys and check usage
        for key in $(jq -r --arg cat "$category" '.references[$cat] | keys[]' "$GRAPH_FILE"); do
            ((total++))
            ref_id="$category:$key"

            # Simple check if ref is in dependencies
            if grep -q "^${ref_id}$" "$TEMP_DEPS"; then
                ((used++))
                echo "    ✅ $key"
            else
                echo "    ⚠️  $key (orphaned)"
            fi
        done

        echo "  📊 Total: $total | Used: $used | Orphaned: $((total - used))"
    else
        echo "  ⚠️  Not an object"
    fi
    echo ""
done

# Cleanup
rm -f "$TEMP_DEPS"

# Quick summary
echo "📈 Summary:"
total=$(jq '[.references | to_entries[] | select(.value | type == "object") | .value | keys | length] | add' "$GRAPH_FILE")
echo "  Total references defined: $total"
echo "  Run './know/know mod flatten-refs' to flatten nested structures"