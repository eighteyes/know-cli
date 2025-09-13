#!/bin/bash

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

for feature in "${features[@]}"; do
    echo "========================================="
    echo "FEATURE: $feature"
    echo "========================================="
    ./know/know check feature "$feature" 2>&1
    echo
    echo "Dependencies:"
    ./know/know deps "feature:$feature" 2>&1 | head -10
    echo
done