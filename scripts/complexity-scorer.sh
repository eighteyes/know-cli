#!/bin/bash

# Score complexity of entities and overall graph architecture
# Usage: ./scripts/complexity-scorer.sh [knowledge-map.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
🧮 Complexity Scorer - Architecture Complexity Analysis

USAGE:
    ./scripts/complexity-scorer.sh [knowledge-map.json]
    ./scripts/complexity-scorer.sh -h|--help

DESCRIPTION:
    Analyzes and scores complexity of entities and overall graph architecture:
    • Entity-level complexity scoring (weighted by dependencies, dependents, depth)
    • Complexity categorization (Simple, Moderate, Complex, Critical)
    • Architectural complexity metrics (depth, fan-out, density, cyclomatic)
    • Complexity hotspots identification
    • Overall complexity assessment with A-F grading
    • Complexity reduction recommendations

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/complexity-scorer.sh
    ./scripts/complexity-scorer.sh my-knowledge-map.json

OUTPUT:
    Complexity analysis with scores, grades, and optimization recommendations
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

echo "🧮 COMPLEXITY SCORING ANALYSIS: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 55
echo

# 1. Entity-level complexity scoring
echo "🔍 ENTITY COMPLEXITY SCORES:"
ENTITY_SCORES=$(apply_pattern "complexity_analysis" "entity_complexity_scores" "$KNOWLEDGE_MAP")

echo "   Score  Entity                          (Details)"
echo "   -----  ------                          ---------"
echo "$ENTITY_SCORES" | while IFS=$'\t' read -r score entity details; do
    printf "   %5.1f  %-30s %s\n" "$score" "$entity" "$details"
done

echo

# 2. Complexity categorization
echo "📊 COMPLEXITY CATEGORIES:"
COMPLEXITY_CATEGORIES=$(apply_pattern "complexity_analysis" "complexity_categories" "$KNOWLEDGE_MAP")

echo "$COMPLEXITY_CATEGORIES" | while read -r line; do
    echo "   $line"
done

echo

# 3. Architectural complexity metrics
echo "🏗️ ARCHITECTURAL COMPLEXITY:"
ARCH_COMPLEXITY=$(apply_pattern "complexity_analysis" "architectural_complexity" "$KNOWLEDGE_MAP")

echo "$ARCH_COMPLEXITY" | while read -r line; do
    echo "   $line"
done

echo

# 4. Complexity trends and hotspots
echo "🌡️ COMPLEXITY HOTSPOTS:"
HOTSPOTS=$(apply_pattern "complexity_analysis" "complexity_hotspots" "$KNOWLEDGE_MAP")

echo "   Impact  Entity"
echo "   ------  ------"
echo "$HOTSPOTS" | while IFS=$'\t' read -r impact entity; do
    printf "   %6s  %s\n" "$impact" "$entity"
done

echo

# 5. Overall complexity assessment
echo "🎯 OVERALL COMPLEXITY ASSESSMENT:"
ASSESSMENT=$(apply_pattern "complexity_analysis" "overall_assessment" "$KNOWLEDGE_MAP")

echo "$ASSESSMENT" | while read -r line; do
    echo "   $line"
done

echo

# 6. Complexity reduction recommendations
echo "💡 COMPLEXITY REDUCTION RECOMMENDATIONS:"
RECOMMENDATIONS=$(apply_pattern "complexity_analysis" "reduction_recommendations" "$KNOWLEDGE_MAP")

if [[ -z "$RECOMMENDATIONS" ]]; then
    echo "   ✅ Architecture complexity is within acceptable ranges"
else
    echo "$RECOMMENDATIONS" | while read -r rec; do
        echo "   $rec"
    done
fi

echo