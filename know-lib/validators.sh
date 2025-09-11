#!/bin/bash

# Validation Engine for know CLI
# Checks entity completeness and consistency

# Validate entity completeness
validate_entity() {
    local entity_ref="$1"
    local resolved_ref
    resolved_ref=$(resolve_entity_ref "$entity_ref")
    
    local type="${resolved_ref%%:*}"
    local id="${resolved_ref#*:}"
    
    echo "🔍 Validating entity: $resolved_ref"
    echo
    
    local validation_passed=true
    
    # Check if entity exists
    if ! validate_entity "$type" "$id"; then
        echo "❌ Entity does not exist in knowledge map"
        return 1
    fi
    
    # Get entity data
    local entity
    entity=$(jq --arg type "$type" --arg id "$id" '.entities[$type][$id]' "$KNOWLEDGE_MAP")
    
    # Basic entity validation
    echo "📋 Basic Entity Validation:"
    
    # Check required fields
    local name
    name=$(echo "$entity" | jq -r '.name // empty')
    if [[ -z "$name" ]]; then
        echo "  ❌ Missing required field: name"
        validation_passed=false
    else
        echo "  ✅ Name: $name"
    fi
    
    # Check type consistency
    local entity_type
    entity_type=$(echo "$entity" | jq -r '.type // empty')
    if [[ -z "$entity_type" ]]; then
        echo "  ❌ Missing required field: type"
        validation_passed=false
    elif [[ "$entity_type" != "${type%s}" && "$entity_type" != "$type" ]]; then
        echo "  ⚠️  Type mismatch: entity.type='$entity_type' but in collection '$type'"
    else
        echo "  ✅ Type: $entity_type"
    fi
    
    # Check ID consistency  
    local entity_id
    entity_id=$(echo "$entity" | jq -r '.id // empty')
    if [[ -z "$entity_id" ]]; then
        echo "  ❌ Missing required field: id"
        validation_passed=false
    elif [[ "$entity_id" != "$id" ]]; then
        echo "  ❌ ID mismatch: entity.id='$entity_id' but key is '$id'"
        validation_passed=false
    else
        echo "  ✅ ID: $entity_id"
    fi
    
    echo
    
    # Description validation
    echo "📝 Description Validation:"
    validate_description "$entity"
    
    echo
    
    # Type-specific validation
    case "$type" in
        features)
            validate_feature_entity "$entity"
            ;;
        functionality) 
            validate_functionality_entity "$entity"
            ;;
        screens|components)
            validate_ui_entity "$entity"
            ;;
        schema)
            validate_model_entity "$entity"
            ;;
        requirements)
            validate_requirement_entity "$entity"
            ;;
    esac
    
    echo
    
    # Graph relationships validation
    echo "🔗 Relationship Validation:"
    validate_graph_relationships "$resolved_ref"
    
    echo
    
    # Acceptance criteria validation
    echo "✅ Acceptance Criteria Validation:"
    validate_acceptance_criteria "$entity"
    
    if [[ "$validation_passed" == "true" ]]; then
        echo
        success "✅ Entity validation passed!"
        return 0
    else
        echo
        error "❌ Entity validation failed!"
        return 1
    fi
}

# Validate description and description_ref
validate_description() {
    local entity="$1"
    
    local description
    description=$(echo "$entity" | jq -r '.description // empty')
    
    local description_ref
    description_ref=$(echo "$entity" | jq -r '.description_ref // empty')
    
    if [[ -n "$description_ref" ]]; then
        # Check if description_ref resolves
        local resolved_desc
        resolved_desc=$(jq -r --arg ref "$description_ref" '.references.descriptions[$ref] // empty' "$KNOWLEDGE_MAP")
        
        if [[ -n "$resolved_desc" ]]; then
            echo "  ✅ Description reference: $description_ref → ${resolved_desc:0:50}..."
        else
            echo "  ❌ Description reference broken: $description_ref"
        fi
    elif [[ -n "$description" ]]; then
        echo "  ✅ Direct description: ${description:0:50}..."
    else
        echo "  ⚠️  No description or description_ref provided"
    fi
}

