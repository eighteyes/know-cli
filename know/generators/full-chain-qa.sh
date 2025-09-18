#!/bin/bash

# Interactive QA workflow for creating complete entity chains
# Guides users through the entire path from User → Objectives → Features → Actions → Components

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"
GRAPH_FILE="${GRAPH_FILE:-$SCRIPT_DIR/../../.ai/spec-graph.json}"
MOD_TOOL="$LIB_DIR/mod-graph.sh"
GAP_TOOL="$LIB_DIR/gap-analysis.sh"
SCORER_TOOL="$LIB_DIR/completeness-scorer.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

# Banner
show_banner() {
    clear
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════"
    echo "       Complete Implementation Chain Builder               "
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo -e "${YELLOW}This wizard guides you through creating a complete"
    echo -e "implementation chain from users to working components.${NC}\n"
    echo -e "${BOLD}Chain Structure:${NC}"
    echo -e "  ${BLUE}User${NC} → ${GREEN}Objectives${NC} → ${YELLOW}Features${NC} → ${MAGENTA}Actions${NC} → ${RED}Components${NC}"
    echo ""
}

# Function to prompt for user input
prompt() {
    local question="$1"
    local var_name="$2"
    local default="${3:-}"

    if [[ -n "$default" ]]; then
        echo -e "${CYAN}$question${NC} [${YELLOW}$default${NC}]: "
    else
        echo -e "${CYAN}$question${NC}: "
    fi

    read -r response
    if [[ -z "$response" && -n "$default" ]]; then
        eval "$var_name='$default'"
    else
        eval "$var_name='$response'"
    fi
}

# Function to prompt yes/no
confirm() {
    local question="$1"
    echo -e "${CYAN}$question${NC} [y/N]: "
    read -r response
    [[ "$response" =~ ^[Yy]$ ]]
}

# Function to convert to kebab-case
to_kebab_case() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' _' '--' | tr -d '.,!?'
}

# Function to show progress
show_progress() {
    local step="$1"
    local total="5"

    echo ""
    echo -e "${BOLD}Progress:${NC}"
    echo -n "["

    for i in $(seq 1 5); do
        if [[ $i -le $step ]]; then
            echo -n "█"
        else
            echo -n "░"
        fi
    done

    echo "] Step $step/$total"
    echo ""
}

# Step 1: Create User
create_user_step() {
    show_progress 1
    echo -e "${BOLD}${BLUE}Step 1: Define User Type${NC}"
    echo -e "${YELLOW}Who will use this system?${NC}\n"

    prompt "User role/type (e.g., admin, operator, customer)" user_name ""
    if [[ -z "$user_name" ]]; then
        echo "User creation cancelled."
        return 1
    fi

    local user_key=$(to_kebab_case "$user_name")
    prompt "Describe this user's role" user_desc "$user_name who interacts with the system"

    # Check if user already exists
    if jq -e ".entities.users[\"$user_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
        echo -e "${YELLOW}ℹ User 'user:$user_key' already exists${NC}"
    else
        # Add user entity
        "$MOD_TOOL" add entity users "$user_key" "$user_desc" > /dev/null 2>&1
        echo -e "${GREEN}✓ Created user: user:$user_key${NC}"
    fi

    echo "$user_key"
}

