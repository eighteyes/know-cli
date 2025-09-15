#!/bin/bash

echo "=== Feature Dependency Analysis ==="
echo
echo "PROBLEM: Features depend on components (implementation details)"
echo "SOLUTION: Features should depend on functionality (business capabilities)"
echo
echo "Current problematic dependencies:"
echo "================================="

for feature in real-time-telemetry predictive-maintenance natural-language-interface fleet-coordination mission-automation; do
    echo
    echo "feature:$feature depends on:"
    jq -r --arg f "feature:$feature" '.graph[$f].depends_on[]' spec-graph.json 2>/dev/null | while read dep; do
        if [[ "$dep" == component:* ]]; then
            echo "  ❌ $dep (implementation detail!)"
        elif [[ "$dep" == platform:* ]]; then
            echo "  ⚠️  $dep (platform constraint)"
        else
            echo "  ✅ $dep"
        fi
    done
done

echo
echo
echo "Available Functionality (what features SHOULD depend on):"
echo "========================================================="
jq -r '.entities.functionality | to_entries[] | "functionality:\(.key) - \(.value.name)"' spec-graph.json

echo
echo
echo "Proposed Mapping:"
echo "================="
echo "feature:real-time-telemetry      → functionality:telemetry-monitoring"
echo "feature:predictive-maintenance   → functionality:maintenance-management"
echo "feature:fleet-coordination       → functionality:fleet-management"
echo "feature:mission-automation       → functionality:mission-planning"
echo "feature:natural-language-interface → functionality:robot-control"
echo "feature:analytics-system         → functionality:analytics-insights"