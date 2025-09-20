#!/bin/bash

# Optimized smart connection system for knowledge graph entities
# Performance improvements: caching, batch processing, early termination

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

# Cache variables for performance
declare -gA HIERARCHY_LEVELS
declare -gA ALLOWED_DEPS
declare -gA NODE_CACHE
declare -gA KEYWORD_CACHE
RULES_LOADED=false
NODES_CACHED=false

# Load allowed dependencies from JSON (once)
load_dependency_rules() {
    if [[ "$RULES_LOADED" == "true" ]]; then
        return 0
    fi

    if [[ ! -f "$DEPENDENCY_RULES_FILE" ]]; then
        echo -e "${RED}Error: dependency-rules.json not found at $DEPENDENCY_RULES_FILE${NC}" >&2
        return 1
    fi

    # Parse allowed_dependencies into associative array
    local deps=$(jq -r '.allowed_dependencies | to_entries[] | "\(.key)=\(.value | join(" "))"' "$DEPENDENCY_RULES_FILE")
    while IFS='=' read -r key value; do
        ALLOWED_DEPS["$key"]="$value"
    done <<< "$deps"

    # Build hierarchy levels
    HIERARCHY_LEVELS["project"]=0
    HIERARCHY_LEVELS["platforms"]=1
    HIERARCHY_LEVELS["users"]=2
    HIERARCHY_LEVELS["requirements"]=3
    HIERARCHY_LEVELS["interfaces"]=4
    HIERARCHY_LEVELS["features"]=5
    HIERARCHY_LEVELS["objectives"]=5
    HIERARCHY_LEVELS["actions"]=6
    HIERARCHY_LEVELS["components"]=7
    HIERARCHY_LEVELS["behavior"]=8
    HIERARCHY_LEVELS["presentation"]=8
    HIERARCHY_LEVELS["data_models"]=8
    HIERARCHY_LEVELS["assets"]=8

    RULES_LOADED=true
}

# Cache all nodes for faster access
cache_all_nodes() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    if [[ "$NODES_CACHED" == "true" ]]; then
        return 0
    fi

    echo -e "${BLUE}⚡ Caching graph nodes...${NC}" >&2

    # Get all nodes in one jq call and cache them
    local nodes=$(jq -r '
        (.entities | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)"),
        (.references | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)")
    ' "$graph_file" 2>/dev/null)

    while IFS= read -r node; do
        [[ -z "$node" ]] && continue
        NODE_CACHE["$node"]=1
    done <<< "$nodes"

    NODES_CACHED=true
    echo -e "${GREEN}✓ Cached ${#NODE_CACHE[@]} nodes${NC}" >&2
}

# Extract and cache keywords
get_keywords_cached() {
    local name="$1"

    # Check cache first
    if [[ -n "${KEYWORD_CACHE[$name]:-}" ]]; then
        echo "${KEYWORD_CACHE[$name]}"
        return
    fi

    # Extract keywords (optimized with single sed)
    local keywords=$(echo "$name" | sed 's/[-_:]/ /g' | tr '[:upper:]' '[:lower:]')
    KEYWORD_CACHE["$name"]="$keywords"
    echo "$keywords"
}

