#!/bin/bash

# LLM Provider Abstraction Layer for Know tool
# Supports: Anthropic API, LM Studio (localhost:1234), Mock responses

set -euo pipefail

# Get script directory for config loading
LLM_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source configuration management
source "$LLM_SCRIPT_DIR/llm-config.sh" 2>/dev/null || true

# Default configuration (with config file support)
DEFAULT_PROVIDER="${LLM_PROVIDER:-$(get_config "provider" 2>/dev/null || echo "mock")}"
DEFAULT_MODEL="${LLM_MODEL:-$(get_config "model" 2>/dev/null || echo "claude-3-haiku-20240307")}"
DEFAULT_MAX_TOKENS="${LLM_MAX_TOKENS:-$(get_config "max_tokens" 2>/dev/null || echo "1024")}"
DEFAULT_TEMPERATURE="${LLM_TEMPERATURE:-$(get_config "temperature" 2>/dev/null || echo "0.7")}"

# Provider endpoints
ANTHROPIC_API_URL="https://api.anthropic.com/v1/messages"
LM_STUDIO_URL="${LM_STUDIO_URL:-http://localhost:1234/v1/chat/completions}"

# Colors for output (reuse if already defined to avoid conflicts)
if [ -z "${RED:-}" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
fi

# Logging function
log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_info() {
    [ "${VERBOSE:-0}" = "1" ] && echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_debug() {
    [ "${DEBUG:-0}" = "1" ] && echo -e "${YELLOW}[DEBUG]${NC} $1" >&2
}

# Mock response generator
generate_mock_response() {
    local prompt="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

    cat <<EOF
{
  "provider": "mock",
  "model": "mock-model",
  "timestamp": "$timestamp",
  "response": "This is a mock response for testing purposes. Your prompt was: ${prompt:0:100}...",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  },
  "success": true
}
EOF
}

# Anthropic API call
call_anthropic() {
    local prompt="$1"
    local model="${2:-$DEFAULT_MODEL}"
    local max_tokens="${3:-$DEFAULT_MAX_TOKENS}"
    local temperature="${4:-$DEFAULT_TEMPERATURE}"

    # Get API key from config or environment
    local api_key
    if command -v get_config >/dev/null 2>&1; then
        api_key=$(get_config "api_key")
    else
        api_key="${ANTHROPIC_API_KEY:-}"
    fi

    # Check for API key
    if [ -z "$api_key" ]; then
        log_error "No API key found. Set it with: know llm config set api_key"
        echo '{"error": "API key not configured", "success": false}'
        return 1
    fi

    local request_body=$(cat <<EOF
{
  "model": "$model",
  "max_tokens": $max_tokens,
  "temperature": $temperature,
  "messages": [
    {
      "role": "user",
      "content": "$prompt"
    }
  ]
}
EOF
    )

    log_debug "Request body: $request_body"

    local response=$(curl -s -X POST "$ANTHROPIC_API_URL" \
        -H "Content-Type: application/json" \
        -H "x-api-key: $api_key" \
        -H "anthropic-version: 2023-06-01" \
        -d "$request_body" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo '{"error": "Failed to connect to Anthropic API", "success": false}'
        return 1
    fi

    # Check for error in response
    if echo "$response" | grep -q '"error"'; then
        echo "$response" | jq '{error: .error, success: false}'
        return 1
    fi

    # Extract and format response
    local content=$(echo "$response" | jq -r '.content[0].text // "No response"')
    local usage=$(echo "$response" | jq '.usage // {}')

    cat <<EOF
{
  "provider": "anthropic",
  "model": "$model",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "response": $(echo "$content" | jq -Rs .),
  "usage": $usage,
  "success": true
}
EOF
}

# LM Studio API call (OpenAI-compatible format)
call_lm_studio() {
    local prompt="$1"
    local model="${2:-local-model}"
    local max_tokens="${3:-$DEFAULT_MAX_TOKENS}"
    local temperature="${4:-$DEFAULT_TEMPERATURE}"

    # Check if LM Studio is running
    if ! curl -s -o /dev/null -w "%{http_code}" "$LM_STUDIO_URL" | grep -q "404"; then
        log_error "LM Studio server not responding at $LM_STUDIO_URL"
        echo '{"error": "LM Studio server not available", "success": false}'
        return 1
    fi

    local request_body=$(cat <<EOF
{
  "model": "$model",
  "messages": [
    {
      "role": "user",
      "content": "$prompt"
    }
  ],
  "max_tokens": $max_tokens,
  "temperature": $temperature
}
EOF
    )

    log_debug "Request body: $request_body"

    local response=$(curl -s -X POST "$LM_STUDIO_URL" \
        -H "Content-Type: application/json" \
        -d "$request_body" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo '{"error": "Failed to connect to LM Studio", "success": false}'
        return 1
    fi

    # Extract and format response
    local content=$(echo "$response" | jq -r '.choices[0].message.content // "No response"')
    local usage=$(echo "$response" | jq '.usage // {}')

    cat <<EOF
{
  "provider": "lm_studio",
  "model": "$model",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "response": $(echo "$content" | jq -Rs .),
  "usage": $usage,
  "success": true
}
EOF
}

# Main LLM function
llm_query() {
    local prompt="$1"
    local provider="${2:-$DEFAULT_PROVIDER}"
    local model="${3:-$DEFAULT_MODEL}"
    local max_tokens="${4:-$DEFAULT_MAX_TOKENS}"
    local temperature="${5:-$DEFAULT_TEMPERATURE}"

    log_info "Provider: $provider, Model: $model"
    log_debug "Prompt: $prompt"

    case "$provider" in
        mock)
            generate_mock_response "$prompt"
            ;;
        anthropic)
            call_anthropic "$prompt" "$model" "$max_tokens" "$temperature"
            ;;
        lm_studio|lmstudio|local)
            call_lm_studio "$prompt" "$model" "$max_tokens" "$temperature"
            ;;
        *)
            log_error "Unknown provider: $provider"
            echo '{"error": "Unknown provider", "success": false}'
            return 1
            ;;
    esac
}

