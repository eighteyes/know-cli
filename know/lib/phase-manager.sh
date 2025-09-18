#!/bin/bash

# phase-manager.sh - Manage implementation phases in spec-graph.json
# Provides display, restructure, and prioritization of project phases

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$PROJECT_ROOT/.ai/spec-graph.json}"
QUERY_GRAPH="$SCRIPT_DIR/query-graph.sh"
MOD_GRAPH="$SCRIPT_DIR/mod-graph.sh"
MAX_WORK_DEFAULT=10
VERBOSE=false
SAVE_CHANGES=false
OUTPUT_FORMAT="text"

# Error handling
error() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${BLUE}ℹ $1${NC}" >&2
}

success() {
    echo -e "${GREEN}✓ $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}" >&2
}

# Show usage
usage() {
    cat << EOF
Phase Manager - Manage implementation phases for the project

USAGE:
    $(basename "$0") <command> [options]

COMMANDS:
    display              Show current phases and their entities
    restructure          Generate optimal phases based on dependencies
    prioritize           Interactive mode to adjust entity priorities
    validate             Check phase dependency validity
    stats                Show phase statistics and metrics

OPTIONS:
    --save               Save changes to spec-graph.json
    --max-work <N>       Max entities per phase (default: $MAX_WORK_DEFAULT)
    --json               Output in JSON format
    --verbose            Show detailed dependency information
    --file <path>        Use custom knowledge map file

EXAMPLES:
    # Display current phases
    $(basename "$0") display

    # Restructure with max 5 entities per phase
    $(basename "$0") restructure --max-work 5

    # Interactively prioritize entities
    $(basename "$0") prioritize

    # Save restructured phases
    $(basename "$0") restructure --save

EOF
}

# Parse command line arguments
parse_args() {
    local args=("$@")
    local i=0

    # First pass: identify the command
    COMMAND=""
    for arg in "${args[@]}"; do
        case "$arg" in
            display|show)
                COMMAND="display"
                break
                ;;
            restructure|rebuild)
                COMMAND="restructure"
                break
                ;;
            prioritize|adjust)
                COMMAND="prioritize"
                break
                ;;
            validate|check)
                COMMAND="validate"
                break
                ;;
            stats|statistics)
                COMMAND="stats"
                break
                ;;
            help|--help|-h)
                usage
                exit 0
                ;;
        esac
    done

    # Default to display if no command found
    [[ -z "$COMMAND" ]] && COMMAND="display"

    # Second pass: parse options
    i=0
    while [[ $i -lt ${#args[@]} ]]; do
        case "${args[$i]}" in
            display|show|restructure|rebuild|prioritize|adjust|validate|check|stats|statistics)
                # Skip command argument
                ((i++))
                ;;
            --save)
                SAVE_CHANGES=true
                ((i++))
                ;;
            --max-work)
                if [[ $((i + 1)) -lt ${#args[@]} ]]; then
                    MAX_WORK="${args[$((i + 1))]}"
                    ((i += 2))
                else
                    error "Option --max-work requires a value"
                fi
                ;;
            --json)
                OUTPUT_FORMAT="json"
                ((i++))
                ;;
            --verbose|-v)
                VERBOSE=true
                ((i++))
                ;;
            --file)
                if [[ $((i + 1)) -lt ${#args[@]} ]]; then
                    KNOWLEDGE_MAP="${args[$((i + 1))]}"
                    ((i += 2))
                else
                    error "Option --file requires a value"
                fi
                ;;
            *)
                ((i++))
                ;;
        esac
    done
}

# Get entity name from reference
get_entity_name() {
    local entity_ref="$1"
    local entity_type="${entity_ref%%:*}"
    local entity_id="${entity_ref#*:}"

    # Handle pluralization
    local entity_type_plural="$entity_type"
    case "$entity_type" in
        user) entity_type_plural="users" ;;
        feature) entity_type_plural="features" ;;
        component) entity_type_plural="components" ;;
        requirement) entity_type_plural="requirements" ;;
        objective) entity_type_plural="objectives" ;;
        interface) entity_type_plural="interfaces" ;;
        action) entity_type_plural="actions" ;;
    esac

    jq -r ".entities.${entity_type_plural}.\"$entity_id\".name // \"$entity_id\"" "$KNOWLEDGE_MAP" 2>/dev/null || echo "$entity_id"
}