# Validate feature entity specifics
validate_feature_entity() {
    local entity="$1"
    
    echo "🎯 Feature-Specific Validation:"
    
    # Check evolution structure
    local evolution
    evolution=$(echo "$entity" | jq -r '.evolution // empty')
    
    if [[ -n "$evolution" ]]; then
        local current_version
        current_version=$(echo "$entity" | jq -r '.current_version // empty')
        
        if [[ -n "$current_version" ]]; then
            local version_exists
            version_exists=$(echo "$entity" | jq -r --arg v "$current_version" '.evolution[$v] != null')
            
            if [[ "$version_exists" == "true" ]]; then
                echo "  ✅ Current version ($current_version) exists in evolution"
                
                # Validate version structure
                local version_data
                version_data=$(echo "$entity" | jq --arg v "$current_version" '.evolution[$v]')
                
                local status
                status=$(echo "$version_data" | jq -r '.status // empty')
                if [[ -n "$status" ]]; then
                    echo "  ✅ Version status: $status"
                else
                    echo "  ❌ Missing status in version $current_version"
                fi
                
                local priority
                priority=$(echo "$version_data" | jq -r '.priority // empty')
                if [[ -n "$priority" ]]; then
                    echo "  ✅ Version priority: $priority"
                else
                    echo "  ⚠️  Missing priority in version $current_version"
                fi
            else
                echo "  ❌ Current version ($current_version) not found in evolution"
            fi
        else
            echo "  ❌ Missing current_version field"
        fi
    else
        echo "  ⚠️  No evolution structure defined"
    fi
}

# Validate functionality entity specifics
validate_functionality_entity() {
    local entity="$1"
    
    echo "⚙️ Functionality-Specific Validation:"
    
    # Functionality should have technical acceptance criteria
    local acceptance_criteria
    acceptance_criteria=$(echo "$entity" | jq -r '.acceptance_criteria // empty')
    
    if [[ -n "$acceptance_criteria" ]]; then
        # Check for performance criteria (important for technical services)
        local performance
        performance=$(echo "$entity" | jq -r '.acceptance_criteria.performance // empty')
        
        if [[ -n "$performance" ]]; then
            echo "  ✅ Performance criteria defined"
        else
            echo "  ⚠️  No performance criteria specified"
        fi
        
        # Check for reliability criteria
        local reliability
        reliability=$(echo "$entity" | jq -r '.acceptance_criteria.reliability // empty')
        
        if [[ -n "$reliability" ]]; then
            echo "  ✅ Reliability criteria defined"
        else
            echo "  ⚠️  No reliability criteria specified"
        fi
    else
        echo "  ❌ No acceptance criteria defined (required for functionality)"
    fi
}

# Validate UI entity specifics (screens/components)
validate_ui_entity() {
    local entity="$1"
    
    echo "🎨 UI Entity Validation:"
    
    # UI entities often have priority
    local priority
    priority=$(echo "$entity" | jq -r '.priority // empty')
    
    if [[ -n "$priority" ]]; then
        if [[ "$priority" =~ ^P[0-3]$ ]]; then
            echo "  ✅ Priority: $priority"
        else
            echo "  ⚠️  Invalid priority format: $priority (should be P0-P3)"
        fi
    else
        echo "  ⚠️  No priority specified"
    fi
}

# Validate model entity specifics
validate_model_entity() {
    local entity="$1"
    
    echo "🗄️ Model Entity Validation:"
    
    # Models should have attributes
    local attributes
    attributes=$(echo "$entity" | jq -r '.attributes // empty')
    
    if [[ -n "$attributes" ]]; then
        local attr_count
        attr_count=$(echo "$entity" | jq '.attributes | length')
        echo "  ✅ Attributes defined: $attr_count fields"
        
        # Check for common required fields
        local has_id
        has_id=$(echo "$entity" | jq -r '.attributes | has("id") or has("entity-id")')
        if [[ "$has_id" == "true" ]]; then
            echo "  ✅ Has ID field"
        else
            echo "  ⚠️  No ID field found"
        fi
    else
        echo "  ❌ No attributes defined (required for models)"
    fi
}

# Validate requirement entity specifics
validate_requirement_entity() {
    local entity="$1"
    
    echo "📋 Requirement Validation:"
    
    # Requirements should have criticality
    local criticality
    criticality=$(echo "$entity" | jq -r '.criticality // empty')
    
    if [[ -n "$criticality" ]]; then
        if [[ "$criticality" =~ ^(critical|high|medium|low)$ ]]; then
            echo "  ✅ Criticality: $criticality"
        else
            echo "  ⚠️  Invalid criticality: $criticality"
        fi
    else
        echo "  ❌ Missing criticality field"
    fi
}

