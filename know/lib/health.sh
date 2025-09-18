#!/bin/bash

# health.sh - Comprehensive graph health checking and repair functions

# Find orphaned entities (nothing depends on them)
find_orphaned_entities() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    # Get all entities that are NOT referenced as dependencies
    jq -r '
        # Get all entity IDs
        (.entities | to_entries | map(.value | to_entries | map("\(.value.id // (. | @base64d.key))")) | flatten) as $all_entities |
        # Get all entities in graph
        (.graph | keys) as $graph_entities |
        # Get all entities that are dependencies
        ([.graph | .[] | .depends_on[]?] | unique) as $referenced |
        # Find entities in graph but not referenced
        $graph_entities - $referenced | .[]
    ' "$graph_file" 2>/dev/null | sort -u
}

# Find entities missing from graph (defined but no graph entry)
find_missing_graph_entries() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    jq -r '
        # Get all entity IDs with their types
        [.entities | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)"] as $all_entities |
        # Get all graph entries
        (.graph | keys) as $graph_keys |
        # Find entities not in graph
        $all_entities - $graph_keys | .[]
    ' "$graph_file" 2>/dev/null | sort -u
}

# Find self-dependencies (entities depending on themselves)
find_self_dependencies() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    jq -r '
        .graph | to_entries[] |
        select(.value.depends_on[]? == .key) |
        .key
    ' "$graph_file" 2>/dev/null | sort -u
}

# Find hanging references (more comprehensive than broken refs)
find_hanging_references() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    jq -r '
        # Get all valid entity IDs
        [.entities | to_entries[] | .key as $type | .value | to_entries[] | "\($type):\(.key)"] as $valid_entities |
        # Get all referenced entities
        [.graph | .[] | .depends_on[]?] | unique[] |
        # Filter to only non-existent references
        select(. as $ref | $valid_entities | index($ref) | not)
    ' "$graph_file" 2>/dev/null | sort -u
}

# Calculate health score
calculate_health_score() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"

    local orphaned_list=$(find_orphaned_entities "$graph_file")
    local orphaned=$([[ -z "$orphaned_list" ]] && echo 0 || echo "$orphaned_list" | wc -l | tr -d ' ')

    local missing_list=$(find_missing_graph_entries "$graph_file")
    local missing=$([[ -z "$missing_list" ]] && echo 0 || echo "$missing_list" | wc -l | tr -d ' ')

    local self_deps_list=$(find_self_dependencies "$graph_file")
    local self_deps=$([[ -z "$self_deps_list" ]] && echo 0 || echo "$self_deps_list" | wc -l | tr -d ' ')

    local hanging_list=$(find_hanging_references "$graph_file")
    local hanging=$([[ -z "$hanging_list" ]] && echo 0 || echo "$hanging_list" | wc -l | tr -d ' ')

    # Check for cycles
    local cycles=0
    if "$LIB_DIR/query-graph.sh" cycles 2>/dev/null | grep -q "Circular dependencies found"; then
        cycles=$("$LIB_DIR/query-graph.sh" cycles 2>/dev/null | grep "🔁" | wc -l)
    fi

    local total_issues=$((orphaned + missing + self_deps + hanging + cycles))

    # Calculate score (100 - penalty for issues)
    local score=100
    [[ $hanging -gt 0 ]] && score=$((score - hanging * 5))      # Critical issues
    [[ $cycles -gt 0 ]] && score=$((score - cycles * 5))        # Critical issues
    [[ $self_deps -gt 0 ]] && score=$((score - self_deps * 3))  # Moderate issues
    [[ $missing -gt 0 ]] && score=$((score - missing * 2))      # Minor issues
    [[ $orphaned -gt 0 ]] && score=$((score - orphaned * 1))    # Minor issues

    # Ensure score doesn't go below 0
    [[ $score -lt 0 ]] && score=0

    echo "$score"
}