# Stream response function (for future implementation)
llm_stream() {
    local prompt="$1"
    local provider="${2:-$DEFAULT_PROVIDER}"

    log_info "Streaming not yet implemented for provider: $provider"
    llm_query "$prompt" "$provider"
}

# List available providers
list_providers() {
    # Check for API key in config or environment
    local has_api_key=false
    if command -v get_config >/dev/null 2>&1; then
        local api_key=$(get_config "api_key")
        [ -n "$api_key" ] && has_api_key=true
    else
        [ -n "${ANTHROPIC_API_KEY:-}" ] && has_api_key=true
    fi

    cat <<EOF
{
  "providers": [
    {
      "name": "mock",
      "description": "Mock provider for testing",
      "available": true
    },
    {
      "name": "anthropic",
      "description": "Anthropic Claude API",
      "available": $([ "$has_api_key" = true ] && echo "true" || echo "false"),
      "requires": "API key (use: know llm config set api_key)"
    },
    {
      "name": "lm_studio",
      "description": "LM Studio local server",
      "available": $(curl -s -o /dev/null -w "%{http_code}" "$LM_STUDIO_URL" 2>/dev/null | grep -q "404" && echo "true" || echo "false"),
      "endpoint": "$LM_STUDIO_URL"
    }
  ]
}
EOF
}

# Test provider connectivity
test_provider() {
    local provider="${1:-$DEFAULT_PROVIDER}"

    log_info "Testing provider: $provider"

    local test_prompt="Hello, this is a connectivity test."
    local result=$(llm_query "$test_prompt" "$provider")

    if echo "$result" | jq -e '.success' > /dev/null; then
        echo "$result" | jq '{provider: .provider, status: "connected", success: true}'
    else
        echo "$result" | jq '{provider: "'$provider'", status: "failed", error: .error, success: false}'
    fi
}

# Configuration helper (delegates to llm-config.sh)
show_config() {
    # Use the config management system
    if command -v list_config >/dev/null 2>&1; then
        list_config
    else
        # Check for API key in config or environment
        local api_key_set=false
        if command -v get_config >/dev/null 2>&1; then
            local api_key=$(get_config "api_key")
            [ -n "$api_key" ] && api_key_set=true
        else
            [ -n "${ANTHROPIC_API_KEY:-}" ] && api_key_set=true
        fi

        # Fallback to basic display
        cat <<EOF
{
  "current_config": {
    "provider": "$DEFAULT_PROVIDER",
    "model": "$DEFAULT_MODEL",
    "max_tokens": $DEFAULT_MAX_TOKENS,
    "temperature": $DEFAULT_TEMPERATURE,
    "api_key_set": $api_key_set,
    "lm_studio_url": "$LM_STUDIO_URL"
  },
  "environment_variables": {
    "LLM_PROVIDER": "Set default provider (mock, anthropic, lm_studio)",
    "LLM_MODEL": "Set default model",
    "LLM_MAX_TOKENS": "Set default max tokens",
    "LLM_TEMPERATURE": "Set default temperature",
    "ANTHROPIC_API_KEY": "API key for Anthropic",
    "LM_STUDIO_URL": "URL for LM Studio server"
  }
}
EOF
    fi
}