# Step 2: Create Objectives
create_objectives_step() {
    local user_key="$1"
    show_progress 2
    echo -e "${BOLD}${GREEN}Step 2: Define Objectives${NC}"
    echo -e "${YELLOW}What does user:$user_key want to achieve?${NC}\n"
    echo -e "Enter 2-3 main objectives (high-level goals):"

    local objectives=()
    local count=1

    while [[ $count -le 3 ]]; do
        prompt "Objective #$count" objective ""
        if [[ -z "$objective" ]]; then
            if [[ $count -eq 1 ]]; then
                echo -e "${RED}At least one objective is required${NC}"
                continue
            else
                break
            fi
        fi

        local obj_key=$(to_kebab_case "$objective")
        local obj_desc="$objective"

        # Add objective if not exists
        if ! jq -e ".entities.objectives[\"$obj_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
            "$MOD_TOOL" add entity objectives "$obj_key" "$obj_desc" > /dev/null 2>&1
            echo -e "${GREEN}✓ Created objective: objective:$obj_key${NC}"
        else
            echo -e "${YELLOW}ℹ Using existing objective: objective:$obj_key${NC}"
        fi

        # Link user to objective
        "$MOD_TOOL" add graph-link "user:$user_key" "objective:$obj_key" > /dev/null 2>&1
        echo -e "${GREEN}✓ Linked user:$user_key → objective:$obj_key${NC}"

        objectives+=("$obj_key")
        ((count++))
    done

    printf '%s\n' "${objectives[@]}"
}

# Step 3: Create Features
create_features_step() {
    local objectives=("$@")
    show_progress 3
    echo -e "${BOLD}${YELLOW}Step 3: Define Features${NC}"
    echo -e "${YELLOW}What features implement these objectives?${NC}\n"

    local all_features=()

    for obj_key in "${objectives[@]}"; do
        echo -e "\n${CYAN}For objective:$obj_key:${NC}"
        local obj_desc=$(jq -r ".entities.objectives[\"$obj_key\"].description" "$GRAPH_FILE")
        echo -e "  ${obj_desc}"
        echo -e "\nWhat feature(s) enable this objective?"

        local feature_count=1
        while [[ $feature_count -le 2 ]]; do
            prompt "Feature #$feature_count (or press Enter to skip)" feature ""
            if [[ -z "$feature" ]]; then
                if [[ $feature_count -eq 1 ]]; then
                    echo -e "${YELLOW}⚠ Skipping features for this objective${NC}"
                fi
                break
            fi

            local feat_key=$(to_kebab_case "$feature")
            local feat_desc="$feature"

            # Add feature if not exists
            if ! jq -e ".entities.features[\"$feat_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
                "$MOD_TOOL" add entity features "$feat_key" "$feat_desc" > /dev/null 2>&1
                echo -e "${GREEN}✓ Created feature: feature:$feat_key${NC}"
            else
                echo -e "${YELLOW}ℹ Using existing feature: feature:$feat_key${NC}"
            fi

            # Link objective to feature
            "$MOD_TOOL" add graph-link "objective:$obj_key" "feature:$feat_key" > /dev/null 2>&1
            echo -e "${GREEN}✓ Linked objective:$obj_key → feature:$feat_key${NC}"

            all_features+=("$feat_key")
            ((feature_count++))
        done
    done

    printf '%s\n' "${all_features[@]}" | sort -u
}

# Step 4: Create Actions
create_actions_step() {
    local features=("$@")
    show_progress 4
    echo -e "${BOLD}${MAGENTA}Step 4: Define Actions${NC}"
    echo -e "${YELLOW}What actions do users perform in these features?${NC}\n"

    local all_actions=()

    for feat_key in "${features[@]}"; do
        echo -e "\n${CYAN}For feature:$feat_key:${NC}"
        local feat_desc=$(jq -r ".entities.features[\"$feat_key\"].description" "$GRAPH_FILE")
        echo -e "  ${feat_desc}"
        echo -e "\nWhat action(s) can users perform?"

        local action_count=1
        while [[ $action_count -le 2 ]]; do
            prompt "Action #$action_count (verb-noun format, e.g., 'create-report')" action ""
            if [[ -z "$action" ]]; then
                if [[ $action_count -eq 1 ]]; then
                    echo -e "${YELLOW}⚠ No actions defined for this feature${NC}"
                fi
                break
            fi

            local act_key=$(to_kebab_case "$action")
            local act_desc="User action to $action"

            # Add action if not exists
            if ! jq -e ".entities.actions[\"$act_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
                "$MOD_TOOL" add entity actions "$act_key" "$act_desc" > /dev/null 2>&1
                echo -e "${GREEN}✓ Created action: action:$act_key${NC}"
            else
                echo -e "${YELLOW}ℹ Using existing action: action:$act_key${NC}"
            fi

            # Link feature to action
            "$MOD_TOOL" add graph-link "feature:$feat_key" "action:$act_key" > /dev/null 2>&1
            echo -e "${GREEN}✓ Linked feature:$feat_key → action:$act_key${NC}"

            all_actions+=("$act_key")
            ((action_count++))
        done
    done

    printf '%s\n' "${all_actions[@]}" | sort -u
}

