#!/bin/bash

# LLM Workflow Executor for Know Tool
# Executes predefined workflows for graph manipulation

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source dependencies
source "$SCRIPT_DIR/llm.sh"

# Load workflow definitions
WORKFLOWS_FILE="$SCRIPT_DIR/llm-workflows.json"
PROVIDERS_FILE="$SCRIPT_DIR/llm-providers.json"

# Cache directory for responses
CACHE_DIR="${LLM_CACHE_DIR:-.ai/cache/llm}"
mkdir -p "$CACHE_DIR"

# Workflow: Vision Statement Processor
process_vision_statement() {
    local vision="$1"
    local context="${2:-{}}"

    # For mock provider, return structured test data
    if [ "${LLM_PROVIDER:-mock}" = "mock" ]; then
        cat <<EOF
{
  "project_name": "Test Project",
  "objectives": ["Enable collaboration", "Track dependencies", "Manage workflows"],
  "users": ["owner", "developer", "viewer"],
  "initial_features": ["dashboard", "editor", "analytics"],
  "requirements": ["web-based", "scalable", "secure"]
}
EOF
        return 0
    fi

    local prompt=$(cat <<EOF
Analyze this project vision and extract structured information:

Vision: $vision

Extract:
1. Project name
2. Primary objectives (3-5 high-level goals)
3. User types/roles
4. Initial feature ideas
5. Core requirements

Return as JSON with keys: project_name, objectives (array), users (array), initial_features (array), requirements (array)
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 2048 0.5)

    # Extract just the response content
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo "$response"
}

# Workflow: Question Generation
generate_questions() {
    local graph_context="$1"
    local focus_area="${2:-general}"
    local existing_questions="${3:-[]}"
    local count="${4:-5}"

    local prompt=$(cat <<EOF
Based on the current project graph:
$graph_context

Generate $count discovery questions focusing on: $focus_area

Avoid these existing questions:
$existing_questions

For each question provide:
- Unique ID (q001, q002, etc.)
- Question text
- Category (user/objective/feature/requirement/action)
- Priority (1-5, where 1 is highest)
- Expected entity types that might be discovered

Return as JSON array:
[
  {
    "id": "q001",
    "text": "What are the main user workflows?",
    "category": "action",
    "priority": 1,
    "expected_entities": ["action", "feature"]
  }
]
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 3000 0.7)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo "[]"
}

# Workflow: Node/Entity Extraction
extract_nodes() {
    local question="$1"
    local answer="$2"
    local graph_context="${3:-{}}"

    local prompt=$(cat <<EOF
Extract graph entities from this Q&A:

Question: $question
Answer: $answer

Current graph context:
$graph_context

Identify:
1. New entities (type, key, description)
2. References (reusable values)
3. Dependencies between entities

Follow naming conventions:
- Use granular keys (e.g., 'user-manager' not 'users')
- Don't reuse parent names
- Dependencies go in connections, not entity attributes

Return as JSON:
{
  "entities": [
    {
      "type": "feature",
      "key": "user-dashboard",
      "description": "Dashboard for user analytics",
      "confidence": 0.9
    }
  ],
  "references": [
    {
      "key": "dashboard_refresh_rate",
      "value": "30 seconds",
      "category": "config"
    }
  ],
  "connections": [
    {
      "from": "feature:user-dashboard",
      "to": "component:analytics-widget",
      "type": "depends_on"
    }
  ]
}
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 2048 0.3)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo '{"entities":[], "references":[], "connections":[]}'
}

# Workflow: Requirements-Objectives Pairing
pair_requirements_objectives() {
    local requirements="$1"
    local objectives="$2"
    local existing_mappings="${3:-{}}"

    local prompt=$(cat <<EOF
Map requirements to objectives:

Requirements:
$requirements

Objectives:
$objectives

Existing mappings to consider:
$existing_mappings

For each requirement:
1. Identify related objectives
2. Rate connection strength (0-1)
3. Identify gaps where requirements don't align with objectives

Return JSON:
{
  "mappings": [
    {
      "requirement": "real-time-sync",
      "objectives": ["enable-collaboration", "track-changes"],
      "strength": 0.8
    }
  ],
  "gaps": [
    {
      "type": "missing_objective",
      "description": "No objective for performance optimization",
      "suggested_entity": {
        "type": "objective",
        "key": "optimize-performance",
        "description": "Ensure system performs efficiently"
      }
    }
  ]
}
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 2048 0.4)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo '{"mappings":[], "gaps":[]}'
}