# Comprehensive health check
check_graph_health() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local format="${2:-text}"  # text or json

    echo "🔍 Graph Health Analysis"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo

    # 1. Hanging references
    echo "🔴 HANGING REFERENCES (referenced but don't exist):"
    local hanging=$(find_hanging_references "$graph_file")
    if [[ -z "$hanging" ]]; then
        echo "   ✅ No hanging references found"
    else
        echo "$hanging" | while read -r ref; do
            echo "   - $ref"
        done
        local hanging_count=$(echo "$hanging" | grep -c .)
        echo "   📊 Total: $hanging_count hanging references"
    fi
    echo

    # 2. Orphaned entities
    echo "🟡 ORPHANED ENTITIES (nothing depends on them):"
    local orphaned=$(find_orphaned_entities "$graph_file")
    if [[ -z "$orphaned" ]]; then
        echo "   ✅ No orphaned entities found"
    else
        echo "$orphaned" | while read -r entity; do
            echo "   - $entity"
        done
        local orphaned_count=$(echo "$orphaned" | grep -c .)
        echo "   📊 Total: $orphaned_count orphaned entities"
    fi
    echo

    # 3. Missing graph entries
    echo "🟠 MISSING FROM GRAPH (defined but not in graph):"
    local missing=$(find_missing_graph_entries "$graph_file")
    if [[ -z "$missing" ]]; then
        echo "   ✅ All entities have graph entries"
    else
        echo "$missing" | while read -r entity; do
            echo "   - $entity"
        done
        local missing_count=$(echo "$missing" | grep -c .)
        echo "   📊 Total: $missing_count entities missing from graph"
    fi
    echo

    # 4. Self-dependencies
    echo "🔄 SELF-DEPENDENCIES (entities depending on themselves):"
    local self_deps=$(find_self_dependencies "$graph_file")
    if [[ -z "$self_deps" ]]; then
        echo "   ✅ No self-dependencies found"
    else
        echo "$self_deps" | while read -r entity; do
            echo "   - $entity"
        done
        local self_count=$(echo "$self_deps" | grep -c .)
        echo "   📊 Total: $self_count self-dependencies"
    fi
    echo

    # 5. Circular dependencies (using existing function)
    echo "🔄 CIRCULAR DEPENDENCIES:"
    if "$LIB_DIR/query-graph.sh" cycles 2>/dev/null | grep -q "No circular dependencies"; then
        echo "   ✅ No circular dependencies found"
    else
        "$LIB_DIR/query-graph.sh" cycles 2>/dev/null | grep "🔁" | sed 's/^/   /'
    fi
    echo

    # 6. Health score
    local score=$(calculate_health_score "$graph_file")
    echo "📈 GRAPH HEALTH SUMMARY:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Use query-graph stats to get totals
    local QUERY_GRAPH="${JSON_GRAPH_QUERY:-$(dirname "$0")/query-graph.sh}"
    local stats_output=$("$QUERY_GRAPH" stats 2>/dev/null)
    local total_entities=$(echo "$stats_output" | grep "Total entities:" | grep -o '[0-9]*' || echo 0)
    local total_deps=$(echo "$stats_output" | grep "Total dependencies:" | grep -o '[0-9]*' || echo 0)

    echo "   📊 Total entities: $total_entities"
    echo "   📊 Total dependencies: $total_deps"
    echo "   🏆 Health Score: $score/100"

    if [[ $score -ge 90 ]]; then
        echo "   ✅ Graph health: EXCELLENT"
    elif [[ $score -ge 75 ]]; then
        echo "   🟢 Graph health: GOOD"
    elif [[ $score -ge 60 ]]; then
        echo "   🟡 Graph health: FAIR"
    elif [[ $score -ge 40 ]]; then
        echo "   🟠 Graph health: POOR"
    else
        echo "   🔴 Graph health: CRITICAL"
    fi

    # 7. Recommendations
    if [[ $score -lt 100 ]]; then
        echo
        echo "🔧 RECOMMENDED ACTIONS:"
        echo "━━━━━━━━━━━━━━━━━━━━━━"

        [[ -n "$hanging" ]] && echo "   1. Remove hanging references: know repair hanging"
        [[ -n "$orphaned" ]] && echo "   2. Connect orphaned entities: know repair orphans"
        [[ -n "$missing" ]] && echo "   3. Add missing graph entries: know repair missing"
        [[ -n "$self_deps" ]] && echo "   4. Remove self-dependencies: know repair self-deps"

        echo
        echo "   💡 Run 'know repair --interactive' for guided fixes"
        echo "   🚀 Run 'know repair --auto' to fix all issues automatically"
    fi
}

