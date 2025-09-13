#!/bin/bash

# backend.sh - Backend delegation to existing graph tools
# Provides a clean interface between know and the core graph scripts

# Path to core scripts
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JSON_GRAPH_QUERY="$LIB_DIR/query-graph.sh"
MOD_GRAPH="$LIB_DIR/mod-graph.sh"

# Ensure backend scripts exist
if [[ ! -f "$JSON_GRAPH_QUERY" ]]; then
    error "Backend script not found: $JSON_GRAPH_QUERY"
fi

if [[ ! -f "$MOD_GRAPH" ]]; then
    error "Backend script not found: $MOD_GRAPH"  
fi

# Dependency analysis - delegates to json-graph-query.sh
show_dependencies() {
    local entity_ref="$1"
    "$JSON_GRAPH_QUERY" deps "$entity_ref"
}

# Impact analysis - delegates to json-graph-query.sh  
show_impact_analysis() {
    local entity_ref="$1"
    "$JSON_GRAPH_QUERY" impact "$entity_ref"
}

# Show user access - delegates to json-graph-query.sh
show_user_access() {
    local user_ref="$1"
    "$JSON_GRAPH_QUERY" user "$user_ref"
}

# Detect circular dependencies - delegates to json-graph-query.sh
detect_cycles() {
    "$JSON_GRAPH_QUERY" cycles
}

# Show graph statistics - delegates to json-graph-query.sh
show_graph_stats() {
    "$JSON_GRAPH_QUERY" stats
}

# Find path between entities - delegates to json-graph-query.sh
find_entity_path() {
    local from="$1"
    local to="$2"
    "$JSON_GRAPH_QUERY" path "$from" "$to"
}

# Entity management - delegates to mod-graph.sh
list_entities() {
    local entity_type="${1:-}"
    "$MOD_GRAPH" list "$entity_type"
}

# Search entities - delegates to mod-graph.sh
search_entities() {
    local search_term="$1"
    local entity_type="${2:-}"
    "$MOD_GRAPH" search "$search_term"
}

# Show entity details - delegates to mod-graph.sh
show_entity_details() {
    local entity_type="$1"
    local entity_id="$2"
    "$MOD_GRAPH" show "$entity_type" "$entity_id"
}

# Get entity types - delegates to mod-graph.sh
get_entity_types() {
    "$MOD_GRAPH" types
}

# Validate graph - delegates to mod-graph.sh
validate_knowledge_map() {
    info "Validating knowledge graph..."
    "$MOD_GRAPH" validate
}

# Show implementation order - analyze dependencies to determine optimal order
show_implementation_order() {
    info "Analyzing implementation order based on dependency chains..."
    
    # Use json-graph-query to get dependency statistics
    echo "📋 Implementation Order Analysis:"
    echo
    
    # Show entities with no dependencies (can be implemented first)
    echo "🟢 Ready to implement (no dependencies):"
    "$JSON_GRAPH_QUERY" stats | grep -A 20 "Most dependent entities:" | tail -n +2 | \
    while read -r line; do
        if [[ "$line" =~ .*:\ 0\ deps ]]; then
            echo "  $line"
        fi
    done
    
    echo
    echo "🟡 Implementation phases (ordered by dependency depth):"
    echo "  Phase 1: Root entities (no dependencies)"
    echo "  Phase 2: Entities depending only on Phase 1"
    echo "  Phase 3: Higher-level integrations"
    echo
    echo "💡 Use 'know deps <entity>' to see specific dependencies"
}