# Display current phases
display_phases() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        jq '.meta.project.phases' "$KNOWLEDGE_MAP"
        return
    fi

    echo -e "\n${BOLD}📊 Current Implementation Phases${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    local phase_count=$(jq '.meta.project.phases | length' "$KNOWLEDGE_MAP")

    for ((i=0; i<phase_count; i++)); do
        local phase_id=$(jq -r ".meta.project.phases[$i].id" "$KNOWLEDGE_MAP")
        local phase_name=$(jq -r ".meta.project.phases[$i].name" "$KNOWLEDGE_MAP")
        local phase_desc=$(jq -r ".meta.project.phases[$i].description // \"\"" "$KNOWLEDGE_MAP")
        local parallelizable=$(jq -r ".meta.project.phases[$i].parallelizable // true" "$KNOWLEDGE_MAP")
        local requirements=$(jq -r ".meta.project.phases[$i].requirements[]" "$KNOWLEDGE_MAP" 2>/dev/null)
        local req_count=$(jq ".meta.project.phases[$i].requirements | length" "$KNOWLEDGE_MAP")

        # Phase header
        echo -e "${MAGENTA}Phase $((i+1)): $phase_name${NC}"
        [[ -n "$phase_desc" ]] && echo -e "${CYAN}  $phase_desc${NC}"
        echo -e "  ${YELLOW}Parallelizable:${NC} $parallelizable"
        echo -e "  ${YELLOW}Entities:${NC} $req_count"

        # Show entities in this phase
        if [[ -n "$requirements" ]]; then
            echo -e "  ${YELLOW}Contents:${NC}"
            while IFS= read -r entity; do
                local entity_name=$(get_entity_name "$entity")
                local entity_type="${entity%%:*}"

                # Color code by type
                case "$entity_type" in
                    user) type_color="${GREEN}" ;;
                    objective) type_color="${BLUE}" ;;
                    requirement) type_color="${YELLOW}" ;;
                    feature) type_color="${MAGENTA}" ;;
                    interface) type_color="${CYAN}" ;;
                    action) type_color="${RED}" ;;
                    component) type_color="${GREEN}" ;;
                    *) type_color="${NC}" ;;
                esac

                echo -e "    ${type_color}• $entity${NC} - $entity_name"

                # Show dependencies if verbose
                if [[ "$VERBOSE" == "true" ]]; then
                    local deps=$("$QUERY_GRAPH" deps "$entity" 2>/dev/null | grep "^  " | head -5)
                    if [[ -n "$deps" ]]; then
                        echo -e "      ${CYAN}└─ Dependencies:${NC}"
                        echo "$deps" | while IFS= read -r dep; do
                            echo -e "        $dep"
                        done
                    fi
                fi
            done <<< "$requirements"
        fi
        echo
    done
}

# Calculate dependency depth for an entity
get_dependency_depth() {
    local entity="$1"
    local max_depth=0
    local visited=()

    # Recursive function to find max depth
    find_depth() {
        local current="$1"
        local depth="$2"

        # Check if already visited (cycle detection)
        for v in "${visited[@]}"; do
            [[ "$v" == "$current" ]] && return
        done
        visited+=("$current")

        # Get dependencies
        local deps=$(jq -r ".graph.\"$current\".depends_on[]?" "$KNOWLEDGE_MAP" 2>/dev/null)

        if [[ -z "$deps" ]]; then
            # No dependencies, this is depth
            [[ $depth -gt $max_depth ]] && max_depth=$depth
        else
            # Check each dependency
            while IFS= read -r dep; do
                [[ -n "$dep" ]] && find_depth "$dep" $((depth + 1))
            done <<< "$deps"
        fi
    }

    find_depth "$entity" 0
    echo "$max_depth"
}

