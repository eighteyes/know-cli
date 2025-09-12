#!/bin/bash

# Calculate comprehensive dependency metrics for knowledge graph
# Usage: ./scripts/dependency-metrics.sh [knowledge-map.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
📊 Dependency Metrics - Comprehensive Graph Analysis

USAGE:
    ./scripts/dependency-metrics.sh [knowledge-map.json]
    ./scripts/dependency-metrics.sh -h|--help

DESCRIPTION:
    Calculates comprehensive dependency metrics for knowledge graphs including:
    • Basic graph statistics (entities, dependencies, fan-in/out)
    • Fan-out and fan-in distribution analysis
    • Dependency depth analysis and layering
    • Centrality metrics (degree centrality)
    • Graph clustering coefficients
    • Stability metrics (instability index)
    • Complexity indicators (cyclomatic, density)
    • Overall quality assessment with scoring

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/dependency-metrics.sh
    ./scripts/dependency-metrics.sh my-knowledge-map.json

METRIC CATEGORIES:
    Basic Statistics      - Entity/dependency counts, max fan-in/out
    Distribution Analysis - How dependencies are spread across entities
    Depth Analysis       - Dependency chain depths and layering
    Centrality Metrics   - Most important/connected entities
    Clustering Analysis  - How tightly interconnected the graph is
    Stability Metrics    - Instability index (efferent vs afferent coupling)
    Complexity Indicators - Cyclomatic complexity, density, hierarchical ratios
    Quality Assessment   - Overall health scoring (1-15 scale)

OUTPUT:
    Comprehensive metrics analysis with quality scores and ratings
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
    exit 1
fi

echo "📊 DEPENDENCY METRICS ANALYSIS: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 55
echo

# 1. Basic graph statistics
echo "📈 BASIC GRAPH STATISTICS:"
BASIC_STATS=$(apply_pattern "dependency_metrics" "basic_statistics" "$KNOWLEDGE_MAP")

echo "$BASIC_STATS" | while read -r line; do
    echo "   $line"
done

echo

# 2. Fan-out distribution (how many things each entity depends on)
echo "📤 FAN-OUT DISTRIBUTION:"
FAN_OUT_DIST=$(apply_pattern "dependency_metrics" "fan_out_distribution" "$KNOWLEDGE_MAP")

echo "   Dependencies → Entity Count"
echo "$FAN_OUT_DIST" | while IFS=$'\t' read -r deps count; do
    printf "   %12s → %s\n" "$deps" "$count"
done

echo

# 3. Fan-in distribution (how many things depend on each entity)
echo "📥 FAN-IN DISTRIBUTION:"
FAN_IN_DIST=$(apply_pattern "dependency_metrics" "fan_in_distribution" "$KNOWLEDGE_MAP")

echo "   Dependents → Entity Count"
echo "$FAN_IN_DIST" | while IFS=$'\t' read -r deps count; do
    printf "   %10s → %s\n" "$deps" "$count"
done

echo

# 4. Dependency depth analysis
echo "🏗️ DEPENDENCY DEPTH ANALYSIS:"
DEPTH_STATS=$(apply_pattern "dependency_metrics" "depth_analysis" "$KNOWLEDGE_MAP")

echo "$DEPTH_STATS" | while read -r line; do
    echo "   $line"
done

echo

# 5. Centrality metrics
echo "🎯 CENTRALITY METRICS:"

# Degree centrality (normalized)
DEGREE_CENTRALITY=$(apply_pattern "dependency_metrics" "degree_centrality" "$KNOWLEDGE_MAP")

echo "   Top 5 by degree centrality:"
echo "$DEGREE_CENTRALITY" | while read -r line; do
    echo "     $line"
done

echo

# 6. Clustering coefficient
echo "🕸️ GRAPH CLUSTERING:"
CLUSTERING=$(apply_pattern "dependency_metrics" "clustering_coefficient" "$KNOWLEDGE_MAP")

echo "$CLUSTERING" | while read -r line; do
    echo "   $line"
done

echo

# 7. Stability metrics
echo "⚖️ GRAPH STABILITY METRICS:"
STABILITY=$(apply_pattern "dependency_metrics" "stability_metrics" "$KNOWLEDGE_MAP")

echo "$STABILITY" | while read -r line; do
    echo "   $line"
done

echo

# 8. Complexity indicators
echo "🧮 COMPLEXITY INDICATORS:"
COMPLEXITY=$(apply_pattern "dependency_metrics" "complexity_indicators" "$KNOWLEDGE_MAP")

echo "$COMPLEXITY" | while read -r line; do
    echo "   $line"
done

echo

# 9. Quality assessment
echo "🏆 QUALITY ASSESSMENT:"
QUALITY=$(apply_pattern "dependency_metrics" "quality_assessment" "$KNOWLEDGE_MAP")

echo "$QUALITY" | while read -r line; do
    echo "   $line"
done

echo