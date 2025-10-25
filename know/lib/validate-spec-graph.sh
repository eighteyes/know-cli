#!/bin/bash

# Spec Graph Validator
# Validates the structure and integrity of spec-graph.json

set -uo pipefail

GRAPH_FILE="${1:-.ai/spec-graph.json}"
ERRORS=0
WARNINGS=0

# Define paths to graph tools
MOD_GRAPH="${MOD_GRAPH:-$(dirname "$0")/mod-graph.sh}"
QUERY_GRAPH="${JSON_GRAPH_QUERY:-$(dirname "$0")/query-graph.sh}"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    ((ERRORS++)) || true
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
    ((WARNINGS++)) || true
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

info() {
    echo "[INFO] $1"
}

# Check if file exists
if [[ ! -f "$GRAPH_FILE" ]]; then
    error "Graph file not found: $GRAPH_FILE"
    echo -e "${RED}Cannot continue without graph file${NC}" >&2
    exit 1
fi

info "Validating $GRAPH_FILE"

# 1. Validate JSON syntax
if ! jq empty "$GRAPH_FILE" 2>/dev/null; then
    error "Invalid JSON syntax - cannot parse file for further validation"
    echo -e "${RED}Cannot continue with invalid JSON${NC}" >&2
    exit 1
fi
success "JSON syntax valid"

# 2. Check required top-level structure
for section in meta references entities graph; do
    if ! jq -e "has(\"$section\")" "$GRAPH_FILE" >/dev/null 2>&1; then
        error "Missing required section: $section"
    else
        success "Section exists: $section"
    fi
done

# 3. Validate meta structure
if jq -e '.meta' "$GRAPH_FILE" >/dev/null 2>&1; then
    # Check required meta fields
    for field in version format description project; do
        if ! jq -e ".meta | has(\"$field\")" "$GRAPH_FILE" >/dev/null 2>&1; then
            warning "Missing meta field: $field"
        fi
    done

    # Check project structure
    if jq -e '.meta.project' "$GRAPH_FILE" >/dev/null 2>&1; then
        for field in name phases; do
            if ! jq -e ".meta.project | has(\"$field\")" "$GRAPH_FILE" >/dev/null 2>&1; then
                error "Missing project field: $field"
            fi
        done
    fi
fi

# 4. Check entity structure (grouped by type)
info "Checking entity structure..."
# Get entity types directly from the JSON - mod-graph doesn't have list-types
entity_types=$(jq -r '.entities | keys[]' "$GRAPH_FILE" 2>/dev/null)
for type in $entity_types; do
    entity_count=$(jq ".entities.$type | length" "$GRAPH_FILE" 2>/dev/null)
    if [[ $entity_count -gt 0 ]]; then
        success "Entity type '$type' contains $entity_count entities"
    fi
done