# Restructure phases based on dependencies
restructure_phases() {
    local max_work="${MAX_WORK:-$MAX_WORK_DEFAULT}"

    echo -e "\n${BOLD}🔄 Restructuring Phases${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    info "Analyzing dependency graph..."
    info "Max entities per phase: $max_work"

    # Get all entities from graph
    local all_entities=$(jq -r '.graph | keys[]' "$KNOWLEDGE_MAP" | sort -u)

    # Calculate dependency depth for each entity
    declare -A entity_depths
    declare -A depth_entities

    while IFS= read -r entity; do
        [[ -z "$entity" ]] && continue
        local depth=$(get_dependency_depth "$entity")
        entity_depths["$entity"]=$depth

        # Group entities by depth
        if [[ -n "${depth_entities[$depth]:-}" ]]; then
            depth_entities[$depth]+=" $entity"
        else
            depth_entities[$depth]="$entity"
        fi
    done <<< "$all_entities"

    # Find max depth
    local max_depth=0
    for d in "${!depth_entities[@]}"; do
        [[ $d -gt $max_depth ]] && max_depth=$d
    done

    info "Found $((max_depth + 1)) dependency levels"

    # Create phases based on depth levels
    local phases_json='[]'
    local phase_num=1

    for ((depth=0; depth<=max_depth; depth++)); do
        [[ -z "${depth_entities[$depth]:-}" ]] && continue

        local entities=(${depth_entities[$depth]})
        local entity_count=${#entities[@]}

        # Split into multiple phases if too many entities
        local start_idx=0
        while [[ $start_idx -lt $entity_count ]]; do
            local end_idx=$((start_idx + max_work))
            [[ $end_idx -gt $entity_count ]] && end_idx=$entity_count

            # Create phase object
            local phase_entities='[]'
            for ((i=start_idx; i<end_idx; i++)); do
                phase_entities=$(echo "$phase_entities" | jq ". += [\"${entities[$i]}\"]")
            done

            # Determine phase name based on entity types
            local phase_name="Phase $phase_num"
            local phase_desc="Dependency level $depth"
            local parallelizable="true"

            if [[ $depth -eq 0 ]]; then
                phase_name="Foundation"
                phase_desc="Core entities with no dependencies"
                parallelizable="false"
            elif [[ $depth -eq 1 ]]; then
                phase_name="Core Services"
                phase_desc="Essential services that enable features"
            elif [[ $depth -eq 2 ]]; then
                phase_name="Features"
                phase_desc="Business capabilities and user features"
            elif [[ $depth -eq 3 ]]; then
                phase_name="Interfaces"
                phase_desc="User-facing components and screens"
            else
                phase_name="Integration Layer $((depth - 3))"
                phase_desc="Higher-level integration components"
            fi

            # Add sub-numbering if split
            if [[ $entity_count -gt $max_work ]]; then
                local sub_num=$(( (start_idx / max_work) + 1 ))
                local total_subs=$(( (entity_count + max_work - 1) / max_work ))
                phase_name="$phase_name (Part $sub_num/$total_subs)"
            fi

            local phase_obj=$(jq -n \
                --arg id "phase_${phase_num}" \
                --arg name "$phase_name" \
                --arg desc "$phase_desc" \
                --argjson parallel "$parallelizable" \
                --argjson reqs "$phase_entities" \
                '{
                    id: $id,
                    name: $name,
                    description: $desc,
                    parallelizable: $parallel,
                    requirements: $reqs
                }')

            phases_json=$(echo "$phases_json" | jq ". += [$phase_obj]")

            start_idx=$end_idx
            phase_num=$((phase_num + 1))
        done
    done

    # Display proposed phases
    echo -e "${GREEN}✓ Generated ${phase_num} phases${NC}\n"

    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "$phases_json"
    else
        # Display in readable format
        echo "$phases_json" | jq -r '.[] |
            "\(.name)\n  Entities: \(.requirements | length)\n  Parallelizable: \(.parallelizable)\n"'
    fi

    # Save if requested
    if [[ "$SAVE_CHANGES" == "true" ]]; then
        save_phases "$phases_json"
    else
        echo
        info "Use --save to update spec-graph.json with these phases"
    fi
}

# Interactive prioritization
prioritize_entities() {
    echo -e "\n${BOLD}🎯 Interactive Phase Prioritization${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    # Load current phases
    local phases=$(jq '.meta.project.phases' "$KNOWLEDGE_MAP")
    local modified=false

    while true; do
        echo -e "\n${YELLOW}Commands:${NC}"
        echo "  move <entity> to <phase_num>  - Move entity to phase"
        echo "  promote <entity>               - Move entity to earlier phase"
        echo "  demote <entity>                - Move entity to later phase"
        echo "  swap <entity1> <entity2>       - Swap two entities"
        echo "  show                           - Display current phases"
        echo "  save                           - Save changes"
        echo "  quit                           - Exit without saving"
        echo

        read -p "Command> " cmd args

        case "$cmd" in
            move)
                local entity=$(echo "$args" | awk '{print $1}')
                local to_phase=$(echo "$args" | awk '{print $3}')

                if [[ -n "$entity" && -n "$to_phase" ]]; then
                    phases=$(move_entity "$phases" "$entity" "$to_phase")
                    modified=true
                    success "Moved $entity to phase $to_phase"
                else
                    error "Usage: move <entity> to <phase_num>"
                fi
                ;;

            promote)
                local entity="$args"
                if [[ -n "$entity" ]]; then
                    phases=$(promote_entity "$phases" "$entity")
                    modified=true
                    success "Promoted $entity"
                else
                    error "Usage: promote <entity>"
                fi
                ;;

            demote)
                local entity="$args"
                if [[ -n "$entity" ]]; then
                    phases=$(demote_entity "$phases" "$entity")
                    modified=true
                    success "Demoted $entity"
                else
                    error "Usage: demote <entity>"
                fi
                ;;

            swap)
                local entity1=$(echo "$args" | awk '{print $1}')
                local entity2=$(echo "$args" | awk '{print $2}')

                if [[ -n "$entity1" && -n "$entity2" ]]; then
                    phases=$(swap_entities "$phases" "$entity1" "$entity2")
                    modified=true
                    success "Swapped $entity1 and $entity2"
                else
                    error "Usage: swap <entity1> <entity2>"
                fi
                ;;

            show)
                echo "$phases" | jq -r '.[] |
                    "\n\(.name) (\(.requirements | length) entities):\n" +
                    (.requirements | map("  • " + .) | join("\n"))'
                ;;

            save)
                if [[ "$modified" == "true" ]]; then
                    save_phases "$phases"
                    success "Changes saved to $KNOWLEDGE_MAP"
                else
                    info "No changes to save"
                fi
                break
                ;;

            quit|exit)
                if [[ "$modified" == "true" ]]; then
                    read -p "Discard changes? (y/N) " -n 1 -r
                    echo
                    [[ $REPLY =~ ^[Yy]$ ]] && break
                else
                    break
                fi
                ;;

            *)
                warning "Unknown command: $cmd"
                ;;
        esac
    done
}

