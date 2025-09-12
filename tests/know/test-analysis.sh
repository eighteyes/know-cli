#!/bin/bash

# Test analysis commands: deps, impact, order, validate
# Uses real entities from knowledge graph

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"

echo "# Testing analysis commands"

# Test setup
setup_test

# Load sample entities for testing
SAMPLE_ENTITIES=()
for entity_type in $(get_entity_types); do
    entities=($(load_test_entities "$entity_type"))
    for entity in "${entities[@]}"; do
        SAMPLE_ENTITIES+=("${entity_type}:${entity}")
    done
done

# Test dependency analysis
test_deps_command() {
    echo "# Testing deps command"
    
    if [[ ${#SAMPLE_ENTITIES[@]} -gt 0 ]]; then
        local entity="${SAMPLE_ENTITIES[0]}"
        
        assert_success "basic deps analysis" \
            "$KNOW_CMD deps $entity" \
            "Dependency"
        
        # Test with different entity types
        if [[ ${#SAMPLE_ENTITIES[@]} -gt 1 ]]; then
            local entity2="${SAMPLE_ENTITIES[1]}"
            assert_success "deps for different entity" \
                "$KNOW_CMD deps $entity2"
        fi
        
        # Test short form (without type prefix if unique)
        local short_id="${entity#*:}"
        assert_success "deps with short ID" \
            "$KNOW_CMD deps $short_id"
        
    else
        skip_test "deps command" "no entities found in knowledge map"
    fi
}

# Test impact analysis
test_impact_command() {
    echo "# Testing impact command"
    
    if [[ ${#SAMPLE_ENTITIES[@]} -gt 0 ]]; then
        local entity="${SAMPLE_ENTITIES[0]}"
        
        assert_success "basic impact analysis" \
            "$KNOW_CMD impact $entity" \
            "Impact"
        
        # Test with different entities
        if [[ ${#SAMPLE_ENTITIES[@]} -gt 1 ]]; then
            local entity2="${SAMPLE_ENTITIES[1]}"
            assert_success "impact for different entity" \
                "$KNOW_CMD impact $entity2"
        fi
        
    else
        skip_test "impact command" "no entities found in knowledge map"
    fi
}

# Test implementation order
test_order_command() {
    echo "# Testing order command"
    
    assert_success "implementation order" \
        "$KNOW_CMD order" \
        "Implementation Order"
}

# Test knowledge map validation
test_validate_command() {
    echo "# Testing validate command"
    
    assert_success "knowledge map validation" \
        "$KNOW_CMD validate"
}

# Test analysis error conditions
test_analysis_errors() {
    echo "# Testing analysis error conditions"
    
    assert_failure "deps missing entity" \
        "$KNOW_CMD deps" \
        "Usage:"
    
    assert_failure "impact missing entity" \
        "$KNOW_CMD impact" \
        "Usage:"
    
    assert_failure "deps nonexistent entity" \
        "$KNOW_CMD deps nonexistent:entity" \
        "not found"
    
    assert_failure "impact nonexistent entity" \
        "$KNOW_CMD impact nonexistent:entity" \
        "not found"
}

# Test with complex entity relationships
test_relationship_analysis() {
    echo "# Testing relationship analysis"
    
    # Find entities with dependencies for more comprehensive testing
    if command -v jq >/dev/null 2>&1; then
        local entities_with_deps
        entities_with_deps=$(jq -r '
            .entities | to_entries[] | 
            select(.value | type == "object" and has("dependencies")) |
            "\(.key):\(.value | keys[0])"
        ' "$KNOWLEDGE_MAP" | head -3)
        
        if [[ -n "$entities_with_deps" ]]; then
            while IFS= read -r entity; do
                [[ -n "$entity" ]] || continue
                
                assert_success "deps for entity with relationships" \
                    "$KNOW_CMD deps $entity"
                
                assert_success "impact for entity with relationships" \
                    "$KNOW_CMD impact $entity"
                    
            done <<< "$entities_with_deps"
        fi
    fi
}

# Run all tests
echo "TAP version 13"

test_deps_command
test_impact_command
test_order_command
test_validate_command
test_analysis_errors
test_relationship_analysis

# Cleanup and summary
cleanup_test
tap_plan $TEST_COUNT
print_summary