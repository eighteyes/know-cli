#!/bin/bash

# Smart connection system for knowledge graph entities
# Pure shell/jq implementation - no AI required

set -euo pipefail

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh" 2>/dev/null || true

# Configuration
DEFAULT_SCORE_THRESHOLD=40
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}"

# Colors (only define if not already defined)
if [[ -z "${RED:-}" ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly MAGENTA='\033[0;35m'
    readonly CYAN='\033[0;36m'
    readonly NC='\033[0m'
fi

# Load dependency rules from JSON file
DEPENDENCY_RULES_FILE="${SCRIPT_DIR}/dependency-rules.json"

# Initialize associative arrays
declare -gA HIERARCHY_LEVELS
declare -gA ALLOWED_DEPS

# Load allowed dependencies from JSON
load_dependency_rules() {
    if [[ ! -f "$DEPENDENCY_RULES_FILE" ]]; then
        echo -e "${RED}Error: dependency-rules.json not found at $DEPENDENCY_RULES_FILE${NC}" >&2
        return 1
    fi

    # Parse allowed_dependencies into associative array
    local deps=$(jq -r '.allowed_dependencies | to_entries[] | "\(.key)=\(.value | join(" "))"' "$DEPENDENCY_RULES_FILE")
    while IFS='=' read -r key value; do
        ALLOWED_DEPS["$key"]="$value"
    done <<< "$deps"

    # Build hierarchy levels from allowed_dependencies
    local level=0
    HIERARCHY_LEVELS["project"]=0

    # Traverse the dependency chain to assign levels
    local processed=("project")
    local current=("project")

    while [[ ${#current[@]} -gt 0 ]]; do
        local next=()
        for entity in "${current[@]}"; do
            local deps="${ALLOWED_DEPS[$entity]}"
            if [[ -n "$deps" ]]; then
                for dep in $deps; do
                    if [[ -z "${HIERARCHY_LEVELS[$dep]:-}" ]]; then
                        HIERARCHY_LEVELS["$dep"]=$((level + 1))
                        next+=("$dep")
                    fi
                done
            fi
        done
        current=("${next[@]}")
        ((level++))
        [[ $level -gt 10 ]] && break  # Prevent infinite loops
    done

    # Set special cases
    HIERARCHY_LEVELS["data_models"]=8
    HIERARCHY_LEVELS["assets"]=8
    HIERARCHY_LEVELS["behavior"]=8
    HIERARCHY_LEVELS["presentation"]=8
}

# Load rules will be called on first use
RULES_LOADED=false

# Extract keywords from entity names
get_keywords() {
    local name="$1"
    # Split on common delimiters: -, _, :
    echo "$name" | tr '\-_:' ' ' | tr '[:upper:]' '[:lower:]'
}

# Calculate similarity score (0-100)
calculate_similarity() {
    local entity1="$1"
    local entity2="$2"

    # Get keywords from both entities
    local keywords1=($(get_keywords "$entity1"))
    local keywords2=($(get_keywords "$entity2"))

    # Count matching keywords
    local matches=0
    for k1 in "${keywords1[@]}"; do
        for k2 in "${keywords2[@]}"; do
            if [[ "$k1" == "$k2" ]]; then
                ((matches++))
                break  # Count each keyword only once
            fi
        done
    done

    # Calculate percentage
    local total=$((${#keywords1[@]} + ${#keywords2[@]}))
    if [[ $total -eq 0 ]]; then
        echo 0
    else
        echo $((matches * 200 / total))  # *200 because we want match/average
    fi
}

# Check if connection is valid per hierarchy
is_valid_connection() {
    local source_type="$1"
    local target_type="$2"

    # Ensure rules are loaded
    if [[ "$RULES_LOADED" != "true" ]]; then
        load_dependency_rules
        RULES_LOADED=true
    fi

    # Check allowed dependencies
    local allowed="${ALLOWED_DEPS[$source_type]:-}"
    if [[ " $allowed " =~ " $target_type " ]]; then
        return 0  # Valid
    fi

    # Check reference descriptions for special connection rules
    # Load reference descriptions to understand what can connect to what
    if [[ -f "$DEPENDENCY_RULES_FILE" ]]; then
        # Check if target is a reference type
        local is_reference=$(jq -r ".reference_descriptions | has(\"$target_type\")" "$DEPENDENCY_RULES_FILE" 2>/dev/null)

        if [[ "$is_reference" == "true" ]]; then
            # References can be dependencies of entities
            case "$source_type" in
                features|actions|components|interfaces|objectives|requirements)
                    return 0
                    ;;
            esac
        fi

        # Check if source is a reference type that should connect to entities
        local source_is_ref=$(jq -r ".reference_descriptions | has(\"$source_type\")" "$DEPENDENCY_RULES_FILE" 2>/dev/null)

        if [[ "$source_is_ref" == "true" ]]; then
            # Special rules for reference->entity connections
            case "$source_type" in
                acceptance_criteria)
                    [[ "$target_type" == "features" ]] && return 0
                    ;;
                business_logic)
                    [[ "$target_type" == "actions" ]] && return 0
                    ;;
                screens)
                    [[ "$target_type" == "interfaces" ]] && return 0
                    ;;
                technical_architecture|libraries|protocols)
                    [[ "$target_type" == "components" ]] && return 0
                    ;;
                data_models)
                    [[ "$target_type" == "components" ]] && return 0
                    ;;
            esac
        fi
    fi

    return 1  # Invalid
}

# Find potential connections for an entity
find_connections() {
    local entity="$1"
    local threshold="${2:-$DEFAULT_SCORE_THRESHOLD}"
    local graph_file="${3:-$KNOWLEDGE_MAP}"

    local entity_type="${entity%%:*}"
    local entity_name="${entity#*:}"

    # Get all entities and references
    local all_nodes=$(jq -r '
        (.entities | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)"),
        (.references | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)")
    ' "$graph_file" 2>/dev/null | sort -u)

    local connections=""

    while IFS= read -r target; do
        [[ "$entity" == "$target" ]] && continue
        [[ -z "$target" ]] && continue

        local target_type="${target%%:*}"
        local target_name="${target#*:}"

        # Check if connection is valid
        if is_valid_connection "$entity_type" "$target_type"; then
            # Calculate similarity
            local score=$(calculate_similarity "$entity_name" "$target_name")

            if [[ $score -ge $threshold ]]; then
                connections="${connections}${target}:${score}\n"
            fi
        fi
    done <<< "$all_nodes"

    echo -e "$connections" | sort -t: -k3 -rn
}

# Connect references by name matching
connect_references() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local preview="${2:-false}"

    local connections=""

    # Match acceptance_criteria
    local criteria=$(jq -r '.references.acceptance_criteria | keys[]?' "$graph_file" 2>/dev/null)
    while IFS= read -r criterion; do
        [[ -z "$criterion" ]] && continue
        # Normalize: real_time_telemetry → real-time-telemetry
        local normalized=$(echo "$criterion" | sed 's/_/-/g' | sed 's/-criteria$//')

        # Find matching feature
        local feature_match=$(jq -r ".entities.features | keys[]?" "$graph_file" 2>/dev/null | grep -i "$normalized" | head -1)
        if [[ -n "$feature_match" ]]; then
            connections="${connections}acceptance_criteria:${criterion}->features:${feature_match}\n"
        fi
    done <<< "$criteria"

    # Match business_logic
    local logic=$(jq -r '.references.business_logic | keys[]?' "$graph_file" 2>/dev/null)
    while IFS= read -r logic_item; do
        [[ -z "$logic_item" ]] && continue
        # Remove _logic suffix and normalize
        local base_name=$(echo "$logic_item" | sed 's/_logic$//' | sed 's/_/-/g')

        # Find matching action
        local action_match=$(jq -r ".entities.actions | keys[]?" "$graph_file" 2>/dev/null | grep -i "$base_name" | head -1)
        if [[ -n "$action_match" ]]; then
            connections="${connections}business_logic:${logic_item}->actions:${action_match}\n"
        fi
    done <<< "$logic"

    # Match screens to interfaces
    local screens=$(jq -r '.references.screens | keys[]?' "$graph_file" 2>/dev/null)
    while IFS= read -r screen; do
        [[ -z "$screen" ]] && continue
        # Extract base name
        local base_name=$(echo "$screen" | cut -d- -f1)

        # Find matching interface
        local interface_match=$(jq -r ".entities.interfaces | keys[]?" "$graph_file" 2>/dev/null | grep -i "$base_name" | head -1)
        if [[ -n "$interface_match" ]]; then
            connections="${connections}screens:${screen}->interfaces:${interface_match}\n"
        fi
    done <<< "$screens"

    echo -e "$connections"
}

# Auto-connect all entities
auto_connect() {
    local preview="${1:-false}"
    local threshold="${2:-$DEFAULT_SCORE_THRESHOLD}"
    local graph_file="${3:-$KNOWLEDGE_MAP}"

    echo -e "${BLUE}🔍 Analyzing entity relationships...${NC}"
    echo

    local all_connections=""
    local connection_count=0

    # Get all entities
    local entities=$(jq -r '.entities | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)"' "$graph_file" 2>/dev/null)

    # Find connections for each entity
    while IFS= read -r entity; do
        [[ -z "$entity" ]] && continue

        local connections=$(find_connections "$entity" "$threshold" "$graph_file")
        while IFS= read -r connection; do
            [[ -z "$connection" ]] && continue

            local target="${connection%:*}"
            local score="${connection##*:}"

            # Check if this connection already exists
            local exists=$(jq -r ".graph[\"$entity\"].depends_on[]? | select(. == \"$target\")" "$graph_file" 2>/dev/null)

            if [[ -z "$exists" ]]; then
                all_connections="${all_connections}${entity}->${target}:${score}\n"
                ((connection_count++))
            fi
        done <<< "$connections"
    done <<< "$entities"

    # Add reference connections
    echo -e "${BLUE}📎 Matching references by name...${NC}"
    local ref_connections=$(connect_references "$graph_file" "$preview")
    if [[ -n "$ref_connections" ]]; then
        all_connections="${all_connections}${ref_connections}"
        local ref_count=$(echo -e "$ref_connections" | grep -c "->")
        ((connection_count += ref_count))
    fi

    # Display results
    echo -e "${GREEN}📊 Found ${connection_count} potential connections:${NC}"
    echo

    # Group by type for better readability
    echo -e "${YELLOW}Entity Connections (similarity > ${threshold}%):${NC}"
    echo -e "$all_connections" | grep -v "acceptance_criteria\|business_logic\|screens\|technical" | sort -t: -k2 -rn | head -20

    echo
    echo -e "${YELLOW}Reference Connections (name matching):${NC}"
    echo -e "$all_connections" | grep "acceptance_criteria\|business_logic\|screens\|technical" | sort

    if [[ "$preview" == "true" ]]; then
        echo
        echo -e "${YELLOW}🔗 Total connections to create: ${connection_count}${NC}"
        echo -e "${CYAN}Run without --preview to apply these connections${NC}"
    else
        echo
        echo -e "${YELLOW}Applying connections...${NC}"
        apply_connections "$all_connections" "$graph_file"
    fi
}

# Apply connections to the graph
apply_connections() {
    local connections="$1"
    local graph_file="${2:-$KNOWLEDGE_MAP}"

    local temp_file=$(mktemp)
    cp "$graph_file" "$temp_file"

    local applied=0
    while IFS= read -r connection; do
        [[ -z "$connection" ]] && continue

        # Parse connection: source->target:score
        local source="${connection%->*}"
        local rest="${connection#*->}"
        local target="${rest%:*}"
        local score="${rest##*:}"

        # Apply connection using jq
        jq --arg source "$source" \
           --arg target "$target" \
           '.graph[$source].depends_on = (.graph[$source].depends_on // [] | . + [$target] | unique)' \
           "$temp_file" > "${temp_file}.tmp" && mv "${temp_file}.tmp" "$temp_file"

        ((applied++))
        echo -e "  ${GREEN}✓${NC} Connected: $source → $target"
    done <<< "$(echo -e "$connections")"

    # Save the updated graph
    mv "$temp_file" "$graph_file"

    echo
    echo -e "${GREEN}✅ Applied ${applied} connections${NC}"
}

# Connect specific entity
connect_entity() {
    local entity="$1"
    local target="${2:-}"
    local graph_file="${3:-$KNOWLEDGE_MAP}"

    if [[ -n "$target" ]]; then
        # Connect to specific target
        local source_type="${entity%%:*}"
        local target_type="${target%%:*}"

        if is_valid_connection "$source_type" "$target_type"; then
            echo -e "${GREEN}✓ Valid connection: $entity → $target${NC}"
            apply_connections "${entity}->${target}:100" "$graph_file"
        else
            echo -e "${RED}✗ Invalid connection: $source_type cannot depend on $target_type${NC}"
            echo -e "${YELLOW}Allowed: ${ALLOWED_DEPS[$source_type]:-none}${NC}"
            return 1
        fi
    else
        # Find and suggest connections for entity
        echo -e "${BLUE}🔍 Finding connections for: $entity${NC}"
        echo

        local connections=$(find_connections "$entity" 30 "$graph_file")
        if [[ -z "$connections" ]]; then
            echo -e "${YELLOW}No connections found with similarity > 30%${NC}"
        else
            echo -e "${GREEN}Potential connections:${NC}"
            echo "$connections" | while IFS= read -r conn; do
                local target="${conn%:*}"
                local score="${conn##*:}"
                echo -e "  → $target ${CYAN}(${score}% match)${NC}"
            done

            echo
            echo -e "${CYAN}To connect, run: know connect $entity <target>${NC}"
        fi
    fi
}

# Main command handler
connect_command() {
    # Ensure rules are loaded
    if [[ "$RULES_LOADED" != "true" ]]; then
        load_dependency_rules
        RULES_LOADED=true
    fi

    local args=("$@")
    local preview=false
    local interactive=false
    local threshold=$DEFAULT_SCORE_THRESHOLD
    local entity=""
    local target=""

    # Parse arguments
    for arg in "${args[@]}"; do
        case "$arg" in
            --auto)
                # Auto mode - handled below
                ;;
            --preview)
                preview=true
                ;;
            --interactive)
                interactive=true
                ;;
            --score-threshold=*)
                threshold="${arg#*=}"
                ;;
            --help)
                connect_help
                return 0
                ;;
            *)
                if [[ -z "$entity" ]]; then
                    entity="$arg"
                else
                    target="$arg"
                fi
                ;;
        esac
    done

    # Execute appropriate mode
    if [[ " ${args[@]} " =~ " --auto " ]]; then
        auto_connect "$preview" "$threshold"
    elif [[ -n "$entity" ]]; then
        connect_entity "$entity" "$target"
    else
        connect_help
    fi
}