# Move entity to a specific phase
move_entity() {
    local phases="$1"
    local entity="$2"
    local target_phase="$3"

    # Remove entity from all phases
    phases=$(echo "$phases" | jq "map(.requirements -= [\"$entity\"])")

    # Add to target phase (0-indexed)
    local phase_idx=$((target_phase - 1))
    phases=$(echo "$phases" | jq ".[$phase_idx].requirements += [\"$entity\"]")

    echo "$phases"
}

# Promote entity to earlier phase
promote_entity() {
    local phases="$1"
    local entity="$2"

    # Find current phase
    local current_phase=$(echo "$phases" | jq -r "to_entries[] | select(.value.requirements[] == \"$entity\") | .key")

    if [[ -n "$current_phase" && "$current_phase" -gt 0 ]]; then
        local new_phase=$((current_phase))
        phases=$(move_entity "$phases" "$entity" "$new_phase")
    else
        warning "Cannot promote $entity further"
    fi

    echo "$phases"
}

# Demote entity to later phase
demote_entity() {
    local phases="$1"
    local entity="$2"

    # Find current phase
    local current_phase=$(echo "$phases" | jq -r "to_entries[] | select(.value.requirements[] == \"$entity\") | .key")
    local max_phase=$(echo "$phases" | jq 'length - 1')

    if [[ -n "$current_phase" && "$current_phase" -lt "$max_phase" ]]; then
        local new_phase=$((current_phase + 2))
        phases=$(move_entity "$phases" "$entity" "$new_phase")
    else
        warning "Cannot demote $entity further"
    fi

    echo "$phases"
}

# Swap two entities
swap_entities() {
    local phases="$1"
    local entity1="$2"
    local entity2="$3"

    # Find phases
    local phase1=$(echo "$phases" | jq -r "to_entries[] | select(.value.requirements[] == \"$entity1\") | .key")
    local phase2=$(echo "$phases" | jq -r "to_entries[] | select(.value.requirements[] == \"$entity2\") | .key")

    if [[ -n "$phase1" && -n "$phase2" ]]; then
        phases=$(move_entity "$phases" "$entity1" $((phase2 + 1)))
        phases=$(move_entity "$phases" "$entity2" $((phase1 + 1)))
    else
        warning "Could not find both entities in phases"
    fi

    echo "$phases"
}

