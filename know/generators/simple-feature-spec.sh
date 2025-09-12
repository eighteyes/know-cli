#!/bin/bash

# simple-feature-spec.sh - Simple working feature specification generator

set -euo pipefail

generate_simple_feature_spec() {
    local entity_ref="$1"
    local format="${2:-md}"
    
    # Parse entity reference
    local entity_type=$(echo "$entity_ref" | cut -d':' -f1)
    local entity_id=$(echo "$entity_ref" | cut -d':' -f2)
    
    # Convert to plural for JSON paths
    local entity_type_plural="${entity_type}s"
    
    # Get entity name and basic info
    local entity_name
    entity_name=$(jq -r --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].name // $id' "$KNOWLEDGE_MAP")
    
    local entity_description
    entity_description=$(jq -r --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].description // "No description available"' "$KNOWLEDGE_MAP")
    
    # Get completeness score
    local completeness_score
    completeness_score=$(get_completeness_score "$entity_ref")
    
    echo "# Feature Specification: $entity_name"
    echo ""
    echo "**Entity Reference:** \`$entity_ref\`"
    echo "**Completeness Score:** $completeness_score%"
    echo "**Generated:** $(date)"
    echo ""
    
    echo "## Overview"
    if [[ "$entity_description" == "No description available" ]]; then
        echo "❌ **INVALID SPECIFICATION - NO DESCRIPTION**"
        echo ""
        echo "This feature cannot be implemented without a clear description of what it does."
        echo ""
        echo "**Required:** Add a comprehensive description explaining:"
        echo "- What problem this feature solves"
        echo "- Who will use it and how"
        echo "- Key functionality and user workflows"
        echo "- Success criteria and expected outcomes"
        echo ""
        echo "**How to fix:** \`./scripts/mod-graph.sh edit $entity_type_plural $entity_id\`"
        echo ""
        return 1
    else
        echo "$entity_description"
    fi
    echo ""
    
    echo "## Implementation Status"
    if [[ $completeness_score -ge 70 ]]; then
        echo "✅ **READY FOR IMPLEMENTATION** ($completeness_score% complete)"
    elif [[ $completeness_score -ge 50 ]]; then
        echo "🟡 **NEEDS MORE WORK** ($completeness_score% complete - requires 70%+ for implementation)"
    else
        echo "🔴 **INCOMPLETE** ($completeness_score% complete - significant work required)"
    fi
    echo ""
    
    echo "## Dependencies"
    # Get dependencies using our working script
    if "$JSON_GRAPH_QUERY" deps "$entity_ref" >/dev/null 2>&1; then
        echo "This feature depends on the following entities:"
        echo ""
        "$JSON_GRAPH_QUERY" deps "$entity_ref" | head -20 | while read -r line; do
            if [[ "$line" =~ ^[[:space:]]*📋[[:space:]](.+)[[:space:]]\((.+):[[:space:]](.+)\)$ ]]; then
                echo "- **${BASH_REMATCH[1]}** (${BASH_REMATCH[2]}): ${BASH_REMATCH[3]}"
            elif [[ "$line" =~ ^[[:space:]]*🎯[[:space:]](.+)[[:space:]]\((.+):[[:space:]](.+)\).*\[ROOT\]$ ]]; then
                echo "- **ROOT**: ${BASH_REMATCH[1]} (${BASH_REMATCH[2]}): ${BASH_REMATCH[3]}"
            fi
        done
    else
        echo "*No dependencies found or dependency analysis failed*"
    fi
    echo ""
    
    echo "## Acceptance Criteria"
    # Check for acceptance criteria in the knowledge map
    local has_criteria=false
    
    if jq -e --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].acceptance_criteria' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        has_criteria=true
        echo "### Defined Criteria:"
        echo ""
        
        # Extract different types of criteria
        for criteria_type in "functional" "performance" "security" "reliability" "integration" "validation"; do
            local criteria_items
            criteria_items=$(jq -r --arg type "${entity_type}s" --arg id "$entity_id" --arg ctype "$criteria_type" '.entities[$type][$id].acceptance_criteria[$ctype][]? // empty' "$KNOWLEDGE_MAP" 2>/dev/null)
            
            if [[ -n "$criteria_items" ]]; then
                echo "#### ${criteria_type^} Requirements"
                while IFS= read -r criterion; do
                    if [[ -n "$criterion" ]]; then
                        echo "- [ ] $criterion"
                    fi
                done <<< "$criteria_items"
                echo ""
            fi
        done
    fi
    
    if [[ "$has_criteria" == "false" ]]; then
        echo "⚠️ **No acceptance criteria defined**"
        echo ""
        echo "To improve this specification, add acceptance criteria using:"
        echo "\`\`\`bash"
        echo "# Add functional criteria"
        echo "./know/know add-criteria $entity_ref functional \"Must handle X concurrent users\""
        echo ""
        echo "# Add performance criteria"
        echo "./know/know add-criteria $entity_ref performance \"Response time < 200ms\""
        echo "\`\`\`"
        echo ""
    fi
    
    echo "## Technical Architecture"
    if jq -e '.references.technical_architecture' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        echo "### Infrastructure Components"
        echo ""
        
        # Parse each architecture component properly
        local components=(api_gateway message_broker database cache_layer)
        
        for component in "${components[@]}"; do
            local component_data
            component_data=$(jq -r --arg comp "$component" '.references.technical_architecture[$comp] // empty' "$KNOWLEDGE_MAP" 2>/dev/null)
            
            if [[ -n "$component_data" && "$component_data" != "null" ]]; then
                # Extract human-readable information
                local tech=$(echo "$component_data" | jq -r '.technology // "Not specified"')
                local version=$(echo "$component_data" | jq -r '.version // empty')
                local base_url=$(echo "$component_data" | jq -r '.base_url // empty')
                local description=$(echo "$component_data" | jq -r '.description // empty')
                
                case "$component" in
                    "api_gateway")
                        echo "**API Gateway**: $tech"
                        [[ -n "$base_url" ]] && echo "  - Base URL: $base_url"
                        echo "  - Handles authentication, rate limiting, and routing"
                        ;;
                    "message_broker")
                        echo "**Message Broker**: $tech"
                        [[ -n "$version" ]] && echo "  - Version: $version"
                        echo "  - Handles asynchronous communication between services"
                        ;;
                    "database") 
                        echo "**Primary Database**: $tech"
                        [[ -n "$version" ]] && echo "  - Version: $version"
                        echo "  - Persistent data storage and transactions"
                        ;;
                    "cache_layer")
                        echo "**Caching Layer**: $tech"
                        [[ -n "$version" ]] && echo "  - Version: $version"
                        echo "  - High-performance in-memory data store"
                        ;;
                esac
                echo ""
            fi
        done
        
        echo "### Development Stack"
        echo "Based on the technical architecture, this feature will integrate with:"
        echo "- RESTful APIs through the API Gateway"
        echo "- Event-driven messaging for real-time updates"
        echo "- Relational database for data persistence"
        echo "- Redis caching for performance optimization"
        echo ""
        
    else
        echo "❌ **MISSING TECHNICAL ARCHITECTURE**"
        echo ""
        echo "Cannot implement without knowing:"
        echo "- Technology stack and frameworks"
        echo "- Database and data models"
        echo "- API endpoints and authentication"
        echo "- Integration patterns and protocols"
        echo ""
        echo "**How to fix:** Define architecture in \`.references.technical_architecture\`"
        echo ""
    fi
    
    echo "## Next Steps"
    if [[ $completeness_score -lt 70 ]]; then
        echo "**Before Implementation:**"
        echo "1. Run \`./know/know gaps $entity_ref\` to see specific missing items"
        echo "2. Run \`./know/know validate $entity_ref --comprehensive\` for detailed analysis"
        echo "3. Use \`./know/know complete $entity_ref\` for interactive gap filling"
        echo ""
        echo "**Target:** Achieve 70%+ completeness score"
    else
        echo "**Ready for Implementation:**"
        echo "1. This feature meets the minimum completeness threshold (70%+)"
        echo "2. Proceed with detailed technical design"
        echo "3. Begin implementation following the acceptance criteria"
        echo "4. Consider running integration tests with dependent systems"
    fi
    echo ""
    
    # Comprehensive Missing Information Analysis for Developers
    echo "## What's Missing for Implementation"
    echo ""
    local missing_count=0
    local missing_items=()
    local critical_missing=()
    local nice_to_have_missing=()
    
    # CRITICAL - Cannot implement without these
    if [[ "$entity_description" == "No description available" ]]; then
        critical_missing+=("🚫 **Feature Description**: What does this feature actually do?")
        critical_missing+=("   - Business value and user impact")
        critical_missing+=("   - Core functionality and user workflows")
        critical_missing+=("   - Success criteria and measurable outcomes")
        ((missing_count++))
    fi
    
    # Check for missing acceptance criteria
    local has_functional=false
    local has_performance=false
    local has_integration=false
    
    if jq -e --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].acceptance_criteria.functional' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        has_functional=true
    fi
    if jq -e --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].acceptance_criteria.performance' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        has_performance=true
    fi
    if jq -e --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].acceptance_criteria.integration' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        has_integration=true
    fi
    
    if [[ "$has_functional" == "false" ]]; then
        critical_missing+=("🚫 **Functional Requirements**: How should this feature behave?")
        critical_missing+=("   - User stories and use cases")
        critical_missing+=("   - Input/output specifications")
        critical_missing+=("   - Business rules and validation logic")
        ((missing_count++))
    fi
    
    if [[ "$has_performance" == "false" ]]; then
        critical_missing+=("🚫 **Performance Requirements**: How fast/scalable must it be?")
        critical_missing+=("   - Response time expectations")
        critical_missing+=("   - Throughput and concurrent user limits")
        critical_missing+=("   - Resource consumption constraints")
        ((missing_count++))
    fi
    
    # Check for API specifications
    if ! jq -e '.references.endpoints' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        critical_missing+=("🚫 **API Specification**: How do other systems interact with this?")
        critical_missing+=("   - HTTP endpoints and methods")
        critical_missing+=("   - Request/response data formats")
        critical_missing+=("   - Authentication and authorization")
        ((missing_count++))
    fi
    
    # Check for data models
    local has_data_models=false
    if "$JSON_GRAPH_QUERY" deps "$entity_ref" 2>/dev/null | grep -q "model:" ; then
        has_data_models=true
    fi
    
    if [[ "$has_data_models" == "false" ]]; then
        critical_missing+=("🚫 **Data Models**: What data does this feature work with?")
        critical_missing+=("   - Database schema and relationships")
        critical_missing+=("   - Data validation rules") 
        critical_missing+=("   - Migration and seeding strategies")
        ((missing_count++))
    fi
    
    # NICE TO HAVE - Would improve implementation but not blocking
    if [[ "$has_integration" == "false" ]]; then
        nice_to_have_missing+=("⚠️ **Integration Testing**: How to verify it works with other systems")
        nice_to_have_missing+=("   - Test scenarios with dependent services")
        nice_to_have_missing+=("   - Mocking and stubbing strategies")
    fi
    
    local has_security=false
    if jq -e --arg type "${entity_type}s" --arg id "$entity_id" '.entities[$type][$id].acceptance_criteria.security' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        has_security=true
    fi
    
    if [[ "$has_security" == "false" ]]; then
        nice_to_have_missing+=("⚠️ **Security Requirements**: Authentication, authorization, data protection")
        nice_to_have_missing+=("   - User permission models")
        nice_to_have_missing+=("   - Data encryption and compliance needs")
    fi
    
    # Check for user access patterns
    if [[ "$entity_type" == "feature" ]]; then
        local user_count
        user_count=$("$JSON_GRAPH_QUERY" impact "$entity_ref" 2>/dev/null | grep -c "user:" 2>/dev/null | head -1 || echo "0")
        # Clean up user_count to ensure it's numeric
        user_count=$(echo "$user_count" | tr -d '\n' | grep -o '^[0-9]*' | head -1)
        [[ -z "$user_count" ]] && user_count=0
        if [[ $user_count -eq 0 ]]; then
            nice_to_have_missing+=("⚠️ **User Personas**: Which user types will use this feature")
            nice_to_have_missing+=("   - User roles and permissions")
            nice_to_have_missing+=("   - Usage patterns and workflows")
        fi
    fi
    
    # Display results in developer-friendly format
    if [[ ${#critical_missing[@]} -eq 0 && ${#nice_to_have_missing[@]} -eq 0 ]]; then
        echo "✅ **IMPLEMENTATION READY**"
        echo ""
        echo "All critical information is present. Developers can proceed with implementation."
        echo ""
    else
        if [[ ${#critical_missing[@]} -gt 0 ]]; then
            echo "🚫 **CANNOT IMPLEMENT - CRITICAL INFORMATION MISSING**"
            echo ""
            echo "The following information is **required** before any developer can start:"
            echo ""
            for item in "${critical_missing[@]}"; do
                echo "$item"
            done
            echo ""
        fi
        
        if [[ ${#nice_to_have_missing[@]} -gt 0 ]]; then
            echo "⚠️ **IMPLEMENTATION RISKS - MISSING DETAILS**"
            echo ""
            echo "These details would improve implementation quality and reduce risks:"
            echo ""
            for item in "${nice_to_have_missing[@]}"; do
                echo "$item"
            done
            echo ""
        fi
        
        echo "### How to Fix This Specification"
        echo ""
        echo "**Priority 1 - Critical (Blocking)**"
        echo "\`\`\`bash"
        echo "# Add feature description"
        echo "# Edit: .entities.$entity_type_plural.$entity_id.description"
        echo "./scripts/mod-graph.sh edit $entity_type_plural $entity_id"
        echo ""
        echo "# Add functional requirements"
        echo "# Edit: .entities.$entity_type_plural.$entity_id.acceptance_criteria.functional"
        echo ""
        echo "# Add performance requirements"
        echo "# Edit: .entities.$entity_type_plural.$entity_id.acceptance_criteria.performance"
        echo ""
        echo "# Define API endpoints"
        echo "# Edit: .references.endpoints"
        echo "\`\`\`"
        echo ""
        echo "**Priority 2 - Quality Improvements**"
        echo "\`\`\`bash"
        echo "# Add integration and security requirements"
        echo "# Connect to user personas and data models"
        echo "./scripts/mod-graph.sh connect $entity_ref user:<user-type>"
        echo "./scripts/mod-graph.sh connect $entity_ref model:<data-model>"
        echo "\`\`\`"
    fi
    
    echo ""
    echo "---"
    echo "*Generated by know CLI - $(date)*"
    echo "*Completeness Score: $completeness_score% | Missing Elements: $missing_count*"
}

# Main entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Load necessary functions
    export MOD_GRAPH="${MOD_GRAPH:-./scripts/mod-graph.sh}"
    export KNOWLEDGE_MAP="${KNOWLEDGE_MAP:-./knowledge-map-cmd.json}"
    export JSON_GRAPH_QUERY="${JSON_GRAPH_QUERY:-./scripts/json-graph-query.sh}"
    
    # Source validation functions for completeness scoring
    source "${LIB_DIR:-./know/lib}/validation-comprehensive.sh"
    
    generate_simple_feature_spec "$@"
fi