# Help function
show_help() {
    cat <<EOF
LLM Provider Abstraction Layer

Usage: source llm.sh && llm_query "prompt" [provider] [model] [max_tokens] [temperature]

Functions:
  llm_query        - Send a query to an LLM provider
  llm_stream       - Stream responses (future implementation)
  list_providers   - List available providers and their status
  test_provider    - Test connectivity to a provider
  show_config      - Show current configuration

Providers:
  mock            - Mock responses for testing
  anthropic       - Anthropic Claude API
  lm_studio       - LM Studio local server

Environment Variables:
  LLM_PROVIDER    - Default provider (default: mock)
  LLM_MODEL       - Default model
  LLM_MAX_TOKENS  - Default max tokens (default: 1024)
  LLM_TEMPERATURE - Default temperature (default: 0.7)
  ANTHROPIC_API_KEY - API key for Anthropic
  LM_STUDIO_URL   - URL for LM Studio (default: http://localhost:1234/v1/chat/completions)

Examples:
  # Use mock provider
  llm_query "What is the capital of France?" mock

  # Use Anthropic
  export ANTHROPIC_API_KEY="your-key"
  llm_query "Explain quantum computing" anthropic claude-3-haiku-20240307

  # Use LM Studio
  llm_query "Write a haiku" lm_studio

  # Test connectivity
  test_provider anthropic

  # List providers
  list_providers
EOF
}

# Export functions for use in other scripts (bash-specific, not needed when sourced)
# export -f llm_query
# export -f llm_stream
# export -f list_providers
# export -f test_provider
# export -f show_config
# export -f generate_mock_response
# export -f call_anthropic
# export -f call_lm_studio

# =====================================================
# Know Tool Specific Workflows
# =====================================================

# 1. Vision Statement Processing
process_vision() {
    local vision_input="$1"
    local provider="${2:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Process the following vision statement for a software project.
Extract and return a JSON object with:
- name: project name
- tagline: brief tagline (max 10 words)
- blurb: project description (1-2 sentences)
- refined_input: cleaned and focused version of the vision

Vision: $vision_input

Return ONLY valid JSON, no markdown or explanations.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        generate_workflow_mock "vision"
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 500 0.7)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to process vision", "success": false}'
    fi
}

# 2. Question Frontier Generation
generate_questions() {
    local context="$1"
    local entity_type="${2:-feature}"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Generate 10 specific questions to explore the "$entity_type" aspects of this project context.
Questions should follow the dependency chain and help identify entities, references, and relationships.

Context: $context

Return a JSON object with:
{
  "questions": [
    {"id": 1, "question": "...", "entity_type": "$entity_type", "dependency_focus": "..."},
    ...
  ]
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        generate_workflow_mock "questions"
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 800 0.8)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to generate questions", "success": false}'
    fi
}

