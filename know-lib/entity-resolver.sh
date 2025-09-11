#!/bin/bash

# Entity Resolution Engine for know CLI
# Handles type aliases, ID normalization, and entity validation

# Type aliases - map singular to plural forms
declare -A TYPE_ALIASES
TYPE_ALIASES["user"]="users"
TYPE_ALIASES["screen"]="screens"
TYPE_ALIASES["component"]="components"
TYPE_ALIASES["feature"]="features"
TYPE_ALIASES["requirement"]="requirements"
TYPE_ALIASES["model"]="schema"
TYPE_ALIASES["schema"]="schema"
TYPE_ALIASES["platform"]="platforms"
TYPE_ALIASES["ui_component"]="ui_components"
TYPE_ALIASES["functionality"]="functionality"

# Normalize entity type (handle aliases)
normalize_type() {
    local input_type="$1"
    
    # Return normalized type or original if no alias
    echo "${TYPE_ALIASES[$input_type]:-$input_type}"
}

# Validate entity exists in knowledge map
validate_entity() {
    local entity_type="$1"
    local entity_id="$2"
    
    local exists
    exists=$(jq -r --arg type "$entity_type" --arg id "$entity_id" '
        .entities[$type][$id] != null
    ' "$KNOWLEDGE_MAP")
    
    [[ "$exists" == "true" ]]
}

# Get entity with full context
get_entity() {
    local entity_type="$1"
    local entity_id="$2"
    
    local normalized_type
    normalized_type=$(normalize_type "$entity_type")
    
    if ! validate_entity "$normalized_type" "$entity_id"; then
        error "Entity not found: $normalized_type:$entity_id"
    fi
    
    # Return entity with resolved description
    jq --arg type "$normalized_type" --arg id "$entity_id" '
        .entities[$type][$id] as $entity |
        $entity + {
            "resolved_description": (
                if $entity.description_ref then
                    .references.descriptions[$entity.description_ref] // $entity.description_ref
                else
                    $entity.description // "No description available"
                end
            )
        }
    ' "$KNOWLEDGE_MAP"
}

# Resolve entity reference to full form (type:id)
resolve_entity_ref() {
    local entity_ref="$1"
    
    # If already in type:id format, validate and return
    if [[ "$entity_ref" =~ ^[a-z_]+:.+ ]]; then
        local type="${entity_ref%%:*}"
        local id="${entity_ref#*:}"
        local normalized_type
        normalized_type=$(normalize_type "$type")
        
        if validate_entity "$normalized_type" "$id"; then
            echo "$normalized_type:$id"
        else
            error "Invalid entity reference: $entity_ref"
        fi
    else
        error "Entity reference must be in format 'type:id', got: $entity_ref"
    fi
}

# Find entity by fuzzy matching name or ID
find_entity() {
    local search_term="$1"
    local entity_type="${2:-}"
    
    info "Searching for entities matching: $search_term"
    
    if [[ -n "$entity_type" ]]; then
        local normalized_type
        normalized_type=$(normalize_type "$entity_type")
        
        jq -r --arg type "$normalized_type" --arg search "$search_term" '
            .entities[$type] | to_entries[] |
            select(.key | contains($search) or (.value.name // "" | ascii_downcase | contains($search | ascii_downcase))) |
            "\($type):\(.key) - \(.value.name // "No name")"
        ' "$KNOWLEDGE_MAP"
    else
        jq -r --arg search "$search_term" '
            .entities | to_entries[] as $type_entry |
            $type_entry.value | to_entries[] |
            select(.key | contains($search) or (.value.name // "" | ascii_downcase | contains($search | ascii_downcase))) |
            "\($type_entry.key):\(.key) - \(.value.name // "No name")"
        ' "$KNOWLEDGE_MAP"
    fi
}

# List all entities of a given type
list_entities() {
    local entity_type="${1:-}"
    
    if [[ -z "$entity_type" ]]; then
        echo "Available entity types:"
        jq -r '.entities | keys[]' "$KNOWLEDGE_MAP" | sed 's/^/  /'
        return
    fi
    
    local normalized_type
    normalized_type=$(normalize_type "$entity_type")
    
    if ! jq -e --arg type "$normalized_type" '.entities[$type]' "$KNOWLEDGE_MAP" >/dev/null; then
        error "Unknown entity type: $entity_type"
    fi
    
    echo "Entities of type '$normalized_type':"
    jq -r --arg type "$normalized_type" '
        .entities[$type] | to_entries[] |
        "  \(.key) - \(.value.name // "No name")"
    ' "$KNOWLEDGE_MAP"
}

# Get entity count by type
get_entity_stats() {
    echo "Entity Statistics:"
    jq -r '
        .entities | to_entries[] |
        "  \(.key): \(.value | length) entities"
    ' "$KNOWLEDGE_MAP"
}

# Extract entity type and ID from various input formats
parse_entity_input() {
    local input="$1"
    
    if [[ "$input" =~ ^([a-z_]+):(.+)$ ]]; then
        # Format: type:id
        local type="${BASH_REMATCH[1]}"
        local id="${BASH_REMATCH[2]}"
        echo "$(normalize_type "$type") $id"
    else
        error "Invalid entity format: $input. Use 'type:id' format (e.g., 'screen:fleet-dashboard')"
    fi
}