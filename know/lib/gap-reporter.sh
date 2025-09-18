#!/bin/bash

# Gap Reporter - Generates comprehensive gap analysis reports

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_FILE="${GRAPH_FILE:-$SCRIPT_DIR/../../.ai/spec-graph.json}"
GAP_TOOL="$SCRIPT_DIR/gap-analysis.sh"
SCORER_TOOL="$SCRIPT_DIR/completeness-scorer.sh"
VALIDATOR_TOOL="$SCRIPT_DIR/chain-validator.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Output format
OUTPUT_FORMAT="${1:-text}"

# Function to generate markdown report
generate_markdown_report() {
    cat << 'EOF'
# Knowledge Graph Gap Analysis Report

## Executive Summary

This report identifies gaps between user objectives (WHAT) and system implementation (HOW).

EOF

    # Get statistics
    local total_users=$(jq -r '.entities.users | length' "$GRAPH_FILE")
    local total_objectives=$(jq -r '.entities.objectives | length' "$GRAPH_FILE")
    local total_features=$(jq -r '.entities.features | length' "$GRAPH_FILE")
    local total_components=$(jq -r '.entities.components | length' "$GRAPH_FILE")
    local components_with_deps=$(jq -r '.graph | with_entries(select(.key | startswith("component:"))) | length' "$GRAPH_FILE")

    cat << EOF
### Statistics
- **Users**: $total_users
- **Objectives**: $total_objectives
- **Features**: $total_features
- **Components**: $total_components (${components_with_deps} implemented)
- **Implementation Rate**: $(( components_with_deps * 100 / (total_components > 0 ? total_components : 1) ))%

## Gap Analysis by User

EOF

    # Analyze each user
    local users=$(jq -r '.entities.users | keys[]' "$GRAPH_FILE")
    for user in $users; do
        local user_id="user:$user"
        local user_desc=$(jq -r ".entities.users[\"$user\"].description" "$GRAPH_FILE")

        echo "### $user_id"
        echo "_${user_desc}_"
        echo ""

        # Get user objectives
        local objectives=$(jq -r ".graph[\"$user_id\"].depends_on[]? // empty" "$GRAPH_FILE" | grep "^objective:")

        if [[ -n "$objectives" ]]; then
            echo "#### Objectives:"
            for obj in $objectives; do
                local obj_key="${obj#objective:}"
                local obj_desc=$(jq -r ".entities.objectives[\"$obj_key\"].description // \"\"" "$GRAPH_FILE")
                local score=$("$SCORER_TOOL" score "$obj" 2>/dev/null | grep -oE '[0-9]+%' || echo "0%")

                echo "- **$obj** ($score complete)"
                echo "  - $obj_desc"

                # Check for missing features
                local features=$(jq -r ".graph[\"$obj\"].depends_on[]? // empty" "$GRAPH_FILE" | grep "^feature:" || true)
                if [[ -z "$features" ]]; then
                    echo "  - ⚠️ **Missing**: No features defined"
                fi
            done
        else
            echo "_No objectives defined for this user_"
        fi
        echo ""
    done

    # Gap Summary
    cat << 'EOF'
## Implementation Gaps

### Critical Gaps (Blocking User Objectives)

EOF

    # Find objectives without complete chains
    local objectives=$(jq -r '.entities.objectives | keys[]' "$GRAPH_FILE")
    for objective in $objectives; do
        local obj_id="objective:$objective"
        local chain_status=$("$GAP_TOOL" --json analyze "$obj_id" 2>/dev/null | jq -r '.chains[]' | grep -c "complete" || echo "0")

        if [[ "$chain_status" == "0" ]]; then
            echo "- **$obj_id**: No complete implementation path"

            # Find what's missing
            local has_features=$(jq -r ".graph[\"$obj_id\"].depends_on[]? // empty" "$GRAPH_FILE" | grep -c "^feature:" || echo "0")
            if [[ "$has_features" == "0" ]]; then
                echo "  - Missing: Features to implement this objective"
            else
                echo "  - Missing: Components to implement features"
            fi
        fi
    done

    cat << 'EOF'

### Partial Implementations

EOF

    # Find partially implemented features
    local features=$(jq -r '.entities.features | keys[]' "$GRAPH_FILE")
    for feature in $features; do
        local feat_id="feature:$feature"
        local score=$("$SCORER_TOOL" score "$feat_id" 2>/dev/null | grep -oE '[0-9]+' || echo "0")

        if [[ "$score" -gt 0 && "$score" -lt 80 ]]; then
            echo "- **$feat_id** (${score}% complete)"

            # Check what's missing
            local actions=$(jq -r ".graph[\"$feat_id\"].depends_on[]? // empty" "$GRAPH_FILE" | grep "^action:" || true)
            if [[ -z "$actions" ]]; then
                echo "  - Missing: Action definitions"
            else
                echo "  - Missing: Component implementations"
            fi
        fi
    done

    cat << 'EOF'

## Recommendations

### Priority 1: Complete Critical Paths

These objectives have no complete implementation and should be prioritized:

EOF

    # List top incomplete objectives
    local priority_count=0
    for objective in $objectives; do
        if [[ $priority_count -lt 5 ]]; then
            local obj_id="objective:$objective"
            local score=$("$SCORER_TOOL" score "$obj_id" 2>/dev/null | grep -oE '[0-9]+' || echo "0")

            if [[ "$score" -lt 50 ]]; then
                echo "1. **$obj_id** - Current: ${score}%"
                ((priority_count++))
            fi
        fi
    done

    cat << 'EOF'

### Priority 2: Fill Feature Gaps

These features need action and component definitions:

EOF

    # List features needing work
    local feature_count=0
    for feature in $features; do
        if [[ $feature_count -lt 5 ]]; then
            local feat_id="feature:$feature"
            local score=$("$SCORER_TOOL" score "$feat_id" 2>/dev/null | grep -oE '[0-9]+' || echo "0")

            if [[ "$score" -gt 0 && "$score" -lt 80 ]]; then
                echo "1. **$feat_id** - Current: ${score}%"
                ((feature_count++))
            fi
        fi
    done

    echo ""
    echo "---"
    echo "_Generated: $(date '+%Y-%m-%d %H:%M:%S')_"
}