# 3. Question Expansion (MC/Recommendations)
expand_question() {
    local question="$1"
    local context="${2:-}"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Expand this question with multiple choice options and recommendations.

Question: $question
Context: $context

Return JSON with:
{
  "question": "$question",
  "multiple_choice": ["option1", "option2", "option3", "option4"],
  "recommendations": ["rec1", "rec2"],
  "tradeoffs": {"option1": "tradeoff description", ...}
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        cat <<EOF
{
  "question": "$question",
  "multiple_choice": ["Graph database", "Document store", "SQL database", "Key-value store"],
  "recommendations": [
    "Graph database for relationships",
    "Consider Neo4j or DGraph",
    "Start with document store for rapid prototyping",
    "Plan migration path from simple to complex"
  ],
  "tradeoffs": {
    "Graph database": "Complex queries but harder to scale",
    "Document store": "Simple but limited relationships",
    "SQL database": "ACID compliance but rigid schema",
    "Key-value store": "High performance but basic queries"
  },
  "challenges": {
    "Graph database": [
      "Learning curve for query languages (Cypher, Gremlin)",
      "Scaling horizontally is complex",
      "Limited tooling compared to SQL databases",
      "Performance tuning requires specialized knowledge"
    ],
    "Document store": [
      "No enforced relationships between documents",
      "Potential data duplication and inconsistency",
      "Complex queries can be inefficient",
      "Schema evolution challenges"
    ],
    "SQL database": [
      "Schema migrations can be complex",
      "Object-relational impedance mismatch",
      "Vertical scaling limitations",
      "Fixed table structure limits flexibility"
    ],
    "Key-value store": [
      "Very limited query capabilities",
      "No built-in relationships",
      "Application must handle data consistency",
      "Debugging and monitoring can be difficult"
    ]
  },
  "alternatives": [
    {
      "option": "Hybrid approach",
      "description": "Use multiple databases for different use cases",
      "benefits": ["Best tool for each job", "Flexibility", "Optimized performance"],
      "drawbacks": ["Increased complexity", "Data synchronization", "Multiple technologies to maintain"]
    },
    {
      "option": "NewSQL databases",
      "description": "Modern databases that combine SQL with NoSQL benefits",
      "benefits": ["ACID compliance", "Horizontal scaling", "Familiar SQL interface"],
      "drawbacks": ["Relatively new technology", "Limited vendor options", "Learning curve for scaling"]
    },
    {
      "option": "Multi-model databases",
      "description": "Single database supporting multiple data models",
      "benefits": ["Single technology stack", "Unified queries", "Simplified architecture"],
      "drawbacks": ["May not excel at any single model", "Vendor lock-in", "Potentially higher costs"]
    }
  ],
  "implementation_considerations": {
    "team_expertise": "Consider current team skills and available training time",
    "data_volume": "Scale requirements will influence database choice",
    "query_patterns": "Known access patterns should drive selection",
    "budget_constraints": "Licensing, infrastructure, and maintenance costs",
    "timeline": "Time available for learning and implementation"
  },
  "decision_matrix": {
    "criteria": ["Performance", "Scalability", "Flexibility", "Team Familiarity", "Cost"],
    "weights": {"Performance": 0.25, "Scalability": 0.20, "Flexibility": 0.20, "Team Familiarity": 0.20, "Cost": 0.15}
  },
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "provider": "mock"
}
EOF
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 600 0.7)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to expand question", "success": false}'
    fi
}

# 4. Node/Connection Extraction
extract_nodes() {
    local input_text="$1"
    local dependency_rules="${2:-}"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Extract entities and references from this input according to dependency rules.

Input: $input_text
Rules: $dependency_rules

Return JSON with:
{
  "entities": {
    "users": ["user1", "user2"],
    "objectives": ["obj1"],
    "features": ["feature1"],
    ...
  },
  "references": {
    "ref_key": "ref_value",
    ...
  },
  "connections": [
    {"from": "entity_type:entity_key", "to": "entity_type:entity_key", "type": "depends_on"}
  ]
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        generate_workflow_mock "extraction"
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 1000 0.6)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to extract nodes", "success": false}'
    fi
}

# 5. Vision Update (Prioritize Users/Requirements/Objectives/Actions)
update_vision() {
    local current_graph="$1"
    local new_input="$2"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Update the vision based on new input, prioritizing:
1. Users (who uses the system)
2. Requirements (what the system must do)
3. Objectives (what goals to achieve)
4. Actions (how users interact)

Current graph state: $current_graph
New input: $new_input

Return JSON with suggested modifications:
{
  "add_entities": {...},
  "modify_entities": {...},
  "add_connections": [...],
  "priority_order": ["users", "requirements", "objectives", "actions"]
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        cat <<EOF
{
  "add_entities": {
    "users": ["developer", "viewer"],
    "requirements": ["scalability", "performance"]
  },
  "modify_entities": {},
  "add_connections": [
    {"from": "user:developer", "to": "requirement:scalability"}
  ],
  "priority_order": ["users", "requirements", "objectives", "actions"],
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "provider": "mock"
}
EOF
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 1200 0.7)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to update vision", "success": false}'
    fi
}

# 6. Requirements-Objectives Pairing
pair_requirements_objectives() {
    local requirements="$1"
    local objectives="$2"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Match requirements to objectives based on their relationships.

Requirements: $requirements
Objectives: $objectives

Return JSON with pairings:
{
  "pairings": [
    {"requirement": "req_key", "objective": "obj_key", "rationale": "..."},
    ...
  ],
  "unmatched_requirements": [],
  "unmatched_objectives": []
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        cat <<EOF
{
  "pairings": [
    {"requirement": "real-time-sync", "objective": "collaboration", "rationale": "Real-time sync enables collaboration"},
    {"requirement": "user-authentication", "objective": "security", "rationale": "Authentication provides security"}
  ],
  "unmatched_requirements": ["data-export"],
  "unmatched_objectives": [],
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "provider": "mock"
}
EOF
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 800 0.6)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to pair requirements and objectives", "success": false}'
    fi
}

