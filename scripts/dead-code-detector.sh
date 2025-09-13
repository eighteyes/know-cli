#!/bin/bash

# Detect potentially unused/dead entities in the dependency graph
# Usage: ./scripts/dead-code-detector.sh [knowledge-map.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
💀 Dead Code Detector - Unused Entity Analysis

USAGE:
    ./scripts/dead-code-detector.sh [knowledge-map.json]
    ./scripts/dead-code-detector.sh -h|--help

DESCRIPTION:
    Detects potentially unused/dead entities in dependency graphs:
    • Completely orphaned entities (dependencies but no dependents)
    • Root entities analysis (no dependents - entry points vs dead code)
    • Low utilization entities (only 1 dependent)
    • Potential utility entities (over-engineered helpers)
    • Dead-end dependency chains analysis
    • Potential duplicate functionality detection
    • Dead code statistics and risk assessment
    • Cleanup recommendations with prioritization

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: spec-graph.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/dead-code-detector.sh
    ./scripts/dead-code-detector.sh my-knowledge-map.json

DETECTION CATEGORIES:
    Orphaned Entities     - Have dependencies but no dependents (likely dead)
    Root Entities        - No dependents (entry points vs unused code)
    Low Utilization      - Only 1 dependent (consolidation candidates)
    Utility Entities     - High dependencies, few dependents (over-engineered)
    Dead-End Chains      - Dependency chains ending in unused entities
    Duplicate Patterns   - Entities with identical dependency patterns
    Risk Assessment      - Overall dead code percentage and cleanup priority

OUTPUT:
    Comprehensive dead code analysis with statistics, risk assessment, and prioritized cleanup recommendations
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

echo "💀 DEAD CODE DETECTION ANALYSIS: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 60
echo

# 1. Find completely orphaned entities (no dependents and not root-level)
echo "👻 COMPLETELY ORPHANED ENTITIES:"
ORPHANED=$(apply_pattern "dead_code_analysis" "orphaned_entities" "$KNOWLEDGE_MAP")

if [[ -z "$ORPHANED" ]]; then
    echo "   ✅ No completely orphaned entities found"
else
    echo "   🚨 Orphaned entities (have dependencies but no dependents):"
    echo "$ORPHANED" | while read -r orphan; do
        echo "     - $orphan"
    done
    ORPHANED_COUNT=$(echo "$ORPHANED" | wc -l | tr -d ' ')
    echo "   📊 Total orphaned: $ORPHANED_COUNT entities"
fi

echo

# 2. Find root entities (no dependents) - potential entry points or dead code
echo "🌱 ROOT ENTITIES (no dependents):"
ROOT_ENTITIES=$(apply_pattern "dead_code_analysis" "root_entities" "$KNOWLEDGE_MAP")

if [[ -z "$ROOT_ENTITIES" ]]; then
    echo "   ✅ No root entities found"
else
    echo "   🌱 Root entities (no dependents):"
    echo "$ROOT_ENTITIES" | while read -r entity; do
        echo "     - $entity"
    done
    ROOT_COUNT=$(echo "$ROOT_ENTITIES" | wc -l | tr -d ' ')
    echo "   📊 Total root entities: $ROOT_COUNT"
fi

echo

# 3. Find entities with very low utilization (few dependents)
echo "📉 LOW UTILIZATION ENTITIES:"
LOW_UTIL=$(apply_pattern "dead_code_analysis" "low_utilization_entities" "$KNOWLEDGE_MAP")

if [[ -z "$LOW_UTIL" ]]; then
    echo "   ✅ No low utilization entities found"
else
    echo "   ⚠️  Entities with only 1 dependent (consider consolidation):"
    echo "$LOW_UTIL" | while read -r entity; do
        echo "     - $entity"
    done
    LOW_UTIL_COUNT=$(echo "$LOW_UTIL" | wc -l | tr -d ' ')
    echo "   📊 Total low utilization: $LOW_UTIL_COUNT entities"
fi

echo

# 4. Find potential utility/helper entities (high dependencies, few dependents)
echo "🔧 POTENTIAL UTILITY ENTITIES:"
UTILITY_ENTITIES=$(apply_pattern "dead_code_analysis" "utility_entities" "$KNOWLEDGE_MAP")

if [[ -z "$UTILITY_ENTITIES" ]]; then
    echo "   ✅ No clear utility entities identified"
else
    echo "   🔧 Entities that might be over-engineered utilities:"
    echo "$UTILITY_ENTITIES" | while read -r entity; do
        echo "     - $entity"
    done
fi

echo