# Function to generate JSON report
generate_json_report() {
    # Collect all gap data
    local users=$(jq -r '.entities.users | keys[]' "$GRAPH_FILE")
    local gaps=()

    for user in $users; do
        local user_id="user:$user"
        local objectives=$(jq -r ".graph[\"$user_id\"].depends_on[]? // empty" "$GRAPH_FILE" | grep "^objective:" || true)

        for obj in $objectives; do
            local score=$("$SCORER_TOOL" score "$obj" 2>/dev/null | grep -oE '[0-9]+' || echo "0")
            local status="incomplete"

            if [[ "$score" -ge 80 ]]; then
                status="complete"
            elif [[ "$score" -ge 50 ]]; then
                status="partial"
            fi

            gaps+=("{\"user\":\"$user_id\",\"objective\":\"$obj\",\"score\":$score,\"status\":\"$status\"}")
        done
    done

    # Build JSON output
    echo "{"
    echo "  \"generated\": \"$(date -Iseconds)\","
    echo "  \"summary\": {"

    local total_users=$(jq -r '.entities.users | length' "$GRAPH_FILE")
    local total_objectives=$(jq -r '.entities.objectives | length' "$GRAPH_FILE")
    local total_features=$(jq -r '.entities.features | length' "$GRAPH_FILE")
    local total_components=$(jq -r '.entities.components | length' "$GRAPH_FILE")

    echo "    \"users\": $total_users,"
    echo "    \"objectives\": $total_objectives,"
    echo "    \"features\": $total_features,"
    echo "    \"components\": $total_components"
    echo "  },"
    echo "  \"gaps\": ["

    local first=true
    for gap in "${gaps[@]}"; do
        if ! $first; then
            echo ","
        fi
        echo -n "    $gap"
        first=false
    done

    echo ""
    echo "  ]"
    echo "}"
}

