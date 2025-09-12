#!/bin/bash

# render.sh - Template rendering engine with Handlebars-style variables

# Render template with data
render_template() {
    local template_file="$1"
    local entity_ref="$2"
    local format="$3"
    
    if [[ ! -f "$template_file" ]]; then
        error "Template not found: $template_file"
    fi
    
    local template_content
    template_content=$(cat "$template_file")
    
    # Get entity data and all related data
    local entity_data
    entity_data=$(get_entity "$entity_ref")
    
    local acceptance_criteria
    acceptance_criteria=$(get_acceptance_criteria "$entity_ref")
    
    local outbound_rels
    outbound_rels=$(get_outbound_relationships "$entity_ref")
    
    local inbound_rels
    inbound_rels=$(get_inbound_relationships "$entity_ref")
    
    local technical_specs
    technical_specs=$(get_technical_specs "$entity_ref")
    
    local ui_specs
    ui_specs=$(get_ui_specs)
    
    local libraries
    libraries=$(get_libraries)
    
    local protocols
    protocols=$(get_protocols)
    
    local endpoints
    endpoints=$(get_endpoints)
    
    # Get project metadata
    local meta_data
    meta_data=$(jq '.meta // {}' "$KNOWLEDGE_MAP")
    
    # Get all references  
    local all_references
    all_references=$(jq '.references // {}' "$KNOWLEDGE_MAP")
    
    # Build complete context object
    local context
    context=$(jq -n \
        --argjson entity "$entity_data" \
        --argjson acceptance_criteria "$acceptance_criteria" \
        --argjson outbound "$outbound_rels" \
        --argjson inbound "$inbound_rels" \
        --argjson references "$all_references" \
        --argjson meta "$meta_data" \
        --arg entity_ref "$entity_ref" \
        '{
            entity: $entity,
            entity_ref: $entity_ref,
            acceptance_criteria: $acceptance_criteria,
            graph: {
                outbound: $outbound,
                inbound: $inbound
            },
            references: $references,
            meta: $meta
        }')
    
    # Substitute variables
    local rendered_content
    rendered_content=$(substitute_variables "$template_content" "$context")
    
    echo "$rendered_content"
}

# Substitute Handlebars-style variables {{variable}} and {{#each array}} blocks
substitute_variables() {
    local content="$1"
    local context="$2"
    
    # Handle {{#each}} blocks
    content=$(process_each_blocks "$content" "$context")
    
    # Finally handle simple {{variable}} substitutions
    content=$(process_simple_variables "$content" "$context")
    
    echo "$content"
}