# Fix hanging references
fix_hanging_references() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local mode="${2:-interactive}"  # interactive or auto

    local hanging=$(find_hanging_references "$graph_file")

    if [[ -z "$hanging" ]]; then
        echo "✅ No hanging references to fix"
        return 0
    fi

    echo "🔴 Found hanging references to fix:"
    echo "$hanging" | nl -w2 -s'. '

    if [[ "$mode" == "interactive" ]]; then
        echo
        echo "Options:"
        echo "1. Remove ALL hanging references"
        echo "2. Skip"
        read -p "Choose (1-2): " choice

        if [[ "$choice" != "1" ]]; then
            echo "Skipped fixing hanging references"
            return 0
        fi
    fi

    # Remove hanging references from graph
    local temp_file=$(mktemp)
    local refs_to_remove=$(echo "$hanging" | jq -R -s 'split("\n") | map(select(length > 0))')

    jq --argjson refs "$refs_to_remove" '
        .graph |= with_entries(
            .value.depends_on = (.value.depends_on // []) - $refs
        )
    ' "$graph_file" > "$temp_file"

    mv "$temp_file" "$graph_file"
    echo "✅ Removed $(echo "$hanging" | wc -l) hanging references"
}

# Fix orphaned entities
fix_orphaned_entities() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local mode="${2:-interactive}"

    local orphaned=$(find_orphaned_entities "$graph_file")

    if [[ -z "$orphaned" ]]; then
        echo "✅ No orphaned entities to fix"
        return 0
    fi

    echo "🟡 Found orphaned entities:"
    echo "$orphaned" | nl -w2 -s'. '

    if [[ "$mode" == "interactive" ]]; then
        echo
        echo "Options:"
        echo "1. Remove orphaned entities from graph"
        echo "2. Keep them (might be entry points)"
        echo "3. Skip"
        read -p "Choose (1-3): " choice

        if [[ "$choice" == "1" ]]; then
            # Remove orphaned entities from graph
            local temp_file=$(mktemp)
            local orphans_to_remove=$(echo "$orphaned" | jq -R -s 'split("\n") | map(select(length > 0))')

            jq --argjson orphans "$orphans_to_remove" '
                .graph |= with_entries(
                    select(.key as $k | $orphans | index($k) | not)
                )
            ' "$graph_file" > "$temp_file"

            mv "$temp_file" "$graph_file"
            echo "✅ Removed $(echo "$orphaned" | wc -l) orphaned entities"
        else
            echo "Kept orphaned entities"
        fi
    fi
}

# Fix missing graph entries
fix_missing_graph_entries() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local mode="${2:-interactive}"

    local missing=$(find_missing_graph_entries "$graph_file")

    if [[ -z "$missing" ]]; then
        echo "✅ No missing graph entries to fix"
        return 0
    fi

    echo "🟠 Found entities missing from graph:"
    echo "$missing" | nl -w2 -s'. '

    if [[ "$mode" == "interactive" ]]; then
        echo
        echo "Options:"
        echo "1. Add empty graph entries for all"
        echo "2. Skip"
        read -p "Choose (1-2): " choice

        if [[ "$choice" != "1" ]]; then
            echo "Skipped adding graph entries"
            return 0
        fi
    fi

    # Add missing entries to graph
    local temp_file=$(mktemp)
    local missing_list=$(echo "$missing" | jq -R -s 'split("\n") | map(select(length > 0))')

    jq --argjson missing "$missing_list" '
        .graph as $g |
        .graph = ($g + ($missing | map({key: ., value: {depends_on: []}}) | from_entries))
    ' "$graph_file" > "$temp_file"

    mv "$temp_file" "$graph_file"
    echo "✅ Added $(echo "$missing" | wc -l) graph entries"
}

