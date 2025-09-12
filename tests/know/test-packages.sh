#!/bin/bash

# Test package generation commands: package, test
# Uses real entities from knowledge graph

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"

echo "# Testing package generation commands"

# Test setup
setup_test

# Load sample entities for testing
SAMPLE_ENTITIES=()
for entity_type in $(get_entity_types); do
    entities=($(load_test_entities "$entity_type"))
    for entity in "${entities[@]}"; do
        SAMPLE_ENTITIES+=("${entity_type}:${entity}")
        # Limit to prevent excessive testing
        if [[ ${#SAMPLE_ENTITIES[@]} -ge 5 ]]; then
            break 2
        fi
    done
done

# Test package generation
test_package_command() {
    echo "# Testing package command"
    
    if [[ ${#SAMPLE_ENTITIES[@]} -gt 0 ]]; then
        local entity="${SAMPLE_ENTITIES[0]}"
        
        assert_success "basic package generation" \
            "$KNOW_CMD package $entity" \
            "Implementation Package"
        
        # Test package with different output formats
        assert_success "package with JSON format" \
            "$KNOW_CMD --format json package $entity" \
            "{"
        
        assert_success "package with YAML format" \
            "$KNOW_CMD --format yaml package $entity"
        
        # Test package to file
        assert_success "package to file" \
            "$KNOW_CMD --output $TEST_DIR/package.md package $entity && test -f $TEST_DIR/package.md"
        
        # Test different entities if available
        if [[ ${#SAMPLE_ENTITIES[@]} -gt 1 ]]; then
            local entity2="${SAMPLE_ENTITIES[1]}"
            assert_success "package for different entity" \
                "$KNOW_CMD package $entity2" \
                "Implementation Package"
        fi
        
    else
        skip_test "package command" "no entities found in knowledge map"
    fi
}

# Test test scenario generation
test_test_command() {
    echo "# Testing test scenario generation"
    
    if [[ ${#SAMPLE_ENTITIES[@]} -gt 0 ]]; then
        local entity="${SAMPLE_ENTITIES[0]}"
        
        assert_success "basic test generation" \
            "$KNOW_CMD test $entity" \
            "Test Scenarios"
        
        # Test with different output formats
        assert_success "test with JSON format" \
            "$KNOW_CMD --format json test $entity" \
            "{"
        
        # Test to file
        assert_success "test to file" \
            "$KNOW_CMD --output $TEST_DIR/tests.md test $entity && test -f $TEST_DIR/tests.md"
        
        # Test different entities if available
        if [[ ${#SAMPLE_ENTITIES[@]} -gt 1 ]]; then
            local entity2="${SAMPLE_ENTITIES[1]}"
            assert_success "test for different entity" \
                "$KNOW_CMD test $entity2" \
                "Test Scenarios"
        fi
        
    else
        skip_test "test command" "no entities found in knowledge map"
    fi
}

# Test AI mode for packages
test_ai_mode_packages() {
    echo "# Testing AI mode for packages"
    
    if [[ ${#SAMPLE_ENTITIES[@]} -gt 0 ]]; then
        local entity="${SAMPLE_ENTITIES[0]}"
        
        assert_success "package with AI mode" \
            "$KNOW_CMD --ai package $entity" \
            "Implementation Package"
        
        assert_success "test with AI mode" \
            "$KNOW_CMD --ai test $entity" \
            "Test Scenarios"
            
    else
        skip_test "AI mode packages" "no entities found in knowledge map"
    fi
}

# Test package generation for specific entity types
test_entity_specific_packages() {
    echo "# Testing packages for specific entity types"
    
    # Test packages for features (usually have good acceptance criteria)
    local features=($(load_test_entities "features"))
    if [[ ${#features[@]} -gt 0 ]]; then
        local feature_id="${features[0]}"
        assert_success "package for feature" \
            "$KNOW_CMD package features:$feature_id" \
            "Implementation Package"
    fi
    
    # Test packages for components
    local components=($(load_test_entities "components"))
    if [[ ${#components[@]} -gt 0 ]]; then
        local component_id="${components[0]}"
        assert_success "package for component" \
            "$KNOW_CMD package components:$component_id" \
            "Implementation Package"
    fi
    
    # Test packages for screens
    local screens=($(load_test_entities "screens"))
    if [[ ${#screens[@]} -gt 0 ]]; then
        local screen_id="${screens[0]}"
        assert_success "package for screen" \
            "$KNOW_CMD package screens:$screen_id" \
            "Implementation Package"
    fi
}

# Test package error conditions
test_package_errors() {
    echo "# Testing package error conditions"
    
    assert_failure "package missing entity" \
        "$KNOW_CMD package" \
        "Usage:"
    
    assert_failure "test missing entity" \
        "$KNOW_CMD test" \
        "Usage:"
    
    assert_failure "package nonexistent entity" \
        "$KNOW_CMD package nonexistent:entity" \
        "not found"
    
    assert_failure "test nonexistent entity" \
        "$KNOW_CMD test nonexistent:entity" \
        "not found"
}

# Test comprehensive package with dependencies
test_comprehensive_packages() {
    echo "# Testing comprehensive packages"
    
    # Find entities that likely have dependencies for comprehensive testing
    if command -v jq >/dev/null 2>&1; then
        local complex_entities
        complex_entities=$(jq -r '
            .entities | to_entries[] |
            select(.value | type == "object" and (
                has("dependencies") or 
                has("acceptance_criteria") or
                (has("references") and (.references | length > 0))
            )) |
            "\(.key):\(.value | keys[0])"
        ' "$KNOWLEDGE_MAP" | head -2)
        
        if [[ -n "$complex_entities" ]]; then
            while IFS= read -r entity; do
                [[ -n "$entity" ]] || continue
                
                assert_success "comprehensive package for $entity" \
                    "$KNOW_CMD package $entity" \
                    "Implementation Package"
                
                assert_success "comprehensive test for $entity" \
                    "$KNOW_CMD test $entity" \
                    "Test Scenarios"
                    
            done <<< "$complex_entities"
        fi
    fi
}

# Run all tests
echo "TAP version 13"

test_package_command
test_test_command
test_ai_mode_packages
test_entity_specific_packages
test_package_errors
test_comprehensive_packages

# Cleanup and summary
cleanup_test
tap_plan $TEST_COUNT
print_summary