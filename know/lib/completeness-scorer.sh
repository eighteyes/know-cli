#!/bin/bash

# Completeness Scorer - Calculates implementation completeness scores for entities

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_FILE="${GRAPH_FILE:-$SCRIPT_DIR/../../.ai/spec-graph.json}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to calculate entity completeness score
calculate_score() {
    local entity_id="$1"
    local entity_type="${entity_id%%:*}"

    # Get all dependencies recursively
    local all_deps=$(get_all_dependencies "$entity_id")

    # Count entity types in dependencies
    local has_features=0
    local has_actions=0
    local has_components=0
    local complete_components=0
    local total_components=0

    for dep in $all_deps; do
        local dep_type="${dep%%:*}"
        case "$dep_type" in
            feature)
                ((has_features++))
                ;;
            action)
                ((has_actions++))
                ;;
            component)
                ((total_components++))
                if is_component_complete "$dep"; then
                    ((complete_components++))
                fi
                ;;
        esac
    done

    # Calculate scores based on entity type
    local score=0
    local max_score=100

    case "$entity_type" in
        user)
            # User completeness: objectives -> features -> actions -> components
            if [[ $has_features -gt 0 ]]; then
                score=$((score + 25))
            fi
            if [[ $has_actions -gt 0 ]]; then
                score=$((score + 25))
            fi
            if [[ $total_components -gt 0 ]]; then
                if [[ $complete_components -gt 0 ]]; then
                    local component_score=$((complete_components * 50 / total_components))
                    score=$((score + component_score))
                else
                    score=$((score + 10)) # Partial credit for having components
                fi
            fi
            ;;

        objective)
            # Objective completeness: features -> actions -> components
            if [[ $has_features -gt 0 ]]; then
                score=$((score + 30))
            fi
            if [[ $has_actions -gt 0 ]]; then
                score=$((score + 30))
            fi
            if [[ $total_components -gt 0 ]]; then
                if [[ $complete_components -gt 0 ]]; then
                    local component_score=$((complete_components * 40 / total_components))
                    score=$((score + component_score))
                else
                    score=$((score + 10))
                fi
            fi
            ;;

        feature)
            # Feature completeness: actions -> components
            if [[ $has_actions -gt 0 ]]; then
                score=$((score + 40))
            fi
            if [[ $total_components -gt 0 ]]; then
                if [[ $complete_components -gt 0 ]]; then
                    local component_score=$((complete_components * 60 / total_components))
                    score=$((score + component_score))
                else
                    score=$((score + 20))
                fi
            fi
            ;;

        action)
            # Action completeness: components with behavior and models
            if [[ $total_components -gt 0 ]]; then
                if [[ $complete_components -gt 0 ]]; then
                    score=$((complete_components * 100 / total_components))
                else
                    score=25 # Has components but incomplete
                fi
            fi
            ;;

        component)
            # Component completeness: behavior + data model
            if is_component_complete "$entity_id"; then
                score=100
            elif has_partial_implementation "$entity_id"; then
                score=50
            else
                score=0
            fi
            ;;

        *)
            score=0
            ;;
    esac

    echo "$score"
}

# Function to get all dependencies recursively
get_all_dependencies() {
    local entity_id="$1"
    local visited="${2:-}"

    if [[ " $visited " == *" $entity_id "* ]]; then
        return
    fi

    visited="$visited $entity_id"

    local deps=$(jq -r ".graph[\"$entity_id\"].depends_on[]? // empty" "$GRAPH_FILE" 2>/dev/null)

    for dep in $deps; do
        echo "$dep"
        get_all_dependencies "$dep" "$visited"
    done
}

# Function to check if component is complete
is_component_complete() {
    local component_id="$1"
    local deps=$(jq -r ".graph[\"$component_id\"].depends_on[]? // empty" "$GRAPH_FILE" 2>/dev/null)

    local has_behavior=false
    local has_model=false

    for dep in $deps; do
        if [[ "$dep" == behavior:* ]] || [[ "$dep" == "business_logic:"* ]]; then
            has_behavior=true
        elif [[ "$dep" == data_models:* ]] || [[ "$dep" == "model:"* ]]; then
            has_model=true
        fi
    done

    [[ "$has_behavior" == true && "$has_model" == true ]]
}

# Function to check partial implementation
has_partial_implementation() {
    local component_id="$1"
    local deps=$(jq -r ".graph[\"$component_id\"].depends_on[]? // empty" "$GRAPH_FILE" 2>/dev/null)

    for dep in $deps; do
        if [[ "$dep" == behavior:* ]] || [[ "$dep" == data_models:* ]] ||
           [[ "$dep" == "business_logic:"* ]] || [[ "$dep" == "model:"* ]]; then
            return 0
        fi
    done
    return 1
}

