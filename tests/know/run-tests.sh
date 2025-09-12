#!/bin/bash

# Test runner for know CLI tool
# Executes all test suites and provides comprehensive reporting

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Test configuration
VERBOSE=false
PATTERN=""
TIMEOUT=300  # 5 minutes default timeout
PARALLEL=false
JUNIT_OUTPUT=""

# Test suite files
TEST_SUITES=(
    "test-entity-specs.sh"
    "test-analysis.sh" 
    "test-discovery.sh"
    "test-packages.sh"
    "test-errors.sh"
)

# Parse command line options
usage() {
    cat << EOF
Test Runner for know CLI Tool

USAGE:
    $0 [options] [test-pattern]

OPTIONS:
    -v, --verbose           Verbose output
    -p, --parallel          Run test suites in parallel
    -t, --timeout SECONDS   Test timeout (default: 300)
    --junit FILE            Generate JUnit XML output
    --pattern PATTERN       Run only tests matching pattern
    --list                  List available test suites
    -h, --help              Show this help

EXAMPLES:
    $0                      Run all tests
    $0 -v                   Run with verbose output
    $0 --pattern entity     Run only entity-related tests
    $0 --parallel           Run test suites in parallel
    $0 --junit results.xml  Generate JUnit XML output

TEST SUITES:
EOF
    for suite in "${TEST_SUITES[@]}"; do
        echo "    ${suite%%.sh}"
    done
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --junit)
            JUNIT_OUTPUT="$2"
            shift 2
            ;;
        --pattern)
            PATTERN="$2"
            shift 2
            ;;
        --list)
            echo "Available test suites:"
            for suite in "${TEST_SUITES[@]}"; do
                echo "  ${suite%%.sh}"
            done
            exit 0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            PATTERN="$1"
            shift
            ;;
    esac
done

# Ensure know command exists
KNOW_CMD="$SCRIPT_DIR/../../know/know"
if [[ ! -f "$KNOW_CMD" ]]; then
    echo -e "${RED}Error: know command not found at $KNOW_CMD${NC}" >&2
    exit 1
fi

# Ensure knowledge map exists
KNOWLEDGE_MAP="$SCRIPT_DIR/../../knowledge-map-cmd.json"
if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    echo -e "${RED}Error: knowledge map not found at $KNOWLEDGE_MAP${NC}" >&2
    exit 1
fi

# Export for test suites
export KNOW_CMD KNOWLEDGE_MAP

# Filter test suites based on pattern
FILTERED_SUITES=()
for suite in "${TEST_SUITES[@]}"; do
    if [[ -z "$PATTERN" ]] || [[ "$suite" == *"$PATTERN"* ]]; then
        FILTERED_SUITES+=("$suite")
    fi
done

