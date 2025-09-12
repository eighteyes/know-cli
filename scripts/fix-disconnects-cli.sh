#!/bin/bash

# CLI tool to fix disconnected entities in dependency graph  
# Usage: ./scripts/fix-disconnects-cli.sh [OPTIONS] [knowledge-map.json]

KNOWLEDGE_MAP="knowledge-map-cmd.json"
BACKUP_FILE=""
VERBOSE=false
DRY_RUN=false

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [knowledge-map.json]

CLI tool to fix disconnected entities in dependency graph

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Show detailed output
    -n, --dry-run           Show what would be done without making changes
    -b, --backup FILE       Specify backup file location
    --fix-hanging           Remove all hanging references
    --fix-orphans           Remove all orphaned entities
    --add-missing           Add missing graph entries with empty dependencies
    --break-cycles          Break all circular dependencies (remove first occurrence)
    --fix-all               Apply all fixes in sequence
    --report                Show detailed health report and exit

EXAMPLES:
    $0 --report                           # Show current issues
    $0 --fix-hanging --verbose            # Fix hanging refs with details
    $0 --fix-all --dry-run                # Show what all fixes would do
    $0 --fix-hanging --fix-orphans my-map.json  # Fix specific issues in custom file
EOF
}

log() {
    if [[ "$VERBOSE" == true ]]; then
        echo "ℹ️  $*"
    fi
}

warn() {
    echo "⚠️  $*" >&2
}

error() {
    echo "❌ $*" >&2
    exit 1
}

success() {
    echo "✅ $*"
}

create_backup() {
    if [[ -z "$BACKUP_FILE" ]]; then
        BACKUP_FILE="${KNOWLEDGE_MAP}.backup.$(date +%s)"
    fi
    cp "$KNOWLEDGE_MAP" "$BACKUP_FILE"
    log "Backup created: $BACKUP_FILE"
}

execute_jq() {
    local filter="$1"
    local message="$2"
    
    if [[ "$DRY_RUN" == true ]]; then
        echo "DRY RUN: Would execute: $message"
        return 0
    fi
    
    log "Executing: $message"
    if jq "$filter" "$KNOWLEDGE_MAP" > "${KNOWLEDGE_MAP}.tmp"; then
        mv "${KNOWLEDGE_MAP}.tmp" "$KNOWLEDGE_MAP"
        return 0
    else
        rm -f "${KNOWLEDGE_MAP}.tmp"
        error "Failed to execute: $message"
    fi
}

get_hanging_references() {
    jq -r '
    ([.entities | .. | objects | select(has("id")) | .id] + [.graph | keys[]] | unique) as $all_entities |
    [.graph | .[] | .depends_on[]?] | unique[] |
    select(startswith("external:") | not) |
    select(. as $ref | $all_entities | index($ref) | not)
    ' "$KNOWLEDGE_MAP" 2>/dev/null || echo ""
}

get_orphaned_entities() {
    jq -r '
    (.graph | keys) as $graph_entities |
    [.graph | .[] | .depends_on[]?] as $referenced |
    $graph_entities[] |
    select(. as $entity | ($referenced | index($entity) | not))
    ' "$KNOWLEDGE_MAP" 2>/dev/null || echo ""
}

get_missing_entities() {
    jq -r '
    [.entities | .. | objects | select(has("id")) | .id] as $entity_ids |
    (.graph | keys) as $graph_entities |
    $entity_ids[] |
    select(. as $entity | $graph_entities | index($entity) | not)
    ' "$KNOWLEDGE_MAP" 2>/dev/null || echo ""
}

get_circular_dependencies() {
    jq -r '
    .graph as $g |
    $g | to_entries[] |
    .key as $entity |
    .value.depends_on[]? as $dep |
    select($g[$dep].depends_on[]? == $entity) |
    [$entity, $dep] | sort | join(" <-> ")
    ' "$KNOWLEDGE_MAP" 2>/dev/null | sort | uniq || echo ""
}