# Process {{#if condition}} conditional blocks
process_if_blocks() {
    local content="$1"
    local context="$2"
    
    # Use a simpler approach to find if blocks without nesting issues
    local temp_content="$content"
    local line_num=1
    
    # Split content by lines to avoid regex greediness issues  
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Check if line contains {{#if condition}}
        if [[ "$line" =~ \{\{#if[[:space:]]+([^}]+)\}\} ]]; then
            local condition_path="${BASH_REMATCH[1]}"
            local if_tag="{{#if $condition_path}}"
            local endif_tag="{{/if}}"
            
            debug "Processing if condition: $condition_path"
            
            # Get condition value
            local condition_value
            condition_value=$(echo "$context" | jq -r --arg path "$condition_path" '
                getpath($path | split(".")) // null
            ' 2>/dev/null || echo "null")
            
            # Check if condition is truthy
            local is_truthy=false
            if [[ "$condition_value" != "null" && "$condition_value" != "" && "$condition_value" != "false" ]]; then
                # Check if it's an empty array or object
                if [[ "$condition_value" == "[]" || "$condition_value" == "{}" ]]; then
                    is_truthy=false
                else
                    is_truthy=true
                fi
            fi
            
            debug "Condition '$condition_path' is truthy: $is_truthy"
            
            # If condition is false, mark this if block for removal
            if [[ "$is_truthy" == "false" ]]; then
                # Replace the {{#if}} line with a removal marker
                content="${content//"$line"/REMOVE_IF_BLOCK_START_$condition_path}"
            else
                # Replace the {{#if}} line with empty (keep content inside)
                content="${content//"$line"/}"
            fi
        fi
        
        # Check if line contains {{/if}}
        if [[ "$line" =~ \{\{/if\}\} ]]; then
            content="${content//"$line"/REMOVE_IF_BLOCK_END}"
        fi
    done <<< "$content"
    
    # Now remove blocks marked for removal
    while [[ "$content" =~ REMOVE_IF_BLOCK_START_([^[:space:]]+)(.*?)REMOVE_IF_BLOCK_END ]]; do
        local condition_name="${BASH_REMATCH[1]}"
        local block_content="${BASH_REMATCH[2]}"
        local full_match="${BASH_REMATCH[0]}"
        
        # Remove the entire block
        content="${content//"$full_match"/}"
    done
    
    echo "$content"
}

# Process {{#each array}} blocks
process_each_blocks() {
    local content="$1"
    local context="$2"
    
    # Find all {{#each}} blocks - match variable name until closing }}
    while [[ "$content" =~ \{\{#each[[:space:]]+([^}]+)\}\}(.*?)\{\{/each\}\} ]]; do
        local array_path="${BASH_REMATCH[1]}"
        local block_content="${BASH_REMATCH[2]}"
        local full_match="${BASH_REMATCH[0]}"
        
        echo "DEBUG: Processing each block for: $array_path" >&2
        echo "DEBUG: Block content: $block_content" >&2
        
        # Get array data
        local array_data
        array_data=$(echo "$context" | jq -r --arg path "$array_path" '
            getpath($path | split(".")) // []
        ' 2>/dev/null || echo "[]")
        
        # Process each item in array
        local rendered_items=""
        if [[ "$array_data" != "[]" && "$array_data" != "null" ]]; then
            while IFS= read -r item; do
                if [[ -n "$item" && "$item" != "null" ]]; then
                    # Replace {{this}} with current item
                    local item_content="${block_content//\{\{this\}\}/$item}"
                    rendered_items+="$item_content"$'\n'
                fi
            done < <(echo "$array_data" | jq -r '.[]?' 2>/dev/null || true)
        fi
        
        # Replace the entire {{#each}} block with rendered items
        content="${content//"$full_match"/$rendered_items}"
    done
    
    echo "$content"
}

# Process simple {{variable}} substitutions with smart handling
process_simple_variables() {
    local content="$1"
    local context="$2"
    
    # Find all {{variable}} patterns (excluding #each, /each, /if)
    local variables
    variables=$(echo "$content" | grep -o '{{[^#/][^}]*}}' | sort -u || true)
    
    while IFS= read -r var_pattern; do
        if [[ -n "$var_pattern" ]]; then
            # Extract variable path
            local var_path="${var_pattern#\{\{}"
            var_path="${var_path%\}\}}"
            var_path=$(echo "$var_path" | xargs) # trim whitespace
            
            debug "Processing variable: $var_path"
            
            # Get value from context
            local value
            value=$(echo "$context" | jq -r --arg path "$var_path" '
                getpath($path | split(".")) // null
            ' 2>/dev/null)
            
            # Smart handling of missing/empty values
            if [[ "$value" == "null" || -z "$value" ]]; then
                case "$var_path" in
                    *.priority)
                        value="⚠️ NO PRIORITY SET"
                        ;;
                    *.status)
                        value="⚠️ STATUS UNKNOWN"
                        ;;
                    *.name)
                        value="⚠️ UNNAMED"
                        ;;
                    *.description*|*resolved_description*)
                        value="⚠️ NO DESCRIPTION PROVIDED"
                        ;;
                    references.*)
                        value="⚠️ NOT CONFIGURED"
                        ;;
                    *)
                        value="⚠️ MISSING: $var_path"
                        ;;
                esac
            fi
            
            # Replace all occurrences
            content="${content//"$var_pattern"/$value}"
        fi
    done < <(echo "$variables")
    
    echo "$content"
}

# Format acceptance criteria as markdown checkboxes
format_acceptance_criteria() {
    local criteria_json="$1"
    
    if [[ "$criteria_json" == "{}" || "$criteria_json" == "null" ]]; then
        echo "No acceptance criteria defined"
        return
    fi
    
    echo "$criteria_json" | jq -r '
        to_entries[] |
        "### " + (.key | ascii_upcase) + " Requirements\n" +
        (.value | map("- [ ] " + .) | join("\n"))
    ' | sed '/^$/d'
}

# Format dependency list
format_dependencies() {
    local deps_array="$1"
    local context="$2"
    
    if [[ "$deps_array" == "[]" || "$deps_array" == "null" ]]; then
        echo "No dependencies"
        return
    fi
    
    echo "$deps_array" | jq -r '.[]' | while IFS= read -r dep; do
        if [[ -n "$dep" ]]; then
            local dep_name
            dep_name=$(get_entity_name "$dep" 2>/dev/null || echo "Unknown")
            echo "- **$dep**: $dep_name"
        fi
    done
}

# Format relationship list with names
format_relationships() {
    local rels_json="$1"
    local rel_type="$2"
    
    if [[ "$rels_json" == "{}" || "$rels_json" == "null" ]]; then
        echo "None"
        return
    fi
    
    echo "$rels_json" | jq -r --arg type "$rel_type" '.[$type][]?' 2>/dev/null | while IFS= read -r rel; do
        if [[ -n "$rel" ]]; then
            local rel_name
            rel_name=$(get_entity_name "$rel" 2>/dev/null || echo "Unknown")
            echo "- $rel ($rel_name)"
        fi
    done
}

# Generate package specifications (multiple related entities)
generate_package() {
    local entity_ref="$1"
    local format="$2"
    local output_file="$3"
    
    info "Generating implementation package for $entity_ref"
    
    # For now, generate the main entity spec plus dependencies
    local main_spec
    main_spec=$(determine_spec_type "$entity_ref")
    
    echo "# Implementation Package: $(get_entity_name "$entity_ref")"
    echo
    echo "## Main Entity Specification"
    echo
    
    # Generate main spec
    generate_spec "$main_spec" "$entity_ref" "$format" ""
    
    echo
    echo "## Dependencies"
    echo
    
    # Show dependency specifications
    get_dependencies "$entity_ref" | while IFS= read -r dep; do
        if [[ -n "$dep" ]]; then
            local dep_spec_type
            dep_spec_type=$(determine_spec_type "$dep")
            local dep_name
            dep_name=$(get_entity_name "$dep")
            
            echo "### $dep ($dep_name)"
            echo
            generate_spec "$dep_spec_type" "$dep" "$format" "" | sed 's/^/    /'
            echo
        fi
    done
}

# Determine specification type from entity reference
determine_spec_type() {
    local entity_ref="$1"
    local type_id
    type_id=$(parse_entity_ref "$entity_ref")
    local type=$(echo "$type_id" | cut -d' ' -f1)
    
    case "$type" in
        features) echo "feature" ;;
        components) echo "component" ;;
        screens) echo "screen" ;;
        functionality) echo "functionality" ;;
        requirements) echo "requirement" ;;
        schema) echo "api" ;;
        *) echo "feature" ;; # default
    esac
}

# Generate test scenarios from acceptance criteria
generate_test_scenarios() {
    local entity_ref="$1"
    local format="$2"
    local output_file="$3"
    
    local entity_name
    entity_name=$(get_entity_name "$entity_ref")
    
    local acceptance_criteria
    acceptance_criteria=$(get_acceptance_criteria "$entity_ref")
    
    echo "# Test Scenarios: $entity_name"
    echo
    echo "## Overview"
    echo "Test scenarios generated from acceptance criteria for $entity_ref"
    echo
    
    if [[ "$acceptance_criteria" == "{}" ]]; then
        echo "No acceptance criteria found - cannot generate test scenarios"
        return
    fi
    
    echo "$acceptance_criteria" | jq -r '
        to_entries[] |
        "## " + (.key | ascii_upcase) + " Tests\n" +
        (.value | to_entries | map(
            "### Test: " + (.key + 1 | tostring) + " - " + .value + "\n" +
            "```gherkin\n" +
            "Scenario: " + .value + "\n" +
            "  Given the system is operational\n" +
            "  When the feature is tested\n" +
            "  Then " + .value + "\n" +
            "```\n"
        ) | join("\n"))
    '
}