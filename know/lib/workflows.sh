#!/bin/bash

# workflows.sh - Interactive workflow commands for PM/Dev productivity

# Interactive feature creation workflow
create_feature_interactive() {
    echo "🎯 Interactive Feature Creation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    
    # Get feature name
    read -p "🏷️  Feature name: " feature_name
    [[ -z "$feature_name" ]] && { error "Feature name is required"; return 1; }
    
    # Generate ID from name
    local feature_id=$(echo "$feature_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
    
    echo "📋 Generated ID: $feature_id"
    read -p "   Use this ID? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -p "📝 Enter custom ID: " feature_id
    fi
    
    # Check if exists
    if "$MOD_GRAPH" show features "$feature_id" >/dev/null 2>&1; then
        error "Feature already exists: $feature_id"
        return 1
    fi
    
    # Get description
    echo
    echo "📄 Feature Description:"
    read -p "   Enter description: " description
    
    # Create the feature entity
    echo
    info "Creating feature entity..."
    if "$MOD_GRAPH" add features "$feature_id" "$feature_name" >/dev/null 2>&1; then
        success "✅ Created feature: features:$feature_id"
    else
        error "Failed to create feature"
        return 1
    fi
    
    # Add description reference if provided
    if [[ -n "$description" ]]; then
        # TODO: Add description to references section
        info "Description noted (will be added to references)"
    fi
    
    echo
    echo "📋 Now let's define acceptance criteria..."
    
    # Add acceptance criteria interactively
    local criteria_types=("functional" "performance" "security" "reliability" "integration")
    
    for ctype in "${criteria_types[@]}"; do
        echo
        echo "🔍 $ctype requirements:"
        local criteria=()
        while true; do
            read -p "   Add $ctype requirement (empty to finish): " requirement
            if [[ -z "$requirement" ]]; then
                break
            fi
            criteria+=("$requirement")
            echo "     ✅ Added: $requirement"
        done
        
        if [[ ${#criteria[@]} -gt 0 ]]; then
            info "Added ${#criteria[@]} $ctype criteria"
            # TODO: Add criteria to knowledge map
        fi
    done
    
    echo
    echo "🔗 Define dependencies..."
    echo "   What does this feature depend on?"
    
    # Show available entities for connection
    echo
    echo "Available platforms:"
    "$MOD_GRAPH" list platforms | head -5
    echo
    echo "Available components:"
    "$MOD_GRAPH" list components | head -5
    
    echo
    local dependencies=()
    while true; do
        echo "💡 Tip: Use format like 'platform:aws-infrastructure' or 'component:fleet-status-map'"
        read -p "   Add dependency (empty to finish): " dependency
        if [[ -z "$dependency" ]]; then
            break
        fi
        
        # Validate dependency exists
        local dep_type=$(echo "$dependency" | cut -d':' -f1)
        local dep_id=$(echo "$dependency" | cut -d':' -f2)
        
        case "$dep_type" in
            platform) dep_type="platforms" ;;
            component) dep_type="components" ;;
            screen) dep_type="screens" ;;
        esac
        
        if "$MOD_GRAPH" show "$dep_type" "$dep_id" >/dev/null 2>&1; then
            dependencies+=("$dependency")
            echo "     ✅ Valid dependency: $dependency"
        else
            echo "     ❌ Invalid dependency: $dependency (entity not found)"
        fi
    done
    
    # Connect dependencies
    for dep in "${dependencies[@]}"; do
        if "$MOD_GRAPH" connect "feature:$feature_id" "$dep" >/dev/null 2>&1; then
            success "🔗 Connected: feature:$feature_id → $dep"
        fi
    done
    
    echo
    echo "✅ Feature Creation Complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show completeness
    local completeness
    completeness=$(get_completeness_score "feature:$feature_id")
    echo "📊 Initial completeness: $completeness%"
    
    if [[ $completeness -lt 70 ]]; then
        echo "🔧 Next steps to improve completeness:"
        echo "  • know gaps feature:$feature_id"
        echo "  • know complete feature:$feature_id"
    else
        echo "🎉 Ready for specification generation!"
        echo "  • know spec feature:$feature_id"
    fi
    
    echo
    echo "💡 Feature created: feature:$feature_id"
}

# Interactive gap completion workflow  
complete_entity_interactive() {
    local entity_ref="$1"
    
    echo "🔧 Interactive Gap Completion: $entity_ref"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Get current completeness
    local current_score
    current_score=$(get_completeness_score "$entity_ref")
    echo "📊 Current completeness: $current_score%"
    
    if [[ $current_score -ge 70 ]]; then
        echo "✅ Entity already meets minimum completeness threshold!"
        return 0
    fi
    
    echo "🎯 Target: 70% (need $(( 70 - current_score ))% more)"
    echo
    
    # Run comprehensive validation to get specific gaps
    echo "🔍 Analyzing gaps..."
    local validation_output
    validation_output=$(validate_entity_comprehensive "$entity_ref" 70 2>/dev/null)
    
    # Extract gaps and recommendations
    local gaps
    gaps=$(echo "$validation_output" | sed -n '/IDENTIFIED GAPS/,/RECOMMENDED ACTIONS/p' | grep "^  [0-9]" || echo "")
    
    local recommendations  
    recommendations=$(echo "$validation_output" | sed -n '/RECOMMENDED ACTIONS/,/$/p' | grep "^  [0-9]" || echo "")
    
    if [[ -n "$gaps" ]]; then
        echo "📋 Found gaps to address:"
        echo "$gaps"
        echo
        
        echo "💡 Recommended actions:"
        echo "$recommendations"
        echo
        
        read -p "Would you like to address these gaps interactively? (Y/n): " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo "🚀 Let's fix the gaps..."
            echo
            echo "💡 For now, please run the recommended commands manually."
            echo "   Future versions will provide full interactive gap filling."
            echo
            echo "📋 Quick reference:"
            echo "$recommendations"
        fi
    else
        echo "🤔 No specific gaps identified. Entity may need manual review."
    fi
    
    echo
    echo "🔄 After making changes, re-run: know completeness-check $entity_ref"
}

# Create implementation chain for complex features
create_implementation_chain() {
    local feature_ref="$1"
    
    echo "🔗 Building Implementation Chain: $feature_ref"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local feature_type=$(echo "$feature_ref" | cut -d':' -f1)
    local feature_id=$(echo "$feature_ref" | cut -d':' -f2)
    
    # Check if feature exists
    case "$feature_type" in
        feature) feature_type="features" ;;
    esac
    
    if ! "$MOD_GRAPH" show "$feature_type" "$feature_id" >/dev/null 2>&1; then
        error "Feature not found: $feature_ref"
        return 1
    fi
    
    echo "🎯 This feature will likely need:"
    echo
    
    # Suggest requirements
    echo "📋 Requirements:"
    echo "  • Security requirements (authentication, authorization)"
    echo "  • Performance requirements (latency, throughput)" 
    echo "  • Reliability requirements (uptime, error handling)"
    read -p "Create requirement entities? (Y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        local req_types=("security" "performance" "reliability")
        for req_type in "${req_types[@]}"; do
            local req_id="${feature_id}-${req_type}"
            echo "  Creating requirement: $req_id"
            if "$MOD_GRAPH" add requirements "$req_id" "${req_type^} Requirements for ${feature_id}" >/dev/null 2>&1; then
                "$MOD_GRAPH" connect "$feature_ref" "requirement:$req_id" >/dev/null 2>&1
                success "✅ Created and connected: requirement:$req_id"
            fi
        done
    fi
    
    echo
    echo "🧩 Components:"
    echo "  • UI components for user interface"
    echo "  • Service components for business logic"
    echo "  • Data access components"
    read -p "Create component entities? (Y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        local comp_types=("ui" "service" "data")
        for comp_type in "${comp_types[@]}"; do
            local comp_id="${feature_id}-${comp_type}"
            echo "  Creating component: $comp_id"
            if "$MOD_GRAPH" add components "$comp_id" "${comp_type^} Component for ${feature_id}" >/dev/null 2>&1; then
                "$MOD_GRAPH" connect "$feature_ref" "component:$comp_id" >/dev/null 2>&1
                success "✅ Created and connected: component:$comp_id"
            fi
        done
    fi
    
    echo
    echo "💾 Data Models:"
    echo "  • Data schemas for persistence"
    echo "  • API models for communication"
    read -p "Create schema entities? (Y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        local schema_types=("data" "api")
        for schema_type in "${schema_types[@]}"; do
            local schema_id="${feature_id}-${schema_type}-model"
            echo "  Creating schema: $schema_id"
            if "$MOD_GRAPH" add schema "$schema_id" "${schema_type^} Model for ${feature_id}" >/dev/null 2>&1; then
                "$MOD_GRAPH" connect "$feature_ref" "schema:$schema_id" >/dev/null 2>&1
                success "✅ Created and connected: schema:$schema_id"
            fi
        done
    fi
    
    echo
    echo "✅ Implementation Chain Created!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show updated completeness
    local new_completeness
    new_completeness=$(get_completeness_score "$feature_ref")
    echo "📊 Updated completeness: $new_completeness%"
    
    echo
    echo "🔍 Next steps:"
    echo "  • know deps $feature_ref (see full dependency chain)"
    echo "  • know gaps $feature_ref (identify remaining gaps)"
    echo "  • Fill in detailed acceptance criteria for each entity"
}

