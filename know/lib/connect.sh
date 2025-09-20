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
else
    # Ensure CYAN is defined if other colors are
    if [[ -z "${CYAN:-}" ]]; then
        readonly CYAN='\033[0;36m'
    fi
fi

# Load dependency rules from JSON file
DEPENDENCY_RULES_FILE="${SCRIPT_DIR}/dependency-rules.json"

# Cache variables for performance
# Check bash version for associative array support
if [[ ${BASH_VERSION%%.*} -ge 4 ]]; then
    declare -A HIERARCHY_LEVELS
    declare -A ALLOWED_DEPS
    declare -A NODE_CACHE
    declare -A KEYWORD_CACHE
else
    # For Bash 3.x, we'll use alternative methods
    HIERARCHY_LEVELS=""
    ALLOWED_DEPS=""
    NODE_CACHE=""
    KEYWORD_CACHE=""
fi
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

    # Process only valid target types to reduce search space
    for node in "${!NODE_CACHE[@]}"; do
        # Skip self
        [[ "$node" == "$entity" ]] && continue

        local target_type="${node%%:*}"

        # Quick type filter FIRST to avoid unnecessary processing
        if ! is_valid_connection_fast "$entity_type" "$target_type"; then
            continue
        fi

        ((checked++))
        local target_name="${node#*:}"

        # Calculate similarity
        local score=$(calculate_similarity_fast "$entity_name" "$target_name")

        if [[ $score -ge $threshold ]]; then
            connections="${connections}${node}:${score}\n"
            ((found++))

            # Early termination if we found enough
            [[ $found -ge 5 ]] && break
        fi

        # Progress indicator every 100 nodes
        if [[ $((checked % 100)) -eq 0 ]]; then
            echo -ne "\rChecked $checked nodes, found $found matches..." >&2
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

    echo -e "${BLUE}Processing priority entities...${NC}"

    for entity_type in $priority_types $other_types; do
        # Get entities of this type
        local entities=$(jq -r ".entities.$entity_type | keys[]?" "$graph_file" 2>/dev/null)
        local entity_count=$(echo "$entities" | grep -c '^' || echo 0)

        echo -e "${BLUE}Processing $entity_count ${entity_type} entities...${NC}" >&2

        while IFS= read -r entity_name; do
            [[ -z "$entity_name" ]] && continue

            local entity="${entity_type}:${entity_name}"
            echo -ne "\r${CYAN}Checking: $entity...${NC}" >&2

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

        echo -ne "\r" >&2  # Clear line
    done

    # Add reference connections
    echo -e "${BLUE}📎 Matching references...${NC}"
    local ref_connections=$(connect_references_fast "$graph_file" "$preview")
    if [[ -n "$ref_connections" ]]; then
        all_connections="${all_connections}${ref_connections}"
        local ref_count=$(echo -e "$ref_connections" | grep -c '\->')
        ((connection_count += ref_count))
    fi

    # Display results
    echo -e "${GREEN}📊 Found ${connection_count} potential connections${NC}"

    if [[ "$preview" == "true" ]]; then
        echo
        echo -e "${YELLOW}Top connections by score:${NC}"
        echo -e "$all_connections" | sort -t: -k3 -rn | head -20
        echo
        echo -e "${BLUE}Run without --preview to apply these connections${NC}"
    else
        echo -e "${YELLOW}Applying connections...${NC}"
        apply_connections "$all_connections" "$graph_file"
    fi
}

# Apply connections (reused from original)
apply_connections() {
    local connections="$1"
    local graph_file="${2:-$KNOWLEDGE_MAP}"

    local applied=0
    local total=$(echo -e "$connections" | grep -c '\->' || echo 0)

    [[ $total -eq 0 ]] && return 0

    while IFS= read -r connection; do
        [[ -z "$connection" ]] && continue

        local source="${connection%->*}"
        local rest="${connection#*->}"
        local target="${rest%:*}"

        echo -e "  Applying: $source → $target"

        # Ensure source node exists
        if ! jq -e ".graph | has(\"$source\")" "$graph_file" > /dev/null 2>&1; then
            jq --arg src "$source" '.graph[$src] = {"depends_on": []}' \
               "$graph_file" > "${graph_file}.tmp" && mv "${graph_file}.tmp" "$graph_file"
        fi

        # Add connection
        jq --arg src "$source" --arg tgt "$target" \
           '.graph[$src].depends_on = ((.graph[$src].depends_on // []) + [$tgt] | unique)' \
           "$graph_file" > "${graph_file}.tmp" && mv "${graph_file}.tmp" "$graph_file"

        ((applied++))
    done <<< "$(echo -e "$connections")"

    echo -e "${GREEN}✅ Applied ${applied} connections${NC}"
}

