#!/bin/bash

# dynamic-commands.sh - Dynamic command generation based on dependency rules

# Load dependency rules and generate available commands
load_dynamic_commands() {
    local rules_file="${1:-$LIB_DIR/dependency-rules.json}"

    if [[ ! -f "$rules_file" ]]; then
        return 1
    fi

    # Extract entity types from rules
    DYNAMIC_ENTITY_TYPES=$(jq -r '.allowed_dependencies | keys[]' "$rules_file" 2>/dev/null | sort -u)
}

# Check if a dependency is allowed based on rules
is_dependency_allowed() {
    local from_type="$1"
    local to_type="$2"
    local rules_file="${3:-$LIB_DIR/dependency-rules.json}"

    # Normalize types (remove plurals)
    from_type="${from_type%s}"
    to_type="${to_type%s}"

    # Check if the dependency is in allowed list
    jq -e --arg from "$from_type" --arg to "$to_type" '
        .allowed_dependencies[$from] // [] | index($to)
    ' "$rules_file" >/dev/null 2>&1
}

# Generate help text based on available entity types
generate_dynamic_help() {
    local rules_file="${1:-$LIB_DIR/dependency-rules.json}"

    echo "ENTITY TYPES (from dependency rules):"
    jq -r '.allowed_dependencies | keys[]' "$rules_file" 2>/dev/null | while read -r entity_type; do
        # Get allowed dependencies for this type
        local deps=$(jq -r --arg type "$entity_type" '.allowed_dependencies[$type] | join(", ")' "$rules_file")
        echo "    $entity_type → $deps"
    done
    echo ""

    echo "DEPENDENCY RULES:"
    jq -r '
        .allowed_dependencies | to_entries[] |
        "    \(.key) can depend on: \(.value | join(", "))"
    ' "$rules_file" 2>/dev/null
}

# Validate a connection based on dependency rules
validate_connection() {
    local from_ref="$1"
    local to_ref="$2"
    local rules_file="${3:-$LIB_DIR/dependency-rules.json}"

    # Extract types from references
    local from_type=$(echo "$from_ref" | cut -d: -f1)
    local to_type=$(echo "$to_ref" | cut -d: -f1)

    if is_dependency_allowed "$from_type" "$to_type" "$rules_file"; then
        echo "✅ Valid: $from_type → $to_type"
        return 0
    else
        echo "❌ Invalid: $from_type cannot depend on $to_type"
        echo "Allowed dependencies for $from_type:"
        jq -r --arg type "${from_type%s}" '.allowed_dependencies[$type] // [] | .[]' "$rules_file" | sed 's/^/  - /'
        return 1
    fi
}

# Generate entity commands dynamically
generate_entity_commands() {
    local rules_file="${1:-$LIB_DIR/dependency-rules.json}"

    # Get all entity types that can exist
    local all_types=$(jq -r '
        [.allowed_dependencies | keys[], .allowed_dependencies | .[] | .[]] |
        unique | .[]
    ' "$rules_file" 2>/dev/null)

    echo "$all_types" | while read -r entity_type; do
        # Create list command
        echo "    know list $entity_type                    List all ${entity_type}s"
        # Create spec generation command
        echo "    know $entity_type <id>                   Generate $entity_type specification"
    done
}

# Auto-detect valid entity types from graph
detect_entity_types() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    jq -r '.entities | keys[]' "$graph_file" 2>/dev/null | sort -u
}

# Suggest valid connections based on rules
suggest_connections() {
    local entity_ref="$1"
    local rules_file="${2:-$LIB_DIR/dependency-rules.json}"
    local graph_file="${3:-$KNOWLEDGE_MAP}"

    local entity_type=$(echo "$entity_ref" | cut -d: -f1)
    entity_type="${entity_type%s}"

    echo "Valid dependency types for $entity_ref ($entity_type):"

    # Get allowed dependency types
    local allowed_types=$(jq -r --arg type "$entity_type" '
        .allowed_dependencies[$type] // [] | .[]
    ' "$rules_file")

    if [[ -z "$allowed_types" ]]; then
        echo "  No dependencies allowed for $entity_type"
        return
    fi

    echo "$allowed_types" | while read -r dep_type; do
        echo ""
        echo "  $dep_type entities you can depend on:"

        # Find entities of this type
        local plural_type="${dep_type}s"
        jq -r --arg type "$plural_type" '
            .entities[$type] // {} | keys[] | "    - " + $type + ":" + .
        ' "$graph_file" 2>/dev/null | head -5
    done
}

# Enforce dependency rules when connecting entities
enforce_connection_rules() {
    local from_ref="$1"
    local to_ref="$2"
    local rules_file="${3:-$LIB_DIR/dependency-rules.json}"

    if ! validate_connection "$from_ref" "$to_ref" "$rules_file"; then
        echo ""
        echo "Suggestion: Try reversing the dependency or use a different entity type."
        suggest_connections "$from_ref" "$rules_file"
        return 1
    fi

    return 0
}

# Export functions for use in main know script
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Being sourced - make functions available
    true
fi