# Fast similarity calculation with early termination
calculate_similarity_fast() {
    local entity1="$1"
    local entity2="$2"

    # Quick exact match check
    if [[ "$entity1" == "$entity2" ]]; then
        echo 100
        return
    fi

    # Get cached keywords
    local keywords1=$(get_keywords_cached "$entity1")
    local keywords2=$(get_keywords_cached "$entity2")

    # Convert to arrays
    local arr1=($keywords1)
    local arr2=($keywords2)

    # Early termination if no overlap possible
    [[ ${#arr1[@]} -eq 0 || ${#arr2[@]} -eq 0 ]] && { echo 0; return; }

    # Count matches (optimized)
    local matches=0
    for k1 in "${arr1[@]}"; do
        for k2 in "${arr2[@]}"; do
            if [[ "$k1" == "$k2" ]]; then
                ((matches++))
                break
            fi
        done
    done

    # Calculate percentage
    local total=$((${#arr1[@]} + ${#arr2[@]}))
    echo $((matches * 200 / total))
}

# Batch check valid connections
is_valid_connection_fast() {
    local source_type="$1"
    local target_type="$2"

    # Quick lookup in allowed deps
    local allowed="${ALLOWED_DEPS[$source_type]:-}"
    [[ " $allowed " =~ " $target_type " ]] && return 0

    # Check if target is a reference (simplified)
    [[ -z "${HIERARCHY_LEVELS[$target_type]:-}" ]] && {
        case "$source_type" in
            features|actions|components|interfaces|objectives|requirements)
                return 0 ;;
        esac
    }

    # Special reference rules (optimized)
    case "$source_type" in
        acceptance_criteria)
            [[ "$target_type" == "features" ]] && return 0 ;;
        business_logic)
            [[ "$target_type" == "actions" ]] && return 0 ;;
        screens)
            [[ "$target_type" == "interfaces" ]] && return 0 ;;
        technical_architecture|libraries|protocols|data_models)
            [[ "$target_type" == "components" ]] && return 0 ;;
    esac

    return 1
}

# Find connections with batch processing
find_connections_batch() {
    local entity="$1"
    local threshold="${2:-$DEFAULT_SCORE_THRESHOLD}"

    local entity_type="${entity%%:*}"
    local entity_name="${entity#*:}"

    # Pre-filter candidates by type
    local valid_types=""
    local allowed="${ALLOWED_DEPS[$entity_type]:-}"

    # Build list of valid target types
    for target_type in $allowed; do
        valid_types="${valid_types}|${target_type}"
    done
    valid_types="${valid_types#|}"

    local connections=""
    local checked=0
    local found=0

    # Process nodes in batches
    for node in "${!NODE_CACHE[@]}"; do
        ((checked++))

        # Skip self
        [[ "$node" == "$entity" ]] && continue

        local target_type="${node%%:*}"
        local target_name="${node#*:}"

        # Quick type filter
        if ! is_valid_connection_fast "$entity_type" "$target_type"; then
            continue
        fi

        # Calculate similarity
        local score=$(calculate_similarity_fast "$entity_name" "$target_name")

        if [[ $score -ge $threshold ]]; then
            connections="${connections}${node}:${score}\n"
            ((found++))

            # Early termination if we found enough
            [[ $found -ge 20 ]] && break
        fi

        # Progress indicator every 100 nodes
        if [[ $((checked % 100)) -eq 0 ]]; then
            echo -ne "\r${CYAN}Checked $checked nodes, found $found matches...${NC}" >&2
        fi
    done

    echo -ne "\r" >&2  # Clear progress line
    echo -e "$connections" | sort -t: -k2 -rn
}

# Optimized reference connection
connect_references_fast() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local preview="${2:-false}"

    echo -e "${BLUE}📎 Matching references by patterns...${NC}" >&2

    # Pre-compile all reference patterns once
    local connections=""

    # Get all acceptance criteria and features in one query
    local criteria_features=$(jq -r '
        {
            criteria: [.references.acceptance_criteria | keys[]?],
            features: [.entities.features | keys[]?]
        }
    ' "$graph_file" 2>/dev/null)

    # Match acceptance criteria to features
    local criteria=$(echo "$criteria_features" | jq -r '.criteria[]' 2>/dev/null)
    local features=$(echo "$criteria_features" | jq -r '.features[]' 2>/dev/null)

    while IFS= read -r criterion; do
        [[ -z "$criterion" ]] && continue
        local normalized=$(echo "$criterion" | sed 's/_/-/g' | sed 's/-criteria$//')

        # Quick match against features
        while IFS= read -r feature; do
            if [[ "$feature" == *"$normalized"* ]] || [[ "$normalized" == *"$feature"* ]]; then
                connections="${connections}acceptance_criteria:${criterion}->features:${feature}\n"
                break
            fi
        done <<< "$features"
    done <<< "$criteria"

    # Similar optimization for business_logic -> actions
    local logic_actions=$(jq -r '
        {
            logic: [.references.business_logic | keys[]?],
            actions: [.entities.actions | keys[]?]
        }
    ' "$graph_file" 2>/dev/null)

    local logic=$(echo "$logic_actions" | jq -r '.logic[]' 2>/dev/null)
    local actions=$(echo "$logic_actions" | jq -r '.actions[]' 2>/dev/null)

    while IFS= read -r logic_item; do
        [[ -z "$logic_item" ]] && continue
        local base_name=$(echo "$logic_item" | sed 's/_logic$//' | sed 's/_/-/g')

        while IFS= read -r action; do
            if [[ "$action" == *"$base_name"* ]] || [[ "$base_name" == *"$action"* ]]; then
                connections="${connections}business_logic:${logic_item}->actions:${action}\n"
                break
            fi
        done <<< "$actions"
    done <<< "$logic"

    echo -e "$connections"
}

# Optimized auto-connect
auto_connect_fast() {
    local preview="${1:-false}"
    local threshold="${2:-$DEFAULT_SCORE_THRESHOLD}"
    local graph_file="${3:-$KNOWLEDGE_MAP}"

    echo -e "${BLUE}🔍 Analyzing entity relationships...${NC}"

    # Load rules and cache nodes
    load_dependency_rules
    cache_all_nodes "$graph_file"

    local all_connections=""
    local connection_count=0

    # Process high-value entities first (features, interfaces, actions)
    local priority_types="features interfaces actions components"
    local other_types="users objectives requirements"

    echo -e "${CYAN}Processing priority entities...${NC}"

    for entity_type in $priority_types $other_types; do
        # Get entities of this type
        local entities=$(jq -r ".entities.$entity_type | keys[]?" "$graph_file" 2>/dev/null)

        while IFS= read -r entity_name; do
            [[ -z "$entity_name" ]] && continue

            local entity="${entity_type}:${entity_name}"
            local connections=$(find_connections_batch "$entity" "$threshold")

            while IFS= read -r connection; do
                [[ -z "$connection" ]] && continue

                local target="${connection%:*}"
                local score="${connection##*:}"

                # Check if connection already exists
                local exists=$(jq -r ".graph[\"$entity\"].depends_on[]? | select(. == \"$target\")" "$graph_file" 2>/dev/null)

                if [[ -z "$exists" ]]; then
                    all_connections="${all_connections}${entity}->${target}:${score}\n"
                    ((connection_count++))
                fi
            done <<< "$connections"
        done <<< "$entities"
    done

    # Add reference connections
    echo -e "${BLUE}📎 Matching references...${NC}"
    local ref_connections=$(connect_references_fast "$graph_file" "$preview")
    if [[ -n "$ref_connections" ]]; then
        all_connections="${all_connections}${ref_connections}"
        local ref_count=$(echo -e "$ref_connections" | grep -c "->")
        ((connection_count += ref_count))
    fi

    # Display results
    echo -e "${GREEN}📊 Found ${connection_count} potential connections${NC}"

    if [[ "$preview" == "true" ]]; then
        echo
        echo -e "${YELLOW}Top connections by score:${NC}"
        echo -e "$all_connections" | sort -t: -k3 -rn | head -20
        echo
        echo -e "${CYAN}Run without --preview to apply these connections${NC}"
    else
        echo -e "${YELLOW}Applying connections...${NC}"
        apply_connections "$all_connections" "$graph_file"
    fi
}

# Apply connections (reused from original)
apply_connections() {
    local connections="$1"
    local graph_file="${2:-$KNOWLEDGE_MAP}"

    local temp_file=$(mktemp)
    cp "$graph_file" "$temp_file"

    local applied=0
    local total=$(echo -e "$connections" | grep -c "->")

    while IFS= read -r connection; do
        [[ -z "$connection" ]] && continue

        local source="${connection%->*}"
        local rest="${connection#*->}"
        local target="${rest%:*}"

        jq --arg source "$source" \
           --arg target "$target" \
           '.graph[$source].depends_on = (.graph[$source].depends_on // [] | . + [$target] | unique)' \
           "$temp_file" > "${temp_file}.tmp" && mv "${temp_file}.tmp" "$temp_file"

        ((applied++))

        # Progress indicator
        if [[ $((applied % 10)) -eq 0 ]]; then
            echo -ne "\r  ${GREEN}Progress: $applied/$total${NC}" >&2
        fi
    done <<< "$(echo -e "$connections")"

    echo -ne "\r" >&2  # Clear progress line
    mv "$temp_file" "$graph_file"

    echo -e "${GREEN}✅ Applied ${applied} connections${NC}"
}

# Optimized main handler
connect_command() {
    # Load rules once at start
    load_dependency_rules

    local args=("$@")
    local preview=false
    local threshold=$DEFAULT_SCORE_THRESHOLD
    local entity=""
    local target=""

    for arg in "${args[@]}"; do
        case "$arg" in
            --auto)
                ;;
            --preview)
                preview=true
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
        auto_connect_fast "$preview" "$threshold"
    elif [[ -n "$entity" ]]; then
        cache_all_nodes

        if [[ -n "$target" ]]; then
            # Connect specific entities
            local source_type="${entity%%:*}"
            local target_type="${target%%:*}"

            if is_valid_connection_fast "$source_type" "$target_type"; then
                echo -e "${GREEN}✓ Valid connection: $entity → $target${NC}"
                apply_connections "${entity}->${target}:100"
            else
                echo -e "${RED}✗ Invalid connection: $source_type cannot depend on $target_type${NC}"
                return 1
            fi
        else
            # Find connections for entity
            echo -e "${BLUE}🔍 Finding connections for: $entity${NC}"
            local connections=$(find_connections_batch "$entity" 30)

            if [[ -z "$connections" ]]; then
                echo -e "${YELLOW}No connections found with similarity > 30%${NC}"
            else
                echo -e "${GREEN}Potential connections:${NC}"
                echo "$connections" | head -10 | while IFS= read -r conn; do
                    local target="${conn%:*}"
                    local score="${conn##*:}"
                    echo -e "  → $target ${CYAN}(${score}% match)${NC}"
                done
            fi
        fi
    else
        connect_help
    fi
}

# Help text
connect_help() {
    cat << EOF
${GREEN}know connect${NC} - Optimized entity connection system

${YELLOW}USAGE:${NC}
    know connect --auto [--preview] [--score-threshold=N]
    know connect <entity>
    know connect <source> <target>

${YELLOW}OPTIMIZATIONS:${NC}
    ⚡ Node caching for faster lookups
    ⚡ Keyword caching to avoid re-parsing
    ⚡ Early termination for sufficient matches
    ⚡ Batch processing with progress indicators
    ⚡ Priority processing for important entities

EOF
}