show_report() {
    echo "📊 DEPENDENCY GRAPH HEALTH REPORT"
    echo "=================================="
    echo
    
    local hanging orphaned missing circular
    hanging=$(get_hanging_references)
    orphaned=$(get_orphaned_entities) 
    missing=$(get_missing_entities)
    circular=$(get_circular_dependencies)
    
    local total_issues=0
    
    echo "🔴 HANGING REFERENCES:"
    if [[ -n "$hanging" ]]; then
        echo "$hanging" | while read -r ref; do
            echo "  - $ref"
        done
        local count=$(echo "$hanging" | wc -l | tr -d ' ')
        echo "  📊 Total: $count"
        total_issues=$((total_issues + count))
    else
        echo "  ✅ None found"
    fi
    echo
    
    echo "🟡 ORPHANED ENTITIES:"  
    if [[ -n "$orphaned" ]]; then
        echo "$orphaned" | while read -r ent; do
            echo "  - $ent"
        done
        local count=$(echo "$orphaned" | wc -l | tr -d ' ')
        echo "  📊 Total: $count"
        total_issues=$((total_issues + count))
    else
        echo "  ✅ None found"
    fi
    echo
    
    echo "🟠 MISSING FROM GRAPH:"
    if [[ -n "$missing" ]]; then
        echo "$missing" | while read -r ent; do
            echo "  - $ent"
        done
        local count=$(echo "$missing" | wc -l | tr -d ' ')
        echo "  📊 Total: $count"
        total_issues=$((total_issues + count))
    else
        echo "  ✅ None found"
    fi
    echo
    
    echo "🔄 CIRCULAR DEPENDENCIES:"
    if [[ -n "$circular" ]]; then
        echo "$circular" | while read -r cycle; do
            echo "  - $cycle"
        done
        local count=$(echo "$circular" | wc -l | tr -d ' ')
        echo "  📊 Total: $count"
        total_issues=$((total_issues + count))
    else
        echo "  ✅ None found"
    fi
    echo
    
    echo "📈 SUMMARY:"
    local total_entities=$(jq '[.graph | keys[]] | length' "$KNOWLEDGE_MAP")
    local total_deps=$(jq '[.graph | .[] | .depends_on[]?] | length' "$KNOWLEDGE_MAP")
    echo "  📊 Total entities: $total_entities"
    echo "  📊 Total dependencies: $total_deps"
    echo "  🚨 Total issues: $total_issues"
    
    if [[ $total_issues -eq 0 ]]; then
        echo "  ✅ Graph health: EXCELLENT"
    elif [[ $total_issues -lt 10 ]]; then
        echo "  🟡 Graph health: GOOD"
    elif [[ $total_issues -lt 30 ]]; then
        echo "  🟠 Graph health: FAIR"
    else
        echo "  🔴 Graph health: POOR"
    fi
}

fix_hanging_references() {
    echo "🔴 FIXING HANGING REFERENCES"
    echo "=========================="
    
    local hanging
    hanging=$(get_hanging_references)
    
    if [[ -z "$hanging" ]]; then
        success "No hanging references found"
        return 0
    fi
    
    local count=$(echo "$hanging" | wc -l | tr -d ' ')
    echo "Found $count hanging references:"
    echo "$hanging" | sed 's/^/  - /'
    echo
    
    execute_jq '
    ([.entities | .. | objects | select(has("id")) | .id] + [.graph | keys[]] | unique) as $valid_entities |
    .graph |= with_entries(
        .value.depends_on = (
            (.value.depends_on // []) | map(select(. as $ref | 
                (startswith("external:") or ($valid_entities | index($ref)))
            ))
        )
    )
    ' "Remove hanging references"
    
    success "Removed $count hanging references"
}

fix_orphaned_entities() {
    echo "🟡 FIXING ORPHANED ENTITIES"
    echo "========================="
    
    local orphaned
    orphaned=$(get_orphaned_entities)
    
    if [[ -z "$orphaned" ]]; then
        success "No orphaned entities found"
        return 0
    fi
    
    local count=$(echo "$orphaned" | wc -l | tr -d ' ')
    echo "Found $count orphaned entities:"
    echo "$orphaned" | sed 's/^/  - /'
    echo
    
    execute_jq '
    (.graph | keys) as $graph_entities |
    [.graph | .[] | .depends_on[]?] as $referenced |
    $graph_entities | map(select(. as $entity | ($referenced | index($entity) | not))) as $orphans |
    reduce $orphans[] as $orphan (.;
        del(.graph[$orphan])
    )
    ' "Remove orphaned entities"
    
    success "Removed $count orphaned entities"
}