if [[ ${#FILTERED_SUITES[@]} -eq 0 ]]; then
    echo -e "${YELLOW}No test suites match pattern: $PATTERN${NC}" >&2
    exit 1
fi

# Create test results directory
RESULTS_DIR="$SCRIPT_DIR/results"
mkdir -p "$RESULTS_DIR"

# Test execution tracking
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0
SUITE_RESULTS=()

# JUnit XML generation
generate_junit_xml() {
    local output_file="$1"
    
    cat > "$output_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="know-cli-tests" tests="$TOTAL_TESTS" failures="$TOTAL_FAILED" time="$(date +%s)">
EOF

    for result in "${SUITE_RESULTS[@]}"; do
        IFS=':' read -r suite_name tests passed failed time_taken <<< "$result"
        
        cat >> "$output_file" << EOF
  <testsuite name="$suite_name" tests="$tests" failures="$failed" time="$time_taken">
EOF
        
        # Add individual test results (simplified for now)
        for ((i=1; i<=tests; i++)); do
            if [[ $i -le $passed ]]; then
                echo "    <testcase name=\"test-$i\" classname=\"$suite_name\" time=\"1\"/>" >> "$output_file"
            else
                echo "    <testcase name=\"test-$i\" classname=\"$suite_name\" time=\"1\">" >> "$output_file"
                echo "      <failure message=\"Test failed\"/>" >> "$output_file"
                echo "    </testcase>" >> "$output_file"
            fi
        done
        
        echo "  </testsuite>" >> "$output_file"
    done
    
    echo "</testsuites>" >> "$output_file"
}

# Run a single test suite
run_test_suite() {
    local suite_file="$1"
    local suite_name="${suite_file%%.sh}"
    
    echo -e "${BLUE}Running $suite_name...${NC}"
    
    local start_time
    start_time=$(date +%s)
    
    local output_file="$RESULTS_DIR/${suite_name}.tap"
    local exit_code=0
    
    # Run with timeout
    if timeout "$TIMEOUT" bash "$SCRIPT_DIR/$suite_file" > "$output_file" 2>&1; then
        exit_code=0
    else
        exit_code=$?
    fi
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Parse TAP output
    local tests_run=0
    local tests_passed=0
    local tests_failed=0
    
    if [[ -f "$output_file" ]]; then
        tests_run=$(grep -c "^ok\|^not ok" "$output_file" 2>/dev/null || echo "0")
        tests_passed=$(grep -c "^ok" "$output_file" 2>/dev/null || echo "0")
        tests_failed=$(grep -c "^not ok" "$output_file" 2>/dev/null || echo "0")
    fi
    
    # Update totals
    TOTAL_TESTS=$((TOTAL_TESTS + tests_run))
    TOTAL_PASSED=$((TOTAL_PASSED + tests_passed))
    TOTAL_FAILED=$((TOTAL_FAILED + tests_failed))
    
    # Store result for JUnit
    SUITE_RESULTS+=("$suite_name:$tests_run:$tests_passed:$tests_failed:$duration")
    
    # Print results
    if [[ $exit_code -eq 0 && $tests_failed -eq 0 ]]; then
        echo -e "${GREEN}✓ $suite_name: $tests_passed/$tests_run passed (${duration}s)${NC}"
    else
        echo -e "${RED}✗ $suite_name: $tests_passed/$tests_run passed, $tests_failed failed (${duration}s)${NC}"
    fi
    
    # Show verbose output if requested
    if [[ "$VERBOSE" == "true" ]] || [[ $tests_failed -gt 0 ]]; then
        echo -e "${CYAN}Output from $suite_name:${NC}"
        cat "$output_file"
        echo
    fi
    
    return $exit_code
}

# Main execution
echo -e "${CYAN}Know CLI Test Runner${NC}"
echo "Running ${#FILTERED_SUITES[@]} test suite(s)..."
echo

# Record start time
START_TIME=$(date +%s)

# Run test suites
if [[ "$PARALLEL" == "true" ]]; then
    echo "Running test suites in parallel..."
    
    pids=()
    for suite in "${FILTERED_SUITES[@]}"; do
        run_test_suite "$suite" &
        pids+=($!)
    done
    
    # Wait for all suites to complete
    for pid in "${pids[@]}"; do
        wait "$pid" || true
    done
else
    # Run sequentially
    for suite in "${FILTERED_SUITES[@]}"; do
        run_test_suite "$suite" || true
        echo
    done
fi

# Record end time
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

# Generate JUnit XML if requested
if [[ -n "$JUNIT_OUTPUT" ]]; then
    generate_junit_xml "$JUNIT_OUTPUT"
    echo -e "${CYAN}JUnit XML report written to: $JUNIT_OUTPUT${NC}"
fi

# Final summary
echo "═══════════════════════════════════════════════════════════"
echo -e "${CYAN}Test Summary${NC}"
echo "Total test suites: ${#FILTERED_SUITES[@]}"
echo "Total tests: $TOTAL_TESTS"
echo "Total time: ${TOTAL_DURATION}s"
echo

if [[ $TOTAL_FAILED -eq 0 ]]; then
    echo -e "${GREEN}✓ All $TOTAL_PASSED tests passed!${NC}"
    echo "Results saved to: $RESULTS_DIR"
    exit 0
else
    echo -e "${RED}✗ $TOTAL_FAILED out of $TOTAL_TESTS tests failed${NC}"
    echo -e "${YELLOW}Passed: $TOTAL_PASSED${NC}"
    echo "Results saved to: $RESULTS_DIR"
    
    # Show failed test details
    echo
    echo -e "${RED}Failed test suites:${NC}"
    for result in "${SUITE_RESULTS[@]}"; do
        IFS=':' read -r suite_name tests passed failed time_taken <<< "$result"
        if [[ $failed -gt 0 ]]; then
            echo "  $suite_name: $failed failed"
        fi
    done
    
    exit 1
fi