# Validate phase dependencies
validate_phases() {
    echo -e "\n${BOLD}🔍 Validating Phase Dependencies${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    local phases=$(jq '.meta.project.phases' "$KNOWLEDGE_MAP")
    local phase_count=$(echo "$phases" | jq 'length')
    local violations=0

    # Check each phase
    for ((i=0; i<phase_count; i++)); do
        local phase_name=$(echo "$phases" | jq -r ".[$i].name")
        local requirements=$(echo "$phases" | jq -r ".[$i].requirements[]" 2>/dev/null)

        echo -e "${MAGENTA}Checking Phase $((i+1)): $phase_name${NC}"

        # Check each entity in this phase
        while IFS= read -r entity; do
            [[ -z "$entity" ]] && continue

            # Get dependencies
            local deps=$(jq -r ".graph.\"$entity\".depends_on[]?" "$KNOWLEDGE_MAP" 2>/dev/null)

            while IFS= read -r dep; do
                [[ -z "$dep" ]] && continue

                # Find which phase the dependency is in
                local dep_phase=-1
                for ((j=0; j<phase_count; j++)); do
                    if echo "$phases" | jq -e ".[$j].requirements[] | select(. == \"$dep\")" >/dev/null 2>&1; then
                        dep_phase=$j
                        break
                    fi
                done

                # Check if dependency is in earlier phase
                if [[ $dep_phase -ge $i ]]; then
                    echo -e "  ${RED}✗ Violation:${NC} $entity depends on $dep (Phase $((dep_phase+1)))"
                    violations=$((violations + 1))
                fi
            done <<< "$deps"
        done <<< "$requirements"
    done

    echo
    if [[ $violations -eq 0 ]]; then
        success "All phase dependencies are valid!"
    else
        error "Found $violations dependency violations"
    fi
}

# Show phase statistics
show_stats() {
    echo -e "\n${BOLD}📈 Phase Statistics${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    local phases=$(jq '.meta.project.phases' "$KNOWLEDGE_MAP")
    local phase_count=$(echo "$phases" | jq 'length')
    local total_entities=$(echo "$phases" | jq '[.[].requirements | length] | add')

    echo -e "${YELLOW}Summary:${NC}"
    echo -e "  Total phases: $phase_count"
    echo -e "  Total entities: $total_entities"
    echo -e "  Average per phase: $((total_entities / phase_count))"
    echo

    # Entity type distribution
    echo -e "${YELLOW}Entity Distribution:${NC}"
    declare -A type_counts

    for ((i=0; i<phase_count; i++)); do
        local requirements=$(echo "$phases" | jq -r ".[$i].requirements[]" 2>/dev/null)

        while IFS= read -r entity; do
            [[ -z "$entity" ]] && continue
            local entity_type="${entity%%:*}"
            type_counts["$entity_type"]=$((${type_counts["$entity_type"]:-0} + 1))
        done <<< "$requirements"
    done

    for type in "${!type_counts[@]}"; do
        echo -e "  $type: ${type_counts[$type]}"
    done | sort

    echo

    # Phase workload
    echo -e "${YELLOW}Phase Workload:${NC}"
    for ((i=0; i<phase_count; i++)); do
        local phase_name=$(echo "$phases" | jq -r ".[$i].name")
        local entity_count=$(echo "$phases" | jq ".[$i].requirements | length")
        local parallelizable=$(echo "$phases" | jq -r ".[$i].parallelizable")

        # Create bar graph
        local bar=""
        for ((j=0; j<entity_count; j++)); do
            bar+="█"
        done

        printf "  Phase %d: %-20s %2d %s\n" $((i+1)) "$phase_name" "$entity_count" "$bar"

        if [[ "$parallelizable" == "false" ]]; then
            echo "           (Sequential - must complete before next phase)"
        fi
    done
}

# Save phases to spec-graph.json
save_phases() {
    local new_phases="$1"

    # Create backup
    local backup_file="${KNOWLEDGE_MAP}.backup.$(date +%s)"
    cp "$KNOWLEDGE_MAP" "$backup_file"
    info "Created backup: $backup_file"

    # Update spec-graph.json
    local updated=$(jq --argjson phases "$new_phases" '.meta.project.phases = $phases' "$KNOWLEDGE_MAP")

    echo "$updated" > "$KNOWLEDGE_MAP"
    success "Updated phases in $KNOWLEDGE_MAP"
}

# Main execution
main() {
    parse_args "$@"

    # Check if knowledge map exists
    if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
        error "Knowledge map not found: $KNOWLEDGE_MAP"
    fi

    # Execute command
    case "${COMMAND:-display}" in
        display)
            display_phases
            ;;
        restructure)
            restructure_phases
            ;;
        prioritize)
            prioritize_entities
            ;;
        validate)
            validate_phases
            ;;
        stats)
            show_stats
            ;;
        *)
            error "Unknown command: $COMMAND"
            ;;
    esac
}

# Run main function
main "$@"