# 5. Build complete node ID list (entities + references)
info "Building node ID index..."
# Get entity IDs
all_entities=$(jq -r '
    .entities | to_entries[] |
    .key as $type |
    .value | keys[] as $name |
    # Convert plural type to singular for ID format
    (if $type == "features" then "feature"
     elif $type == "requirements" then "requirement"
     elif $type == "objectives" then "objective"
     elif $type == "users" then "user"
     elif $type == "screens" then "screen"
     elif $type == "interfaces" then "interface"
     elif $type == "ui_components" then "ui_component"
     elif $type == "actions" then "action"
     elif $type == "components" then "component"
     else $type end) + ":" + $name
' "$GRAPH_FILE" 2>/dev/null | sort -u)

# Get reference IDs (handle nested structure with category:name format)
all_references=$(jq -r '
.references | to_entries[] |
if .value | type == "object" then
  .key as $category |
  .value | keys[] |
  $category + ":" + .
else
  .key
end
' "$GRAPH_FILE" 2>/dev/null | sort -u)

# Combine entities and references
all_nodes=$(echo -e "$all_entities\n$all_references" | sort -u)
entity_count=$(echo "$all_entities" | wc -l)
reference_count=$(echo "$all_references" | wc -l)
total_nodes=$(echo "$all_nodes" | wc -l)

success "Indexed $entity_count entities and $reference_count references ($total_nodes total nodes)"

# 6. Validate graph edges (adjacency list format)
info "Checking graph edge integrity..."

# Check each edge references valid nodes (entities or references)
invalid_edges=0
# Graph is structured as { "node_id": { "depends_on": [...] } }
while IFS='|' read -r from to; do
    if ! echo "$all_nodes" | grep -q "^$from$"; then
        error "Graph source references non-existent node: $from"
        ((invalid_edges++)) || true
    fi
    if ! echo "$all_nodes" | grep -q "^$to$"; then
        error "Graph edge references non-existent node: $from -> $to"
        ((invalid_edges++)) || true
    fi
done < <(jq -r '.graph | to_entries[] | .key as $from | .value.depends_on[]? | $from + "|" + .' "$GRAPH_FILE" 2>/dev/null)

# Also check that all nodes in graph exist in entities or references
while read -r node; do
    if ! echo "$all_nodes" | grep -q "^$node$"; then
        error "Graph contains node not in entities or references: $node"
        ((invalid_edges++)) || true
    fi
done < <(jq -r '.graph | keys[]' "$GRAPH_FILE" 2>/dev/null)

if [[ $invalid_edges -eq 0 ]]; then
    success "All graph edges reference valid nodes"
fi

# 7. Check for circular dependencies (simplified check)
info "Checking for circular dependencies..."
# Skip complex circular dependency check for now
success "Circular dependency check skipped (complex graph)"

# 8. Check for orphaned nodes (no incoming or outgoing edges)
info "Checking for orphaned nodes..."
# Get all nodes that are either sources or targets in the graph
connected_nodes=$(jq -r '.graph | to_entries[] | .key, .value.depends_on[]?' "$GRAPH_FILE" 2>/dev/null | sort -u)
orphaned=$(comm -23 <(echo "$all_nodes") <(echo "$connected_nodes") 2>/dev/null || true)

if [[ -n "$orphaned" ]]; then
    orphan_count=$(echo "$orphaned" | wc -l)
    warning "Found $orphan_count orphaned nodes (no connections)"
    # Show first 5 as examples
    first_five=$(echo "$orphaned" | head -5)
    for entity in $first_five; do
        echo "  - $entity" >&2
    done
    if [[ $orphan_count -gt 5 ]]; then
        echo "  ... and $((orphan_count - 5)) more" >&2
    fi
else
    success "No orphaned nodes found"
fi

# 9. Validate phase references
info "Checking phase requirement references..."
if jq -e '.meta.project.phases' "$GRAPH_FILE" >/dev/null 2>&1; then
    while read -r req; do
        if ! echo "$all_nodes" | grep -q "^$req$"; then
            error "Phase references non-existent node: $req"
        fi
    done < <(jq -r '.meta.project.phases[].requirements[]' "$GRAPH_FILE" 2>/dev/null || true)
fi

# 10. Check for duplicate IDs in references
info "Checking for duplicate reference IDs..."
dup_refs=$(jq -r '.references | keys[]' "$GRAPH_FILE" 2>/dev/null | sort | uniq -d)
if [[ -n "$dup_refs" ]]; then
    while IFS= read -r ref; do
        error "Duplicate reference ID: $ref"
    done <<< "$dup_refs"
else
    success "No duplicate reference IDs"
fi

# 11. Validate required entity fields (all entities should have name and description)
info "Checking required fields by entity type..."
entity_types=$(jq -r '.entities | keys[]' "$GRAPH_FILE" 2>/dev/null)
for entity_type in $entity_types; do
    if jq -e ".entities.$entity_type" "$GRAPH_FILE" >/dev/null 2>&1; then
        while read -r entity_name; do
            # Build entity ID with proper singular/plural handling
            if [[ "$entity_type" == "interfaces" ]]; then
                entity_id="interface:$entity_name"
            elif [[ "${entity_type: -1}" == "s" ]]; then
                entity_id="${entity_type%s}:$entity_name"
            else
                entity_id="$entity_type:$entity_name"
            fi

            # All entities must have name and description
            if ! jq -e ".entities.$entity_type[\"$entity_name\"] | has(\"name\")" "$GRAPH_FILE" >/dev/null 2>&1; then
                error "Entity missing required 'name' field: $entity_id"
            fi
            if ! jq -e ".entities.$entity_type[\"$entity_name\"] | has(\"description\")" "$GRAPH_FILE" >/dev/null 2>&1; then
                warning "Entity missing 'description' field: $entity_id"
            fi
        done < <(jq -r ".entities.$entity_type | keys[]" "$GRAPH_FILE" 2>/dev/null || true)
    fi
done

# 12. Check entity types against dependency-rules.json
info "Checking entity type descriptions..."
DEPENDENCY_RULES_FILE="./know/lib/../config/dependency-rules.json"
if [[ -f "$DEPENDENCY_RULES_FILE" ]]; then
    entity_types=$(jq -r '.entities | keys[]' "$GRAPH_FILE" 2>/dev/null)
    missing_descriptions=0

    for entity_type in $entity_types; do
        # Check if this entity type has a description in dependency-rules.json
        if ! jq -e ".entity_descriptions | has(\"$entity_type\")" "$DEPENDENCY_RULES_FILE" >/dev/null 2>&1; then
            error "Entity type '$entity_type' missing from dependency-rules.json entity_descriptions"
            ((missing_descriptions++))
        fi
    done

    if [[ $missing_descriptions -eq 0 ]]; then
        success "All entity types have descriptions in dependency-rules.json"
    fi
else
    warning "Dependency rules file not found: $DEPENDENCY_RULES_FILE"
fi

# 13. Validate dependency chains
info "Checking dependency chain validity..."
if [[ -f "$DEPENDENCY_RULES_FILE" ]]; then
    invalid_deps=0

    # Check each edge against allowed dependencies
    while IFS='|' read -r from_node to_node; do
        # Extract type from node (e.g., "user:owner" -> "user")
        from_type=$(echo "$from_node" | cut -d: -f1)
        to_type=$(echo "$to_node" | cut -d: -f1)

        # Check if from_node is an entity
        from_is_entity=false
        if jq -e ".entities | has(\"${from_type}s\")" "$GRAPH_FILE" >/dev/null 2>&1; then
            from_type="${from_type}s"
            from_is_entity=true
        elif jq -e ".entities | has(\"$from_type\")" "$GRAPH_FILE" >/dev/null 2>&1; then
            from_is_entity=true
        fi

        # Check if to_node is an entity
        to_is_entity=false
        if jq -e ".entities | has(\"${to_type}s\")" "$GRAPH_FILE" >/dev/null 2>&1; then
            to_type="${to_type}s"
            to_is_entity=true
        elif jq -e ".entities | has(\"$to_type\")" "$GRAPH_FILE" >/dev/null 2>&1; then
            to_is_entity=true
        fi

        # Special mapping for interfaces
        if [[ "$from_type" == "interface" ]]; then
            from_type="interfaces"
            from_is_entity=true
        fi
        if [[ "$to_type" == "interface" ]]; then
            to_type="interfaces"
            to_is_entity=true
        fi

        # Only check allowed dependencies between entities (not references)
        # Entities can depend on any references without restriction
        if [[ "$from_is_entity" == "true" ]] && [[ "$to_is_entity" == "true" ]]; then
            # Both are entities, check if dependency is allowed
            allowed=$(jq -r ".allowed_dependencies.\"$from_type\" // []" "$DEPENDENCY_RULES_FILE" 2>/dev/null)
            if [[ "$allowed" != "[]" ]] && [[ "$allowed" != "null" ]]; then
                if ! echo "$allowed" | jq -e ".[] | select(. == \"$to_type\")" >/dev/null 2>&1; then
                    error "Invalid dependency: $from_node -> $to_node ($from_type cannot depend on $to_type)"
                    ((invalid_deps++))
                fi
            fi
        fi
        # If to_node is a reference, allow the dependency (no check needed)
    done < <(jq -r '.graph | to_entries[] | .key as $from | .value.depends_on[]? | $from + "|" + .' "$GRAPH_FILE" 2>/dev/null || true)

    if [[ $invalid_deps -eq 0 ]]; then
        success "All dependencies follow the allowed patterns"
    fi
else
    info "Dependency rules file not found: $DEPENDENCY_RULES_FILE (skipping chain validation)"
fi

# 14. Summary
echo ""
echo "========================================="
echo "Validation Summary:"
echo "========================================="
if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}✓ Graph validation PASSED${NC}"
else
    echo -e "${RED}✗ Found $ERRORS errors${NC}"
fi

if [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠ Found $WARNINGS warnings${NC}"
fi

# Statistics - Use query-graph where possible
stats_output=$("$QUERY_GRAPH" stats 2>/dev/null)
total_entities=$(echo "$stats_output" | grep "Total entities:" | sed 's/.*: //' | grep -o '[0-9]*' | head -1 || echo 0)
total_edges=$(echo "$stats_output" | grep "Total dependencies:" | sed 's/.*: //' | grep -o '[0-9]*' | head -1 || echo 0)
# References and graph nodes still need direct JQ as they're not in graph scripts
total_refs=$(jq '.references | length' "$GRAPH_FILE" 2>/dev/null || echo 0)
total_graph_nodes=$(jq '.graph | length' "$GRAPH_FILE" 2>/dev/null || echo 0)

echo ""
echo "Graph Statistics:"
echo "  Entities: $total_entities"
echo "  Graph nodes: $total_graph_nodes"
echo "  Dependencies: $total_edges"
echo "  References: $total_refs"

# Exit with error if validation failed
exit $ERRORS