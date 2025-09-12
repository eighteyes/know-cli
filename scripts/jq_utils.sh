#!/bin/bash

# JQ Utilities - Centralized jq pattern loader and executor
# Uses jq_ref.json for consistent graph operations across all scripts

set -euo pipefail

# Path to jq reference file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
JQ_REF_FILE="${JQ_REF_FILE:-$SCRIPT_DIR/jq_ref.json}"

# Validate jq_ref.json exists
if [[ ! -f "$JQ_REF_FILE" ]]; then
    echo "Error: jq_ref.json not found at $JQ_REF_FILE" >&2
    exit 1
fi

# Load a jq pattern by category and name
load_jq_pattern() {
    local category="$1"
    local pattern="$2"
    
    local jq_pattern
    jq_pattern=$(jq -r --arg cat "$category" --arg pat "$pattern" \
        '.patterns[$cat][$pat] // empty' "$JQ_REF_FILE")
    
    if [[ -z "$jq_pattern" ]]; then
        echo "Error: Pattern not found: $category.$pattern" >&2
        return 1
    fi
    
    echo "$jq_pattern"
}

# Apply a jq pattern with variable substitution
apply_pattern() {
    local category="$1"
    local pattern="$2"
    local knowledge_map="$3"
    shift 3
    
    local jq_pattern
    jq_pattern=$(load_jq_pattern "$category" "$pattern")
    
    if [[ -n "$jq_pattern" ]]; then
        jq -r "$jq_pattern" "$@" "$knowledge_map"
    else
        return 1
    fi
}

# Apply pattern with common entity variables
apply_entity_pattern() {
    local category="$1"
    local pattern="$2" 
    local knowledge_map="$3"
    local entity_type="$4"
    local entity_id="${5:-}"
    
    local jq_pattern
    jq_pattern=$(load_jq_pattern "$category" "$pattern")
    
    if [[ -n "$entity_id" ]]; then
        jq -r --arg type "$entity_type" --arg id "$entity_id" \
            "$jq_pattern" "$knowledge_map"
    else
        jq -r --arg type "$entity_type" \
            "$jq_pattern" "$knowledge_map"
    fi
}

# Apply pattern with graph entity reference
apply_graph_pattern() {
    local category="$1"
    local pattern="$2"
    local knowledge_map="$3"
    local entity_ref="$4"
    
    local jq_pattern
    jq_pattern=$(load_jq_pattern "$category" "$pattern")
    
    jq -r --arg entity "$entity_ref" \
        "$jq_pattern" "$knowledge_map"
}

# List available patterns in a category
list_patterns() {
    local category="${1:-}"
    
    if [[ -n "$category" ]]; then
        jq -r --arg cat "$category" \
            '.patterns[$cat] | keys[]' "$JQ_REF_FILE"
    else
        jq -r '.patterns | keys[]' "$JQ_REF_FILE"
    fi
}

# Get all entity types using standardized pattern
get_entity_types() {
    local knowledge_map="$1"
    apply_pattern "entities" "get_all_types" "$knowledge_map"
}

# Get entities of a specific type
get_type_entities() {
    local knowledge_map="$1"
    local entity_type="$2"
    apply_entity_pattern "entities" "get_type_entities" "$knowledge_map" "$entity_type"
}

# Get entity details
get_entity() {
    local knowledge_map="$1"
    local entity_type="$2"
    local entity_id="$3"
    apply_entity_pattern "entities" "get_entity" "$knowledge_map" "$entity_type" "$entity_id"
}

# Get entity name
get_entity_name() {
    local knowledge_map="$1"
    local entity_type="$2"
    local entity_id="$3"
    apply_entity_pattern "entities" "get_entity_name" "$knowledge_map" "$entity_type" "$entity_id"
}

# Get entity dependencies from graph
get_entity_dependencies() {
    local knowledge_map="$1"
    local entity_ref="$2"
    apply_graph_pattern "graph" "get_dependencies" "$knowledge_map" "$entity_ref"
}

# Find what depends on an entity
find_dependents() {
    local knowledge_map="$1"
    local target_entity="$2"
    jq -r --arg target "$target_entity" \
        "$(load_jq_pattern "graph" "find_dependents")" "$knowledge_map"
}

# Get acceptance criteria for entity
get_acceptance_criteria() {
    local knowledge_map="$1"
    local entity_type="$2"
    local entity_id="$3"
    apply_entity_pattern "entities" "get_acceptance_criteria" "$knowledge_map" "$entity_type" "$entity_id"
}

# Get description from references
get_description() {
    local knowledge_map="$1"
    local desc_ref="$2"
    jq -r --arg ref "$desc_ref" \
        "$(load_jq_pattern "references" "get_description")" "$knowledge_map"
}