# Workflow: Action Inference
infer_actions() {
    local objectives="$1"
    local features="$2"
    local users="$3"

    local prompt=$(cat <<EOF
Infer user actions from objectives and features:

Users: $users
Objectives: $objectives
Features: $features

For each objective, identify concrete actions users would take.
Each action should:
- Have a specific key (verb-noun format, e.g., "create-report", "view-dashboard")
- Link to one user type
- Support one objective
- Use one or more features

Return JSON:
{
  "actions": [
    {
      "key": "review-analytics",
      "description": "Review system analytics and metrics",
      "user": "owner",
      "objective": "monitor-performance",
      "features_used": ["analytics-dashboard", "report-generator"]
    }
  ]
}
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 2048 0.6)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo '{"actions":[]}'
}

# Workflow: Workpath Completion
complete_workpath() {
    local partial_path="$1"
    local available_nodes="$2"
    local target_type="${3:-any}"

    local prompt=$(cat <<EOF
Complete this workflow path:

Partial path: $partial_path
Available nodes: $available_nodes
Target type: $target_type

Suggest:
1. Missing intermediate steps
2. Required connections
3. New nodes if needed

Return JSON:
{
  "completed_paths": [
    {
      "path": ["user:developer", "action:write-code", "feature:code-editor", "component:syntax-highlighter"],
      "confidence": 0.85,
      "missing_nodes": [
        {
          "type": "component",
          "key": "file-manager",
          "description": "Manages project files"
        }
      ]
    }
  ]
}
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 2048 0.5)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo '{"completed_paths":[]}'
}

# Workflow: Dependency Chain Builder
build_dependency_chain() {
    local feature="$1"
    local components="$2"
    local behaviors="$3"
    local data_models="$4"

    local prompt=$(cat <<EOF
Build dependency chain for feature:

Feature: $feature
Components: $components
Behaviors: $behaviors
Data Models: $data_models

Create dependency hierarchy following:
Feature → Component → (Behaviors + Presentation + Data Models)

Each level should have clear dependencies.

Return JSON:
{
  "chains": [
    {
      "feature": "user-dashboard",
      "dependencies": [
        {
          "type": "component",
          "key": "dashboard-layout",
          "level": 1
        },
        {
          "type": "behavior",
          "key": "refresh-data",
          "level": 2
        },
        {
          "type": "data_model",
          "key": "user-metrics",
          "level": 2
        }
      ]
    }
  ]
}
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 2048 0.3)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo '{"chains":[]}'
}

# Workflow: Graph Consistency Validator
validate_consistency() {
    local graph="$1"
    local rules="${2:-{}}"

    local prompt=$(cat <<EOF
Validate graph consistency:

Graph:
$graph

Validation rules:
$rules

Check for:
1. Circular dependencies
2. Orphaned nodes (entities with no connections)
3. Missing references
4. Naming convention violations (should use kebab-case, granular names)
5. Invalid entity types

Return JSON:
{
  "issues": [
    {
      "type": "circular_dependency",
      "severity": "error",
      "location": "feature:dashboard -> component:widget -> feature:dashboard",
      "description": "Circular dependency detected",
      "suggested_fix": {
        "action": "remove_connection",
        "from": "component:widget",
        "to": "feature:dashboard"
      }
    }
  ],
  "valid": false
}
EOF
    )

    local response=$(llm_query "$prompt" "${LLM_PROVIDER:-mock}" "${LLM_MODEL:-claude-3-haiku-20240307}" 3000 0.2)
    echo "$response" | jq -r '.response' | jq '.' 2>/dev/null || echo '{"issues":[], "valid":true}'
}