# Iterative connection finder - finds best connections in small batches
auto_connect_iterative() {
    local preview="${1:-false}"
    local threshold="${2:-$DEFAULT_SCORE_THRESHOLD}"
    local graph_file="${3:-$KNOWLEDGE_MAP}"
    local max_per_pass="${4:-5}"

    echo -e "${BLUE}🔍 Starting iterative connection discovery...${NC}"
    echo -e "${CYAN}Finding up to $max_per_pass connections per pass${NC}"

    # Load rules and cache nodes once
    load_dependency_rules
    echo -e "${BLUE}Loaded ${#ALLOWED_DEPS[@]} dependency rules${NC}"
    cache_all_nodes "$graph_file"

    # Cache existing dependencies for faster lookups
    declare -A EXISTING_DEPS
    echo -e "${BLUE}Caching existing dependencies...${NC}"
    local deps_data=$(jq -r '.graph | to_entries[] | "\(.key):\(.value.depends_on[]?)"' "$graph_file" 2>/dev/null)
    while IFS=: read -r src tgt; do
        [[ -z "$src" || -z "$tgt" ]] && continue
        EXISTING_DEPS["${src}->${tgt}"]=1
    done <<< "$deps_data"
    echo -e "${GREEN}Cached ${#EXISTING_DEPS[@]} existing connections${NC}"

    # Cache entities by type for fast access
    declare -A ENTITIES_BY_TYPE
    echo -e "${BLUE}Caching entities by type...${NC}"
    for etype in features interfaces actions components users objectives requirements behavior presentation data_models assets; do
        ENTITIES_BY_TYPE["$etype"]=$(jq -r ".entities.$etype | keys[]? | \"$etype:\\(.)\"" "$graph_file" 2>/dev/null | tr '\n' '|')
    done

    local total_found=0
    local pass_num=1

    while [[ $pass_num -le 10 ]]; do  # Max 10 passes
        echo
        echo -e "${YELLOW}=== Pass $pass_num ===${NC}"

        local pass_connections=""
        local pass_count=0

        # Get entities with fewest dependencies
        local entities_to_check=$(jq -r '
            .graph as $g |
            .entities | to_entries[] | .key as $type | .value | to_entries[] |
            "\($type):\(.key)" as $entity |
            "\($entity):\(($g[$entity].depends_on // []) | length)"
        ' "$graph_file" 2>/dev/null | sort -t: -k3 -n | head -10)

        echo -e "${CYAN}Checking 10 least-connected entities...${NC}"

        while IFS= read -r entity_line; do
            [[ -z "$entity_line" ]] && continue

            # Parse the line: entity_type:entity_name:dep_count
            local entity="${entity_line%:*}"  # Everything except last field
            local dep_count="${entity_line##*:}"  # Last field
            local entity_type="${entity%%:*}"  # First part of entity
            local entity_name="${entity#*:}"  # Rest of entity

            # Skip if already has enough connections
            [[ ${dep_count:-0} -ge 3 ]] && continue

            # Find single best match
            local best_match=""
            local best_score=0
            local checked=0

            # Get allowed target types for this entity type
            local allowed="${ALLOWED_DEPS[$entity_type]:-}"

            # If no allowed deps, skip this entity
            if [[ -z "$allowed" ]]; then
                echo -e "  ${YELLOW}⚠ No dependencies defined for $entity_type${NC}"
                continue
            fi

            echo -ne "\r${CYAN}Checking $entity (can connect to: $allowed)...${NC}" >&2

            # Only check nodes of allowed types (using cache)
            local nodes_to_check=""
            for allowed_type in $allowed; do
                # Get cached nodes of this type
                local type_nodes="${ENTITIES_BY_TYPE[$allowed_type]:-}"
                if [[ -n "$type_nodes" ]]; then
                    # Convert pipe-separated to newline-separated
                    nodes_to_check="${nodes_to_check}$(echo "$type_nodes" | tr '|' '\n')\n"
                fi
            done

            while IFS= read -r node; do
                [[ -z "$node" ]] && continue
                [[ "$node" == "$entity" ]] && continue

                ((checked++))
                local target_name="${node#*:}"
                local score=$(calculate_similarity_fast "$entity_name" "$target_name")

                if [[ $score -gt $best_score ]] && [[ $score -ge $threshold ]]; then
                    # Check not already connected using cache
                    local conn_key="${entity}->${node}"
                    if [[ -z "${EXISTING_DEPS[$conn_key]:-}" ]]; then
                        best_match="$node"
                        best_score=$score

                        # If we found a great match (>80%), stop looking
                        [[ $best_score -ge 80 ]] && break
                    fi
                fi

                # Stop after checking reasonable number of candidates
                [[ $checked -ge 50 ]] && break
            done <<< "$(echo -e "$nodes_to_check")"

            if [[ -n "$best_match" ]]; then
                pass_connections="${pass_connections}${entity}->${best_match}:${best_score}\n"
                echo -e "  ${GREEN}✓${NC} $entity → $best_match (${best_score}%)"
                ((pass_count++))

                [[ $pass_count -ge $max_per_pass ]] && break
            fi
        done <<< "$entities_to_check"

        # Also check reference patterns
        if [[ $pass_count -lt $max_per_pass ]]; then
            local ref_connections=$(connect_references_fast "$graph_file" "true" | head -2)
            if [[ -n "$ref_connections" ]]; then
                while IFS= read -r ref_conn; do
                    [[ -z "$ref_conn" ]] && continue
                    pass_connections="${pass_connections}${ref_conn}\n"
                    echo -e "  ${GREEN}✓${NC} Reference: $ref_conn"
                    ((pass_count++))
                    [[ $pass_count -ge $max_per_pass ]] && break
                done <<< "$ref_connections"
            fi
        fi

        if [[ $pass_count -eq 0 ]]; then
            echo -e "${YELLOW}No new connections found${NC}"
            break
        fi

        ((total_found += pass_count))

        if [[ "$preview" == "false" ]]; then
            # Apply this batch
            apply_connections "$pass_connections" "$graph_file"

            # Update cache with new connections
            while IFS= read -r conn; do
                [[ -z "$conn" ]] && continue
                local conn_key="${conn%:*}"  # Remove score
                EXISTING_DEPS["$conn_key"]=1
            done <<< "$(echo -e "$pass_connections")"
        fi

        ((pass_num++))
    done

    echo
    echo -e "${GREEN}✅ Found $total_found total connections${NC}"

    if [[ "$preview" == "true" ]]; then
        echo -e "${CYAN}Run without --preview to apply${NC}"
    fi
}

# Optimized main handler
connect_command() {
    # Load rules once at start
    load_dependency_rules

    local args=("$@")
    local preview=false
    local threshold=$DEFAULT_SCORE_THRESHOLD
    local iterative=false
    local entity=""
    local target=""

    for arg in "${args[@]}"; do
        case "$arg" in
            --auto)
                ;;
            --iterative)
                iterative=true
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
        if [[ "$iterative" == "true" ]] || [[ " ${args[@]} " =~ " --iterative " ]]; then
            auto_connect_iterative "$preview" "$threshold"
        else
            auto_connect_fast "$preview" "$threshold"
        fi
    elif [[ -n "$entity" ]]; then
        cache_all_nodes

        if [[ -n "$target" ]]; then
            # Connect specific entities
            local source_type="${entity%%:*}"
            local target_type="${target%%:*}"

            if is_valid_connection_fast "$source_type" "$target_type"; then
                echo -e "${GREEN}✓ Valid connection: $entity → $target${NC}"
                apply_connections "${entity}->${target}:100" "$KNOWLEDGE_MAP"
                return 0
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
                    echo -e "  → $target ${BLUE}(${score}% match)${NC}"
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
    know connect --auto --iterative [--preview] [--score-threshold=N]
        Iterative mode: finds 5 connections per pass

    know connect --auto [--preview] [--score-threshold=N]
        Full scan mode: attempts to find all connections at once

    know connect <entity>
        Find potential connections for a specific entity

    know connect <source> <target>
        Connect two specific entities

${YELLOW}OPTIONS:${NC}
    --iterative     Use iterative mode (finds 5 connections per pass)
    --preview       Show connections without applying them
    --score-threshold=N  Minimum similarity score (default: 40)

${YELLOW}OPTIMIZATIONS:${NC}
    ⚡ Iterative discovery - finds best matches in small batches
    ⚡ Prioritizes least-connected entities first
    ⚡ Node and keyword caching for speed
    ⚡ Early termination when good matches found
    ⚡ Type filtering to reduce search space

EOF
}