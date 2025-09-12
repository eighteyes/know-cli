#!/bin/bash

# Test error handling and edge cases for know CLI
# Comprehensive error condition testing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"

echo "# Testing error handling and edge cases"

# Test setup
setup_test

# Test help and usage
test_help_usage() {
    echo "# Testing help and usage"
    
    assert_success "help flag" \
        "$KNOW_CMD --help" \
        "ENTITY SPECIFICATIONS"
    
    assert_success "help short flag" \
        "$KNOW_CMD -h" \
        "ENTITY SPECIFICATIONS"
    
    assert_failure "no arguments" \
        "$KNOW_CMD" \
        "Usage:"
    
    assert_success "help in usage output" \
        "$KNOW_CMD 2>&1 || true" \
        "know --help"
}

# Test invalid options
test_invalid_options() {
    echo "# Testing invalid options"
    
    assert_failure "unknown option" \
        "$KNOW_CMD --invalid-option" \
        "Unknown option"
    
    assert_failure "invalid format" \
        "$KNOW_CMD --format invalid feature some-id" \
        "format"
    
    assert_failure "option without value" \
        "$KNOW_CMD --format" \
        "option"
    
    assert_failure "output without value" \
        "$KNOW_CMD --output" \
        "option"
    
    assert_failure "map without value" \
        "$KNOW_CMD --map" \
        "option"
}

# Test nonexistent knowledge map
test_invalid_knowledge_map() {
    echo "# Testing invalid knowledge map"
    
    assert_failure "nonexistent knowledge map" \
        "KNOWLEDGE_MAP=/nonexistent/path.json $KNOW_CMD list" \
        "Knowledge map not found"
    
    # Test with invalid JSON
    echo "invalid json content" > "$TEST_DIR/invalid.json"
    assert_failure "invalid JSON knowledge map" \
        "KNOWLEDGE_MAP=$TEST_DIR/invalid.json $KNOW_CMD list" \
        "parse error"
}

# Test entity resolution errors
test_entity_resolution_errors() {
    echo "# Testing entity resolution errors"
    
    assert_failure "completely invalid entity" \
        "$KNOW_CMD deps totally-nonexistent-entity-12345" \
        "not found"
    
    assert_failure "invalid entity type" \
        "$KNOW_CMD deps invalidtype:some-id" \
        "not found"
    
    assert_failure "ambiguous entity resolution" \
        "$KNOW_CMD deps ambiguous" \
        "not found"
    
    # Test malformed entity references
    assert_failure "malformed entity reference" \
        "$KNOW_CMD deps :no-type" \
        "not found"
    
    assert_failure "malformed entity reference 2" \
        "$KNOW_CMD deps type:" \
        "not found"
}

# Test file permission errors
test_file_permissions() {
    echo "# Testing file permission errors"
    
    # Test unwritable output directory
    if [[ -w "/tmp" ]]; then
        mkdir -p "$TEST_DIR/readonly"
        chmod 555 "$TEST_DIR/readonly"
        
        # Get a sample entity
        local sample_entity
        sample_entity=$(get_sample_entity)
        
        assert_failure "unwritable output directory" \
            "$KNOW_CMD --output $TEST_DIR/readonly/output.md feature $sample_entity" \
            "Permission denied"
        
        chmod 755 "$TEST_DIR/readonly"  # Cleanup
    else
        skip_test "file permission tests" "/tmp not writable"
    fi
}

# Test missing dependencies
test_missing_dependencies() {
    echo "# Testing missing dependencies"
    
    # Test without jq (simulate by using invalid PATH)
    assert_failure "missing jq dependency" \
        "PATH=/nonexistent $KNOW_CMD list" \
        "jq is required"
}

# Test resource limits and timeouts
test_resource_limits() {
    echo "# Testing resource limits"
    
    # Test with very long entity ID
    local long_id
    long_id=$(printf 'a%.0s' {1..1000})
    
    assert_failure "extremely long entity ID" \
        "$KNOW_CMD deps $long_id" \
        "not found"
    
    # Test with special characters in entity ID
    assert_failure "entity ID with special chars" \
        "$KNOW_CMD deps 'entity;rm -rf /' 2>/dev/null || true" \
        "not found"
}

# Test concurrent access
test_concurrent_access() {
    echo "# Testing concurrent access"
    
    # Test multiple know commands running simultaneously
    local sample_entity
    sample_entity=$(get_sample_entity)
    
    if [[ -n "$sample_entity" ]]; then
        # Run multiple commands in background and wait
        local pids=()
        for i in {1..3}; do
            "$KNOW_CMD" list > "$TEST_DIR/concurrent_$i.out" 2>&1 &
            pids+=($!)
        done
        
        # Wait for all to complete
        local all_success=true
        for pid in "${pids[@]}"; do
            if ! wait "$pid"; then
                all_success=false
            fi
        done
        
        if [[ "$all_success" == "true" ]]; then
            echo "ok $((++TEST_COUNT)) - concurrent access handling"
            PASS_COUNT=$((PASS_COUNT + 1))
        else
            echo "not ok $((++TEST_COUNT)) - concurrent access handling"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    else
        skip_test "concurrent access" "no sample entity available"
    fi
}

# Test edge cases in command parsing
test_command_parsing_edge_cases() {
    echo "# Testing command parsing edge cases"
    
    assert_failure "empty command" \
        "$KNOW_CMD ''" \
        "Unknown command"
    
    assert_failure "command with only spaces" \
        "$KNOW_CMD '   '" \
        "Unknown command"
    
    assert_failure "command with null bytes" \
        "$KNOW_CMD $'\0'" \
        "Unknown command"
    
    # Test commands that look similar to valid ones
    assert_failure "typo in command" \
        "$KNOW_CMD featur some-id" \
        "Unknown command"
    
    assert_failure "case sensitive command" \
        "$KNOW_CMD FEATURE some-id" \
        "Unknown command"
}

# Test output format edge cases
test_output_format_edge_cases() {
    echo "# Testing output format edge cases"
    
    local sample_entity
    sample_entity=$(get_sample_entity)
    
    if [[ -n "$sample_entity" ]]; then
        # Test with mixed case format
        assert_failure "mixed case format" \
            "$KNOW_CMD --format Md deps $sample_entity" \
            "format"
        
        # Test with extra spaces
        assert_failure "format with spaces" \
            "$KNOW_CMD --format ' md ' deps $sample_entity" \
            "format"
            
    else
        skip_test "output format edge cases" "no sample entity available"
    fi
}

# Test signal handling
test_signal_handling() {
    echo "# Testing signal handling"
    
    # This is difficult to test comprehensively in a script
    # Just verify that know doesn't leave temp files around
    local temp_count_before
    temp_count_before=$(find /tmp -name "*know*" 2>/dev/null | wc -l)
    
    "$KNOW_CMD" list > /dev/null 2>&1 || true
    
    local temp_count_after
    temp_count_after=$(find /tmp -name "*know*" 2>/dev/null | wc -l)
    
    if [[ $temp_count_after -eq $temp_count_before ]]; then
        echo "ok $((++TEST_COUNT)) - no temporary file leakage"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "not ok $((++TEST_COUNT)) - temporary file leakage detected"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# Run all tests
echo "TAP version 13"

test_help_usage
test_invalid_options
test_invalid_knowledge_map
test_entity_resolution_errors
test_file_permissions
test_missing_dependencies
test_resource_limits
test_concurrent_access
test_command_parsing_edge_cases
test_output_format_edge_cases
test_signal_handling

# Cleanup and summary
cleanup_test
tap_plan $TEST_COUNT
print_summary