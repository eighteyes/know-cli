#!/bin/bash

# Test entity specification generation commands
# Tests: feature, component, screen, functionality, requirement, api

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"

echo "# Testing entity specification generation commands"

# Test setup
setup_test

# Load real entities from knowledge map for testing
FEATURES=($(load_test_entities "features"))
COMPONENTS=($(load_test_entities "components"))
SCREENS=($(load_test_entities "screens"))
FUNCTIONALITY=($(load_test_entities "functionality"))
REQUIREMENTS=($(load_test_entities "requirements"))
APIS=($(load_test_entities "schema"))

# Test feature specification generation
test_feature_specs() {
    echo "# Testing feature specification generation"
    
    if [[ ${#FEATURES[@]} -gt 0 ]]; then
        local feature_id="${FEATURES[0]}"
        assert_success "feature spec generation" \
            "$KNOW_CMD feature $feature_id" \
            "# Feature Specification"
        
        assert_success "feature spec with format option" \
            "$KNOW_CMD --format md feature $feature_id" \
            "Feature Specification"
        
        assert_success "feature spec to file" \
            "$KNOW_CMD --output $TEST_DIR/feature.md feature $feature_id && test -f $TEST_DIR/feature.md"
        
        if [[ ${#FEATURES[@]} -gt 1 ]]; then
            local feature2="${FEATURES[1]}"
            assert_success "different feature spec" \
                "$KNOW_CMD feature $feature2" \
                "# Feature Specification"
        fi
    else
        skip_test "feature spec generation" "no features found in knowledge map"
    fi
}

# Test component specification generation
test_component_specs() {
    echo "# Testing component specification generation"
    
    if [[ ${#COMPONENTS[@]} -gt 0 ]]; then
        local component_id="${COMPONENTS[0]}"
        assert_success "component spec generation" \
            "$KNOW_CMD component $component_id" \
            "# Component Specification"
        
        assert_success "component spec with AI mode" \
            "$KNOW_CMD --ai component $component_id" \
            "Component Specification"
        
        if [[ ${#COMPONENTS[@]} -gt 1 ]]; then
            local component2="${COMPONENTS[1]}"
            assert_success "different component spec" \
                "$KNOW_CMD component $component2" \
                "# Component Specification"
        fi
    else
        skip_test "component spec generation" "no components found in knowledge map"
    fi
}

# Test screen specification generation
test_screen_specs() {
    echo "# Testing screen specification generation"
    
    if [[ ${#SCREENS[@]} -gt 0 ]]; then
        local screen_id="${SCREENS[0]}"
        assert_success "screen spec generation" \
            "$KNOW_CMD screen $screen_id" \
            "# Screen Specification"
        
        assert_success "screen spec JSON format" \
            "$KNOW_CMD --format json screen $screen_id" \
            "{"
        
        if [[ ${#SCREENS[@]} -gt 1 ]]; then
            local screen2="${SCREENS[1]}"
            assert_success "different screen spec" \
                "$KNOW_CMD screen $screen2" \
                "# Screen Specification"
        fi
    else
        skip_test "screen spec generation" "no screens found in knowledge map"
    fi
}

# Test functionality specification generation
test_functionality_specs() {
    echo "# Testing functionality specification generation"
    
    if [[ ${#FUNCTIONALITY[@]} -gt 0 ]]; then
        local func_id="${FUNCTIONALITY[0]}"
        assert_success "functionality spec generation" \
            "$KNOW_CMD functionality $func_id" \
            "# Functionality Specification"
        
        if [[ ${#FUNCTIONALITY[@]} -gt 1 ]]; then
            local func2="${FUNCTIONALITY[1]}"
            assert_success "different functionality spec" \
                "$KNOW_CMD functionality $func2" \
                "# Functionality Specification"
        fi
    else
        skip_test "functionality spec generation" "no functionality found in knowledge map"
    fi
}

# Test requirement specification generation
test_requirement_specs() {
    echo "# Testing requirement specification generation"
    
    if [[ ${#REQUIREMENTS[@]} -gt 0 ]]; then
        local req_id="${REQUIREMENTS[0]}"
        assert_success "requirement spec generation" \
            "$KNOW_CMD requirement $req_id" \
            "# Requirement Specification"
        
        if [[ ${#REQUIREMENTS[@]} -gt 1 ]]; then
            local req2="${REQUIREMENTS[1]}"
            assert_success "different requirement spec" \
                "$KNOW_CMD requirement $req2" \
                "# Requirement Specification"
        fi
    else
        skip_test "requirement spec generation" "no requirements found in knowledge map"
    fi
}

# Test API specification generation
test_api_specs() {
    echo "# Testing API specification generation"
    
    if [[ ${#APIS[@]} -gt 0 ]]; then
        local api_id="${APIS[0]}"
        assert_success "API spec generation" \
            "$KNOW_CMD api $api_id" \
            "# API Specification"
        
        if [[ ${#APIS[@]} -gt 1 ]]; then
            local api2="${APIS[1]}"
            assert_success "different API spec" \
                "$KNOW_CMD api $api2" \
                "# API Specification"
        fi
    else
        skip_test "API spec generation" "no APIs found in knowledge map"
    fi
}

# Test error conditions
test_spec_errors() {
    echo "# Testing error conditions for spec generation"
    
    assert_failure "invalid entity type" \
        "$KNOW_CMD invalidtype some-id" \
        "Unknown command"
    
    assert_failure "missing entity ID" \
        "$KNOW_CMD feature" \
        "Usage:"
    
    assert_failure "nonexistent entity" \
        "$KNOW_CMD feature nonexistent-feature-id" \
        "not found"
}

# Run all tests
echo "TAP version 13"

test_feature_specs
test_component_specs  
test_screen_specs
test_functionality_specs
test_requirement_specs
test_api_specs
test_spec_errors

# Cleanup and summary
cleanup_test
tap_plan $TEST_COUNT
print_summary