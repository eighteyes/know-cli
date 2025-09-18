#!/bin/bash

# Gap Analysis Tool for Knowledge Graph
# Identifies incomplete chains from users/objectives to implemented components

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_FILE="${GRAPH_FILE:-$SCRIPT_DIR/../../.ai/spec-graph.json}"
QUERY_TOOL="$SCRIPT_DIR/query-graph.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    cat << EOF
Gap Analysis Tool for Knowledge Graph

USAGE:
  $(basename "$0") [options] <command> [args]

OPTIONS:
  --file, -f <file>    Use specified graph file (default: .ai/spec-graph.json)
  --verbose, -v        Show detailed analysis
  --json               Output results as JSON

COMMANDS:
  analyze <entity_id>   Analyze gaps for specific entity
  analyze-all          Analyze all users and objectives
  chain <entity_id>    Show complete chain analysis for entity
  summary              Show gap analysis summary
  missing              List all missing entity types in chains

EXAMPLES:
  $(basename "$0") analyze user:owner
  $(basename "$0") analyze objective:fleet-management
  $(basename "$0") analyze-all
  $(basename "$0") --json summary

EOF
    exit 0
}

# Parse command line arguments
VERBOSE=false
JSON_OUTPUT=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            ;;
        -f|--file)
            GRAPH_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

COMMAND="${1:-}"
shift || true

# Validate graph file exists
if [[ ! -f "$GRAPH_FILE" ]]; then
    echo "Error: Graph file not found: $GRAPH_FILE" >&2
    exit 1
fi

# Function to check if entity exists
entity_exists() {
    local entity_id="$1"
    local entity_type="${entity_id%%:*}"
    local entity_key="${entity_id#*:}"

    # Check if it's a plural entity type and convert to singular for entities check
    case "$entity_type" in
        user) entity_type="users" ;;
        objective) entity_type="objectives" ;;
        feature) entity_type="features" ;;
        action) entity_type="actions" ;;
        component) entity_type="components" ;;
        interface) entity_type="interfaces" ;;
        requirement) entity_type="requirements" ;;
        behavior) entity_type="behavior" ;;
    esac

    jq -e ".entities.$entity_type[\"$entity_key\"] // false" "$GRAPH_FILE" > /dev/null 2>&1
}

# Function to get entity dependencies
get_dependencies() {
    local entity_id="$1"
    jq -r ".graph[\"$entity_id\"].depends_on[]? // empty" "$GRAPH_FILE" 2>/dev/null
}

# Function to check if component is complete
is_component_complete() {
    local component_id="$1"

    # Get component's dependencies
    local deps=$(get_dependencies "$component_id")

    # Check for behavior and data model dependencies
    local has_behavior=false
    local has_model=false

    for dep in $deps; do
        if [[ "$dep" == behavior:* ]]; then
            has_behavior=true
        elif [[ "$dep" == data_models:* ]]; then
            has_model=true
        fi
    done

    if $has_behavior && $has_model; then
        echo "complete"
    elif $has_behavior || $has_model; then
        echo "partial"
    else
        echo "incomplete"
    fi
}

# Function to traverse chain and find gaps
analyze_chain() {
    local start_entity="$1"
    local current_depth="${2:-0}"
    local max_depth=10
    local chain_path="${3:-$start_entity}"

    if [[ $current_depth -gt $max_depth ]]; then
        echo "WARNING: Maximum depth reached for $start_entity" >&2
        return 1
    fi

    local entity_type="${start_entity%%:*}"
    local deps=$(get_dependencies "$start_entity")

    # If no dependencies, check if this is a terminal node
    if [[ -z "$deps" ]]; then
        # Check if it's a component
        if [[ "$entity_type" == "component" ]]; then
            local status=$(is_component_complete "$start_entity")
            echo "$chain_path|$status"
        else
            echo "$chain_path|missing_deps"
        fi
        return
    fi

    # Traverse dependencies
    local found_complete=false
    for dep in $deps; do
        local dep_type="${dep%%:*}"

        # Skip references (terminal nodes)
        if ! entity_exists "$dep"; then
            if [[ "$dep_type" == "component" ]]; then
                echo "$chain_path -> $dep|missing_component"
            fi
            continue
        fi

        # Recursive traversal
        local sub_chains=$(analyze_chain "$dep" $((current_depth + 1)) "$chain_path -> $dep")

        # Check if any sub-chain is complete
        while IFS= read -r sub_chain; do
            if [[ -n "$sub_chain" ]]; then
                echo "$sub_chain"
                if [[ "$sub_chain" == *"|complete" ]]; then
                    found_complete=true
                fi
            fi
        done <<< "$sub_chains"
    done

    # If no complete chains found at this level
    if ! $found_complete && [[ "$current_depth" == 0 ]]; then
        echo "$chain_path|no_complete_chains"
    fi
}

