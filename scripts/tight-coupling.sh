#!/bin/bash

# Find tightly coupled components and strongly connected components in knowledge graph
# Usage: ./scripts/tight-coupling.sh [knowledge-map.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
🔗 Tight Coupling Detector - Dependency Coupling Analysis

USAGE:
    ./scripts/tight-coupling.sh [knowledge-map.json]
    ./scripts/tight-coupling.sh -h|--help

DESCRIPTION:
    Analyzes tight coupling patterns in dependency graphs to identify:
    • Bidirectional dependencies (mutual coupling)
    • Strongly connected components (circular dependencies)
    • High fan-in entities (dependency magnets)
    • High fan-out entities (dependency consumers)
    • Overall coupling metrics and health assessment
    • Decoupling recommendations

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: spec-graph.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/tight-coupling.sh
    ./scripts/tight-coupling.sh my-knowledge-map.json

ANALYSIS TYPES:
    Bidirectional Dependencies   - A depends on B AND B depends on A
    Strongly Connected Components - Circular dependency chains of any length
    High Fan-In (3+ dependents)  - Entities many others depend on
    High Fan-Out (5+ dependencies) - Entities that depend on many others
    Coupling Metrics             - Afferent/efferent coupling averages
    Health Assessment            - Overall coupling quality grading

OUTPUT:
    Coupling analysis with metrics, health assessment, and decoupling recommendations
EOF
}

# Check for help flag
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

KNOWLEDGE_MAP="${1:-spec-graph.json}"

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "❌ Knowledge map file not found: $KNOWLEDGE_MAP"
    exit 1
fi

echo "🔗 TIGHT COUPLING ANALYSIS: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 50
echo

# 1. Find bidirectional dependencies (mutual coupling)
echo "🔄 BIDIRECTIONAL DEPENDENCIES (mutual coupling):"
BIDIRECTIONAL=$(apply_pattern "coupling_analysis" "bidirectional_deps" "$KNOWLEDGE_MAP")

if [[ -z "$BIDIRECTIONAL" ]]; then
    echo "   ✅ No bidirectional dependencies found"
else
    echo "$BIDIRECTIONAL" | while read -r pair; do
        echo "   - $pair"
    done
    BIDIRECTIONAL_COUNT=$(echo "$BIDIRECTIONAL" | wc -l | tr -d ' ')
    echo "   📊 Total bidirectional pairs: $BIDIRECTIONAL_COUNT"
fi

echo

# 2. Find strongly connected components (cycles of any length)
echo "🌀 STRONGLY CONNECTED COMPONENTS:"
SCC=$(apply_pattern "graph_health" "circular_dependencies_2hop" "$KNOWLEDGE_MAP" 2>/dev/null)

if [[ -z "$SCC" ]]; then
    echo "   ✅ No strongly connected components found"
else
    echo "$SCC" | while read -r component; do
        echo "   - $component"
    done
    SCC_COUNT=$(echo "$SCC" | wc -l | tr -d ' ')
    echo "   📊 Total strongly connected components: $SCC_COUNT"
fi

echo

# 3. Find high fan-in entities (many things depend on them)
echo "📥 HIGH FAN-IN ENTITIES (dependency magnets):"
FAN_IN=$(apply_pattern "coupling_analysis" "high_fan_in" "$KNOWLEDGE_MAP")

if [[ -z "$FAN_IN" ]]; then
    echo "   ✅ No high fan-in entities found (threshold: 3+)"
else
    echo "$FAN_IN" | while IFS=$'\t' read -r count entity; do
        echo "   $count dependents: $entity"
    done
fi

echo

# 4. Find high fan-out entities (depend on many things)  
echo "📤 HIGH FAN-OUT ENTITIES (dependency consumers):"
FAN_OUT=$(apply_pattern "coupling_analysis" "high_fan_out" "$KNOWLEDGE_MAP" | sort -nr)

if [[ -z "$FAN_OUT" ]]; then
    echo "   ✅ No high fan-out entities found (threshold: 5+)"