# Step 5: Create Components
create_components_step() {
    local actions=("$@")
    show_progress 5
    echo -e "${BOLD}${RED}Step 5: Define Components${NC}"
    echo -e "${YELLOW}What components implement these actions?${NC}\n"
    echo -e "Components need:"
    echo -e "  • ${GREEN}Behavior${NC} (business logic)"
    echo -e "  • ${BLUE}Data Model${NC} (data structures)"
    echo -e "  • ${YELLOW}Presentation${NC} (UI - optional)\n"

    for act_key in "${actions[@]}"; do
        echo -e "\n${CYAN}For action:$act_key:${NC}"
        local act_desc=$(jq -r ".entities.actions[\"$act_key\"].description // \"$act_key\"" "$GRAPH_FILE")
        echo -e "  ${act_desc}"

        prompt "Component name (e.g., 'report-generator')" component ""
        if [[ -z "$component" ]]; then
            echo -e "${YELLOW}⚠ Skipping component for this action${NC}"
            continue
        fi

        local comp_key=$(to_kebab_case "$component")
        prompt "Component description" comp_desc "Component that handles $act_key"

        # Add component if not exists
        if ! jq -e ".entities.components[\"$comp_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
            "$MOD_TOOL" add entity components "$comp_key" "$comp_desc" > /dev/null 2>&1
            echo -e "${GREEN}✓ Created component: component:$comp_key${NC}"
        else
            echo -e "${YELLOW}ℹ Using existing component: component:$comp_key${NC}"
        fi

        # Link action to component
        "$MOD_TOOL" add graph-link "action:$act_key" "component:$comp_key" > /dev/null 2>&1
        echo -e "${GREEN}✓ Linked action:$act_key → component:$comp_key${NC}"

        # Add behavior
        echo -e "\n${BOLD}Define Behavior (Business Logic):${NC}"
        prompt "Behavior name (e.g., 'validate-and-process')" behavior ""
        if [[ -n "$behavior" ]]; then
            local behav_key=$(to_kebab_case "$behavior")
            prompt "Behavior description" behav_desc "Business logic for $comp_key"

            # Add behavior entity if not exists
            if ! jq -e ".entities.behavior[\"$behav_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
                "$MOD_TOOL" add entity behavior "$behav_key" "$behav_desc" > /dev/null 2>&1
                echo -e "${GREEN}✓ Created behavior: behavior:$behav_key${NC}"
            fi

            # Link component to behavior
            "$MOD_TOOL" add graph-link "component:$comp_key" "behavior:$behav_key" > /dev/null 2>&1
            echo -e "${GREEN}✓ Linked component:$comp_key → behavior:$behav_key${NC}"

            # Add to references for implementation details
            local impl_details=""
            prompt "Key business rules (optional)" impl_details ""
            if [[ -n "$impl_details" ]]; then
                "$MOD_TOOL" add reference business_logic "$behav_key" "$impl_details" > /dev/null 2>&1
                echo -e "${GREEN}✓ Added business logic reference${NC}"
            fi
        fi

        # Add data model
        echo -e "\n${BOLD}Define Data Model:${NC}"
        prompt "Data model name (e.g., 'report-schema')" model ""
        if [[ -n "$model" ]]; then
            local model_key=$(to_kebab_case "$model")
            prompt "Model description" model_desc "Data structure for $comp_key"

            # Add to references (data models are typically references, not entities)
            "$MOD_TOOL" add reference data_models "$model_key" "$model_desc" > /dev/null 2>&1
            echo -e "${GREEN}✓ Created data model: data_models:$model_key${NC}"

            # Link component to data model
            "$MOD_TOOL" add graph-link "component:$comp_key" "data_models:$model_key" > /dev/null 2>&1
            echo -e "${GREEN}✓ Linked component:$comp_key → data_models:$model_key${NC}"

            # Optionally add schema details
            if confirm "Add schema fields?"; then
                echo "Enter fields (comma-separated, e.g., 'id, title, content, created_at'):"
                read -r fields
                if [[ -n "$fields" ]]; then
                    "$MOD_TOOL" add reference data_models "${model_key}_fields" "$fields" > /dev/null 2>&1
                    echo -e "${GREEN}✓ Added model fields${NC}"
                fi
            fi
        fi

        # Optional: Add presentation
        if confirm "Add UI/presentation layer?"; then
            prompt "UI template name (e.g., 'report-view')" ui ""
            if [[ -n "$ui" ]]; then
                local ui_key=$(to_kebab_case "$ui")
                "$MOD_TOOL" add reference ui_templates "$ui_key" "UI for $comp_key" > /dev/null 2>&1
                "$MOD_TOOL" add graph-link "component:$comp_key" "ui_templates:$ui_key" > /dev/null 2>&1
                echo -e "${GREEN}✓ Added presentation: ui_templates:$ui_key${NC}"
            fi
        fi

        echo -e "${GREEN}✅ Component chain complete for action:$act_key${NC}"
    done
}

