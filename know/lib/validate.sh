#!/bin/bash

# validate.sh - Smart validation and completeness checking

# Validate entity completeness before generation
validate_entity_completeness() {
    local entity_ref="$1"
    local spec_type="$2"
    
    echo "🔍 Validating entity completeness for $entity_ref"
    echo
    
    local validation_passed=true
    local warnings=()
    local errors=()
    
    # Get entity data
    local entity_data
    entity_data=$(get_entity "$entity_ref")
    
    local entity_name
    entity_name=$(echo "$entity_data" | jq -r '.name // empty')
    
    local entity_description
    entity_description=$(echo "$entity_data" | jq -r '.resolved_description // empty')
    
    local acceptance_criteria
    acceptance_criteria=$(get_acceptance_criteria "$entity_ref")
    
    local outbound_rels
    outbound_rels=$(get_outbound_relationships "$entity_ref")
    
    # Basic validation
    if [[ -z "$entity_name" ]]; then
        errors+=("❌ Missing entity name")
        validation_passed=false
    else
        echo "✅ Entity name: $entity_name"
    fi
    
    if [[ -z "$entity_description" || "$entity_description" == "No description available" ]]; then
        errors+=("❌ Missing or invalid description")
        validation_passed=false
    else
        echo "✅ Description: ${entity_description:0:50}..."
    fi
    
    # Type-specific validation
    case "$spec_type" in
        feature)
            validate_feature_completeness "$entity_ref" "$entity_data" "$acceptance_criteria" errors warnings
            ;;
        component)
            validate_component_completeness "$entity_ref" "$entity_data" "$outbound_rels" errors warnings
            ;;
        screen)
            validate_screen_completeness "$entity_ref" "$entity_data" "$outbound_rels" errors warnings
            ;;
        api)
            validate_api_completeness "$entity_ref" "$entity_data" errors warnings
            ;;
    esac
    
    echo
    
    # Show warnings
    if [[ ${#warnings[@]} -gt 0 ]]; then
        echo "⚠️  Warnings (spec will have missing sections):"
        for warning in "${warnings[@]}"; do
            echo "  $warning"
        done
        echo
    fi
    
    # Show errors
    if [[ ${#errors[@]} -gt 0 ]]; then
        echo "❌ Errors (spec generation may fail):"
        for error in "${errors[@]}"; do
            echo "  $error"
        done
        echo
    fi
    
    if [[ "$validation_passed" == "true" && ${#warnings[@]} -eq 0 ]]; then
        echo "✅ Entity is complete and ready for specification generation"
        return 0
    elif [[ "$validation_passed" == "true" ]]; then
        echo "⚠️  Entity has warnings but can generate specification"
        return 0
    else
        echo "❌ Entity has critical errors - fix before generating specification"
        return 1
    fi
}

# Validate feature-specific requirements
validate_feature_completeness() {
    local entity_ref="$1"
    local entity_data="$2"
    local acceptance_criteria="$3"
    # Arrays passed by reference  
    declare -g errors warnings
    
    # Check acceptance criteria
    if [[ "$acceptance_criteria" == "{}" || "$acceptance_criteria" == "null" ]]; then
        errors_ref+=("❌ No acceptance criteria defined")
    else
        local criteria_count
        criteria_count=$(echo "$acceptance_criteria" | jq 'to_entries | length')
        echo "✅ Acceptance criteria: $criteria_count categories"
        
        # Check for key criteria types
        local functional_count
        functional_count=$(echo "$acceptance_criteria" | jq '.functional | length // 0')
        if [[ $functional_count -eq 0 ]]; then
            warnings_ref+=("⚠️  No functional requirements defined")
        fi
        
        local performance_count
        performance_count=$(echo "$acceptance_criteria" | jq '.performance | length // 0')
        if [[ $performance_count -eq 0 ]]; then
            warnings_ref+=("⚠️  No performance requirements defined")
        fi
    fi
    
    # Check evolution/versioning for features
    local current_version
    current_version=$(echo "$entity_data" | jq -r '.current_version // empty')
    if [[ -z "$current_version" ]]; then
        warnings_ref+=("⚠️  No current version specified")
    else
        echo "✅ Current version: $current_version"
    fi
    
    # Check dependencies
    local deps
    deps=$(get_dependencies "$entity_ref")
    if [[ -z "$deps" ]]; then
        warnings_ref+=("⚠️  No dependencies defined - feature may be isolated")
    else
        local dep_count
        dep_count=$(echo "$deps" | wc -l)
        echo "✅ Dependencies: $dep_count found"
    fi
}

# Validate component-specific requirements
validate_component_completeness() {
    local entity_ref="$1"
    local entity_data="$2"
    local outbound_rels="$3"
    # Arrays passed by reference  
    declare -g errors warnings
    
    # Check if component implements any features
    local implemented_features
    implemented_features=$(echo "$outbound_rels" | jq -r '.implements[]? // empty')
    if [[ -z "$implemented_features" ]]; then
        warnings_ref+=("⚠️  Component doesn't implement any features")
    else
        local feature_count
        feature_count=$(echo "$implemented_features" | wc -l)
        echo "✅ Implements features: $feature_count"
    fi
    
    # Check UI component relationships
    local ui_components
    ui_components=$(echo "$outbound_rels" | jq -r '.uses_ui[]? // empty')
    if [[ -z "$ui_components" ]]; then
        warnings_ref+=("⚠️  No UI components specified - may not follow design system")
    else
        local ui_count
        ui_count=$(echo "$ui_components" | wc -l)
        echo "✅ UI components: $ui_count"
    fi
    
    # Check data model usage
    local models
    models=$(echo "$outbound_rels" | jq -r '.displays[]?, .uses[]? // empty | select(startswith("model:") or startswith("schema:"))')
    if [[ -z "$models" ]]; then
        warnings_ref+=("⚠️  No data models specified - component may be purely presentational")
    else
        local model_count
        model_count=$(echo "$models" | wc -l)
        echo "✅ Data models: $model_count"
    fi
}

# Validate screen-specific requirements  
validate_screen_completeness() {
    local entity_ref="$1"
    local entity_data="$2"
    local outbound_rels="$3"
    # Arrays passed by reference  
    declare -g errors warnings
    
    # Check if screen contains components
    local contained_components
    contained_components=$(echo "$outbound_rels" | jq -r '.contains[]? // empty')
    if [[ -z "$contained_components" ]]; then
        errors_ref+=("❌ Screen contains no components")
    else
        local component_count
        component_count=$(echo "$contained_components" | wc -l)
        echo "✅ Contains components: $component_count"
    fi
    
    # Check user access
    local accessing_users
    accessing_users=$(get_accessing_users "$entity_ref")
    if [[ -z "$accessing_users" ]]; then
        warnings_ref+=("⚠️  No users can access this screen")
    else
        local user_count
        user_count=$(echo "$accessing_users" | wc -l)
        echo "✅ Accessible by users: $user_count"
    fi
    
    # Check priority
    local priority
    priority=$(echo "$entity_data" | jq -r '.priority // empty')
    if [[ -z "$priority" ]]; then
        warnings_ref+=("⚠️  No priority specified")
    else
        echo "✅ Priority: $priority"
    fi
}

# Validate API/schema completeness
validate_api_completeness() {
    local entity_ref="$1"
    local entity_data="$2"
    # Arrays passed by reference  
    declare -g errors warnings
    
    # Check if schema has attributes
    local attributes
    attributes=$(echo "$entity_data" | jq '.attributes // {}')
    if [[ "$attributes" == "{}" ]]; then
        errors_ref+=("❌ Schema has no attributes defined")
    else
        local attr_count
        attr_count=$(echo "$attributes" | jq 'keys | length')
        echo "✅ Attributes: $attr_count defined"
    fi
    
    # Check for ID field
    local has_id
    has_id=$(echo "$attributes" | jq 'has("id") or has("entity-id") or has("uuid")')
    if [[ "$has_id" != "true" ]]; then
        warnings_ref+=("⚠️  No ID field found in schema")
    fi
}

# Preview what will be generated
preview_generation() {
    local spec_type="$1"
    local entity_ref="$2"
    
    echo "📋 Preview of $spec_type specification for $entity_ref:"
    echo
    
    local entity_name
    entity_name=$(get_entity_name "$entity_ref")
    
    echo "# $spec_type: $entity_name"
    echo
    
    case "$spec_type" in
        feature)
            preview_feature_sections "$entity_ref"
            ;;
        component)
            preview_component_sections "$entity_ref"
            ;;
        screen)
            preview_screen_sections "$entity_ref"
            ;;
        api)
            preview_api_sections "$entity_ref"
            ;;
    esac
}

# Preview feature sections
preview_feature_sections() {
    local entity_ref="$1"
    
    local acceptance_criteria
    acceptance_criteria=$(get_acceptance_criteria "$entity_ref")
    
    echo "## Sections that will be generated:"
    echo "✅ Overview and description"
    
    if [[ "$acceptance_criteria" != "{}" ]]; then
        local categories
        categories=$(echo "$acceptance_criteria" | jq -r 'keys[]')
        echo "✅ Acceptance criteria ($(echo "$categories" | wc -l) categories)"
        while IFS= read -r category; do
            local count
            count=$(echo "$acceptance_criteria" | jq -r ".$category | length")
            echo "   - $category: $count items"
        done <<< "$categories"
    else
        echo "❌ Acceptance criteria (missing)"
    fi
    
    local deps
    deps=$(get_dependencies "$entity_ref")
    if [[ -n "$deps" ]]; then
        echo "✅ Dependencies ($(echo "$deps" | wc -l) items)"
    else
        echo "⚠️  Dependencies (none found)"
    fi
    
    echo "✅ Technical implementation details"
    echo "✅ Architecture requirements"
}

# Preview component sections
preview_component_sections() {
    local entity_ref="$1"
    
    local outbound_rels
    outbound_rels=$(get_outbound_relationships "$entity_ref")
    
    echo "## Sections that will be generated:"
    echo "✅ Overview and description"
    
    local features
    features=$(echo "$outbound_rels" | jq -r '.implements[]? // empty')
    if [[ -n "$features" ]]; then
        echo "✅ Features implemented ($(echo "$features" | wc -l) items)"
    else
        echo "⚠️  Features implemented (none found)"
    fi
    
    local ui_components
    ui_components=$(echo "$outbound_rels" | jq -r '.uses_ui[]? // empty')
    if [[ -n "$ui_components" ]]; then
        echo "✅ UI components ($(echo "$ui_components" | wc -l) items)"
    else
        echo "⚠️  UI components (none specified)"
    fi
    
    echo "✅ Technical stack and dependencies"
    echo "✅ Testing strategy"
}

# Preview screen sections
preview_screen_sections() {
    local entity_ref="$1"
    
    local outbound_rels
    outbound_rels=$(get_outbound_relationships "$entity_ref")
    
    echo "## Sections that will be generated:"
    echo "✅ Overview and description"
    
    local components
    components=$(echo "$outbound_rels" | jq -r '.contains[]? // empty')
    if [[ -n "$components" ]]; then
        echo "✅ Components ($(echo "$components" | wc -l) items)"
    else
        echo "❌ Components (none found - critical)"
    fi
    
    local features
    features=$(echo "$outbound_rels" | jq -r '.implements[]? // empty')
    if [[ -n "$features" ]]; then
        echo "✅ Features ($(echo "$features" | wc -l) items)"
    else
        echo "⚠️  Features (none found)"
    fi
    
    local users
    users=$(get_accessing_users "$entity_ref")
    if [[ -n "$users" ]]; then
        echo "✅ User access ($(echo "$users" | wc -l) users)"
    else
        echo "⚠️  User access (none found)"
    fi
    
    echo "✅ Technical implementation details"
}

# Preview API sections
preview_api_sections() {
    local entity_ref="$1"
    
    local entity_data
    entity_data=$(get_entity "$entity_ref")
    
    local attributes
    attributes=$(echo "$entity_data" | jq '.attributes // {}')
    
    echo "## Sections that will be generated:"
    echo "✅ OpenAPI 3.0 specification"
    
    if [[ "$attributes" != "{}" ]]; then
        local attr_count
        attr_count=$(echo "$attributes" | jq 'keys | length')
        echo "✅ Schema definition ($attr_count attributes)"
    else
        echo "❌ Schema definition (no attributes - critical)"
    fi
    
    echo "✅ CRUD endpoints (GET, POST, PUT, DELETE)"
    echo "✅ Authentication integration"
}