# Show implementation priorities based on dependencies
show_implementation_priorities() {
    local format="${1:-text}"
    
    if [[ "$format" == "json" ]]; then
        show_implementation_priorities_json
        return
    fi
    
    echo "🎯 Implementation Priorities"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    
    echo "🟢 Ready to Implement (70%+ complete):"
    for entity_type in features components screens; do
        analyze_completeness_batch "$entity_type" | grep "🟢.*Ready" | head -3
    done
    
    echo
    echo "🟡 Needs Work (50-69% complete):"  
    for entity_type in features components screens; do
        analyze_completeness_batch "$entity_type" | grep "🟡.*work" | head -3
    done
    
    echo
    echo "🔴 High Priority Blockers (<50% complete):"
    for entity_type in features components screens; do
        analyze_completeness_batch "$entity_type" | grep "🔴.*Incomplete" | head -3
    done
    
    echo
    echo "💡 Recommended Implementation Order:"
    echo "   1. Fix blockers first (🔴 entities)"
    echo "   2. Complete entities needing work (🟡 entities)" 
    echo "   3. Implement ready entities (🟢 entities)"
    echo "   4. Use: know deps <entity> to check prerequisites"
}

# JSON version of implementation priorities
show_implementation_priorities_json() {
    local ready_entities=()
    local needs_work_entities=()
    local blocked_entities=()
    
    # Collect entities by priority level
    for entity_type in features components screens; do
        local entities
        entities=$("$MOD_GRAPH" list "$entity_type" | grep "  " | cut -d' ' -f3 | cut -d'-' -f1 | head -5)
        
        while IFS= read -r entity_id; do
            [[ -z "$entity_id" ]] && continue
            
            local score
            score=$(get_completeness_score "${entity_type%s}:$entity_id")
            
            local priority_data
            priority_data=$(jq -n \
                --arg id "$entity_id" \
                --arg type "${entity_type%s}" \
                --arg entity_ref "${entity_type%s}:$entity_id" \
                --argjson score "$score" \
                '{
                    id: $id,
                    type: $type,
                    entity_ref: $entity_ref,
                    completeness_score: $score
                }')
            
            if [[ $score -ge 70 ]]; then
                ready_entities+=("$priority_data")
            elif [[ $score -ge 50 ]]; then
                needs_work_entities+=("$priority_data")
            else
                blocked_entities+=("$priority_data")
            fi
        done <<< "$entities"
    done
    
    # Generate JSON output
    {
        printf '%s\n' "${ready_entities[@]}" | jq -s . > /tmp/ready.json
        printf '%s\n' "${needs_work_entities[@]}" | jq -s . > /tmp/needs_work.json  
        printf '%s\n' "${blocked_entities[@]}" | jq -s . > /tmp/blocked.json
        
        jq -n \
            --slurpfile ready /tmp/ready.json \
            --slurpfile needs_work /tmp/needs_work.json \
            --slurpfile blocked /tmp/blocked.json \
            '{
                timestamp: now,
                priority_levels: {
                    ready_to_implement: {
                        description: "70%+ complete - Ready for implementation",
                        entities: $ready[0],
                        count: ($ready[0] | length)
                    },
                    needs_work: {
                        description: "50-69% complete - Needs additional work",
                        entities: $needs_work[0],
                        count: ($needs_work[0] | length)
                    },
                    blocked: {
                        description: "<50% complete - High priority blockers",
                        entities: $blocked[0],
                        count: ($blocked[0] | length)
                    }
                },
                recommended_order: [
                    "Fix blockers first (blocked entities)",
                    "Complete entities needing work", 
                    "Implement ready entities",
                    "Use dependency analysis to check prerequisites"
                ]
            }'
        
        # Cleanup temp files
        rm -f /tmp/ready.json /tmp/needs_work.json /tmp/blocked.json
    }
}

# Export workflow functions for use in main know script
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    export -f create_feature_interactive
    export -f complete_entity_interactive
    export -f create_implementation_chain
    export -f show_implementation_priorities
    export -f show_implementation_priorities_json
fi