# Function to show chain summary
show_chain_summary() {
    local user_key="$1"

    echo -e "\n${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}Chain Summary for user:$user_key${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}\n"

    # Get completeness score
    local score=$("$SCORER_TOOL" score "user:$user_key" 2>/dev/null | grep -oE '[0-9]+%' | head -1 || echo "0%")

    echo -e "${BOLD}Completeness Score:${NC} $score"
    echo ""

    # Show the dependency chain
    echo -e "${BOLD}Dependency Chain:${NC}"
    "$GAP_TOOL" chain "user:$user_key" 2>/dev/null | while IFS='|' read -r chain status; do
        if [[ -n "$chain" ]]; then
            case "$status" in
                complete)
                    echo -e "${GREEN}✓${NC} $chain"
                    ;;
                partial)
                    echo -e "${YELLOW}⚠${NC} $chain (partial)"
                    ;;
                *)
                    echo -e "${RED}✗${NC} $chain (incomplete)"
                    ;;
            esac
        fi
    done

    echo ""

    # Show next steps if incomplete
    if [[ "$score" != "100%" ]]; then
        echo -e "${YELLOW}Next Steps:${NC}"
        echo "1. Run 'know gap-analyze user:$user_key' to see detailed gaps"
        echo "2. Use 'know complete user:$user_key' to fill missing pieces"
        echo "3. Generate specs with 'know feature <feature-name>'"
    else
        echo -e "${GREEN}✅ Complete implementation chain!${NC}"
        echo "Ready to generate specifications for all components."
    fi
}

