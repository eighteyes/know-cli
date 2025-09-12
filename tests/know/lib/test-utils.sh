#!/bin/bash

# Test utilities for know CLI tool
# Uses TAP (Test Anything Protocol) output format

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Test counters
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# Test configuration
KNOW_CMD="${KNOW_CMD:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)/know/know}"
KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)/knowledge-map-cmd.json}"

# Ensure know command exists
if [[ ! -f "$KNOW_CMD" ]]; then
    echo "Error: know command not found at $KNOW_CMD" >&2
    exit 1
fi

if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo "Error: knowledge map not found at $KNOWLEDGE_MAP" >&2
    exit 1
fi

# Dynamic entity loading from knowledge map
load_test_entities() {
    local entity_type="$1"
    jq -r ".entities.${entity_type} // {} | keys[]" "$KNOWLEDGE_MAP" 2>/dev/null | head -3
}

# Get all entity types
get_entity_types() {
    jq -r '.entities | keys[]' "$KNOWLEDGE_MAP"
}

# Get a sample entity of any type
get_sample_entity() {
    local entity_type
    entity_type=$(get_entity_types | head -1)
    local entity_id
    entity_id=$(load_test_entities "$entity_type" | head -1)
    echo "${entity_type}:${entity_id}"
}

# Test assertion functions
assert_success() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="${3:-}"
    
    TEST_COUNT=$((TEST_COUNT + 1))
    
    local output
    local exit_code=0
    
    output=$(eval "$command" 2>&1) || exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        if [[ -n "$expected_pattern" ]] && ! echo "$output" | grep -q "$expected_pattern"; then
            echo "not ok $TEST_COUNT - $test_name (missing expected pattern: $expected_pattern)"
            echo "# Command: $command"
            echo "# Output: $output"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        else
            echo "ok $TEST_COUNT - $test_name"
            PASS_COUNT=$((PASS_COUNT + 1))
        fi
    else
        echo "not ok $TEST_COUNT - $test_name (exit code: $exit_code)"
        echo "# Command: $command"
        echo "# Output: $output"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_failure() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="${3:-}"
    
    TEST_COUNT=$((TEST_COUNT + 1))
    
    local output
    local exit_code=0
    
    output=$(eval "$command" 2>&1) || exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        if [[ -n "$expected_pattern" ]] && ! echo "$output" | grep -q "$expected_pattern"; then
            echo "not ok $TEST_COUNT - $test_name (missing expected error pattern: $expected_pattern)"
            echo "# Command: $command"
            echo "# Output: $output"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        else
            echo "ok $TEST_COUNT - $test_name"
            PASS_COUNT=$((PASS_COUNT + 1))
        fi
    else
        echo "not ok $TEST_COUNT - $test_name (expected failure but command succeeded)"
        echo "# Command: $command"
        echo "# Output: $output"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

assert_contains() {
    local test_name="$1"
    local command="$2"
    local expected_pattern="$3"
    
    assert_success "$test_name" "$command" "$expected_pattern"
}

# Test output capture
capture_output() {
    local command="$1"
    eval "$command" 2>&1
}

# Setup test environment
setup_test() {
    # Create temporary directory for test outputs
    TEST_DIR=$(mktemp -d)
    export TEST_DIR
}

# Cleanup test environment
cleanup_test() {
    if [[ -n "${TEST_DIR:-}" ]] && [[ -d "$TEST_DIR" ]]; then
        rm -rf "$TEST_DIR"
    fi
}

# Print test summary
print_summary() {
    echo
    echo "# Test Summary:"
    echo "# Total tests: $TEST_COUNT"
    echo "# Passed: $PASS_COUNT"
    echo "# Failed: $FAIL_COUNT"
    
    if [[ $FAIL_COUNT -eq 0 ]]; then
        echo -e "${GREEN}# All tests passed!${NC}" >&2
        return 0
    else
        echo -e "${RED}# $FAIL_COUNT test(s) failed${NC}" >&2
        return 1
    fi
}

# Run test with timeout
run_with_timeout() {
    local timeout_seconds="$1"
    local command="$2"
    
    timeout "$timeout_seconds" bash -c "$command" 2>&1
}

# Generate TAP plan
tap_plan() {
    local expected_tests="$1"
    echo "1..$expected_tests"
}

# Skip test
skip_test() {
    local test_name="$1"
    local reason="$2"
    
    TEST_COUNT=$((TEST_COUNT + 1))
    echo "ok $TEST_COUNT - $test_name # SKIP $reason"
    PASS_COUNT=$((PASS_COUNT + 1))
}