add_missing_entities() {
    echo "🟠 ADDING MISSING GRAPH ENTRIES"
    echo "=============================="
    
    local missing
    missing=$(get_missing_entities)
    
    if [[ -z "$missing" ]]; then
        success "All entities have graph entries"
        return 0
    fi
    
    local count=$(echo "$missing" | wc -l | tr -d ' ')
    echo "Found $count missing entities:"
    echo "$missing" | sed 's/^/  - /'
    echo
    
    execute_jq '
    [.entities | .. | objects | select(has("id")) | .id] as $entity_ids |
    (.graph | keys) as $graph_entities |
    ($entity_ids | map(select(. as $entity | $graph_entities | index($entity) | not))) as $missing |
    reduce $missing[] as $entity (.;
        .graph[$entity] = {"depends_on": []}
    )
    ' "Add missing graph entries"
    
    success "Added $count missing graph entries"
}

break_circular_dependencies() {
    echo "🔄 BREAKING CIRCULAR DEPENDENCIES"
    echo "==============================="
    
    local circular
    circular=$(get_circular_dependencies)
    
    if [[ -z "$circular" ]]; then
        success "No circular dependencies found"
        return 0
    fi
    
    local count=$(echo "$circular" | wc -l | tr -d ' ')
    echo "Found $count circular dependencies:"
    echo "$circular" | sed 's/^/  - /'
    echo
    
    # Break cycles by removing the first dependency in each pair
    execute_jq '
    .graph as $g |
    ($g | to_entries[] |
     .key as $entity |
     .value.depends_on[]? as $dep |
     select($g[$dep].depends_on[]? == $entity) |
     [$entity, $dep] | sort) as $cycles |
    reduce $cycles as $cycle (.;
        .graph[$cycle[0]].depends_on = (.graph[$cycle[0]].depends_on | map(select(. != $cycle[1])))
    )
    ' "Break circular dependencies"
    
    success "Broke $count circular dependencies"
}

# Parse command line arguments
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -b|--backup)
            BACKUP_FILE="$2"
            shift 2
            ;;
        --fix-hanging)
            FIX_HANGING=true
            shift
            ;;
        --fix-orphans)
            FIX_ORPHANS=true
            shift
            ;;
        --add-missing)
            ADD_MISSING=true
            shift
            ;;
        --break-cycles)
            BREAK_CYCLES=true
            shift
            ;;
        --fix-all)
            FIX_HANGING=true
            FIX_ORPHANS=true
            ADD_MISSING=true
            BREAK_CYCLES=true
            shift
            ;;
        --report)
            REPORT_ONLY=true
            shift
            ;;
        --)
            shift
            break
            ;;
        -*)
            error "Unknown option: $1"
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

# Restore positional parameters
set -- "${POSITIONAL[@]}"

# Set knowledge map file
if [[ $# -gt 0 ]]; then
    KNOWLEDGE_MAP="$1"
fi

# Validate file exists
if [[ ! -f "$KNOWLEDGE_MAP" ]]; then
    error "Knowledge map file not found: $KNOWLEDGE_MAP"
fi

log "Using knowledge map: $KNOWLEDGE_MAP"

# Show report and exit if requested
if [[ "$REPORT_ONLY" == true ]]; then
    show_report
    exit 0
fi

# If no fix options specified, show report
if [[ "$FIX_HANGING" != true && "$FIX_ORPHANS" != true && "$ADD_MISSING" != true && "$BREAK_CYCLES" != true ]]; then
    echo "No fix options specified. Showing report:"
    echo
    show_report
    echo
    echo "Use --help for available fix options"
    exit 0
fi

# Create backup before making changes
if [[ "$DRY_RUN" != true ]]; then
    create_backup
fi

echo "🔧 DEPENDENCY GRAPH REPAIR TOOL (CLI Mode)"
echo "=========================================="
echo

# Execute fixes in logical order
if [[ "$FIX_HANGING" == true ]]; then
    fix_hanging_references
    echo
fi

if [[ "$ADD_MISSING" == true ]]; then
    add_missing_entities
    echo
fi

if [[ "$BREAK_CYCLES" == true ]]; then
    break_circular_dependencies
    echo
fi

if [[ "$FIX_ORPHANS" == true ]]; then
    fix_orphaned_entities
    echo
fi

if [[ "$DRY_RUN" != true ]]; then
    echo "🎉 REPAIR COMPLETE"
    echo "=================="
    echo "Changes applied to: $KNOWLEDGE_MAP"
    echo "Backup available at: $BACKUP_FILE"
    echo
    echo "Final health check:"
    show_report
fi