# Function to analyze all users and objectives
analyze_all() {
    local all_results=""
    local total_entities=0
    local complete_chains=0
    local partial_chains=0
    local incomplete_chains=0

    # Analyze all users
    local users=$(jq -r '.entities.users | keys[]' "$GRAPH_FILE" 2>/dev/null || true)
    if [[ -n "$users" ]]; then
        while IFS= read -r user; do
            local user_id="user:$user"
            local chains=$(analyze_chain "$user_id")
            all_results+="$chains"$'\n'
            ((total_entities++))

            if [[ "$chains" == *"|complete" ]]; then
                ((complete_chains++))
            elif [[ "$chains" == *"|partial" ]]; then
                ((partial_chains++))
            else
                ((incomplete_chains++))
            fi
        done <<< "$users"
    fi

    # Analyze all objectives
    local objectives=$(jq -r '.entities.objectives | keys[]' "$GRAPH_FILE" 2>/dev/null || true)
    if [[ -n "$objectives" ]]; then
        while IFS= read -r objective; do
            local objective_id="objective:$objective"
            local chains=$(analyze_chain "$objective_id")
            all_results+="$chains"$'\n'
            ((total_entities++))

            if [[ "$chains" == *"|complete" ]]; then
                ((complete_chains++))
            elif [[ "$chains" == *"|partial" ]]; then
                ((partial_chains++))
            else
                ((incomplete_chains++))
            fi
        done <<< "$objectives"
    fi

    # Output results
    if $JSON_OUTPUT; then
        jq -n \
            --arg total "$total_entities" \
            --arg complete "$complete_chains" \
            --arg partial "$partial_chains" \
            --arg incomplete "$incomplete_chains" \
            --arg chains "$all_results" \
            '{
                summary: {
                    total: $total|tonumber,
                    complete: $complete|tonumber,
                    partial: $partial|tonumber,
                    incomplete: $incomplete|tonumber
                },
                chains: ($chains | split("\n") | map(select(. != "")))
            }'
    else
        echo -e "${CYAN}=== Gap Analysis Summary ===${NC}"
        echo -e "Total Entities Analyzed: ${BLUE}$total_entities${NC}"
        echo -e "Complete Chains: ${GREEN}$complete_chains${NC}"
        echo -e "Partial Chains: ${YELLOW}$partial_chains${NC}"
        echo -e "Incomplete Chains: ${RED}$incomplete_chains${NC}"
        echo ""
        echo -e "${CYAN}=== Chain Details ===${NC}"
        echo "$all_results" | while IFS='|' read -r chain status; do
            if [[ -n "$chain" ]]; then
                case "$status" in
                    complete)
                        echo -e "${GREEN}✓${NC} $chain"
                        ;;
                    partial)
                        echo -e "${YELLOW}⚠${NC} $chain (partial implementation)"
                        ;;
                    missing_deps)
                        echo -e "${RED}✗${NC} $chain (missing dependencies)"
                        ;;
                    missing_component)
                        echo -e "${RED}✗${NC} $chain (component not found)"
                        ;;
                    no_complete_chains)
                        echo -e "${RED}✗${NC} $chain (no complete implementation)"
                        ;;
                    *)
                        echo -e "${RED}?${NC} $chain (unknown status: $status)"
                        ;;
                esac
            fi
        done
    fi
}