# Generate package for entity (comprehensive spec)
generate_package() {
    local entity_ref="$1"
    local format="${2:-md}"
    local output_file="$3"
    
    local temp_file=$(mktemp)
    
    {
        echo "# Implementation Package: $entity_ref"
        echo
        echo "Generated: $(date)"
        echo
        
        echo "## Entity Details"
        # Parse entity_ref to get type and id
        local entity_type=$(echo "$entity_ref" | cut -d':' -f1)
        local entity_id=$(echo "$entity_ref" | cut -d':' -f2)
        
        # Handle plural to singular mapping for mod-graph
        case "$entity_type" in
            feature) entity_type="features" ;;
            component) entity_type="components" ;;
            screen) entity_type="screens" ;;
            user) entity_type="users" ;;
            platform) entity_type="platforms" ;;
        esac
        
        "$MOD_GRAPH" show "$entity_type" "$entity_id" 2>/dev/null || echo "Entity details not available"
        
        echo
        echo "## Dependencies"
        "$JSON_GRAPH_QUERY" deps "$entity_ref" 2>/dev/null || echo "No dependencies found"
        
        echo
        echo "## Impact Analysis"
        "$JSON_GRAPH_QUERY" impact "$entity_ref" 2>/dev/null || echo "No dependents found"
        
        echo
        echo "## Implementation Notes"
        echo "- Review all dependencies before implementation"
        echo "- Ensure dependent entities are updated after changes"
        echo "- Run validation after implementation: \`know validate\`"
        
    } > "$temp_file"
    
    if [[ -n "$output_file" ]]; then
        mv "$temp_file" "$output_file"
        success "Package generated: $output_file"
    else
        cat "$temp_file"
        rm "$temp_file"
    fi
}

# Generate test scenarios based on entity
generate_test_scenarios() {
    local entity_ref="$1" 
    local format="${2:-md}"
    local output_file="$3"
    
    local temp_file=$(mktemp)
    
    {
        echo "# Test Scenarios: $entity_ref"
        echo
        echo "Generated: $(date)"
        echo
        
        echo "## Dependencies Test"
        echo "Verify all dependencies are available and functional:"
        "$JSON_GRAPH_QUERY" deps "$entity_ref" 2>/dev/null | sed 's/^/- Test: /' || echo "- No dependencies to test"
        
        echo
        echo "## Integration Test"
        echo "Verify entities that depend on this component:"
        "$JSON_GRAPH_QUERY" impact "$entity_ref" 2>/dev/null | sed 's/^/- Integration test with: /' || echo "- No integration tests needed"
        
        echo
        echo "## Validation Tests"
        echo "- Verify entity appears in graph: \`know deps $entity_ref\`"
        echo "- Validate graph integrity: \`know validate\`"
        echo "- Check for circular dependencies: \`know cycles\`"
        
    } > "$temp_file"
    
    if [[ -n "$output_file" ]]; then
        mv "$temp_file" "$output_file" 
        success "Test scenarios generated: $output_file"
    else
        cat "$temp_file"
        rm "$temp_file"
    fi
}

# Preview generation (show what would be generated)
preview_generation() {
    local spec_type="$1"
    local entity_ref="$2"
    
    info "Preview: $spec_type specification for $entity_ref"
    
    echo "📋 This would generate:"
    echo "  - Entity details and metadata"
    echo "  - Dependency analysis"
    echo "  - Impact assessment" 
    echo "  - Implementation guidelines"
    
    case "$spec_type" in
        feature)
            echo "  - Feature acceptance criteria"
            echo "  - User story breakdown"
            ;;
        component)
            echo "  - Component interface specification"
            echo "  - UI component dependencies"
            ;;
        screen)
            echo "  - Screen layout and components"
            echo "  - User access patterns"
            ;;
        package)
            echo "  - Complete implementation package"
            echo "  - Test scenarios"
            ;;
    esac
    
    echo
    echo "💡 Run without 'preview' to generate the actual specification"
}


# Check entity completeness for generation
validate_entity_completeness() {
    local entity_ref="$1"
    local spec_type="$2"
    
    local entity_type=$(echo "$entity_ref" | cut -d':' -f1)
    local entity_id=$(echo "$entity_ref" | cut -d':' -f2)
    
    # Handle plural mapping
    case "$entity_type" in
        feature) entity_type="features" ;;
        component) entity_type="components" ;;
        screen) entity_type="screens" ;;
        user) entity_type="users" ;;
        platform) entity_type="platforms" ;;
    esac
    
    info "Validating completeness for $entity_ref"
    
    # Check if entity exists
    if ! "$MOD_GRAPH" show "$entity_type" "$entity_id" >/dev/null 2>&1; then
        echo "❌ Entity not found: $entity_ref"
        return 1
    fi
    
    # Check if entity has graph entry
    if ! "$JSON_GRAPH_QUERY" deps "$entity_ref" >/dev/null 2>&1; then
        echo "⚠️  No graph entry found for $entity_ref"
    fi
    
    echo "✅ Entity validation passed"
    return 0
}