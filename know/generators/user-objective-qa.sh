#!/bin/bash

# Interactive QA workflow for gathering user types and objectives
# Helps identify gaps between WHAT users want and HOW it's implemented

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/../lib"
GRAPH_FILE="${GRAPH_FILE:-$SCRIPT_DIR/../../.ai/spec-graph.json}"
MOD_TOOL="$LIB_DIR/mod-graph.sh"
GAP_TOOL="$LIB_DIR/gap-analysis.sh"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════"
    echo "          Knowledge Graph User & Objective Builder          "
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo -e "${YELLOW}This tool helps you define WHO will use your system and"
    echo -e "WHAT they're trying to accomplish, then identifies gaps"
    echo -e "in HOW these objectives will be implemented.${NC}\n"
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

# Function to create user entity
create_user() {
    echo -e "\n${MAGENTA}=== Define a User Type ===${NC}"

    prompt "User role/type (e.g., admin, operator, customer)" user_key ""
    if [[ -z "$user_key" ]]; then
        echo "User creation cancelled."
        return 1
    fi

    # Convert to kebab-case
    user_key=$(echo "$user_key" | tr '[:upper:]' '[:lower:]' | tr ' _' '--')

    prompt "User description" user_desc "User who interacts with the system"

    # Check if user already exists
    if jq -e ".entities.users[\"$user_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
        echo -e "${YELLOW}User 'user:$user_key' already exists${NC}"
    else
        # Add user entity
        "$MOD_TOOL" add entity users "$user_key" "$user_desc" > /dev/null 2>&1
        echo -e "${GREEN}✓ Created user: user:$user_key${NC}"
    fi

    # Ask about objectives for this user
    echo -e "\n${CYAN}What are this user's main objectives?${NC}"
    echo -e "${YELLOW}(Enter objectives one at a time, empty line to finish)${NC}"

    local obj_count=1
    while true; do
        prompt "Objective #$obj_count" objective ""
        if [[ -z "$objective" ]]; then
            break
        fi

        # Create objective entity
        local obj_key=$(echo "$objective" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -d '.,!?')
        local obj_desc="$objective"

        # Add objective if not exists
        if ! jq -e ".entities.objectives[\"$obj_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
            "$MOD_TOOL" add entity objectives "$obj_key" "$obj_desc" > /dev/null 2>&1
            echo -e "${GREEN}✓ Created objective: objective:$obj_key${NC}"
        fi

        # Link user to objective
        "$MOD_TOOL" add graph-link "user:$user_key" "objective:$obj_key" > /dev/null 2>&1
        echo -e "${GREEN}✓ Linked user:$user_key → objective:$obj_key${NC}"

        ((obj_count++))
    done

    echo "$user_key"
}

# Function to create standalone objective
create_objective() {
    echo -e "\n${MAGENTA}=== Define an Objective ===${NC}"

    prompt "What goal/outcome should be achieved?" objective ""
    if [[ -z "$objective" ]]; then
        echo "Objective creation cancelled."
        return 1
    fi

    local obj_key=$(echo "$objective" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -d '.,!?')
    local obj_desc="$objective"

    # Check if objective already exists
    if jq -e ".entities.objectives[\"$obj_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
        echo -e "${YELLOW}Objective 'objective:$obj_key' already exists${NC}"
    else
        "$MOD_TOOL" add entity objectives "$obj_key" "$obj_desc" > /dev/null 2>&1
        echo -e "${GREEN}✓ Created objective: objective:$obj_key${NC}"
    fi

    # Ask if this should be linked to an existing user
    if confirm "Link this objective to an existing user?"; then
        echo -e "\n${CYAN}Available users:${NC}"
        jq -r '.entities.users | to_entries[] | "  - user:\(.key) (\(.value.description))"' "$GRAPH_FILE"

        prompt "Enter user key (without 'user:' prefix)" user_key ""
        if [[ -n "$user_key" ]]; then
            if jq -e ".entities.users[\"$user_key\"]" "$GRAPH_FILE" > /dev/null 2>&1; then
                "$MOD_TOOL" add graph-link "user:$user_key" "objective:$obj_key" > /dev/null 2>&1
                echo -e "${GREEN}✓ Linked user:$user_key → objective:$obj_key${NC}"
            else
                echo -e "${YELLOW}User not found: $user_key${NC}"
            fi
        fi
    fi

    echo "$obj_key"
}

# Function to run gap analysis
run_gap_analysis() {
    echo -e "\n${MAGENTA}=== Running Gap Analysis ===${NC}"
    echo -e "${YELLOW}Analyzing all users and objectives for implementation gaps...${NC}\n"

    "$GAP_TOOL" analyze-all
}

# Function to generate focused report
generate_gap_report() {
    local entity_id="$1"

    echo -e "\n${MAGENTA}=== Gap Report for $entity_id ===${NC}"

    # Run chain analysis
    "$GAP_TOOL" chain "$entity_id"

    # Get completeness score
    echo -e "\n${CYAN}Completeness Score:${NC}"
    "$LIB_DIR/completeness-scorer.sh" score "$entity_id"
}

# Main workflow
main() {
    show_banner

    while true; do
        echo -e "\n${CYAN}What would you like to do?${NC}"
        echo "  1) Add a new user and their objectives"
        echo "  2) Add a standalone objective"
        echo "  3) Run gap analysis on all entities"
        echo "  4) Analyze specific user/objective"
        echo "  5) View completeness report"
        echo "  6) Exit"

        prompt "Select option [1-6]" choice ""

        case "$choice" in
            1)
                user_key=$(create_user)
                if [[ -n "$user_key" ]]; then
                    if confirm "Run gap analysis for this user now?"; then
                        generate_gap_report "user:$user_key"
                    fi
                fi
                ;;

            2)
                obj_key=$(create_objective)
                if [[ -n "$obj_key" ]]; then
                    if confirm "Run gap analysis for this objective now?"; then
                        generate_gap_report "objective:$obj_key"
                    fi
                fi
                ;;

            3)
                run_gap_analysis
                ;;

            4)
                echo -e "\n${CYAN}Available entities:${NC}"
                echo -e "${YELLOW}Users:${NC}"
                jq -r '.entities.users | keys[] | "  - user:\(.)"' "$GRAPH_FILE"
                echo -e "${YELLOW}Objectives:${NC}"
                jq -r '.entities.objectives | keys[] | "  - objective:\(.)"' "$GRAPH_FILE"

                prompt "Enter entity ID (e.g., user:owner)" entity_id ""
                if [[ -n "$entity_id" ]]; then
                    generate_gap_report "$entity_id"
                fi
                ;;

            5)
                "$LIB_DIR/completeness-scorer.sh" report
                ;;

            6)
                echo -e "\n${GREEN}Thank you for using the Knowledge Graph Builder!${NC}"
                exit 0
                ;;

            *)
                echo -e "${YELLOW}Invalid option. Please select 1-6.${NC}"
                ;;
        esac
    done
}

# Run main workflow
main