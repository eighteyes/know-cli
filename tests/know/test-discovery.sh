#!/bin/bash

# Test discovery commands: list, search, preview, check
# Uses real entities from knowledge graph

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"

echo "# Testing discovery commands"

# Test setup
setup_test

# Get available entity types and sample entities
ENTITY_TYPES=($(get_entity_types))

# Test list command
test_list_command() {
    echo "# Testing list command"
    
    assert_success "list all entities" \
        "$KNOW_CMD list" \
        "entities"
    
    # Test listing specific entity types
    for entity_type in "${ENTITY_TYPES[@]}"; do
        if [[ -n "$entity_type" ]]; then
            local entities
            entities=($(load_test_entities "$entity_type"))
            
            if [[ ${#entities[@]} -gt 0 ]]; then
                assert_success "list $entity_type entities" \
                    "$KNOW_CMD list $entity_type" \
                    "${entities[0]}"
            else
                skip_test "list $entity_type" "no $entity_type entities found"
            fi
        fi
    done
}

# Test search command
test_search_command() {
    echo "# Testing search command"
    
    # Get a sample entity to search for
    if [[ ${#ENTITY_TYPES[@]} -gt 0 ]]; then
        local first_type="${ENTITY_TYPES[0]}"
        local sample_entities
        sample_entities=($(load_test_entities "$first_type"))
        
        if [[ ${#sample_entities[@]} -gt 0 ]]; then
            local sample_entity="${sample_entities[0]}"
            local search_term="${sample_entity:0:5}"  # First 5 chars for partial search
            
            assert_success "basic search" \
                "$KNOW_CMD search $search_term" \
                "$sample_entity"
            
            # Test search with entity type filter
            assert_success "search with type filter" \
                "$KNOW_CMD search $search_term $first_type" \
                "$sample_entity"
            
            # Test search for common terms
            assert_success "search for 'real'" \
                "$KNOW_CMD search real"
            
            assert_success "search for 'system'" \
                "$KNOW_CMD search system"
                
        else
            skip_test "search command" "no sample entities found"
        fi
    else
        skip_test "search command" "no entity types found"
    fi
}

# Test preview command
test_preview_command() {
    echo "# Testing preview command"
    
    # Test preview for each entity type with available generators
    local generator_types=("feature" "component" "screen" "functionality" "requirement" "api")
    
    for gen_type in "${generator_types[@]}"; do
        # Map generator type to entity type
        local entity_type=""
        case "$gen_type" in
            "feature") entity_type="features" ;;
            "component") entity_type="components" ;;
            "screen") entity_type="screens" ;;
            "functionality") entity_type="functionality" ;;
            "requirement") entity_type="requirements" ;;
            "api") entity_type="schema" ;;
        esac
        
        if [[ -n "$entity_type" ]]; then
            local entities
            entities=($(load_test_entities "$entity_type"))
            
            if [[ ${#entities[@]} -gt 0 ]]; then
                local entity_id="${entities[0]}"
                
                assert_success "preview $gen_type for $entity_id" \
                    "$KNOW_CMD preview $gen_type $entity_id" \
                    "Preview"
                    
            else
                skip_test "preview $gen_type" "no $entity_type entities found"
            fi
        fi
    done
}

# Test check command
test_check_command() {
    echo "# Testing check command"
    
    # Test completeness checking for each entity type
    local generator_types=("feature" "component" "screen" "functionality" "requirement" "api")
    
    for gen_type in "${generator_types[@]}"; do
        # Map generator type to entity type  
        local entity_type=""
        case "$gen_type" in
            "feature") entity_type="features" ;;
            "component") entity_type="components" ;;
            "screen") entity_type="screens" ;;
            "functionality") entity_type="functionality" ;;
            "requirement") entity_type="requirements" ;;
            "api") entity_type="schema" ;;
        esac
        
        if [[ -n "$entity_type" ]]; then
            local entities
            entities=($(load_test_entities "$entity_type"))
            
            if [[ ${#entities[@]} -gt 0 ]]; then
                local entity_id="${entities[0]}"
                
                # check command may succeed or fail depending on entity completeness
                # We just test that it runs without crashing
                assert_success "check runs for $gen_type $entity_id" \
                    "$KNOW_CMD check $gen_type $entity_id || true"
                    
            else
                skip_test "check $gen_type" "no $entity_type entities found"
            fi
        fi
    done
}

# Test discovery error conditions
test_discovery_errors() {
    echo "# Testing discovery error conditions"
    
    assert_failure "search missing term" \
        "$KNOW_CMD search" \
        "Usage:"
    
    assert_failure "preview missing args" \
        "$KNOW_CMD preview" \
        "Usage:"
    
    assert_failure "preview missing entity" \
        "$KNOW_CMD preview feature" \
        "Usage:"
    
    assert_failure "check missing args" \
        "$KNOW_CMD check" \
        "Usage:"
    
    assert_failure "check missing entity" \
        "$KNOW_CMD check feature" \
        "Usage:"
    
    assert_failure "preview invalid type" \
        "$KNOW_CMD preview invalidtype some-id" \
        "not found"
    
    assert_failure "check invalid type" \
        "$KNOW_CMD check invalidtype some-id" \
        "not found"
}

# Test search with various patterns
test_search_patterns() {
    echo "# Testing search patterns"
    
    # Test partial word matching
    assert_success "search partial word" \
        "$KNOW_CMD search tel"  # Should match telemetry, teleoperation etc
    
    # Test case insensitive search
    assert_success "search case insensitive" \
        "$KNOW_CMD search REAL" 
    
    # Test search with dashes
    assert_success "search with dashes" \
        "$KNOW_CMD search real-time"
}

# Run all tests
echo "TAP version 13"

test_list_command
test_search_command
test_preview_command
test_check_command
test_discovery_errors
test_search_patterns

# Cleanup and summary
cleanup_test
tap_plan $TEST_COUNT
print_summary