else
    echo "$FAN_OUT" | while IFS=$'\t' read -r count entity; do
        echo "   $count dependencies: $entity"
    done
fi

echo

# 5. Calculate coupling metrics
echo "📊 COUPLING METRICS:"
echo "=" | tr '=' '=' | head -c 20
echo

TOTAL_ENTITIES=$(apply_pattern "graph_health" "total_entities" "$KNOWLEDGE_MAP")
TOTAL_DEPS=$(apply_pattern "graph_health" "total_dependencies" "$KNOWLEDGE_MAP")

# Afferent coupling (Ca) - things that depend on this entity
AFFERENT_COUPLING=$(apply_pattern "coupling_analysis" "afferent_coupling" "$KNOWLEDGE_MAP")

# Efferent coupling (Ce) - things this entity depends on
EFFERENT_COUPLING=$(apply_pattern "coupling_analysis" "efferent_coupling" "$KNOWLEDGE_MAP")

printf "   📈 Average afferent coupling (Ca): %.2f\n" "$AFFERENT_COUPLING"
printf "   📈 Average efferent coupling (Ce): %.2f\n" "$EFFERENT_COUPLING"

if [[ $TOTAL_ENTITIES -gt 0 ]]; then
    COUPLING_RATIO=$(echo "scale=2; $TOTAL_DEPS / $TOTAL_ENTITIES" | bc 2>/dev/null || echo "0")
    echo "   📈 Overall coupling ratio: $COUPLING_RATIO"
fi

# Calculate tightly coupled clusters
TIGHT_CLUSTERS=$(echo "$BIDIRECTIONAL" | wc -l | tr -d ' ')
if [[ -n "$SCC" ]]; then
    SCC_CLUSTERS=$(echo "$SCC" | wc -l | tr -d ' ')
else
    SCC_CLUSTERS=0
fi

TOTAL_COUPLING_ISSUES=$((TIGHT_CLUSTERS + SCC_CLUSTERS))

echo "   🔗 Bidirectional coupling pairs: $TIGHT_CLUSTERS"
echo "   🌀 Strongly connected components: $SCC_CLUSTERS"
echo "   🚨 Total coupling issues: $TOTAL_COUPLING_ISSUES"

echo

# 6. Coupling health assessment
echo "🏥 COUPLING HEALTH ASSESSMENT:"
if [[ $TOTAL_COUPLING_ISSUES -eq 0 ]]; then
    echo "   ✅ EXCELLENT - No tight coupling detected"
elif [[ $TOTAL_COUPLING_ISSUES -le 2 ]]; then
    echo "   🟡 GOOD - Minor coupling issues"
elif [[ $TOTAL_COUPLING_ISSUES -le 5 ]]; then
    echo "   🟠 MODERATE - Some coupling concerns"
else
    echo "   🔴 POOR - Significant coupling problems"
fi

# 7. Decoupling recommendations
if [[ $TOTAL_COUPLING_ISSUES -gt 0 ]]; then
    echo
    echo "🔧 DECOUPLING RECOMMENDATIONS:"
    echo "=" | tr '=' '=' | head -c 30
    echo
    
    if [[ $TIGHT_CLUSTERS -gt 0 ]]; then
        echo "   1. Break bidirectional dependencies using:"
        echo "      - Dependency injection"
        echo "      - Event-driven patterns"
        echo "      - Interface segregation"
    fi
    
    if [[ $SCC_CLUSTERS -gt 0 ]]; then
        echo "   2. Resolve circular dependencies by:"
        echo "      - Extracting shared interfaces"
        echo "      - Creating intermediate layers"
        echo "      - Using observer patterns"
    fi
    
    if [[ -n "$FAN_IN" ]]; then
        echo "   3. Reduce high fan-in by splitting responsibilities"
    fi
    
    if [[ -n "$FAN_OUT" ]]; then
        echo "   4. Reduce high fan-out using facade patterns"
    fi
fi

echo