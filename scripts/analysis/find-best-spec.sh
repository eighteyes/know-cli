#!/bin/bash

echo "=== FINDING BEST SPEC CANDIDATES ==="
echo

types=("features" "components" "screens" "functionality" "requirements")

for type in "${types[@]}"; do
    echo "--- Testing $type ---"

    # Get first entity of this type
    first_entity=$(./know/know list $type 2>/dev/null | head -n1 | grep -o '^[[:space:]]*[^[:space:]]*' | xargs)

    if [[ -n "$first_entity" ]]; then
        echo "Testing: $first_entity"

        # Check completeness
        ./know/know check ${type%s} "$first_entity" 2>/dev/null | grep -E "(✅|❌|⚠️)"

        # Try preview
        echo "Preview test:"
        ./know/know preview ${type%s} "$first_entity" 2>/dev/null | grep -E "(✅|❌|⚠️)" | head -3

        echo
    else
        echo "No entities found for $type"
        echo
    fi
done

echo "=== SPECIFIC CANDIDATES ==="
echo
candidates=(
    "feature:real-time-telemetry"
    "component:fleet-status-map"
    "screen:fleet-dashboard"
    "functionality:fleet-management"
)

for candidate in "${candidates[@]}"; do
    type=$(echo "$candidate" | cut -d: -f1)
    id=$(echo "$candidate" | cut -d: -f2)

    echo "--- $candidate ---"
    ./know/know check "$type" "$id" 2>/dev/null | grep -E "(✅|❌|⚠️|Status)"
    echo
done