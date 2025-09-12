#!/bin/bash

# simple-screen-spec.sh - Human-readable screen specification generator

set -euo pipefail

generate_simple_screen_spec() {
    local entity_ref="$1"
    local format="${2:-md}"
    
    # Parse entity reference
    local entity_type=$(echo "$entity_ref" | cut -d':' -f1)
    local entity_id=$(echo "$entity_ref" | cut -d':' -f2)
    
    # Convert to plural for JSON paths
    local entity_type_plural="${entity_type}s"
    
    # Get entity name and basic info
    local entity_name
    entity_name=$(jq -r --arg type "$entity_type_plural" --arg id "$entity_id" '.entities[$type][$id].name // $id' "$KNOWLEDGE_MAP")
    
    local entity_description
    entity_description=$(jq -r --arg type "$entity_type_plural" --arg id "$entity_id" '.entities[$type][$id].description // "No description available"' "$KNOWLEDGE_MAP")
    
    # Get completeness score
    local completeness_score
    completeness_score=$(get_completeness_score "$entity_ref")
    
    echo "# Screen Specification: $entity_name"
    echo ""
    echo "**Entity Reference:** \`$entity_ref\`"
    echo "**Completeness Score:** $completeness_score%"
    echo "**Generated:** $(date)"
    echo ""
    
    echo "## Screen Purpose"
    if [[ "$entity_description" == "No description available" ]]; then
        echo "❌ **INVALID SPECIFICATION - NO DESCRIPTION**"
        echo ""
        echo "Cannot design a screen without knowing what it's supposed to do."
        echo ""
        echo "**Required:** Add description explaining the screen's purpose and user goals"
        echo ""
        return 1
    else
        echo "$entity_description"
    fi
    echo ""
    
    echo "## User Interface Layout"
    echo ""
    
    # Get components that belong to this screen
    local screen_components=()
    if "$JSON_GRAPH_QUERY" deps "$entity_ref" >/dev/null 2>&1; then
        echo "### UI Components on this Screen"
        echo ""
        "$JSON_GRAPH_QUERY" deps "$entity_ref" | while read -r line; do
            if [[ "$line" =~ component:([^[:space:]]+) ]]; then
                local component_id="${BASH_REMATCH[1]}"
                local component_name=$(jq -r --arg id "$component_id" '.entities.components[$id].name // $id' "$KNOWLEDGE_MAP")
                local component_desc=$(jq -r --arg id "$component_id" '.entities.components[$id].description // ""' "$KNOWLEDGE_MAP")
                
                echo "**$component_name** (\`component:$component_id\`)"
                [[ -n "$component_desc" && "$component_desc" != "null" ]] && echo "  - $component_desc"
                
                # Get component functionality if available
                local functionality
                functionality=$(jq -r --arg id "$component_id" '.entities.components[$id].functionality[]? // empty' "$KNOWLEDGE_MAP" 2>/dev/null)
                if [[ -n "$functionality" ]]; then
                    echo "  - **Functions:**"
                    while IFS= read -r func; do
                        [[ -n "$func" ]] && echo "    • $func"
                    done <<< "$functionality"
                fi
                echo ""
            fi
        done
    else
        echo "⚠️ **No UI components defined for this screen**"
        echo ""
        echo "This screen needs components to display data and handle user interactions."
        echo ""
    fi
    
    echo "### Data Displayed"
    echo ""
    
    # Find data models connected to this screen
    local has_data_models=false
    if "$JSON_GRAPH_QUERY" deps "$entity_ref" 2>/dev/null | grep -q "model:" ; then
        echo "This screen displays data from the following models:"
        echo ""
        "$JSON_GRAPH_QUERY" deps "$entity_ref" | while read -r line; do
            if [[ "$line" =~ model:([^[:space:]]+) ]]; then
                local model_id="${BASH_REMATCH[1]}"
                local model_name=$(jq -r --arg id "$model_id" '.entities.models[$id].name // $id' "$KNOWLEDGE_MAP")
                local model_desc=$(jq -r --arg id "$model_id" '.entities.models[$id].description // ""' "$KNOWLEDGE_MAP")
                
                echo "**$model_name** (\`model:$model_id\`)"
                [[ -n "$model_desc" && "$model_desc" != "null" ]] && echo "  - Purpose: $model_desc"
                
                # Get model fields/schema if available
                local schema_fields
                schema_fields=$(jq -r --arg id "$model_id" '.entities.models[$id].schema.fields | keys[]? // empty' "$KNOWLEDGE_MAP" 2>/dev/null)
                if [[ -n "$schema_fields" ]]; then
                    echo "  - **Data Fields:**"
                    while IFS= read -r field; do
                        [[ -n "$field" ]] && echo "    • $field"
                    done <<< "$schema_fields"
                fi
                echo ""
                has_data_models=true
            fi
        done
    fi
    
    if [[ "$has_data_models" == "false" ]]; then
        echo "❌ **No data models connected**"
        echo ""
        echo "This screen needs to be connected to data models that define:"
        echo "- What information is displayed to users"
        echo "- Data structure and field definitions"
        echo "- Real-time vs static data requirements"
        echo ""
    fi
    
    echo "### User Actions Available"
    echo ""
    
    # Check for user interactions/functionality
    local screen_functionality
    screen_functionality=$(jq -r --arg type "$entity_type_plural" --arg id "$entity_id" '.entities[$type][$id].functionality[]? // empty' "$KNOWLEDGE_MAP" 2>/dev/null)
    
    if [[ -n "$screen_functionality" ]]; then
        echo "Users can perform these actions on this screen:"
        echo ""
        while IFS= read -r action; do
            [[ -n "$action" ]] && echo "- $action"
        done <<< "$screen_functionality"
        echo ""
    else
        echo "⚠️ **No user actions defined**"
        echo ""
        echo "Consider defining what users can do on this screen:"
        echo "- Navigation and workflow actions"
        echo "- Data input and form interactions"
        echo "- Export, filter, or search capabilities"
        echo ""
    fi
    
    echo "### Target Users"
    echo ""
    
    # Find users who can access this screen
    local user_count
    user_count=$("$JSON_GRAPH_QUERY" impact "$entity_ref" 2>/dev/null | grep -c "user:" 2>/dev/null | head -1 || echo "0")
    # Clean up user_count to ensure it's numeric
    user_count=$(echo "$user_count" | tr -d '\n' | grep -o '^[0-9]*' | head -1)
    [[ -z "$user_count" ]] && user_count=0
    
    if [[ $user_count -gt 0 ]]; then
        echo "This screen is designed for:"
        echo ""
        "$JSON_GRAPH_QUERY" impact "$entity_ref" | while read -r line; do
            if [[ "$line" =~ user:([^[:space:]]+) ]]; then
                local user_id="${BASH_REMATCH[1]}"
                local user_name=$(jq -r --arg id "$user_id" '.entities.users[$id].name // $id' "$KNOWLEDGE_MAP")
                local user_desc=$(jq -r --arg id "$user_id" '.entities.users[$id].description // ""' "$KNOWLEDGE_MAP")
                
                echo "**$user_name** (\`user:$user_id\`)"
                [[ -n "$user_desc" && "$user_desc" != "null" ]] && echo "  - Role: $user_desc"
                echo ""
            fi
        done
    else
        echo "❌ **No target users defined**"
        echo ""
        echo "This screen needs to specify which user types will access it."
        echo ""
    fi
    
    echo "## Technical Implementation"
    echo ""
    
    echo "### UI Framework Requirements"
    if jq -e '.references.technical_architecture' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        echo "Based on the system architecture:"
        echo ""
        echo "- **Frontend Framework**: React with TypeScript (inferred from system)"
        echo "- **State Management**: Redux/Context for data flow"
        echo "- **Styling**: CSS-in-JS or styled-components"
        echo "- **Real-time Updates**: WebSocket connections for live data"
        echo ""
    else
        echo "⚠️ **No frontend architecture defined**"
        echo ""
        echo "Define UI framework and styling approach in technical architecture."
        echo ""
    fi
    
    echo "### API Integration"
    # Check for API endpoints
    if jq -e '.references.endpoints' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        echo "This screen will integrate with defined API endpoints."
        echo ""
        echo "See system API documentation for specific endpoints."
        echo ""
    else
        echo "⚠️ **No API endpoints defined**"
        echo ""
        echo "Screen needs API endpoints for:"
        echo "- Loading initial data"
        echo "- Real-time data updates"
        echo "- User action handling (CRUD operations)"
        echo ""
    fi
    
    echo "## Implementation Readiness"
    echo ""
    
    # Count missing critical elements
    local critical_missing=()
    local implementation_blockers=0
    
    [[ "$entity_description" == "No description available" ]] && critical_missing+=("Screen purpose and user goals") && ((implementation_blockers++))
    [[ $user_count -eq 0 ]] && critical_missing+=("Target user personas") && ((implementation_blockers++))
    [[ "$has_data_models" == "false" ]] && critical_missing+=("Data models and schema") && ((implementation_blockers++))
    [[ -z "$screen_functionality" ]] && critical_missing+=("User interaction flows") && ((implementation_blockers++))
    
    if [[ $implementation_blockers -eq 0 ]]; then
        echo "✅ **READY FOR UI DEVELOPMENT**"
        echo ""
        echo "All critical information is present. Frontend developers can:"
        echo "1. Design wireframes and mockups"
        echo "2. Implement UI components"
        echo "3. Connect to data sources"
        echo "4. Add user interaction handlers"
    else
        echo "🚫 **CANNOT IMPLEMENT - MISSING CRITICAL INFO**"
        echo ""
        echo "UI developers need these details before starting:"
        echo ""
        for missing in "${critical_missing[@]}"; do
            echo "- **$missing**"
        done
        echo ""
        echo "**How to fix:** Use \`./scripts/mod-graph.sh edit $entity_type_plural $entity_id\` to add missing information."
    fi
    
    echo ""
    echo "---"
    echo "*Generated by know CLI - $(date)*"
    echo "*Screen Readiness: $((4 - implementation_blockers))/4 critical elements complete*"
}

# Main entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Load necessary functions
    export MOD_GRAPH="${MOD_GRAPH:-./scripts/mod-graph.sh}"
    export KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-./knowledge-map-cmd.json}"
    export JSON_GRAPH_QUERY="${JSON_GRAPH_QUERY:-./scripts/json-graph-query.sh}"
    
    # Source validation functions for completeness scoring
    source "${LIB_DIR:-./know/lib}/validation-comprehensive.sh"
    
    generate_simple_screen_spec "$@"
fi