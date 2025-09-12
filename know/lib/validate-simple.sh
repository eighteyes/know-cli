#!/bin/bash

# validate-simple.sh - Simple validation without complex array passing

# Validate entity completeness before generation
validate_entity_completeness() {
    local entity_ref="$1"
    local spec_type="$2"
    
    echo "🔍 Validating entity completeness for $entity_ref"
    echo
    
    local validation_passed=true
    local warning_count=0
    local error_count=0
    
    # Get entity data
    local entity_data
    entity_data=$(get_entity "$entity_ref")
    
    local entity_name
    entity_name=$(echo "$entity_data" | jq -r '.name // empty')
    
    local entity_description
    entity_description=$(echo "$entity_data" | jq -r '.resolved_description // empty')
    
    # Basic validation
    if [[ -z "$entity_name" ]]; then
        echo "❌ Missing entity name"
        ((error_count++))
        validation_passed=false
    else
        echo "✅ Entity name: $entity_name"
    fi
    
    if [[ -z "$entity_description" || "$entity_description" == "No description available" ]]; then
        echo "❌ Missing or invalid description"
        ((error_count++))
        validation_passed=false
    else
        echo "✅ Description: ${entity_description:0:50}..."
    fi
    
    # Type-specific validation
    case "$spec_type" in
        feature)
            local feature_results
            feature_results=$(validate_feature_simple "$entity_ref" "$entity_data")
            local feature_status=$(echo "$feature_results" | head -1)
            local feature_warnings=$(echo "$feature_results" | tail -n +2 | grep "⚠️" | wc -l)
            local feature_errors=$(echo "$feature_results" | tail -n +2 | grep "❌" | wc -l)
            
            echo "$feature_results" | tail -n +2
            
            ((warning_count += feature_warnings))
            ((error_count += feature_errors))
            [[ "$feature_status" == "false" ]] && validation_passed=false
            ;;
        component|screen|api)
            echo "✅ Basic validation complete for $spec_type"
            ;;
    esac
    
    echo
    
    # Summary
    if [[ $error_count -gt 0 ]]; then
        echo "❌ Found $error_count critical errors"
    fi
    
    if [[ $warning_count -gt 0 ]]; then
        echo "⚠️  Found $warning_count warnings"
    fi
    
    if [[ "$validation_passed" == "true" && $warning_count -eq 0 ]]; then
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

# Simple feature validation
validate_feature_simple() {
    local entity_ref="$1"
    local entity_data="$2"
    
    local passed=true
    
    # Check acceptance criteria
    local acceptance_criteria
    acceptance_criteria=$(get_acceptance_criteria "$entity_ref")
    
    if [[ "$acceptance_criteria" == "{}" || "$acceptance_criteria" == "null" ]]; then
        echo "❌ No acceptance criteria defined"
        passed=false
    else
        local criteria_count
        criteria_count=$(echo "$acceptance_criteria" | jq 'to_entries | length')
        echo "✅ Acceptance criteria: $criteria_count categories"
        
        # Check for key criteria types
        local functional_count
        functional_count=$(echo "$acceptance_criteria" | jq '.functional | length // 0')
        if [[ $functional_count -eq 0 ]]; then
            echo "⚠️  No functional requirements defined"
        fi
        
        local performance_count
        performance_count=$(echo "$acceptance_criteria" | jq '.performance | length // 0')
        if [[ $performance_count -eq 0 ]]; then
            echo "⚠️  No performance requirements defined"
        fi
    fi
    
    # Check dependencies
    local deps
    deps=$(get_dependencies "$entity_ref")
    if [[ -z "$deps" ]]; then
        echo "⚠️  No dependencies defined - feature may be isolated"
    else
        local dep_count
        dep_count=$(echo "$deps" | wc -l)
        echo "✅ Dependencies: $dep_count found"
    fi
    
    # Return status first, then messages
    echo "$passed"
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
            echo "## Sections that will be generated:"
            echo "✅ Overview and description"
            
            local acceptance_criteria
            acceptance_criteria=$(get_acceptance_criteria "$entity_ref")
            
            if [[ "$acceptance_criteria" != "{}" ]]; then
                local categories
                categories=$(echo "$acceptance_criteria" | jq -r 'keys[]')
                echo "✅ Acceptance criteria ($(echo "$categories" | wc -l) categories)"
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
            ;;
        *)
            echo "✅ Standard sections for $spec_type"
            ;;
    esac
    
    echo
    echo "💡 Use 'know check $spec_type ${entity_ref#*:}' to validate before generation"
}