# Main workflow function
create_complete_chain() {
    show_banner

    # Step 1: Create User
    echo -e "${BOLD}Starting Complete Chain Creation...${NC}\n"
    local user_key=$(create_user_step)
    if [[ -z "$user_key" ]]; then
        echo -e "${RED}Chain creation aborted.${NC}"
        return 1
    fi

    # Step 2: Create Objectives
    local objectives_raw=$(create_objectives_step "$user_key")
    if [[ -z "$objectives_raw" ]]; then
        echo -e "${YELLOW}No objectives created. Chain incomplete.${NC}"
        show_chain_summary "$user_key"
        return 1
    fi

    # Convert objectives to array
    local objectives=()
    while IFS= read -r obj; do
        [[ -n "$obj" ]] && objectives+=("$obj")
    done <<< "$objectives_raw"

    # Step 3: Create Features
    local features_raw=$(create_features_step "${objectives[@]}")
    if [[ -z "$features_raw" ]]; then
        echo -e "${YELLOW}No features created. Chain incomplete.${NC}"
        show_chain_summary "$user_key"
        return 1
    fi

    # Convert features to array
    local features=()
    while IFS= read -r feat; do
        [[ -n "$feat" ]] && features+=("$feat")
    done <<< "$features_raw"

    # Step 4: Create Actions
    local actions_raw=$(create_actions_step "${features[@]}")
    if [[ -z "$actions_raw" ]]; then
        echo -e "${YELLOW}No actions created. Chain incomplete.${NC}"
        show_chain_summary "$user_key"
        return 1
    fi

    # Convert actions to array
    local actions=()
    while IFS= read -r act; do
        [[ -n "$act" ]] && actions+=("$act")
    done <<< "$actions_raw"

    # Step 5: Create Components
    create_components_step "${actions[@]}"

    # Show final summary
    show_chain_summary "$user_key"
}

# Main menu
main_menu() {
    while true; do
        echo -e "\n${CYAN}Complete Chain Builder Menu${NC}"
        echo "════════════════════════════════════"
        echo "1) Create new complete chain (guided)"
        echo "2) Extend existing user's chain"
        echo "3) Fill gaps in existing chains"
        echo "4) View all chains status"
        echo "5) Generate gap report"
        echo "6) Exit"

        prompt "Select option [1-6]" choice ""

        case "$choice" in
            1)
                create_complete_chain
                ;;

            2)
                echo -e "\n${CYAN}Available users:${NC}"
                jq -r '.entities.users | to_entries[] | "  - user:\(.key): \(.value.description)"' "$GRAPH_FILE"

                prompt "Enter user key (without 'user:' prefix)" user_key ""
                if [[ -n "$user_key" ]]; then
                    if jq -e ".entities.users[\"$user_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
                        # Start from objectives step
                        local objectives_raw=$(create_objectives_step "$user_key")
                        if [[ -n "$objectives_raw" ]]; then
                            local objectives=()
                            while IFS= read -r obj; do
                                [[ -n "$obj" ]] && objectives+=("$obj")
                            done <<< "$objectives_raw"

                            local features_raw=$(create_features_step "${objectives[@]}")
                            if [[ -n "$features_raw" ]]; then
                                local features=()
                                while IFS= read -r feat; do
                                    [[ -n "$feat" ]] && features+=("$feat")
                                done <<< "$features_raw"

                                local actions_raw=$(create_actions_step "${features[@]}")
                                if [[ -n "$actions_raw" ]]; then
                                    local actions=()
                                    while IFS= read -r act; do
                                        [[ -n "$act" ]] && actions+=("$act")
                                    done <<< "$actions_raw"

                                    create_components_step "${actions[@]}"
                                fi
                            fi
                        fi
                        show_chain_summary "$user_key"
                    else
                        echo -e "${RED}User not found: $user_key${NC}"
                    fi
                fi
                ;;

            3)
                echo -e "\n${CYAN}Analyzing gaps...${NC}"
                "$GAP_TOOL" analyze-all | head -20
                echo ""
                echo -e "${YELLOW}Use option 2 to extend specific chains${NC}"
                ;;

            4)
                "$SCORER_TOOL" report
                ;;

            5)
                "$LIB_DIR/gap-reporter.sh" text
                ;;

            6)
                echo -e "\n${GREEN}Thank you for using the Complete Chain Builder!${NC}"
                exit 0
                ;;

            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac
    done
}

# Run main menu
main_menu