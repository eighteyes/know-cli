#!/bin/bash

# utils.sh - Common utility functions for know CLI

# Debug mode toggle
DEBUG=${DEBUG:-false}

# Path to dependency rules
DEPENDENCY_RULES="${LIB_DIR:-$(dirname "${BASH_SOURCE[0]}")}/dependency-rules.json"

# No longer need external jq utilities - functionality integrated

# Debug logging
debug() {
    [[ "$DEBUG" == "true" ]] && echo -e "${YELLOW}[DEBUG] $1${NC}" >&2
}

# Validate JSON with jq
validate_json() {
    local json_content="$1"
    echo "$json_content" | jq empty 2>/dev/null
}

# Get entity count by type
get_entity_stats() {
    jq -r '
        .entities | to_entries[] |
        "  \(.key): \(.value | length) entities"
    ' "$KNOWLEDGE_MAP"
}

# Get available entity types from dependency rules
get_entity_types() {
    if [[ -f "$DEPENDENCY_RULES" ]]; then
        # Get all unique entity types from allowed_dependencies
        (
            jq -r '.allowed_dependencies | keys[]' "$DEPENDENCY_RULES" 2>/dev/null
            jq -r '.allowed_dependencies | to_entries[] | .value[]' "$DEPENDENCY_RULES" 2>/dev/null
        ) | sort -u
    else
        # Fallback to getting from knowledge map
        apply_pattern "entities" "get_all_types" "$KNOWLEDGE_MAP" 2>/dev/null || \
        jq -r '.entities | keys[]' "$KNOWLEDGE_MAP" 2>/dev/null
    fi
}

# Check if entity exists (now uses centralized pattern)
entity_exists() {
    local entity_type="$1"
    local entity_id="$2"
    
    local entity_data
    entity_data=$(get_entity "$KNOWLEDGE_MAP" "$entity_type" "$entity_id")
    [[ "$entity_data" != "null" && -n "$entity_data" ]]
}

# List entities of a given type (now uses centralized pattern)
list_entities() {
    local entity_type="$1"
    
    if [[ -z "$entity_type" ]]; then
        echo "Available entity types:"
        get_entity_types | sed 's/^/  /'
        return
    fi
    
    # Check if entity type exists
    local type_exists
    type_exists=$(get_entity_types | grep -x "$entity_type" || true)
    if [[ -z "$type_exists" ]]; then
        error "Unknown entity type: $entity_type"
    fi
    
    echo "Entities of type '$entity_type':"
    "$MOD_GRAPH" list "$entity_type" 2>/dev/null | grep -v "^📋" | grep -v "^$" || true
}

# Normalize entity type (singular to plural)
normalize_entity_type() {
    local input_type="$1"

    case "$input_type" in
        user) echo "users" ;;
        screen) echo "screens" ;;
        component) echo "components" ;;
        feature) echo "features" ;;
        requirement) echo "requirements" ;;
        model) echo "schema" ;;
        platform) echo "platforms" ;;
        ui_component) echo "ui_components" ;;
        action) echo "actions" ;;
        *) echo "$input_type" ;;
    esac
}

# Parse entity reference (type:id)
parse_entity_ref() {
    local entity_ref="$1"
    
    if [[ "$entity_ref" =~ ^([a-z_]+):(.+)$ ]]; then
        local type="${BASH_REMATCH[1]}"
        local id="${BASH_REMATCH[2]}"
        echo "$(normalize_entity_type "$type") $id"
    else
        error "Invalid entity reference format: $entity_ref. Use 'type:id' format"
    fi
}

# Get entity name from reference (now uses centralized pattern)
get_entity_name() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    local id=$(echo "$type_id" | cut -d' ' -f2-)
    
    local entity_json
    entity_json=$("$MOD_GRAPH" show "$type" "$id" 2>/dev/null | sed -n '/Entity Details/,/^$/p' | sed '1d' | sed 's/\x1b\[[0-9;]*m//g')
    if [[ -n "$entity_json" ]]; then
        echo "$entity_json" | jq -r '.name // empty' 2>/dev/null || echo "$id"
    else
        echo "$id"
    fi
}

# Format acceptance criteria as checkboxes
format_acceptance_criteria() {
    local criteria_json="$1"
    
    echo "$criteria_json" | jq -r '
        to_entries[] |
        "### \(.key | ascii_upcase) Requirements\n" +
        (.value | map("- [ ] " + .) | join("\n"))
    ' | sed '/^$/d'
}

# Extract template variables from text
extract_template_vars() {
    local template_content="$1"
    grep -o '{{[^}]*}}' <<< "$template_content" | sort -u || true
}

# Get entity descriptions from dependency rules
get_entity_description() {
    local entity_type="$1"
    if [[ -f "$DEPENDENCY_RULES" ]]; then
        jq -r --arg type "$entity_type" '.entity_descriptions[$type] // ""' "$DEPENDENCY_RULES" 2>/dev/null
    fi
}

# Get reference categories from dependency rules
get_reference_categories() {
    if [[ -f "$DEPENDENCY_RULES" ]]; then
        jq -r '.reference_categories | keys[]' "$DEPENDENCY_RULES" 2>/dev/null
    fi
}

# Get reference category description
get_reference_description() {
    local category="$1"
    if [[ -f "$DEPENDENCY_RULES" ]]; then
        jq -r --arg cat "$category" '.reference_categories[$cat] // ""' "$DEPENDENCY_RULES" 2>/dev/null
    fi
}

# Get allowed dependencies for an entity type
get_allowed_dependencies() {
    local entity_type="$1"
    # Normalize to singular form for lookup
    local singular_type="${entity_type%s}"
    if [[ -f "$DEPENDENCY_RULES" ]]; then
        jq -r --arg type "$singular_type" '.allowed_dependencies[$type] // [] | .[]' "$DEPENDENCY_RULES" 2>/dev/null
    fi
}