# Function to generate text report
generate_text_report() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        Knowledge Graph Gap Analysis Report            ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Summary statistics
    echo -e "${YELLOW}📊 SUMMARY STATISTICS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━${NC}"

    local total_users=$(jq -r '.entities.users | length' "$GRAPH_FILE")
    local total_objectives=$(jq -r '.entities.objectives | length' "$GRAPH_FILE")
    local total_features=$(jq -r '.entities.features | length' "$GRAPH_FILE")
    local total_actions=$(jq -r '.entities.actions | length' "$GRAPH_FILE")
    local total_components=$(jq -r '.entities.components | length' "$GRAPH_FILE")
    local components_with_deps=$(jq -r '.graph | with_entries(select(.key | startswith("component:"))) | length' "$GRAPH_FILE")

    echo -e "  Users:         ${BLUE}$total_users${NC}"
    echo -e "  Objectives:    ${BLUE}$total_objectives${NC}"
    echo -e "  Features:      ${BLUE}$total_features${NC}"
    echo -e "  Actions:       ${BLUE}$total_actions${NC}"
    echo -e "  Components:    ${BLUE}$total_components${NC} (${GREEN}$components_with_deps${NC} implemented)"

    local impl_rate=0
    if [[ $total_components -gt 0 ]]; then
        impl_rate=$(( components_with_deps * 100 / total_components ))
    fi

    echo ""
    echo -e "  Implementation Rate: "
    if [[ $impl_rate -ge 80 ]]; then
        echo -e "    ${GREEN}$impl_rate%${NC} ████████░░"
    elif [[ $impl_rate -ge 60 ]]; then
        echo -e "    ${YELLOW}$impl_rate%${NC} ██████░░░░"
    elif [[ $impl_rate -ge 40 ]]; then
        echo -e "    ${YELLOW}$impl_rate%${NC} ████░░░░░░"
    else
        echo -e "    ${RED}$impl_rate%${NC} ██░░░░░░░░"
    fi

    echo ""
    echo -e "${YELLOW}🎯 USER OBJECTIVES ANALYSIS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Analyze each user
    local users=$(jq -r '.entities.users | keys[]' "$GRAPH_FILE")
    for user in $users; do
        local user_id="user:$user"
        local user_desc=$(jq -r ".entities.users[\"$user\"].description" "$GRAPH_FILE")

        echo ""
        echo -e "  ${CYAN}$user_id${NC}"
        echo -e "  └─ ${user_desc}"

        # Get objectives for this user
        local objectives=$(jq -r ".graph[\"$user_id\"].depends_on[]? // empty" "$GRAPH_FILE" | grep "^objective:" || true)

        if [[ -n "$objectives" ]]; then
            for obj in $objectives; do
                local obj_key="${obj#objective:}"
                local score=$("$SCORER_TOOL" score "$obj" 2>/dev/null | grep -oE '[0-9]+%' | head -1 | tr -d '%' || echo "0")

                if [[ $score -ge 80 ]]; then
                    echo -e "      ${GREEN}✓${NC} $obj (${GREEN}${score}%${NC})"
                elif [[ $score -ge 50 ]]; then
                    echo -e "      ${YELLOW}⚠${NC} $obj (${YELLOW}${score}%${NC})"
                else
                    echo -e "      ${RED}✗${NC} $obj (${RED}${score}%${NC})"
                fi
            done
        else
            echo -e "      ${RED}⚠ No objectives defined${NC}"
        fi
    done

    echo ""
    echo -e "${YELLOW}🔍 CRITICAL GAPS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━${NC}"

    # Find objectives with no implementation
    local gap_count=0
    local objectives=$(jq -r '.entities.objectives | keys[]' "$GRAPH_FILE")
    for objective in $objectives; do
        local obj_id="objective:$objective"
        local score=$("$SCORER_TOOL" score "$obj_id" 2>/dev/null | grep -oE '[0-9]+' || echo "0")

        if [[ "$score" -lt 30 ]]; then
            ((gap_count++))
            echo -e "  ${RED}Gap #$gap_count:${NC} $obj_id"

            # Identify missing pieces
            local features=$(jq -r ".graph[\"$obj_id\"].depends_on[]? // empty" "$GRAPH_FILE" | grep -c "^feature:" || echo "0")
            if [[ "$features" == "0" ]]; then
                echo -e "    └─ ${RED}Missing:${NC} Feature definitions"
            else
                echo -e "    └─ ${RED}Missing:${NC} Component implementations"
            fi
        fi
    done

    if [[ $gap_count -eq 0 ]]; then
        echo -e "  ${GREEN}✓ No critical gaps found!${NC}"
    fi

    echo ""
    echo -e "${YELLOW}📋 RECOMMENDATIONS${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━${NC}"

    if [[ $gap_count -gt 0 ]]; then
        echo -e "  ${MAGENTA}1.${NC} Address critical gaps in objective implementations"
        echo -e "  ${MAGENTA}2.${NC} Define features for objectives without them"
        echo -e "  ${MAGENTA}3.${NC} Create action specifications for features"
        echo -e "  ${MAGENTA}4.${NC} Implement components with behavior + data models"
    else
        echo -e "  ${GREEN}✓${NC} System is well-implemented!"
        echo -e "  ${MAGENTA}•${NC} Consider adding new user types or objectives"
        echo -e "  ${MAGENTA}•${NC} Review existing implementations for optimization"
    fi

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Report generated: $(date '+%Y-%m-%d %H:%M:%S')"
}

# Main execution based on format
case "$OUTPUT_FORMAT" in
    markdown|md)
        generate_markdown_report
        ;;
    json)
        generate_json_report
        ;;
    text|*)
        generate_text_report
        ;;
esac