# Batch processor for QA sessions
batch_process_qa() {
    local session_file="$1"
    local workflow="${2:-node_extraction}"
    local output_file="${3:-qa_results.json}"

    # Read session data
    local session_data=$(cat "$session_file")
    local results='{"session_id":"'$(date +%s)'","results":[]}'

    # Process each Q&A pair
    echo "$session_data" | jq -c '.qa_pairs[]' | while read -r qa_pair; do
        local question=$(echo "$qa_pair" | jq -r '.question')
        local answer=$(echo "$qa_pair" | jq -r '.answer')

        case "$workflow" in
            node_extraction)
                local extraction=$(extract_nodes "$question" "$answer" "{}")
                results=$(echo "$results" | jq --argjson ext "$extraction" '.results += [$ext]')
                ;;
            *)
                echo "Unknown workflow: $workflow" >&2
                ;;
        esac
    done

    echo "$results" > "$output_file"
    echo "Results saved to: $output_file"
}

# Cache management
cache_response() {
    local key="$1"
    local response="$2"
    local cache_file="$CACHE_DIR/$(echo -n "$key" | sha256sum | cut -d' ' -f1).json"

    echo "$response" > "$cache_file"
    touch -d "+1 hour" "$cache_file"  # Set expiry
}

get_cached_response() {
    local key="$1"
    local cache_file="$CACHE_DIR/$(echo -n "$key" | sha256sum | cut -d' ' -f1).json"

    if [[ -f "$cache_file" ]] && [[ $(find "$cache_file" -mmin -60) ]]; then
        cat "$cache_file"
        return 0
    fi
    return 1
}

# Workflow chain executor
execute_workflow_chain() {
    local chain_name="$1"
    local input_data="$2"

    case "$chain_name" in
        discovery_session)
            # Execute discovery workflow chain
            local vision=$(echo "$input_data" | jq -r '.vision')
            local vision_result=$(process_vision_statement "$vision")

            local questions=$(generate_questions "$vision_result" "general" "[]" 10)

            echo '{"vision_analysis":'$vision_result',"questions":'$questions'}'
            ;;

        graph_completion)
            # Execute graph completion chain
            local graph=$(echo "$input_data" | jq -r '.graph')
            local validation=$(validate_consistency "$graph")

            echo "$validation"
            ;;

        *)
            echo '{"error":"Unknown workflow chain: '$chain_name'"}'
            ;;
    esac
}

# Help function
show_help() {
    cat <<EOF
LLM Workflow Executor for Know Tool

Usage: $0 <workflow> [arguments]

Workflows:
  vision <text>                     - Process vision statement
  questions <graph> [focus] [count] - Generate discovery questions
  extract <question> <answer>       - Extract entities from Q&A
  pair <requirements> <objectives>  - Pair requirements to objectives
  actions <objectives> <features> <users> - Infer user actions
  workpath <path> <nodes> [target]  - Complete workflow paths
  chain <feature> <components>      - Build dependency chains
  validate <graph>                  - Validate graph consistency
  batch <session_file> [workflow]   - Batch process QA session
  execute_chain <chain> <data>      - Execute workflow chain

Examples:
  $0 vision "Build a project management tool"
  $0 questions '{"entities":{}}' "features" 5
  $0 extract "What features?" "Dashboard and reporting"
  $0 validate graph.json

Environment:
  LLM_PROVIDER - Set provider (mock, anthropic, lm_studio)
  LLM_MODEL    - Set model to use
  LLM_CACHE_DIR - Cache directory (default: .ai/cache/llm)
EOF
}

# Main execution
case "${1:-help}" in
    vision)
        process_vision_statement "${2:-}"
        ;;
    questions)
        generate_questions "${2:-{}}" "${3:-general}" "${4:-[]}" "${5:-5}"
        ;;
    extract)
        extract_nodes "${2:-}" "${3:-}" "${4:-{}}"
        ;;
    pair)
        pair_requirements_objectives "${2:-[]}" "${3:-[]}" "${4:-{}}"
        ;;
    actions)
        infer_actions "${2:-[]}" "${3:-[]}" "${4:-[]}"
        ;;
    workpath)
        complete_workpath "${2:-[]}" "${3:-{}}" "${4:-any}"
        ;;
    chain)
        build_dependency_chain "${2:-}" "${3:-[]}" "${4:-[]}" "${5:-[]}"
        ;;
    validate)
        validate_consistency "${2:-{}}" "${3:-{}}"
        ;;
    batch)
        batch_process_qa "${2:-}" "${3:-node_extraction}" "${4:-qa_results.json}"
        ;;
    execute_chain)
        execute_workflow_chain "${2:-}" "${3:-{}}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac