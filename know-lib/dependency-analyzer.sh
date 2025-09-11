#!/bin/bash

# Dependency Analysis Engine for know CLI
# Leverages patterns from json-graph-query.sh for graph traversal

# Show dependencies for an entity (what it depends on)
show_dependencies() {
    local entity_ref="$1"
    local resolved_ref
    resolved_ref=$(resolve_entity_ref "$entity_ref")
    
    echo "📦 Dependencies for $resolved_ref:"
    echo
    
    # Find direct dependencies from graph relationships
    local deps
    deps=$(jq -r --arg entity "$resolved_ref" '
        .graph[$entity].outbound | to_entries[] |
        select(.key | test("depends_on|uses|requires")) |
        .value[] | select(length > 0)
    ' "$KNOWLEDGE_MAP" 2>/dev/null)
    
    if [[ -z "$deps" ]]; then
        echo "  ✅ No dependencies found"
        return
    fi
    
    echo "$deps" | while IFS= read -r dep; do
        if [[ -n "$dep" ]]; then
            local dep_info
            dep_info=$(get_entity_info "$dep")
            echo "  📋 $dep ($dep_info)"
        fi
    done
    
    echo
    echo "🔍 Transitive Dependencies:"
    
    # Find transitive dependencies using jq recursion
    jq -r --arg entity "$resolved_ref" '
        def find_deps($e; $visited):
            if $visited | has($e) then empty
            else
                (.graph[$e].outbound | to_entries[] | 
                 select(.key | test("depends_on|uses|requires")) | 
                 .value[]?) as $dep |
                if $dep then
                    $dep, find_deps($dep; $visited + {($e): true})
                else
                    empty
                end
            end;
        
        [find_deps($entity; {})] | unique | .[]
    ' "$KNOWLEDGE_MAP" 2>/dev/null | while IFS= read -r dep; do
        if [[ -n "$dep" && "$dep" != "$resolved_ref" ]]; then
            local dep_info
            dep_info=$(get_entity_info "$dep")
            echo "  🔗 $dep ($dep_info)"
        fi
    done
}

# Show impact analysis (what depends on this entity)
show_impact() {
    local entity_ref="$1"
    local resolved_ref
    resolved_ref=$(resolve_entity_ref "$entity_ref")
    
    echo "💥 Impact Analysis for $resolved_ref:"
    echo "   (Entities that would be affected by changes to this entity)"
    echo
    
    # Find direct dependents
    local dependents
    dependents=$(jq -r --arg entity "$resolved_ref" '
        .graph | to_entries[] |
        select(.value.outbound | to_entries[] | 
               select(.key | test("depends_on|uses|requires")) | 
               .value[] == $entity) |
        .key
    ' "$KNOWLEDGE_MAP" 2>/dev/null)
    
    if [[ -z "$dependents" ]]; then
        echo "  ✅ No direct dependents found"
    else
        echo "📌 Direct Impact:"
        echo "$dependents" | while IFS= read -r dependent; do
            if [[ -n "$dependent" ]]; then
                local dep_info
                dep_info=$(get_entity_info "$dependent")
                echo "  ⚡ $dependent ($dep_info)"
            fi
        done
    fi
    
    echo
    echo "🌊 Transitive Impact:"
    
    # Find transitive impact using jq recursion
    jq -r --arg entity "$resolved_ref" '
        def find_impact($e; $visited):
            if $visited | has($e) then empty
            else
                (.graph | to_entries[] |
                 select(.value.outbound | to_entries[] | 
                        select(.key | test("depends_on|uses|requires")) |
                        .value[] == $e) | .key) as $dependent |
                if $dependent then
                    $dependent, find_impact($dependent; $visited + {($e): true})
                else
                    empty
                end
            end;
        
        [find_impact($entity; {})] | unique | .[]
    ' "$KNOWLEDGE_MAP" 2>/dev/null | while IFS= read -r impact; do
        if [[ -n "$impact" && "$impact" != "$resolved_ref" ]]; then
            local impact_info
            impact_info=$(get_entity_info "$impact")
            echo "  🔗 $impact ($impact_info)"
        fi
    done
}

# Get entity basic info (type and name)
get_entity_info() {
    local entity_ref="$1"
    
    # Parse entity reference
    if [[ "$entity_ref" =~ ^([a-z_]+):(.+)$ ]]; then
        local type="${BASH_REMATCH[1]}"
        local id="${BASH_REMATCH[2]}"
        
        local name
        name=$(jq -r --arg type "$type" --arg id "$id" '
            .entities[$type][$id].name // "Unknown"
        ' "$KNOWLEDGE_MAP" 2>/dev/null)
        
        echo "$type: $name"
    else
        echo "unknown: $entity_ref"
    fi
}

# Show implementation depth analysis
show_implementation_depth() {
    local entity_ref="$1"
    local resolved_ref
    resolved_ref=$(resolve_entity_ref "$entity_ref")
    
    echo "🏗️  Implementation Depth Analysis for $resolved_ref:"
    echo
    
    # Calculate depth by counting dependency layers
    local depth
    depth=$(jq -r --arg entity "$resolved_ref" '
        def calc_depth($e; $visited):
            if $visited | has($e) then 0
            else
                [(.graph[$e].outbound | to_entries[] | 
                  select(.key | test("depends_on|uses|requires")) | 
                  .value[]?) as $dep |
                  if $dep then calc_depth($dep; $visited + {($e): true}) + 1 else 0 end] |
                if length > 0 then max else 0 end
            end;
        
        calc_depth($entity; {})
    ' "$KNOWLEDGE_MAP" 2>/dev/null)
    
    echo "  📏 Implementation Depth: $depth"
    
    case $depth in
        0) echo "  ✅ Foundation Layer - Can be implemented first" ;;
        1) echo "  🟡 Core Feature Layer - Implement after foundation" ;;
        2) echo "  🟠 Platform Layer - Implement after core features" ;;
        *) echo "  🔴 Advanced Layer - Implement last" ;;
    esac
    
    echo
    echo "📊 Dependency Breakdown:"
    
    # Show dependencies by relationship type
    jq -r --arg entity "$resolved_ref" '
        .graph[$entity].outbound | to_entries[] |
        select(.value | length > 0) |
        "  \(.key): \(.value | length) entities"
    ' "$KNOWLEDGE_MAP" 2>/dev/null || echo "  No dependencies found"
}

# Find circular dependencies involving this entity
check_circular_dependencies() {
    local entity_ref="$1"
    local resolved_ref
    resolved_ref=$(resolve_entity_ref "$entity_ref")
    
    echo "🔄 Checking for circular dependencies involving $resolved_ref:"
    echo
    
    local has_cycle
    has_cycle=$(jq -r --arg entity "$resolved_ref" '
        def has_cycle($start; $current; $visited):
            if $visited | has($current) then
                if $current == $start then true else false end
            else
                (.graph[$current].outbound | to_entries[] | 
                 select(.key | test("depends_on|uses|requires")) | 
                 .value[]?) as $next |
                if $next then has_cycle($start; $next; $visited + {($current): true}) else false end
            end;
        
        has_cycle($entity; $entity; {})
    ' "$KNOWLEDGE_MAP" 2>/dev/null)
    
    if [[ "$has_cycle" == "true" ]]; then
        echo "  ⚠️  Circular dependency detected!"
        echo "  🔁 This entity is part of a dependency cycle"
        
        # Try to trace the cycle
        echo
        echo "🔍 Attempting to trace cycle path:"
        show_dependencies "$entity_ref" | grep -E "📋|🔗" | head -10
    else
        echo "  ✅ No circular dependencies found"
    fi
}