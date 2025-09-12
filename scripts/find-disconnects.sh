#!/bin/bash

# Find disconnected, orphaned, and missing entities in pure dependency graph
# Usage: ./scripts/find-disconnects.sh [knowledge-map.json]

# Load jq utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/jq_utils.sh"

# Help function
show_help() {
    cat << 'EOF'
🔍 Find Disconnects - Graph Health Analyzer

USAGE:
    ./scripts/find-disconnects.sh [knowledge-map.json]
    ./scripts/find-disconnects.sh -h|--help

DESCRIPTION:
    Analyzes dependency graph for health issues including:
    • Hanging references (referenced but don't exist)
    • Orphaned entities (nothing depends on them)
    • Missing graph entries (defined but not in dependency graph)
    • Self-dependencies and circular dependencies

ARGUMENTS:
    knowledge-map.json    Path to knowledge map file (default: knowledge-map-cmd.json)

OPTIONS:
    -h, --help           Show this help message

EXAMPLES:
    ./scripts/find-disconnects.sh
    ./scripts/find-disconnects.sh my-knowledge-map.json

OUTPUT:
    Provides comprehensive health analysis with actionable recommendations
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

echo "🔍 Analyzing dependency graph: $KNOWLEDGE_MAP"
echo "=" | tr '=' '=' | head -c 60
echo

# 1. Find hanging references (dependencies that don't exist as entities)
echo "🔴 HANGING REFERENCES (referenced but don't exist):"
HANGING=$(apply_pattern "graph_health" "hanging_references" "$KNOWLEDGE_MAP" | sort)

if [[ -z "$HANGING" ]]; then
    echo "   ✅ No hanging references found"
else
    echo "$HANGING" | while read -r ref; do
        echo "   - $ref"
    done
    HANGING_COUNT=$(echo "$HANGING" | wc -l | tr -d ' ')
    echo "   📊 Total: $HANGING_COUNT hanging references"
fi

echo

# 2. Find orphaned entities (nothing depends on them)
echo "🟡 ORPHANED ENTITIES (nothing depends on them):"
ORPHANED=$(apply_pattern "graph_health" "orphaned_entities" "$KNOWLEDGE_MAP" | sort)

if [[ -z "$ORPHANED" ]]; then
    echo "   ✅ No orphaned entities found"
else
    echo "$ORPHANED" | while read -r entity; do
        echo "   - $entity"
    done
    ORPHANED_COUNT=$(echo "$ORPHANED" | wc -l | tr -d ' ')
    echo "   📊 Total: $ORPHANED_COUNT orphaned entities"
fi

echo

# 3. Find missing entities (exist in entities section but not in graph)
echo "🟠 MISSING FROM GRAPH (defined in entities but not in graph):"
MISSING_FROM_GRAPH=$(apply_pattern "graph_health" "missing_graph_entries" "$KNOWLEDGE_MAP" | sort)

if [[ -z "$MISSING_FROM_GRAPH" ]]; then
    echo "   ✅ All entities have graph entries"
else
    echo "$MISSING_FROM_GRAPH" | while read -r entity; do
        echo "   - $entity"
    done
    MISSING_GRAPH_COUNT=$(echo "$MISSING_FROM_GRAPH" | wc -l | tr -d ' ')
    echo "   📊 Total: $MISSING_GRAPH_COUNT entities missing from graph"
fi

echo

# 4. Find self-dependencies (entities that depend on themselves)
echo "🔄 SELF-DEPENDENCIES (entities depending on themselves):"
SELF_DEPS=$(apply_pattern "graph_health" "self_dependencies" "$KNOWLEDGE_MAP" | sort)

if [[ -z "$SELF_DEPS" ]]; then
    echo "   ✅ No self-dependencies found"
else
    echo "$SELF_DEPS" | while read -r entity; do
        echo "   - $entity"
    done
    SELF_COUNT=$(echo "$SELF_DEPS" | wc -l | tr -d ' ')
    echo "   📊 Total: $SELF_COUNT self-dependencies"
fi

echo

# 5. Find circular dependencies (simple 2-hop cycles)
echo "🔄 CIRCULAR DEPENDENCIES (2-hop cycles):"
CIRCULAR=$(apply_pattern "graph_health" "circular_dependencies_2hop" "$KNOWLEDGE_MAP" | sort | uniq)

if [[ -z "$CIRCULAR" ]]; then
    echo "   ✅ No 2-hop circular dependencies found"
else
    echo "$CIRCULAR" | while read -r cycle; do
        echo "   - $cycle"
    done
    CIRCULAR_COUNT=$(echo "$CIRCULAR" | wc -l | tr -d ' ')
    echo "   📊 Total: $CIRCULAR_COUNT circular dependencies"
fi

echo

# 6. Summary report
echo "📈 DEPENDENCY GRAPH HEALTH SUMMARY:"
echo "=" | tr '=' '=' | head -c 40
echo

TOTAL_ENTITIES=$(apply_pattern "graph_health" "total_entities" "$KNOWLEDGE_MAP")
TOTAL_DEPENDENCIES=$(apply_pattern "graph_health" "total_dependencies" "$KNOWLEDGE_MAP")
UNIQUE_DEPENDENCIES=$(apply_pattern "graph_health" "unique_dependencies" "$KNOWLEDGE_MAP")

echo "   📊 Total entities in graph: $TOTAL_ENTITIES"
echo "   📊 Total dependency relationships: $TOTAL_DEPENDENCIES"
echo "   📊 Unique dependencies referenced: $UNIQUE_DEPENDENCIES"

# Calculate health score
ISSUES=0
[[ -n "$HANGING" ]] && ISSUES=$((ISSUES + $(echo "$HANGING" | wc -l | tr -d ' ')))
[[ -n "$ORPHANED" ]] && ISSUES=$((ISSUES + $(echo "$ORPHANED" | wc -l | tr -d ' ')))
[[ -n "$MISSING_FROM_GRAPH" ]] && ISSUES=$((ISSUES + $(echo "$MISSING_FROM_GRAPH" | wc -l | tr -d ' ')))
[[ -n "$SELF_DEPS" ]] && ISSUES=$((ISSUES + $(echo "$SELF_DEPS" | wc -l | tr -d ' ')))
[[ -n "$CIRCULAR" ]] && ISSUES=$((ISSUES + $(echo "$CIRCULAR" | wc -l | tr -d ' ')))

echo "   🚨 Total issues found: $ISSUES"

if [[ $ISSUES -eq 0 ]]; then
    echo "   ✅ Graph health: EXCELLENT (no issues detected)"
elif [[ $ISSUES -lt 5 ]]; then
    echo "   🟡 Graph health: GOOD (minor issues)"
elif [[ $ISSUES -lt 15 ]]; then
    echo "   🟠 Graph health: FAIR (moderate issues)"
else
    echo "   🔴 Graph health: POOR (many issues need attention)"
fi

echo

# 7. Quick fix suggestions
if [[ $ISSUES -gt 0 ]]; then
    echo "🔧 QUICK FIX SUGGESTIONS:"
    echo "=" | tr '=' '=' | head -c 25
    echo
    
    if [[ -n "$HANGING" ]]; then
        echo "   1. Add missing entities to entities section or remove invalid references"
    fi
    
    if [[ -n "$ORPHANED" ]]; then
        echo "   2. Connect orphaned entities or remove if unused"
    fi
    
    if [[ -n "$MISSING_FROM_GRAPH" ]]; then
        echo "   3. Add graph entries for entities missing from dependency graph"  
    fi
    
    if [[ -n "$SELF_DEPS" ]]; then
        echo "   4. Remove self-dependencies (entities shouldn't depend on themselves)"
    fi
    
    if [[ -n "$CIRCULAR" ]]; then
        echo "   5. Break circular dependencies by removing or restructuring relationships"
    fi
fi

echo