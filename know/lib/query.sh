#!/bin/bash

# query.sh - Graph traversal and query functions for know CLI

# Get outbound relationships for an entity
get_outbound_relationships() {
    local entity_ref="$1"
    
    jq --arg entity "$entity_ref" '
        .graph[$entity].outbound // {}
    ' "$KNOWLEDGE_MAP"
}

# Get inbound relationships for an entity
get_inbound_relationships() {
    local entity_ref="$1"
    
    jq --arg entity "$entity_ref" '
        .graph[$entity].inbound // {}
    ' "$KNOWLEDGE_MAP"
}

# Get dependencies (from graph section)
get_dependencies() {
    local entity_ref="$1"

    # Check if dependencies exist in the graph section
    jq -r --arg entity "$entity_ref" '
        .graph[$entity].depends_on[]? // empty
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get dependents (entities that depend on this one)
get_dependents() {
    local entity_ref="$1"

    # Find all entities that have this entity in their depends_on array
    jq -r --arg entity "$entity_ref" '
        .graph | to_entries[] |
        select(.value.depends_on[]? == $entity) |
        .key
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get UI components used by a screen
get_ui_components() {
    local screen_ref="$1"
    
    jq -r --arg entity "$screen_ref" '
        .graph[$entity].outbound.uses_ui[]? // empty
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get components contained by a screen
get_screen_components() {
    local screen_ref="$1"
    
    jq -r --arg entity "$screen_ref" '
        .graph[$entity].outbound.contains[]? // empty
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get features implemented by a component/screen
get_implemented_features() {
    local entity_ref="$1"
    
    jq -r --arg entity "$entity_ref" '
        .graph[$entity].outbound.implements[]? // empty
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get functionality used by a feature
get_functionality() {
    local feature_ref="$1"
    
    jq -r --arg entity "$feature_ref" '
        .graph[$entity].outbound.uses[]? // empty | select(startswith("functionality:"))
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get models used by an entity
get_used_models() {
    local entity_ref="$1"
    
    jq -r --arg entity "$entity_ref" '
        .graph[$entity].outbound | to_entries[] |
        select(.key | test("uses|displays|processes")) |
        .value[] | select(startswith("model:") or startswith("schema:"))
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get screens that contain a component
get_parent_screens() {
    local component_ref="$1"
    
    jq -r --arg entity "$component_ref" '
        .graph | to_entries[] |
        select(.value.outbound.contains[]? == $entity) |
        .key
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get users who can access an entity
get_accessing_users() {
    local entity_ref="$1"
    
    jq -r --arg entity "$entity_ref" '
        .graph | to_entries[] |
        select(.value.outbound.accesses[]? == $entity) |
        .key
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Get platforms that implement a feature
get_implementing_platforms() {
    local feature_ref="$1"
    
    jq -r --arg entity "$feature_ref" '
        .graph | to_entries[] |
        select(.value.outbound.implements[]? == $entity) |
        .key | select(startswith("platform:"))
    ' "$KNOWLEDGE_MAP" 2>/dev/null || true
}

# Show full dependency analysis
show_dependencies() {
    local entity_ref="$1"
    
    echo "📦 Dependencies for $entity_ref:"
    echo
    
    local deps
    deps=$(get_dependencies "$entity_ref")
    
    if [[ -z "$deps" ]]; then
        echo "  ✅ No dependencies found"
        return
    fi
    
    echo "📌 Direct Dependencies:"
    while IFS= read -r dep; do
        if [[ -n "$dep" ]]; then
            local dep_name
            dep_name=$(get_entity_name "$dep")
            echo "  📋 $dep ($dep_name)"
        fi
    done <<< "$deps"
    
    echo
    echo "🔍 Transitive Dependencies:"
    
    # Use jq to find transitive dependencies
    jq -r --arg entity "$entity_ref" '
        def find_deps($e; $visited):
            if $visited | has($e) then empty
            else
                (.graph[$e].outbound | to_entries[] | 
                 select(.key | test("requires|uses|depends_on")) | 
                 .value[]?) as $dep |
                if $dep then
                    $dep, find_deps($dep; $visited + {($e): true})
                else
                    empty
                end
            end;
        
        [find_deps($entity; {})] | unique | .[]
    ' "$KNOWLEDGE_MAP" 2>/dev/null | while IFS= read -r dep; do
        if [[ -n "$dep" && "$dep" != "$entity_ref" ]]; then
            local dep_name
            dep_name=$(get_entity_name "$dep")
            echo "  🔗 $dep ($dep_name)"
        fi
    done
}

# Show impact analysis
show_impact_analysis() {
    local entity_ref="$1"
    
    echo "💥 Impact Analysis for $entity_ref:"
    echo "   (Entities that would be affected by changes)"
    echo
    
    local dependents
    dependents=$(get_dependents "$entity_ref")
    
    if [[ -z "$dependents" ]]; then
        echo "  ✅ No direct dependents found"
    else
        echo "📌 Direct Impact:"
        while IFS= read -r dependent; do
            if [[ -n "$dependent" ]]; then
                local dep_name
                dep_name=$(get_entity_name "$dependent")
                echo "  ⚡ $dependent ($dep_name)"
            fi
        done <<< "$dependents"
    fi
    
    echo
    echo "🌊 Transitive Impact:"
    
    # Use jq to find transitive impact
    jq -r --arg entity "$entity_ref" '
        def find_impact($e; $visited):
            if $visited | has($e) then empty
            else
                (.graph | to_entries[] |
                 select(.value.outbound | to_entries[] | 
                        select(.key | test("requires|uses|depends_on")) |
                        .value[] == $e) | .key) as $dependent |
                if $dependent then
                    $dependent, find_impact($dependent; $visited + {($e): true})
                else
                    empty
                end
            end;
        
        [find_impact($entity; {})] | unique | .[]
    ' "$KNOWLEDGE_MAP" 2>/dev/null | while IFS= read -r impact; do
        if [[ -n "$impact" && "$impact" != "$entity_ref" ]]; then
            local impact_name
            impact_name=$(get_entity_name "$impact")
            echo "  🔗 $impact ($impact_name)"
        fi
    done
}

# Show implementation order based on dependency depth
show_implementation_order() {
    echo "🏗️ Optimal Implementation Order:"
    echo
    
    # Calculate depth for each entity and group by depth
    local depths_json
    depths_json=$(jq '
        def calc_depth($e; $visited):
            if $visited | has($e) then 0
            else
                [(.graph[$e].outbound | to_entries[] | 
                  select(.key | test("requires|uses|depends_on")) | 
                  .value[]?) as $dep |
                  if $dep then calc_depth($dep; $visited + {($e): true}) + 1 else 0 end] |
                if length > 0 then max else 0 end
            end;
        
        [.graph | keys[] as $entity | {entity: $entity, depth: calc_depth($entity; {})}] |
        group_by(.depth) | 
        map({depth: .[0].depth, entities: map(.entity)})
    ' "$KNOWLEDGE_MAP")
    
    echo "$depths_json" | jq -r '
        .[] | 
        "### Depth \(.depth) (\(.entities | length) entities)" + "\n" +
        (.entities | map("- " + .) | join("\n")) + "\n"
    '
}

# Validate knowledge map integrity
validate_knowledge_map() {
    echo "🔍 Validating knowledge map integrity..."
    echo
    
    local broken_refs=0
    local total_refs=0
    
    # Check all graph references
    while IFS= read -r ref; do
        if [[ -n "$ref" ]]; then
            ((total_refs++))
            
            local type_id
            if type_id=$(parse_entity_ref "$ref" 2>/dev/null); then
                local type=$(echo "$type_id" | cut -d' ' -f1)
                local id=$(echo "$type_id" | cut -d' ' -f2-)
                
                if ! entity_exists "$type" "$id"; then
                    echo "❌ Broken reference: $ref"
                    ((broken_refs++))
                fi
            else
                echo "⚠️ Invalid reference format: $ref"
                ((broken_refs++))
            fi
        fi
    done < <(jq -r '.graph | to_entries[] | .value.outbound | to_entries[] | .value[]' "$KNOWLEDGE_MAP" 2>/dev/null)
    
    echo
    if [[ $broken_refs -eq 0 ]]; then
        success "✅ All $total_refs entity references are valid!"
    else
        error "❌ Found $broken_refs broken references out of $total_refs total"
    fi
}