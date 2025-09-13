#!/bin/bash

echo "FEATURE GAP ANALYSIS REPORT"
echo "============================"
echo

features=(
    "real-time-telemetry"
    "predictive-maintenance"
    "natural-language-interface"
    "fleet-coordination"
    "mission-automation"
    "analytics-system"
    "parts-ordering-system"
    "maintenance-alert-system"
    "ai-anomaly-detection"
)

total_features=0
complete_features=0
missing_desc=0
missing_criteria=0
isolated_features=0

for feature in "${features[@]}"; do
    total_features=$((total_features + 1))
    echo "----------------------------------------"
    echo "Feature: $feature"

    # Get resolved description
    desc=$(jq -r --arg f "feature:$feature" '.graph[$f].resolved_description // "MISSING"' spec-graph.json)
    if [[ "$desc" == "MISSING" || "$desc" == "No description available" || "$desc" == *"-desc"* ]]; then
        echo "  ❌ Description: MISSING or placeholder"
        missing_desc=$((missing_desc + 1))
    else
        echo "  ✅ Description: ${desc:0:60}..."
    fi

    # Check acceptance criteria
    criteria_count=$(jq -r --arg f "feature:$feature" '.graph[$f].acceptance_criteria // {} | keys | length' spec-graph.json)
    if [[ "$criteria_count" -eq 0 ]]; then
        echo "  ❌ Acceptance Criteria: NONE"
        missing_criteria=$((missing_criteria + 1))
    else
        echo "  ✅ Acceptance Criteria: $criteria_count categories"
        jq -r --arg f "feature:$feature" '.graph[$f].acceptance_criteria // {} | keys[] | "      - \(.)"' spec-graph.json
    fi

    # Check dependencies
    dep_count=$(jq -r --arg f "feature:$feature" '.graph[$f].outbound.depends_on // [] | length' spec-graph.json)
    if [[ "$dep_count" -eq 0 ]]; then
        echo "  ⚠️  Dependencies: NONE (isolated feature)"
        isolated_features=$((isolated_features + 1))
    else
        echo "  ✅ Dependencies: $dep_count"
        jq -r --arg f "feature:$feature" '.graph[$f].outbound.depends_on // [] | .[] | "      → \(.)"' spec-graph.json | head -5
    fi

    # Overall status
    if [[ "$desc" != "MISSING" && "$desc" != "No description available" && ! "$desc" =~ -desc && "$criteria_count" -gt 0 ]]; then
        echo "  📊 Status: COMPLETE ✅"
        complete_features=$((complete_features + 1))
    else
        echo "  📊 Status: INCOMPLETE ❌"
    fi
    echo
done

echo "========================================"
echo "SUMMARY"
echo "========================================"
echo "Total Features: $total_features"
echo "Complete Features: $complete_features"
echo "Missing Descriptions: $missing_desc"
echo "Missing Acceptance Criteria: $missing_criteria"
echo "Isolated Features (no deps): $isolated_features"
echo
echo "Completeness Score: $(( complete_features * 100 / total_features ))%"
echo

echo "========================================"
echo "RECOMMENDATIONS"
echo "========================================"
echo "1. Add proper descriptions to features with placeholders"
echo "2. Define acceptance criteria for all features"
echo "3. Connect isolated features to their dependencies"
echo "4. Priority fixes needed for:"

# List most critical gaps
jq -r '.graph | to_entries[] | select(.key | startswith("feature:")) |
    select(.value.resolved_description == null or
           .value.resolved_description == "No description available" or
           (.value.resolved_description | test("-desc"))) |
    .key' spec-graph.json | while read -r feature; do
    echo "   - $feature (missing description)"
done