# 5. Analyze dependency chains ending in dead ends
echo "🕳️ DEAD-END DEPENDENCY CHAINS:"
DEAD_ENDS=$(jq -r '
def find_dead_ends($entity; $path; $visited):
    if ($visited | index($entity)) then []
    elif (.graph[$entity].depends_on // [] | length) == 0 then
        # Check if this leaf has any dependents
        [.graph | .[] | .depends_on[]?] as $all_deps |
        if ($all_deps | index($entity) | not) then [($path + [$entity])]
        else []
        end
    else
        [(.graph[$entity].depends_on // [])[] | 
         find_dead_ends(.; $path + [$entity]; $visited + [$entity])] |
        flatten(1)
    end;

# Find all dead end chains
[.graph | keys[] as $start |
 find_dead_ends($start; []; [])[] |
 select(length > 2)] |  # Only show chains of 3+ entities

# Remove duplicates and format
unique |
if length > 0 then
    .[] | join(" → ")
else empty
end
' "$KNOWLEDGE_MAP")

if [[ -z "$DEAD_ENDS" ]]; then
    echo "   ✅ No significant dead-end chains found"
else
    echo "   🕳️  Dependency chains ending in unused entities:"
    echo "$DEAD_ENDS" | while read -r chain; do
        echo "     - $chain"
    done
    DEAD_END_COUNT=$(echo "$DEAD_ENDS" | wc -l | tr -d ' ')
    echo "   📊 Total dead-end chains: $DEAD_END_COUNT"
fi

echo

# 6. Find entities that might be duplicating functionality
echo "🔄 POTENTIAL DUPLICATE FUNCTIONALITY:"
POTENTIAL_DUPES=$(apply_pattern "dead_code_analysis" "duplicate_patterns" "$KNOWLEDGE_MAP")

if [[ -z "$POTENTIAL_DUPES" ]]; then
    echo "   ✅ No entities with identical dependency patterns"
else
    echo "   🔄 Entities with identical dependency patterns (potential duplication):"
    echo "$POTENTIAL_DUPES"
fi

echo

# 7. Calculate dead code statistics
echo "📊 DEAD CODE STATISTICS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

DEAD_CODE_STATS=$(apply_pattern "dead_code_analysis" "dead_code_statistics" "$KNOWLEDGE_MAP")

echo "$DEAD_CODE_STATS" | while read -r line; do
    echo "   $line"
done

echo

# 8. Dead code risk assessment
echo "🎯 DEAD CODE RISK ASSESSMENT:"
RISK_ASSESSMENT=$(jq -r '
(.graph | keys | length) as $total_entities |
[.graph | .[] | .depends_on[]?] as $all_deps |

{
    no_dependents_count: (
        (.graph | keys) as $entities |
        [$entities[] | select($all_deps | index(.) | not)] | length
    ),
    true_orphans_count: (
        (.graph | keys) as $entities |
        [$entities[] as $entity |
         select($all_deps | index($entity) | not) |
         select((.graph[$entity].depends_on // [] | length) > 0)] | length
    ),
    total_entities: $total_entities
} |

.dead_code_percentage = ((.no_dependents_count * 100) / .total_entities) |

if .dead_code_percentage <= 5 then
    "🟢 LOW RISK: \(.dead_code_percentage | round)% entities have no dependents"
elif .dead_code_percentage <= 15 then
    "🟡 MODERATE RISK: \(.dead_code_percentage | round)% entities have no dependents" 
elif .dead_code_percentage <= 25 then
    "🟠 HIGH RISK: \(.dead_code_percentage | round)% entities have no dependents"
else
    "🔴 CRITICAL RISK: \(.dead_code_percentage | round)% entities have no dependents"
end +

"\n\nRecommendations:" +
(if .true_orphans_count > 0 then
    "\n• Review \(.true_orphans_count) true orphan(s) - likely dead code"
else ""
end) +
(if .dead_code_percentage > 15 then
    "\n• Consider regular dead code cleanup"
else ""
end) +
(if .dead_code_percentage > 25 then
    "\n• Implement automated dead code detection in CI/CD"
else ""
end) +
"\n• Verify that leaf nodes are intentional entry points" +
"\n• Consider marking public APIs to prevent false positives"
' "$KNOWLEDGE_MAP")

echo "$RISK_ASSESSMENT" | while read -r line; do
    echo "   $line"
done

echo

# 9. Cleanup recommendations
echo "🧹 CLEANUP RECOMMENDATIONS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CLEANUP_RECS=$(jq -r '
(.graph | keys | length) as $total_entities |
[.graph | .[] | .depends_on[]?] as $all_deps |

{
    true_orphans: (
        (.graph | keys) as $entities |
        [$entities[] as $entity |
         select($all_deps | index($entity) | not) |
         select((.graph[$entity].depends_on // [] | length) > 0)] | length
    ),
    low_util: (
        (.graph | keys) as $entities |
        [$entities[] as $entity |
         select(($all_deps | map(select(. == $entity)) | length) == 1)] | length
    ),
    leaves: (
        [.graph | .[] | select((.depends_on // []) | length == 0)] | length
    )
} |

[
    "1. 🎯 High Priority:",
    (if .true_orphans > 0 then "   • Remove \(.true_orphans) true orphan entities (definite dead code)" else empty end),
    "",
    "2. 🔍 Medium Priority:", 
    (if .low_util > 0 then "   • Review \(.low_util) entities with single dependents for consolidation" else empty end),
    (if .leaves > 5 then "   • Verify that \(.leaves) leaf entities are intentional endpoints" else empty end),
    "",
    "3. 🔧 Process Improvements:",
    "   • Add dependency tracking to new feature development",
    "   • Implement regular dead code analysis (monthly/quarterly)",
    "   • Consider marking public APIs to prevent false dead code detection",
    "   • Set up alerts for entities that lose all dependents"
] |
map(select(. != empty)) |
.[]
' "$KNOWLEDGE_MAP")

echo "$CLEANUP_RECS" | while read -r rec; do
    echo "   $rec"
done

echo