# Validate graph relationships
validate_graph_relationships() {
    local entity_ref="$1"
    
    # Check if entity exists in graph
    local graph_entry
    graph_entry=$(jq -r --arg entity "$entity_ref" '.graph[$entity] // empty' "$KNOWLEDGE_MAP")
    
    if [[ -n "$graph_entry" ]]; then
        echo "  ✅ Entity exists in graph"
        
        # Check outbound relationships
        local outbound_count
        outbound_count=$(jq --arg entity "$entity_ref" '.graph[$entity].outbound | to_entries | length' "$KNOWLEDGE_MAP" 2>/dev/null || echo "0")
        echo "  📤 Outbound relationships: $outbound_count"
        
        # Check inbound relationships  
        local inbound_count
        inbound_count=$(jq --arg entity "$entity_ref" '.graph[$entity].inbound | to_entries | length' "$KNOWLEDGE_MAP" 2>/dev/null || echo "0")
        echo "  📥 Inbound relationships: $inbound_count"
        
        # Validate relationship targets exist
        local broken_refs
        broken_refs=$(jq -r --arg entity "$entity_ref" '
            .graph[$entity].outbound | to_entries[] | .value[] as $target |
            if (.entities | to_entries[] | .value | has($target | split(":")[1]) and .key == ($target | split(":")[0])) then
                empty
            else
                "❌ Broken reference: " + $target
            end
        ' "$KNOWLEDGE_MAP" 2>/dev/null)
        
        if [[ -n "$broken_refs" ]]; then
            echo "$broken_refs"
        else
            echo "  ✅ All relationship targets exist"
        fi
    else
        echo "  ⚠️  Entity not found in graph (relationships missing)"
    fi
}

# Validate acceptance criteria structure
validate_acceptance_criteria() {
    local entity="$1"
    
    local acceptance_criteria
    acceptance_criteria=$(echo "$entity" | jq -r '.acceptance_criteria // empty')
    
    if [[ -n "$acceptance_criteria" ]]; then
        local criteria_count
        criteria_count=$(echo "$entity" | jq '.acceptance_criteria | length')
        echo "  ✅ Acceptance criteria defined: $criteria_count categories"
        
        # Check for standard categories
        local categories=("functional" "performance" "integration" "reliability" "safety" "security" "validation")
        
        for category in "${categories[@]}"; do
            local has_category
            has_category=$(echo "$entity" | jq -r --arg cat "$category" '.acceptance_criteria | has($cat)')
            
            if [[ "$has_category" == "true" ]]; then
                local item_count
                item_count=$(echo "$entity" | jq --arg cat "$category" '.acceptance_criteria[$cat] | length')
                echo "    ✅ $category: $item_count criteria"
            fi
        done
    else
        echo "  ⚠️  No acceptance criteria defined"
    fi
}

# Validate entity references across the knowledge map
validate_all_references() {
    echo "🔍 Validating all entity references in knowledge map..."
    echo
    
    # Find all entity references in graph
    local all_refs
    all_refs=$(jq -r '.graph | to_entries[] | .value.outbound | to_entries[] | .value[]' "$KNOWLEDGE_MAP" 2>/dev/null | sort -u)
    
    local broken_count=0
    local total_count=0
    
    while IFS= read -r ref; do
        if [[ -n "$ref" ]]; then
            ((total_count++))
            
            # Check if reference exists
            if [[ "$ref" =~ ^([a-z_]+):(.+)$ ]]; then
                local ref_type="${BASH_REMATCH[1]}"
                local ref_id="${BASH_REMATCH[2]}"
                
                if ! validate_entity "$ref_type" "$ref_id" 2>/dev/null; then
                    echo "❌ Broken reference: $ref"
                    ((broken_count++))
                fi
            else
                echo "⚠️  Invalid reference format: $ref"
                ((broken_count++))
            fi
        fi
    done <<< "$all_refs"
    
    echo
    if [[ $broken_count -eq 0 ]]; then
        success "✅ All $total_count entity references are valid!"
    else
        error "❌ Found $broken_count broken references out of $total_count total"
    fi
}