# 7. Action Inference
infer_actions() {
    local objectives="$1"
    local existing_actions="${2:-[]}"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Infer user actions needed to achieve these objectives.

Objectives: $objectives
Existing actions: $existing_actions

Return JSON with:
{
  "inferred_actions": [
    {"action": "action_key", "description": "...", "objective": "obj_key"},
    ...
  ],
  "action_dependencies": [
    {"action": "action1", "depends_on": "action2"}
  ]
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        cat <<EOF
{
  "inferred_actions": [
    {"action": "create-project", "description": "Create a new project", "objective": "collaboration"},
    {"action": "view-dashboard", "description": "View project dashboard", "objective": "tracking"}
  ],
  "action_dependencies": [
    {"action": "view-dashboard", "depends_on": "create-project"}
  ],
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "provider": "mock"
}
EOF
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 800 0.7)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to infer actions", "success": false}'
    fi
}

# 8. Workpath Completion Analysis
analyze_workpath() {
    local graph_state="$1"
    local target_feature="${2:-}"
    local provider="${3:-$DEFAULT_PROVIDER}"

    local prompt=$(cat <<EOF
Analyze the completeness of the workpath for implementing this feature.

Graph state: $graph_state
Target feature: $target_feature

Identify gaps and return JSON:
{
  "completeness_score": 0.85,
  "missing_entities": {...},
  "missing_connections": [...],
  "recommendations": ["..."],
  "next_steps": ["..."]
}

Return ONLY valid JSON.
EOF
    )

    # Use mock response for testing
    if [ "$provider" = "mock" ]; then
        cat <<EOF
{
  "completeness_score": 0.65,
  "missing_entities": {
    "components": ["dashboard-widget", "data-processor"]
  },
  "missing_connections": [
    {"from": "feature:dashboard", "to": "component:dashboard-widget"}
  ],
  "recommendations": [
    "Add dashboard components",
    "Define data processing pipeline"
  ],
  "next_steps": [
    "Create component specifications",
    "Map component dependencies"
  ],
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "provider": "mock"
}
EOF
        return 0
    fi

    local response=$(llm_query "$prompt" "$provider" "$DEFAULT_MODEL" 1000 0.6)

    if echo "$response" | jq -e '.success' > /dev/null; then
        echo "$response" | jq '.response' | jq -r '.'
    else
        echo '{"error": "Failed to analyze workpath", "success": false}'
    fi
}

# Mock implementations for workflows (enhanced)
generate_workflow_mock() {
    local workflow="$1"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

    case "$workflow" in
        vision)
            cat <<EOF
{
  "name": "mock-project",
  "tagline": "A mock project for testing",
  "blurb": "This is a mock project description for testing the vision processing workflow.",
  "refined_input": "Create a collaborative project management tool",
  "timestamp": "$timestamp",
  "provider": "mock"
}
EOF
            ;;
        questions)
            cat <<EOF
{
  "questions": [
    {"id": 1, "question": "What users will interact with this system?", "entity_type": "user", "dependency_focus": "requirements"},
    {"id": 2, "question": "What are the main objectives?", "entity_type": "objective", "dependency_focus": "features"},
    {"id": 3, "question": "What features are required?", "entity_type": "feature", "dependency_focus": "components"}
  ],
  "timestamp": "$timestamp",
  "provider": "mock"
}
EOF
            ;;
        extraction)
            cat <<EOF
{
  "entities": {
    "users": ["admin", "developer", "viewer"],
    "objectives": ["collaboration", "tracking"],
    "features": ["dashboard", "notifications"]
  },
  "references": {
    "api_version": "v1.0",
    "theme": "modern"
  },
  "connections": [
    {"from": "user:admin", "to": "objective:collaboration", "type": "depends_on"}
  ],
  "timestamp": "$timestamp",
  "provider": "mock"
}
EOF
            ;;
        *)
            echo '{"error": "Unknown workflow for mock", "timestamp": "'$timestamp'", "provider": "mock"}'
            ;;
    esac
}

# Export workflow functions
# export -f process_vision
# export -f generate_questions
# export -f expand_question
# export -f extract_nodes
# export -f update_vision
# export -f pair_requirements_objectives
# export -f infer_actions
# export -f analyze_workpath
# export -f generate_workflow_mock

# Export original functions
# export -f generate_mock_response
# export -f call_anthropic
# export -f call_lm_studio

# If script is executed directly, show help
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    show_help
fi