# Validate entity exists in graph
entity_exists_in_graph() {
    local knowledge_map="$1"
    local entity_ref="$2"
    local exists
    exists=$(jq -r --arg entity "$entity_ref" \
        "$(load_jq_pattern "graph" "entity_exists_in_graph")" "$knowledge_map")
    [[ "$exists" == "true" ]]
}

# Find circular dependencies
find_circular_dependencies() {
    local knowledge_map="$1"
    jq -r "$(load_jq_pattern "analysis" "circular_dependencies")" "$knowledge_map"
}

# Get dependency chains for entity
get_dependency_chains() {
    local knowledge_map="$1"
    local entity_ref="$2"
    jq -r --arg entity "$entity_ref" \
        "$(load_jq_pattern "analysis" "dependency_chains")" "$knowledge_map"
}

# Generate system summary
generate_system_summary() {
    local knowledge_map="$1"
    jq "$(load_jq_pattern "reporting" "system_summary")" "$knowledge_map"
}

# Find orphaned entities
find_orphaned_entities() {
    local knowledge_map="$1"
    jq -r "$(load_jq_pattern "graph" "find_orphaned_entities")" "$knowledge_map"
}

# Get critical dependencies (most used)
get_critical_dependencies() {
    local knowledge_map="$1"
    jq -r "$(load_jq_pattern "analysis" "critical_dependencies")" "$knowledge_map"
}

# Validate reference integrity
validate_reference_integrity() {
    local knowledge_map="$1"
    jq -r "$(load_jq_pattern "validation" "reference_integrity")" "$knowledge_map"
}

# Search entities by name
search_entities_by_name() {
    local knowledge_map="$1"
    local entity_type="$2"
    local search_term="$3"
    jq -r --arg type "$entity_type" --arg term "$search_term" \
        "$(load_jq_pattern "entities" "search_entities_by_name")" "$knowledge_map"
}

# Count dependencies for entity
count_entity_dependencies() {
    local knowledge_map="$1"
    local entity_ref="$2"
    jq -r --arg entity "$entity_ref" \
        "$(load_jq_pattern "graph" "count_dependencies")" "$knowledge_map"
}

# Helper function for scripts to validate they have required parameters
require_params() {
    local required_count="$1"
    local actual_count="$2"
    local usage_msg="$3"
    
    if [[ $actual_count -lt $required_count ]]; then
        echo "Error: Insufficient parameters" >&2
        echo "$usage_msg" >&2
        exit 1
    fi
}

# Debug function to show pattern content
debug_pattern() {
    local category="$1"
    local pattern="$2"
    
    echo "Pattern: $category.$pattern"
    echo "Content:"
    load_jq_pattern "$category" "$pattern" | sed 's/^/  /'
}

# Check if jq_ref.json is valid
validate_jq_ref() {
    if ! jq empty "$JQ_REF_FILE" 2>/dev/null; then
        echo "Error: Invalid JSON in $JQ_REF_FILE" >&2
        return 1
    fi
    
    # Check required sections exist
    local required_sections=("patterns" "functions" "meta")
    for section in "${required_sections[@]}"; do
        if ! jq -e "has(\"$section\")" "$JQ_REF_FILE" >/dev/null; then
            echo "Error: Missing required section '$section' in jq_ref.json" >&2
            return 1
        fi
    done
    
    echo "jq_ref.json is valid"
}

# Show usage information
show_jq_utils_usage() {
    cat << EOF
JQ Utils - Centralized jq pattern utilities

USAGE:
    source scripts/jq_utils.sh
    
FUNCTIONS:
    load_jq_pattern <category> <pattern>                Load jq pattern string
    apply_pattern <category> <pattern> <file> [args]    Apply pattern to file
    get_entity_types <knowledge_map>                     Get all entity types
    get_entity <knowledge_map> <type> <id>               Get entity details
    get_entity_dependencies <knowledge_map> <ref>       Get entity dependencies
    find_dependents <knowledge_map> <target>           Find what depends on target
    find_circular_dependencies <knowledge_map>         Find circular deps
    generate_system_summary <knowledge_map>            Generate summary report
    
EXAMPLES:
    # Get all entity types
    get_entity_types knowledge-map-cmd.json
    
    # Get feature details
    get_entity knowledge-map-cmd.json features real-time-telemetry
    
    # Find what depends on a feature
    find_dependents knowledge-map-cmd.json feature:real-time-telemetry
    
    # Generate system report
    generate_system_summary knowledge-map-cmd.json

EOF
}

# Initialize validation
if [[ "${1:-}" == "validate" ]]; then
    validate_jq_ref
    exit $?
fi

if [[ "${1:-}" == "help" ]]; then
    show_jq_utils_usage
    exit 0
fi