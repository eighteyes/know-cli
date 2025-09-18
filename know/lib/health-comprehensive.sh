#!/bin/bash

# health-comprehensive.sh - Comprehensive health check that integrates all validation tools

# Source the original health check for structural checks
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/health.sh"

# Comprehensive health check that calls all validation tools
comprehensive_health_check() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local verbose="${2:-false}"

    echo "🏥 COMPREHENSIVE GRAPH HEALTH CHECK"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "📂 Graph: $graph_file"
    echo

    # Track overall health metrics
    local total_score=0
    local section_count=0
    local critical_issues=0
    local warnings=0
    local suggestions=0

    # ═══════════════════════════════════════════════════════════
    # SECTION 1: STRUCTURAL INTEGRITY (from original health.sh)
    # ═══════════════════════════════════════════════════════════
    echo "══════════════════════════════════════════════════════════"
    echo "1️⃣ STRUCTURAL INTEGRITY"
    echo "══════════════════════════════════════════════════════════"

    # Calculate structural health score
    local structural_score=$(calculate_health_score "$graph_file")
    echo "   📊 Structural Health Score: $structural_score/100"

    # Quick structural checks
    local hanging=$(find_hanging_references "$graph_file" | wc -l | tr -d ' ')
    local orphaned=$(find_orphaned_entities "$graph_file" | wc -l | tr -d ' ')
    local missing=$(find_missing_graph_entries "$graph_file" | wc -l | tr -d ' ')
    local self_deps=$(find_self_dependencies "$graph_file" | wc -l | tr -d ' ')

    if [[ $hanging -gt 0 ]]; then
        echo "   🔴 Hanging references: $hanging"
        ((critical_issues++))
    fi
    if [[ $orphaned -gt 0 ]]; then
        echo "   🟡 Orphaned entities: $orphaned"
        ((warnings++))
    fi
    if [[ $missing -gt 0 ]]; then
        echo "   🟠 Missing graph entries: $missing"
        ((warnings++))
    fi
    if [[ $self_deps -gt 0 ]]; then
        echo "   🔴 Self-dependencies: $self_deps"
        ((critical_issues++))
    fi

    # Check for cycles
    if "$SCRIPT_DIR/query-graph.sh" cycles 2>/dev/null | grep -q "Circular dependencies found"; then
        local cycle_count=$("$SCRIPT_DIR/query-graph.sh" cycles 2>/dev/null | grep "🔁" | wc -l)
        echo "   🔴 Circular dependencies: $cycle_count"
        ((critical_issues++))
    else
        echo "   ✅ No circular dependencies"
    fi

    total_score=$((total_score + structural_score))
    ((section_count++))
    echo

    # ═══════════════════════════════════════════════════════════
    # SECTION 2: DEPENDENCY VALIDATION
    # ═══════════════════════════════════════════════════════════
    echo "══════════════════════════════════════════════════════════"
    echo "2️⃣ DEPENDENCY VALIDATION"
    echo "══════════════════════════════════════════════════════════"

    # Run dependency validation
    local dep_validation=$("$SCRIPT_DIR/validate-dependencies.sh" "$graph_file" 2>&1 || true)

    if echo "$dep_validation" | grep -q "✅"; then
        echo "   ✅ All dependencies follow allowed patterns"
        local dep_score=100
    elif echo "$dep_validation" | grep -q "violations found"; then
        local violation_count=$(echo "$dep_validation" | grep -c "❌" || echo 0)
        echo "   ❌ Dependency rule violations: $violation_count"
        ((critical_issues += violation_count))
        local dep_score=$((100 - violation_count * 10))
        [[ $dep_score -lt 0 ]] && dep_score=0
    else
        echo "   ⚠️ Dependency validation unavailable"
        local dep_score=50
    fi

    echo "   📊 Dependency Validation Score: $dep_score/100"
    total_score=$((total_score + dep_score))
    ((section_count++))
    echo

    # ═══════════════════════════════════════════════════════════
    # SECTION 3: ENTITY COMPLETENESS
    # ═══════════════════════════════════════════════════════════
    echo "══════════════════════════════════════════════════════════"
    echo "3️⃣ ENTITY COMPLETENESS"
    echo "══════════════════════════════════════════════════════════"

    # Check completeness for major entity types
    local total_completeness=0
    local completeness_count=0

    for entity_type in features components screens; do
        local entities=$(jq -r ".entities.$entity_type | keys[]" "$graph_file" 2>/dev/null | head -5)
        local type_total=0
        local type_count=0

        while IFS= read -r entity_id; do
            [[ -z "$entity_id" ]] && continue
            local score=$("$SCRIPT_DIR/completeness-scorer.sh" score "${entity_type%s}:$entity_id" 2>/dev/null || echo 0)
            type_total=$((type_total + score))
            ((type_count++))

            if [[ $score -lt 50 ]]; then
                [[ "$verbose" == "true" ]] && echo "     🔴 ${entity_type%s}:$entity_id - $score%"
                ((critical_issues++))
            elif [[ $score -lt 70 ]]; then
                [[ "$verbose" == "true" ]] && echo "     🟡 ${entity_type%s}:$entity_id - $score%"
                ((warnings++))
            fi
        done <<< "$entities"

        if [[ $type_count -gt 0 ]]; then
            local type_avg=$((type_total / type_count))
            echo "   📊 $entity_type average: $type_avg%"
            total_completeness=$((total_completeness + type_avg))
            ((completeness_count++))
        fi
    done

    local completeness_score=50
    if [[ $completeness_count -gt 0 ]]; then
        completeness_score=$((total_completeness / completeness_count))
    fi

    echo "   📊 Overall Completeness Score: $completeness_score/100"
    total_score=$((total_score + completeness_score))
    ((section_count++))
    echo

    # ═══════════════════════════════════════════════════════════
    # SECTION 4: REFERENCE VALIDATION
    # ═══════════════════════════════════════════════════════════
    echo "══════════════════════════════════════════════════════════"
    echo "4️⃣ REFERENCE VALIDATION"
    echo "══════════════════════════════════════════════════════════"

    # Check reference parents
    local ref_check=$("$SCRIPT_DIR/check-reference-parents.sh" 2>&1 || true)
    local orphaned_refs=$(echo "$ref_check" | grep -c "has no parent entity" || echo 0)

    if [[ $orphaned_refs -eq 0 ]]; then
        echo "   ✅ All reference keys have parent entities"
        local ref_score=100
    else
        echo "   🟡 Orphaned reference keys: $orphaned_refs"
        ((warnings += orphaned_refs))
        local ref_score=$((100 - orphaned_refs * 5))
        [[ $ref_score -lt 0 ]] && ref_score=0
    fi

    echo "   📊 Reference Validation Score: $ref_score/100"
    total_score=$((total_score + ref_score))
    ((section_count++))
    echo

    # ═══════════════════════════════════════════════════════════
    # SECTION 5: GAP ANALYSIS
    # ═══════════════════════════════════════════════════════════
    echo "══════════════════════════════════════════════════════════"
    echo "5️⃣ GAP ANALYSIS"
    echo "══════════════════════════════════════════════════════════"

    # Run gap summary
    local gap_summary=$("$SCRIPT_DIR/gap-analysis.sh" summary 2>&1 || true)
    local total_gaps=$(echo "$gap_summary" | grep -c "Missing" || echo 0)

    if [[ $total_gaps -eq 0 ]]; then
        echo "   ✅ No significant gaps found"
        local gap_score=100
    else
        echo "   🟡 Total gaps identified: $total_gaps"
        ((suggestions += total_gaps))
        local gap_score=$((100 - total_gaps * 3))
        [[ $gap_score -lt 0 ]] && gap_score=0
    fi

    echo "   📊 Gap Analysis Score: $gap_score/100"
    total_score=$((total_score + gap_score))
    ((section_count++))
    echo

    # ═══════════════════════════════════════════════════════════
    # FINAL HEALTH SUMMARY
    # ═══════════════════════════════════════════════════════════
    echo "══════════════════════════════════════════════════════════"
    echo "📊 OVERALL HEALTH SUMMARY"
    echo "══════════════════════════════════════════════════════════"

    # Calculate final score
    local final_score=$((total_score / section_count))

    # Determine health status
    local health_status=""
    local health_emoji=""
    if [[ $final_score -ge 90 ]]; then
        health_status="EXCELLENT"
        health_emoji="✅"
    elif [[ $final_score -ge 75 ]]; then
        health_status="GOOD"
        health_emoji="🟢"
    elif [[ $final_score -ge 60 ]]; then
        health_status="FAIR"
        health_emoji="🟡"
    elif [[ $final_score -ge 40 ]]; then
        health_status="POOR"
        health_emoji="🟠"
    else
        health_status="CRITICAL"
        health_emoji="🔴"
    fi

    echo "   $health_emoji Overall Health: $health_status ($final_score/100)"
    echo
    echo "   📈 Section Scores:"
    echo "      • Structural Integrity: $structural_score/100"
    echo "      • Dependency Validation: $dep_score/100"
    echo "      • Entity Completeness: $completeness_score/100"
    echo "      • Reference Validation: $ref_score/100"
    echo "      • Gap Analysis: $gap_score/100"
    echo
    echo "   📊 Issue Summary:"
    echo "      • 🔴 Critical Issues: $critical_issues"
    echo "      • 🟡 Warnings: $warnings"
    echo "      • 💡 Suggestions: $suggestions"
    echo

    # ═══════════════════════════════════════════════════════════
    # RECOMMENDED ACTIONS
    # ═══════════════════════════════════════════════════════════
    if [[ $final_score -lt 100 ]]; then
        echo "══════════════════════════════════════════════════════════"
        echo "🔧 RECOMMENDED ACTIONS"
        echo "══════════════════════════════════════════════════════════"

        local action_count=1

        # Critical issues first
        if [[ $hanging -gt 0 || $self_deps -gt 0 || $critical_issues -gt 0 ]]; then
            echo "   ${action_count}. 🔴 CRITICAL - Fix structural issues:"
            [[ $hanging -gt 0 ]] && echo "      • know repair hanging"
            [[ $self_deps -gt 0 ]] && echo "      • know repair self-deps"
            echo "      • know repair --auto"
            ((action_count++))
            echo
        fi

        # Dependency violations
        if [[ $dep_score -lt 80 ]]; then
            echo "   ${action_count}. 🟠 HIGH - Fix dependency violations:"
            echo "      • know validate-deps"
            echo "      • know mod resolve-cycles"
            ((action_count++))
            echo
        fi

        # Completeness issues
        if [[ $completeness_score -lt 70 ]]; then
            echo "   ${action_count}. 🟡 MEDIUM - Improve entity completeness:"
            echo "      • know completeness features"
            echo "      • know gap-analyze-all"
            echo "      • know chain-builder"
            ((action_count++))
            echo
        fi

        # Reference issues
        if [[ $orphaned_refs -gt 0 ]]; then
            echo "   ${action_count}. 🟡 MEDIUM - Connect orphaned references:"
            echo "      • know connect-references interactive"
            ((action_count++))
            echo
        fi

        # Gap issues
        if [[ $gap_score -lt 80 ]]; then
            echo "   ${action_count}. 💡 LOW - Address implementation gaps:"
            echo "      • know gap-report"
            echo "      • know todo"
            ((action_count++))
            echo
        fi

        echo "   💡 Quick Fix: Run 'know repair --interactive' for guided repair"
        echo "   🚀 Auto Fix: Run 'know repair --auto' to fix all structural issues"
    else
        echo "══════════════════════════════════════════════════════════"
        echo "✅ GRAPH IS HEALTHY"
        echo "══════════════════════════════════════════════════════════"
        echo "   No immediate actions required."
        echo "   Continue with: know todo"
    fi

    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 For detailed analysis of specific areas:"
    echo "   • know validate-graph     - Full validation with rules"
    echo "   • know gap-analyze-all    - Comprehensive gap analysis"
    echo "   • know completeness       - Detailed completeness report"
    echo "   • know check references   - Reference parent validation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# If called directly, run comprehensive check
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    comprehensive_health_check "$@"
fi