#!/bin/bash

# validation-comprehensive.sh - Advanced validation and gap detection for know CLI
# Provides comprehensive analysis for PM/Dev workflows

# Enhanced validation with comprehensive gap detection
validate_entity_comprehensive() {
    local entity_ref="$1"
    local min_completeness="${2:-70}"  # Default minimum 70%
    
    local entity_type=$(echo "$entity_ref" | cut -d':' -f1)
    local entity_id=$(echo "$entity_ref" | cut -d':' -f2)
    
    # Handle plural mapping
    case "$entity_type" in
        feature) entity_type="features" ;;
        component) entity_type="components" ;;
        screen) entity_type="screens" ;;
        user) entity_type="users" ;;
        platform) entity_type="platforms" ;;
        requirement) entity_type="requirements" ;;
    esac
    
    echo "🔍 Comprehensive Analysis: $entity_ref"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local total_score=0
    local max_score=0
    local gaps=()
    local recommendations=()
    local critical_issues=()
    
    # 1. Basic Entity Information (Weight: 20%)
    echo
    echo "📋 Basic Information"
    local basic_score=0
    local basic_max=20
    
    # Check if entity exists
    if ! "$MOD_GRAPH" show "$entity_type" "$entity_id" >/dev/null 2>&1; then
        critical_issues+=("❌ Entity does not exist: $entity_ref")
        recommendations+=("1. Create entity: know create $entity_type $entity_id")
        echo "  ❌ Entity exists: No"
    else
        echo "  ✅ Entity exists: Yes"
        basic_score=$((basic_score + 5))
        
        # Get entity data for detailed analysis
        local entity_data
        entity_data=$("$MOD_GRAPH" show "$entity_type" "$entity_id" 2>/dev/null | grep -A 20 "Entity Details:")
        
        # Check name
        if echo "$entity_data" | grep -q '"name"'; then
            echo "  ✅ Name defined: Yes"
            basic_score=$((basic_score + 5))
        else
            echo "  ❌ Name defined: No"
            gaps+=("Missing entity name")
            recommendations+=("Add name: know edit $entity_type $entity_id --name")
        fi
        
        # Check type
        if echo "$entity_data" | grep -q '"type"'; then
            echo "  ✅ Type defined: Yes"
            basic_score=$((basic_score + 5))
        else
            echo "  ❌ Type defined: No"
            gaps+=("Missing entity type")
        fi
        
        # Check description reference
        if echo "$entity_data" | grep -q 'description_ref'; then
            echo "  ✅ Description reference: Yes"
            basic_score=$((basic_score + 5))
        else
            echo "  ❌ Description reference: No"
            gaps+=("Missing description reference")
            recommendations+=("Add description: know add-description $entity_ref")
        fi
    fi
    
    echo "  📊 Basic Information Score: $basic_score/$basic_max ($(( basic_score * 100 / basic_max ))%)"
    total_score=$((total_score + basic_score))
    max_score=$((max_score + basic_max))
    
    # 2. Acceptance Criteria Analysis (Weight: 25%)
    echo
    echo "📝 Acceptance Criteria"
    local criteria_score=0
    local criteria_max=25
    
    # Check if entity has acceptance criteria
    local has_criteria=false
    if "$MOD_GRAPH" show "$entity_type" "$entity_id" 2>/dev/null | grep -q "acceptance_criteria"; then
        has_criteria=true
        echo "  ✅ Has acceptance criteria: Yes"
        criteria_score=$((criteria_score + 5))
        
        # Analyze coverage of different criteria types
        local criteria_types=("functional" "performance" "integration" "reliability" "security" "safety" "validation")
        local covered_types=0
        
        for ctype in "${criteria_types[@]}"; do
            if jq -e --arg type "$entity_type" --arg id "$entity_id" --arg ctype "$ctype" \
               '.entities[$type][$id].acceptance_criteria[$ctype] != null' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
                echo "  ✅ $ctype criteria: Defined"
                covered_types=$((covered_types + 1))
                criteria_score=$((criteria_score + 2))
            else
                echo "  ❌ $ctype criteria: Missing"
                gaps+=("Missing $ctype acceptance criteria")
                recommendations+=("Add $ctype criteria: know add-criteria $entity_ref $ctype")
            fi
        done
        
        # Bonus for comprehensive coverage
        if [[ $covered_types -ge 5 ]]; then
            criteria_score=$((criteria_score + 6))
            echo "  🌟 Comprehensive coverage bonus: +6 points"
        fi
        
    else
        echo "  ❌ Has acceptance criteria: No"
        gaps+=("No acceptance criteria defined")
        recommendations+=("Add acceptance criteria: know add-criteria $entity_ref")
        critical_issues+=("❌ No acceptance criteria - cannot determine requirements")
    fi
    
    echo "  📊 Acceptance Criteria Score: $criteria_score/$criteria_max ($(( criteria_score * 100 / criteria_max ))%)"
    total_score=$((total_score + criteria_score))
    max_score=$((max_score + criteria_max))
    
    # 3. Dependencies & Relationships (Weight: 20%)
    echo
    echo "🔗 Dependencies & Relationships"
    local deps_score=0
    local deps_max=20
    
    # Check graph connections
    local has_deps=false
    local dep_count=0
    if "$JSON_GRAPH_QUERY" deps "$entity_ref" >/dev/null 2>&1; then
        dep_count=$("$JSON_GRAPH_QUERY" deps "$entity_ref" 2>/dev/null | grep -c "📋" || echo "0")
        if [[ $dep_count -gt 0 ]]; then
            has_deps=true
            echo "  ✅ Has dependencies: Yes ($dep_count dependencies)"
            deps_score=$((deps_score + 10))
            
            # Score based on dependency count (reasonable range)
            if [[ $dep_count -ge 3 && $dep_count -le 10 ]]; then
                deps_score=$((deps_score + 5))
                echo "  ✅ Dependency count: Reasonable ($dep_count)"
            elif [[ $dep_count -gt 10 ]]; then
                echo "  ⚠️  Dependency count: High ($dep_count) - may indicate complexity"
                recommendations+=("Review dependencies: consider breaking down $entity_ref")
                deps_score=$((deps_score + 2))
            else
                deps_score=$((deps_score + 3))
            fi
        else
            echo "  ❌ Has dependencies: No connections found"
            gaps+=("No dependencies defined")
            recommendations+=("Define dependencies: know connect $entity_ref <target>")
        fi
    else
        echo "  ❌ Graph entry: Not found"
        gaps+=("No graph entry exists")
        recommendations+=("Create graph entry: know connect $entity_ref <dependency>")
        critical_issues+=("❌ No graph connections - entity appears isolated")
    fi
    
    # Check for dependents (impact analysis)
    local dependent_count=0
    if "$JSON_GRAPH_QUERY" impact "$entity_ref" >/dev/null 2>&1; then
        dependent_count=$("$JSON_GRAPH_QUERY" impact "$entity_ref" 2>/dev/null | grep -c "⚡" || echo "0")
        if [[ $dependent_count -gt 0 ]]; then
            echo "  ✅ Has dependents: Yes ($dependent_count entities depend on this)"
            deps_score=$((deps_score + 5))
        else
            echo "  ⚠️  Has dependents: No (this may be a leaf entity)"
        fi
    fi
    
    echo "  📊 Dependencies Score: $deps_score/$deps_max ($(( deps_score * 100 / deps_max ))%)"
    total_score=$((total_score + deps_score))
    max_score=$((max_score + deps_max))
    
    # 4. Technical Architecture (Weight: 15%)
    echo
    echo "🏗️ Technical Architecture"
    local arch_score=0
    local arch_max=15
    
    # Check for technical references
    local has_tech_arch=false
    if jq -e '.references.technical_architecture' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        has_tech_arch=true
        echo "  ✅ Technical architecture: Defined"
        arch_score=$((arch_score + 8))
        
        # Check for specific architecture components
        local arch_components=("database" "api_gateway" "message_broker" "cache_layer")
        local found_components=0
        for component in "${arch_components[@]}"; do
            if jq -e --arg comp "$component" '.references.technical_architecture[$comp]' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
                found_components=$((found_components + 1))
            fi
        done
        
        if [[ $found_components -ge 2 ]]; then
            arch_score=$((arch_score + 4))
            echo "  ✅ Architecture components: $found_components/4 defined"
        else
            echo "  ⚠️  Architecture components: Limited ($found_components/4)"
            recommendations+=("Define architecture: know add-architecture $entity_ref")
        fi
        
        # Bonus for endpoints definition
        if jq -e '.references.endpoints' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
            arch_score=$((arch_score + 3))
            echo "  ✅ API endpoints: Defined"
        else
            echo "  ❌ API endpoints: Not defined"
            gaps+=("Missing API endpoint specifications")
        fi
        
    else
        echo "  ❌ Technical architecture: Not defined"
        gaps+=("Missing technical architecture")
        recommendations+=("Define technical stack: know add-architecture $entity_ref")
        critical_issues+=("❌ No technical architecture defined")
    fi
    
    echo "  📊 Technical Architecture Score: $arch_score/$arch_max ($(( arch_score * 100 / arch_max ))%)"
    total_score=$((total_score + arch_score))
    max_score=$((max_score + arch_max))
    
    # 5. User Access & Workflows (Weight: 20%)
    echo
    echo "👥 User Access & Workflows"
    local user_score=0
    local user_max=20
    
    # Check for user connections
    local user_connections=0
    if [[ "$entity_type" == "features" || "$entity_type" == "screens" || "$entity_type" == "components" ]]; then
        # Check what users have access to this entity
        user_connections=$("$JSON_GRAPH_QUERY" impact "$entity_ref" 2>/dev/null | grep -c "user:" || echo "0")
        
        if [[ $user_connections -gt 0 ]]; then
            echo "  ✅ User access defined: Yes ($user_connections user types)"
            user_score=$((user_score + 15))
            
            if [[ $user_connections -ge 3 ]]; then
                echo "  ✅ Multi-user support: Comprehensive"
                user_score=$((user_score + 5))
            fi
        else
            echo "  ❌ User access defined: No"
            gaps+=("No user access patterns defined")
            recommendations+=("Define user access: know connect user:<type> $entity_ref")
            critical_issues+=("❌ No user access defined - unclear who can use this")
        fi
    else
        echo "  ℹ️  User access: Not applicable for this entity type"
        user_score=$((user_score + user_max))  # Full score for non-user-facing entities
    fi
    
    echo "  📊 User Access Score: $user_score/$user_max ($(( user_score * 100 / user_max ))%)"
    total_score=$((total_score + user_score))
    max_score=$((max_score + user_max))
    
    # Calculate final completeness percentage
    local completeness_percentage=$(( total_score * 100 / max_score ))
    
    # Final Summary
    echo
    echo "📊 COMPLETENESS SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Overall Score: $total_score/$max_score ($completeness_percentage%)"
    
    if [[ $completeness_percentage -ge 90 ]]; then
        echo "  🟢 Status: EXCELLENT - Ready for implementation"
    elif [[ $completeness_percentage -ge $min_completeness ]]; then
        echo "  🟡 Status: ACCEPTABLE - Can proceed with implementation"
    elif [[ $completeness_percentage -ge 50 ]]; then
        echo "  🟠 Status: NEEDS WORK - Address gaps before implementation"
    else
        echo "  🔴 Status: INCOMPLETE - Significant work required"
    fi
    
    # Show critical issues
    if [[ ${#critical_issues[@]} -gt 0 ]]; then
        echo
        echo "🚨 CRITICAL ISSUES (Must Fix First)"
        for issue in "${critical_issues[@]}"; do
            echo "  $issue"
        done
    fi
    
    # Show gaps
    if [[ ${#gaps[@]} -gt 0 ]]; then
        echo
        echo "📋 IDENTIFIED GAPS"
        local gap_num=1
        for gap in "${gaps[@]}"; do
            echo "  $gap_num. $gap"
            gap_num=$((gap_num + 1))
        done
    fi
    
    # Show recommendations
    if [[ ${#recommendations[@]} -gt 0 ]]; then
        echo
        echo "💡 RECOMMENDED ACTIONS"
        local rec_num=1
        for rec in "${recommendations[@]}"; do
            echo "  $rec_num. $rec"
            rec_num=$((rec_num + 1))
        done
    fi
    
    echo
    if [[ $completeness_percentage -ge $min_completeness ]]; then
        echo "✅ READY: Entity meets minimum completeness threshold ($min_completeness%)"
        echo "💡 Run: know spec $entity_ref --complete"
        return 0
    else
        echo "❌ NOT READY: Entity below minimum completeness threshold ($min_completeness%)"
        echo "📈 Need $(( min_completeness - completeness_percentage ))% more completeness"
        echo "🔧 Complete the recommended actions above, then re-run validation"
        return 1
    fi
}

# Quick completeness check (returns just the percentage)
get_completeness_score() {
    local entity_ref="$1"
    
    # This is a simplified version for quick checks
    local entity_type=$(echo "$entity_ref" | cut -d':' -f1)
    local entity_id=$(echo "$entity_ref" | cut -d':' -f2)
    
    case "$entity_type" in
        feature) entity_type="features" ;;
        component) entity_type="components" ;;
        screen) entity_type="screens" ;;
    esac
    
    local score=0
    
    # Basic existence (25%)
    if "$MOD_GRAPH" show "$entity_type" "$entity_id" >/dev/null 2>&1; then
        score=$((score + 25))
    fi
    
    # Has acceptance criteria (25%)
    if jq -e --arg type "$entity_type" --arg id "$entity_id" \
       '.entities[$type][$id].acceptance_criteria != null' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        score=$((score + 25))
    fi
    
    # Has dependencies (25%)
    if "$JSON_GRAPH_QUERY" deps "$entity_ref" >/dev/null 2>&1; then
        score=$((score + 25))
    fi
    
    # Has technical architecture (25%)
    if jq -e '.references.technical_architecture' "$KNOWLEDGE_MAP" >/dev/null 2>&1; then
        score=$((score + 25))
    fi
    
    echo "$score"
}

# Batch completeness analysis
analyze_completeness_batch() {
    local entity_type="$1"
    
    echo "📊 Completeness Analysis: $entity_type"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    case "$entity_type" in
        feature) entity_type="features" ;;
        component) entity_type="components" ;;
        screen) entity_type="screens" ;;
    esac
    
    local entities
    entities=$("$MOD_GRAPH" list "$entity_type" | grep "  " | cut -d' ' -f3 | cut -d'-' -f1)
    
    local total_entities=0
    local ready_entities=0
    local needs_work=0
    
    while IFS= read -r entity_id; do
        [[ -z "$entity_id" ]] && continue
        total_entities=$((total_entities + 1))
        
        local score
        score=$(get_completeness_score "${entity_type%s}:$entity_id")
        
        if [[ $score -ge 70 ]]; then
            echo "  🟢 $entity_id: $score% - Ready"
            ready_entities=$((ready_entities + 1))
        elif [[ $score -ge 50 ]]; then
            echo "  🟡 $entity_id: $score% - Needs work"
            needs_work=$((needs_work + 1))
        else
            echo "  🔴 $entity_id: $score% - Incomplete"
        fi
    done <<< "$entities"
    
    echo
    echo "📈 Summary: $ready_entities/$total_entities ready for implementation ($needs_work need work)"
}

# Generate structured output for validation results
generate_validation_json() {
    local entity_ref="$1"
    local total_score="$2"
    local max_score="$3"
    local completeness_percentage="$4"
    local min_completeness="${5:-70}"
    shift 5
    local gaps=("$@")
    
    # Split arrays (gaps vs recommendations)
    local gap_count=0
    local rec_count=0
    for item in "${gaps[@]}"; do
        if [[ "$item" == "RECOMMENDATIONS_SPLIT" ]]; then
            break
        fi
        ((gap_count++))
    done
    rec_count=$(( ${#gaps[@]} - gap_count - 1 ))
    
    local status="incomplete"
    local status_description="INCOMPLETE - Significant work required"
    
    if [[ $completeness_percentage -ge 90 ]]; then
        status="excellent"
        status_description="EXCELLENT - Ready for implementation"
    elif [[ $completeness_percentage -ge $min_completeness ]]; then
        status="acceptable"  
        status_description="ACCEPTABLE - Can proceed with implementation"
    elif [[ $completeness_percentage -ge 50 ]]; then
        status="needs_work"
        status_description="NEEDS WORK - Address gaps before implementation"
    fi
    
    # Build JSON structure
    jq -n \
        --arg entity_ref "$entity_ref" \
        --argjson score "$total_score" \
        --argjson max_score "$max_score" \
        --argjson percentage "$completeness_percentage" \
        --argjson min_threshold "$min_completeness" \
        --arg status "$status" \
        --arg status_desc "$status_description" \
        --argjson ready "$(if [[ $completeness_percentage -ge $min_completeness ]]; then echo true; else echo false; fi)" \
        --argjson gap_count "$gap_count" \
        --argjson rec_count "$rec_count" \
        '{
            entity: $entity_ref,
            completeness: {
                score: $score,
                max_score: $max_score,
                percentage: $percentage,
                threshold: $min_threshold,
                ready: $ready
            },
            status: {
                level: $status,
                description: $status_desc
            },
            analysis: {
                gaps_identified: $gap_count,
                recommendations: $rec_count,
                timestamp: now
            }
        }'
}

# Batch completeness analysis with JSON output
analyze_completeness_batch_json() {
    local entity_type="$1"
    
    case "$entity_type" in
        feature) entity_type="features" ;;
        component) entity_type="components" ;;
        screen) entity_type="screens" ;;
    esac
    
    local entities
    entities=$("$MOD_GRAPH" list "$entity_type" | grep "  " | cut -d' ' -f3 | cut -d'-' -f1)
    
    local results=()
    
    while IFS= read -r entity_id; do
        [[ -z "$entity_id" ]] && continue
        
        local score
        score=$(get_completeness_score "${entity_type%s}:$entity_id")
        
        local status="incomplete"
        local ready=false
        
        if [[ $score -ge 70 ]]; then
            status="ready"
            ready=true
        elif [[ $score -ge 50 ]]; then
            status="needs_work"
        fi
        
        local result
        result=$(jq -n \
            --arg id "$entity_id" \
            --arg entity_ref "${entity_type%s}:$entity_id" \
            --argjson score "$score" \
            --arg status "$status" \
            --argjson ready "$ready" \
            '{
                id: $id,
                entity_ref: $entity_ref,
                score: $score,
                status: $status,
                ready: $ready
            }')
        results+=("$result")
    done <<< "$entities"
    
    # Combine all results into single JSON array
    printf '%s\n' "${results[@]}" | jq -s \
        --arg entity_type "$entity_type" \
        '{
            entity_type: $entity_type,
            entities: .,
            summary: {
                total: length,
                ready: [.[] | select(.ready == true)] | length,
                needs_work: [.[] | select(.status == "needs_work")] | length,
                incomplete: [.[] | select(.status == "incomplete")] | length,
                timestamp: now
            }
        }'
}

# Export validation functions for use in main know script
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # Being sourced - export functions
    export -f validate_entity_comprehensive
    export -f get_completeness_score  
    export -f analyze_completeness_batch
    export -f generate_validation_json
    export -f analyze_completeness_batch_json
fi