# Function to show gap summary
show_summary() {
    local total_users=$(jq -r '.entities.users | length' "$GRAPH_FILE")
    local total_objectives=$(jq -r '.entities.objectives | length' "$GRAPH_FILE")
    local total_features=$(jq -r '.entities.features | length' "$GRAPH_FILE")
    local total_actions=$(jq -r '.entities.actions | length' "$GRAPH_FILE")
    local total_components=$(jq -r '.entities.components | length' "$GRAPH_FILE")

    # Count components with dependencies
    local components_with_deps=$(jq -r '.graph | with_entries(select(.key | startswith("component:"))) | length' "$GRAPH_FILE")

    if $JSON_OUTPUT; then
        jq -n \
            --arg users "$total_users" \
            --arg objectives "$total_objectives" \
            --arg features "$total_features" \
            --arg actions "$total_actions" \
            --arg components "$total_components" \
            --arg components_deps "$components_with_deps" \
            '{
                entities: {
                    users: $users|tonumber,
                    objectives: $objectives|tonumber,
                    features: $features|tonumber,
                    actions: $actions|tonumber,
                    components: {
                        total: $components|tonumber,
                        with_dependencies: $components_deps|tonumber
                    }
                }
            }'
    else
        echo -e "${CYAN}=== Knowledge Graph Summary ===${NC}"
        echo -e "Users: ${BLUE}$total_users${NC}"
        echo -e "Objectives: ${BLUE}$total_objectives${NC}"
        echo -e "Features: ${BLUE}$total_features${NC}"
        echo -e "Actions: ${BLUE}$total_actions${NC}"
        echo -e "Components: ${BLUE}$total_components${NC}"
        echo -e "  └─ With Dependencies: ${GREEN}$components_with_deps${NC}"
        echo ""

        # Calculate completion percentage
        local completion_rate=0
        if [[ $total_components -gt 0 ]]; then
            completion_rate=$((components_with_deps * 100 / total_components))
        fi

        echo -e "Overall Implementation: ${YELLOW}$completion_rate%${NC}"
    fi
}

# Function to list missing entity types
list_missing() {
    echo -e "${CYAN}=== Missing Entity Analysis ===${NC}"

    # Check for objectives without features
    echo -e "\n${YELLOW}Objectives without Features:${NC}"
    jq -r '.entities.objectives | keys[]' "$GRAPH_FILE" | while read -r objective; do
        local obj_id="objective:$objective"
        local deps=$(get_dependencies "$obj_id")
        local has_feature=false

        for dep in $deps; do
            if [[ "$dep" == feature:* ]]; then
                has_feature=true
                break
            fi
        done

        if ! $has_feature; then
            echo "  - $obj_id"
        fi
    done

    # Check for features without actions
    echo -e "\n${YELLOW}Features without Actions:${NC}"
    jq -r '.entities.features | keys[]' "$GRAPH_FILE" | while read -r feature; do
        local feat_id="feature:$feature"
        local deps=$(get_dependencies "$feat_id")
        local has_action=false

        for dep in $deps; do
            if [[ "$dep" == action:* ]]; then
                has_action=true
                break
            fi
        done

        if ! $has_action; then
            echo "  - $feat_id"
        fi
    done

    # Check for actions without components
    echo -e "\n${YELLOW}Actions without Components:${NC}"
    jq -r '.entities.actions | keys[]' "$GRAPH_FILE" | while read -r action; do
        local act_id="action:$action"
        local deps=$(get_dependencies "$act_id")
        local has_component=false

        for dep in $deps; do
            if [[ "$dep" == component:* ]]; then
                has_component=true
                break
            fi
        done

        if ! $has_component; then
            echo "  - $act_id"
        fi
    done
}

# Main command execution
case "$COMMAND" in
    analyze)
        ENTITY_ID="${1:-}"
        if [[ -z "$ENTITY_ID" ]]; then
            echo "Error: Entity ID required" >&2
            exit 1
        fi

        if ! entity_exists "$ENTITY_ID"; then
            echo "Error: Entity not found: $ENTITY_ID" >&2
            exit 1
        fi

        echo -e "${CYAN}Analyzing gaps for: $ENTITY_ID${NC}\n"
        analyze_chain "$ENTITY_ID"
        ;;

    analyze-all)
        analyze_all
        ;;

    chain)
        ENTITY_ID="${1:-}"
        if [[ -z "$ENTITY_ID" ]]; then
            echo "Error: Entity ID required" >&2
            exit 1
        fi

        echo -e "${CYAN}Chain analysis for: $ENTITY_ID${NC}\n"
        analyze_chain "$ENTITY_ID"
        ;;

    summary)
        show_summary
        ;;

    missing)
        list_missing
        ;;

    *)
        echo "Error: Unknown command: $COMMAND" >&2
        show_usage
        ;;
esac