# Fix self-dependencies
fix_self_dependencies() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local mode="${2:-interactive}"

    local self_deps=$(find_self_dependencies "$graph_file")

    if [[ -z "$self_deps" ]]; then
        echo "✅ No self-dependencies to fix"
        return 0
    fi

    echo "🔄 Found self-dependencies:"
    echo "$self_deps" | nl -w2 -s'. '

    if [[ "$mode" == "interactive" ]]; then
        echo
        echo "Options:"
        echo "1. Remove ALL self-dependencies"
        echo "2. Skip"
        read -p "Choose (1-2): " choice

        if [[ "$choice" != "1" ]]; then
            echo "Skipped fixing self-dependencies"
            return 0
        fi
    fi

    # Remove self-dependencies
    local temp_file=$(mktemp)

    jq '
        .graph |= with_entries(
            .value.depends_on = (.value.depends_on // []) - [.key]
        )
    ' "$graph_file" > "$temp_file"

    mv "$temp_file" "$graph_file"
    echo "✅ Removed $(echo "$self_deps" | wc -l) self-dependencies"
}

# Main repair function
repair_graph() {
    local graph_file="${1:-$KNOWLEDGE_MAP}"
    local mode="${2:-interactive}"  # interactive, auto, or specific type

    # Create backup
    local backup_file="${graph_file}.backup.$(date +%s)"
    cp "$graph_file" "$backup_file"
    echo "💾 Backup created: $backup_file"
    echo

    case "$mode" in
        "hanging")
            fix_hanging_references "$graph_file" "auto"
            ;;
        "orphans")
            fix_orphaned_entities "$graph_file" "auto"
            ;;
        "missing")
            fix_missing_graph_entries "$graph_file" "auto"
            ;;
        "self-deps")
            fix_self_dependencies "$graph_file" "auto"
            ;;
        "cycles")
            "$LIB_DIR/mod-graph.sh" resolve-cycles
            ;;
        "auto")
            echo "🔧 AUTO-REPAIR MODE"
            echo "━━━━━━━━━━━━━━━━━━━━━"
            echo
            fix_hanging_references "$graph_file" "auto"
            echo
            fix_self_dependencies "$graph_file" "auto"
            echo
            fix_missing_graph_entries "$graph_file" "auto"
            echo
            "$LIB_DIR/mod-graph.sh" resolve-cycles 2>/dev/null
            echo
            echo "✅ Auto-repair complete"
            ;;
        "interactive"|*)
            echo "🔧 INTERACTIVE REPAIR MODE"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo

            while true; do
                echo "What would you like to fix?"
                echo "1. 🔴 Hanging references"
                echo "2. 🟡 Orphaned entities"
                echo "3. 🟠 Missing graph entries"
                echo "4. 🔄 Self-dependencies"
                echo "5. 🔄 Circular dependencies"
                echo "6. 📊 Show current health"
                echo "7. ✅ Done"
                echo
                read -p "Choose (1-7): " choice

                case $choice in
                    1) fix_hanging_references "$graph_file" "interactive" ;;
                    2) fix_orphaned_entities "$graph_file" "interactive" ;;
                    3) fix_missing_graph_entries "$graph_file" "interactive" ;;
                    4) fix_self_dependencies "$graph_file" "interactive" ;;
                    5) "$LIB_DIR/mod-graph.sh" resolve-cycles ;;
                    6) check_graph_health "$graph_file" ;;
                    7) break ;;
                    *) echo "Invalid choice" ;;
                esac
                echo
            done
            ;;
    esac

    echo
    echo "📊 Final Health Check:"
    echo "━━━━━━━━━━━━━━━━━━━━"
    local final_score=$(calculate_health_score "$graph_file")
    echo "🏆 Health Score: $final_score/100"
}