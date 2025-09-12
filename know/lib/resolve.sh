#!/bin/bash

# resolve.sh - Entity and reference resolution for know CLI

# Resolve entity reference with optional type inference  
resolve_entity_reference() {
    local input="$1"
    local hint_type="${2:-}"
    
    # If already in type:id format, return as-is (backend tools will validate)
    if [[ "$input" =~ ^[a-z_]+:.+ ]]; then
        echo "$input"
        return
    fi
    
    # If hint_type provided, try that first
    if [[ -n "$hint_type" ]]; then
        local normalized_type
        normalized_type=$(normalize_entity_type "$hint_type")
        echo "${normalized_type}:${input}"
        return
    fi
    
    # Try to find entity by searching (simplified approach)
    # The backend tools will handle validation
    echo "feature:$input"  # Default to feature for backwards compatibility
}

# Find entity by ID with optional type hint
find_entity_by_id() {
    local entity_id="$1"
    local hint_type="${2:-}"
    
    if [[ -n "$hint_type" ]]; then
        local normalized_type
        normalized_type=$(normalize_entity_type "$hint_type")
        
        if entity_exists "$normalized_type" "$entity_id"; then
            echo "$normalized_type:$entity_id"
            return
        fi
    fi
    
    # Search across all entity types
    local found_refs
    found_refs=$(jq -r --arg id "$entity_id" '
        .entities | to_entries[] | 
        select(.value | has($id)) |
        "\(.key):\($id)"
    ' "$KNOWLEDGE_MAP")
    
    local ref_count
    ref_count=$(echo "$found_refs" | grep -c . || echo "0")
    
    case $ref_count in
        0)
            error "Entity ID '$entity_id' not found in any type"
            ;;
        1)
            echo "$found_refs"
            ;;
        *)
            error "Ambiguous entity ID '$entity_id' found in multiple types: $(echo "$found_refs" | tr '\n' ' ')"
            ;;
    esac
}

# Get entity data with resolved references
get_entity() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    local id=$(echo "$type_id" | cut -d' ' -f2-)
    
    jq --arg type "$type" --arg id "$id" '
        .entities[$type][$id] as $entity |
        $entity + {
            "entity_ref": ($type + ":" + $id),
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

# Resolve description reference
resolve_description_ref() {
    local description_ref="$1"
    
    jq -r --arg ref "$description_ref" '
        .references.descriptions[$ref] // empty
    ' "$KNOWLEDGE_MAP"
}

# Get acceptance criteria for entity
get_acceptance_criteria() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    local id=$(echo "$type_id" | cut -d' ' -f2-)
    
    jq --arg type "$type" --arg id "$id" '
        .entities[$type][$id].acceptance_criteria // {}
    ' "$KNOWLEDGE_MAP"
}

# Get technical specifications from references
get_technical_specs() {
    local entity_ref="$1"
    
    jq '
        .references.technical_architecture // {}
    ' "$KNOWLEDGE_MAP"
}

# Get UI design system specs
get_ui_specs() {
    jq '
        .references.ui // {}
    ' "$KNOWLEDGE_MAP"
}

# Get libraries and frameworks
get_libraries() {
    jq '
        .references.libraries // {}
    ' "$KNOWLEDGE_MAP"
}

# Get protocol specifications  
get_protocols() {
    jq '
        .references.protocols // {}
    ' "$KNOWLEDGE_MAP"
}

# Get endpoints
get_endpoints() {
    jq '
        .references.endpoints // {}
    ' "$KNOWLEDGE_MAP"
}

# Get project roadmap status
get_project_status() {
    local entity_ref="$1"
    
    jq --arg entity "$entity_ref" '
        .project.roadmap[$entity] // {}
    ' "$KNOWLEDGE_MAP"
}

# Resolve feature evolution data
get_feature_evolution() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    local id=$(echo "$type_id" | cut -d' ' -f2-)
    
    if [[ "$type" == "features" ]]; then
        jq --arg type "$type" --arg id "$id" '
            .entities[$type][$id].evolution // {}
        ' "$KNOWLEDGE_MAP"
    else
        echo "{}"
    fi
}

# Get current version for features
get_current_version() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    local id=$(echo "$type_id" | cut -d' ' -f2-)
    
    if [[ "$type" == "features" ]]; then
        jq -r --arg type "$type" --arg id "$id" '
            .entities[$type][$id].current_version // "v1"
        ' "$KNOWLEDGE_MAP"
    else
        echo ""
    fi
}

# Get entity attributes (for schema entities)
get_entity_attributes() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    local id=$(echo "$type_id" | cut -d' ' -f2-)
    
    jq --arg type "$type" --arg id "$id" '
        .entities[$type][$id].attributes // {}
    ' "$KNOWLEDGE_MAP"
}