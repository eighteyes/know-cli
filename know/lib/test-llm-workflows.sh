#!/bin/bash

# Test suite for LLM workflows
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Source the LLM modules
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/llm.sh"

echo -e "${YELLOW}Testing LLM Workflow Integration${NC}"
echo "=================================="

# Test 1: Vision Processing
test_vision() {
    echo -e "\n${YELLOW}Test 1: Vision Statement Processing${NC}"
    local vision="Build a collaborative knowledge management system with graph-based relationships"

    local result=$(process_vision "$vision" "mock")

    if echo "$result" | jq -e '.name' > /dev/null; then
        echo -e "${GREEN}✓ Vision processing successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Vision processing failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 2: Question Generation
test_questions() {
    echo -e "\n${YELLOW}Test 2: Question Generation${NC}"
    local context='{"project": "knowledge management", "entities": {}}'

    local result=$(generate_questions "$context" "feature" "mock")

    if echo "$result" | jq -e '.questions' > /dev/null; then
        echo -e "${GREEN}✓ Question generation successful${NC}"
        echo "$result" | jq '.questions | length' | xargs echo "Generated questions:"
        echo "$result" | jq '.questions[:2]'
    else
        echo -e "${RED}✗ Question generation failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 3: Question Expansion
test_expansion() {
    echo -e "\n${YELLOW}Test 3: Question Expansion${NC}"
    local question="What are the main features needed?"
    local context='{"project": "knowledge management"}'

    local result=$(expand_question "$question" "$context" "mock")

    if echo "$result" | jq -e '.multiple_choice' > /dev/null; then
        echo -e "${GREEN}✓ Question expansion successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Question expansion failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 4: Node Extraction
test_extraction() {
    echo -e "\n${YELLOW}Test 4: Node/Connection Extraction${NC}"
    local input="Users need a dashboard to view analytics and managers require reporting features"

    local result=$(extract_nodes "$input" "{}" "mock")

    if echo "$result" | jq -e '.entities' > /dev/null; then
        echo -e "${GREEN}✓ Node extraction successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Node extraction failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 5: Vision Update
test_vision_update() {
    echo -e "\n${YELLOW}Test 5: Vision Update${NC}"
    local current='{"entities": {"users": ["admin"]}}'
    local new_input="Add developer and viewer user types"

    local result=$(update_vision "$current" "$new_input" "mock")

    if echo "$result" | jq -e '.add_entities' > /dev/null; then
        echo -e "${GREEN}✓ Vision update successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Vision update failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 6: Requirements-Objectives Pairing
test_pairing() {
    echo -e "\n${YELLOW}Test 6: Requirements-Objectives Pairing${NC}"
    local requirements='["real-time-sync", "user-authentication", "data-export"]'
    local objectives='["collaboration", "security", "data-management"]'

    local result=$(pair_requirements_objectives "$requirements" "$objectives" "mock")

    if echo "$result" | jq -e '.pairings' > /dev/null; then
        echo -e "${GREEN}✓ Pairing successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Pairing failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 7: Action Inference
test_actions() {
    echo -e "\n${YELLOW}Test 7: Action Inference${NC}"
    local objectives='["collaboration", "tracking", "reporting"]'
    local existing='[]'

    local result=$(infer_actions "$objectives" "$existing" "mock")

    if echo "$result" | jq -e '.inferred_actions' > /dev/null; then
        echo -e "${GREEN}✓ Action inference successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Action inference failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 8: Workpath Analysis
test_workpath() {
    echo -e "\n${YELLOW}Test 8: Workpath Completion Analysis${NC}"
    local graph='{"entities": {"features": ["dashboard"], "components": []}}'
    local target="dashboard"

    local result=$(analyze_workpath "$graph" "$target" "mock")

    if echo "$result" | jq -e '.completeness_score' > /dev/null; then
        echo -e "${GREEN}✓ Workpath analysis successful${NC}"
        echo "$result" | jq '.'
    else
        echo -e "${RED}✗ Workpath analysis failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 9: Workflow Executor
test_executor() {
    echo -e "\n${YELLOW}Test 9: Workflow Executor${NC}"

    # Test vision workflow through executor
    local result=$("$SCRIPT_DIR/llm-workflow-executor.sh" vision "Build a project management tool" 2>/dev/null)

    if echo "$result" | jq -e '.' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Workflow executor successful${NC}"
        echo "$result" | jq '.' | head -10
    else
        echo -e "${RED}✗ Workflow executor failed${NC}"
        echo "$result"
        return 1
    fi
}

# Test 10: Provider Configuration
test_providers() {
    echo -e "\n${YELLOW}Test 10: Provider Configuration${NC}"

    local providers=$(list_providers)

    if echo "$providers" | jq -e '.providers' > /dev/null; then
        echo -e "${GREEN}✓ Provider listing successful${NC}"
        echo "$providers" | jq '.providers[] | {name, available}'
    else
        echo -e "${RED}✗ Provider listing failed${NC}"
        echo "$providers"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    local failed=0

    test_vision || ((failed++))
    test_questions || ((failed++))
    test_expansion || ((failed++))
    test_extraction || ((failed++))
    test_vision_update || ((failed++))
    test_pairing || ((failed++))
    test_actions || ((failed++))
    test_workpath || ((failed++))
    test_executor || ((failed++))
    test_providers || ((failed++))

    echo -e "\n=================================="
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}$failed tests failed${NC}"
        return 1
    fi
}

# Main execution
case "${1:-all}" in
    vision)
        test_vision
        ;;
    questions)
        test_questions
        ;;
    expansion)
        test_expansion
        ;;
    extraction)
        test_extraction
        ;;
    update)
        test_vision_update
        ;;
    pairing)
        test_pairing
        ;;
    actions)
        test_actions
        ;;
    workpath)
        test_workpath
        ;;
    executor)
        test_executor
        ;;
    providers)
        test_providers
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo "Usage: $0 [test_name|all]"
        echo "Tests: vision, questions, expansion, extraction, update, pairing, actions, workpath, executor, providers"
        exit 1
        ;;
esac