# Help text
connect_help() {
    cat << EOF
${GREEN}know connect${NC} - Intelligently connect entities in the knowledge graph

${YELLOW}USAGE:${NC}
    know connect --auto [--preview] [--score-threshold=N]
        Automatically connect all entities based on similarity

    know connect <entity>
        Find potential connections for a specific entity

    know connect <source> <target>
        Connect two specific entities (validates rules)

${YELLOW}OPTIONS:${NC}
    --auto              Auto-connect all entities
    --preview           Show connections without applying
    --score-threshold=N Minimum similarity score (default: 40)
    --interactive       Choose connections interactively (coming soon)

${YELLOW}EXAMPLES:${NC}
    # Preview all automatic connections
    know connect --auto --preview

    # Apply automatic connections
    know connect --auto

    # Find connections for specific entity
    know connect feature:real-time-telemetry

    # Connect specific entities
    know connect feature:real-time-telemetry action:stream-telemetry

    # Auto-connect with higher threshold
    know connect --auto --score-threshold=60

${YELLOW}CONNECTION RULES:${NC}
    The hierarchy follows these rules:
    - Project → Requirements → Interfaces → Features → Actions → Components
    - Users → Objectives → Features/Actions
    - Components → Behavior/Presentation/Data Models/Assets
    - References connect to their appropriate entity types

EOF
}