# Function to generate completeness report
generate_report() {
    local entity_filter="${1:-}"

    echo -e "${CYAN}=== Completeness Score Report ===${NC}\n"

    # Score all entities
    local total_score=0
    local entity_count=0
    local results=""

    # Process users
    if [[ -z "$entity_filter" ]] || [[ "$entity_filter" == "users" ]]; then
        echo -e "${YELLOW}Users:${NC}"
        local users=$(jq -r '.entities.users | keys[]' "$GRAPH_FILE" 2>/dev/null)
        for user in $users; do
            local user_id="user:$user"
            local score=$(calculate_score "$user_id")
            total_score=$((total_score + score))
            ((entity_count++))

            if [[ $score -ge 80 ]]; then
                echo -e "  ${GREEN}✓${NC} $user_id: ${GREEN}${score}%${NC}"
            elif [[ $score -ge 50 ]]; then
                echo -e "  ${YELLOW}⚠${NC} $user_id: ${YELLOW}${score}%${NC}"
            else
                echo -e "  ${RED}✗${NC} $user_id: ${RED}${score}%${NC}"
            fi
        done
        echo ""
    fi

    # Process objectives
    if [[ -z "$entity_filter" ]] || [[ "$entity_filter" == "objectives" ]]; then
        echo -e "${YELLOW}Objectives:${NC}"
        local objectives=$(jq -r '.entities.objectives | keys[]' "$GRAPH_FILE" 2>/dev/null)
        for objective in $objectives; do
            local obj_id="objective:$objective"
            local score=$(calculate_score "$obj_id")
            total_score=$((total_score + score))
            ((entity_count++))

            if [[ $score -ge 80 ]]; then
                echo -e "  ${GREEN}✓${NC} $obj_id: ${GREEN}${score}%${NC}"
            elif [[ $score -ge 50 ]]; then
                echo -e "  ${YELLOW}⚠${NC} $obj_id: ${YELLOW}${score}%${NC}"
            else
                echo -e "  ${RED}✗${NC} $obj_id: ${RED}${score}%${NC}"
            fi
        done
        echo ""
    fi

    # Process features
    if [[ -z "$entity_filter" ]] || [[ "$entity_filter" == "features" ]]; then
        echo -e "${YELLOW}Features:${NC}"
        local features=$(jq -r '.entities.features | keys[]' "$GRAPH_FILE" 2>/dev/null)
        for feature in $features; do
            local feat_id="feature:$feature"
            local score=$(calculate_score "$feat_id")
            total_score=$((total_score + score))
            ((entity_count++))

            if [[ $score -ge 80 ]]; then
                echo -e "  ${GREEN}✓${NC} $feat_id: ${GREEN}${score}%${NC}"
            elif [[ $score -ge 50 ]]; then
                echo -e "  ${YELLOW}⚠${NC} $feat_id: ${YELLOW}${score}%${NC}"
            else
                echo -e "  ${RED}✗${NC} $feat_id: ${RED}${score}%${NC}"
            fi
        done
        echo ""
    fi

    # Calculate average
    if [[ $entity_count -gt 0 ]]; then
        local avg_score=$((total_score / entity_count))
        echo -e "${CYAN}Overall Completeness Score: ${NC}"

        if [[ $avg_score -ge 80 ]]; then
            echo -e "  ${GREEN}${avg_score}%${NC} - Excellent implementation coverage"
        elif [[ $avg_score -ge 60 ]]; then
            echo -e "  ${YELLOW}${avg_score}%${NC} - Good progress, some gaps remain"
        elif [[ $avg_score -ge 40 ]]; then
            echo -e "  ${YELLOW}${avg_score}%${NC} - Moderate implementation, significant work needed"
        else
            echo -e "  ${RED}${avg_score}%${NC} - Early stage, substantial implementation required"
        fi
    fi
}

# Main execution
case "${1:-report}" in
    score)
        if [[ -z "${2:-}" ]]; then
            echo "Usage: $(basename "$0") score <entity_id>"
            exit 1
        fi
        score=$(calculate_score "$2")
        echo -e "${CYAN}Completeness score for $2:${NC} ${score}%"
        ;;

    report)
        generate_report "${2:-}"
        ;;

    *)
        echo "Usage: $(basename "$0") [score <entity_id>|report [entity_type]]"
        echo "Examples:"
        echo "  $(basename "$0") score user:owner"
        echo "  $(basename "$0") report"
        echo "  $(basename "$0") report objectives"
        ;;
esac