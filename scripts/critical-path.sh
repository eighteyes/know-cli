#!/bin/bash

# Find critical paths and longest dependency chains in knowledge graph
# Usage: ./scripts/critical-path.sh [knowledge-map.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
🎯 Critical Path Analyzer

USAGE:
    ./scripts/critical-path.sh [knowledge-map.json]
    ./scripts/critical-path.sh -h|--help

DESCRIPTION:
    Analyzes critical paths and bottlenecks in dependency graph:
    • Longest dependency chains and maximum depth
    • Critical bottlenecks (most depended upon entities)
    • Entities on critical paths (highest impact)
    • Fan-out champions (entities with most dependencies)
    • Complexity assessment and optimization recommendations

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/critical-path.sh
    ./scripts/critical-path.sh my-knowledge-map.json

OUTPUT:
    Critical path analysis with complexity scoring and optimization suggestions
EOF
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-knowledge-map-cmd.json}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    echo "💡 Use -h for help"
    exit 1
fi

echo "🎯 CRITICAL PATH ANALYSIS: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 50
echo


# 1. Find longest dependency chains
echo "📏 LONGEST DEPENDENCY CHAINS:"
CHAIN_DATA=$(apply_pattern "critical_path_analysis" "max_dependency_depth" "$KNOWLEDGE_MAP")

echo "$CHAIN_DATA" | while IFS=$'\t' read -r depth entity; do
    echo "   $depth levels: $entity"
done

MAX_DEPTH=$(echo "$CHAIN_DATA" | head -1 | cut -f1)
echo "   📊 Maximum dependency depth: $MAX_DEPTH levels"

echo

# 2. Find critical bottlenecks (entities with most dependents)
echo "🚧 CRITICAL BOTTLENECKS (most depended upon):"
BOTTLENECKS=$(apply_pattern "critical_path_analysis" "critical_bottlenecks" "$KNOWLEDGE_MAP")

if [[ -z "$BOTTLENECKS" ]]; then
    echo "   ✅ No significant bottlenecks found"
else
    echo "$BOTTLENECKS" | while IFS=$'\t' read -r count entity; do
        echo "   $count dependents: $entity"
    done
fi

echo

# 3. Find entities on critical paths (part of longest chains)
echo "⚡ ENTITIES ON CRITICAL PATHS:"
CRITICAL_ENTITIES=$(apply_pattern "critical_path_analysis" "critical_path_entities" "$KNOWLEDGE_MAP")

if [[ -z "$CRITICAL_ENTITIES" ]]; then
    echo "   ✅ No critical path entities identified"
else
    echo "$CRITICAL_ENTITIES" | while read -r entity; do
        echo "   - $entity"
    done
    CRITICAL_COUNT=$(echo "$CRITICAL_ENTITIES" | wc -l | tr -d ' ')
    echo "   📊 Total critical path entities: $CRITICAL_COUNT"
fi

echo

# 4. Find fan-out champions (entities with most direct dependencies)
echo "🌟 FAN-OUT CHAMPIONS (depend on most things):"
FAN_OUT=$(apply_pattern "critical_path_analysis" "fan_out_champions" "$KNOWLEDGE_MAP" | sort -nr | head -10)

if [[ -z "$FAN_OUT" ]]; then
    echo "   ✅ No entities with dependencies found"
else
    echo "$FAN_OUT" | while IFS=$'\t' read -r count entity; do
        echo "   $count dependencies: $entity"
    done
fi

echo

# 5. Path analysis summary
echo "📊 CRITICAL PATH SUMMARY:"
echo "=" | tr '=' '=' | head -c 30
echo

SUMMARY_STATS=$(apply_pattern "critical_path_analysis" "summary_stats" "$KNOWLEDGE_MAP")
TOTAL_ENTITIES=$(echo "$SUMMARY_STATS" | jq -r '.total_entities')
ENTITIES_WITH_DEPS=$(echo "$SUMMARY_STATS" | jq -r '.entities_with_deps')
AVG_DEPENDENCIES=$(echo "$SUMMARY_STATS" | jq -r '.avg_dependencies')

echo "   📈 Total entities: $TOTAL_ENTITIES"
echo "   📈 Entities with dependencies: $ENTITIES_WITH_DEPS"
printf "   📈 Average dependencies per entity: %.2f\n" "$AVG_DEPENDENCIES"
echo "   📈 Maximum dependency chain length: $MAX_DEPTH"

# Calculate complexity score
if [[ $MAX_DEPTH -le 3 ]]; then
    COMPLEXITY="🟢 LOW"
elif [[ $MAX_DEPTH -le 6 ]]; then
    COMPLEXITY="🟡 MODERATE"  
elif [[ $MAX_DEPTH -le 10 ]]; then
    COMPLEXITY="🟠 HIGH"
else
    COMPLEXITY="🔴 EXTREME"
fi

echo "   🎯 Dependency complexity: $COMPLEXITY ($MAX_DEPTH levels)"

echo

# 6. Optimization suggestions
if [[ $MAX_DEPTH -gt 5 ]]; then
    echo "🔧 OPTIMIZATION SUGGESTIONS:"
    echo "=" | tr '=' '=' | head -c 25
    echo
    echo "   1. Consider breaking down entities with deep dependency chains"
    echo "   2. Look for opportunities to reduce transitive dependencies"
    echo "   3. Consider creating intermediate abstraction layers"
    if [[ -n "$CRITICAL_ENTITIES" ]]; then
        echo "   4. Focus optimization efforts on critical path entities"
    fi
fi

echo