#!/bin/bash

# Component Map Tool - Maps components to interfaces through feature dependencies
set -e

GRAPH_FILE="${KNOWLEDGE_MAP:-./.ai/spec-graph.json}"

# Display options
VERBOSE=false
NAME_ONLY=false
ID_ONLY=false

show_help() {
    echo "Component Map Tool - Shows which components are used by which interfaces"
    echo ""
    echo "USAGE:"
    echo "  $0 [OPTIONS] <command> [args...]"
    echo ""
    echo "OPTIONS:"
    echo "  --file, -f <file>    Use specified graph file (default: .ai/spec-graph.json)"
    echo "  -v, --verbose        Show full dependency paths"
    echo "  --name-only          Display only entity names"
    echo "  --id-only            Display only entity IDs"
    echo ""
    echo "COMMANDS:"
    echo "  interfaces           - List all interfaces with their components"
    echo "  components           - List all components with their interfaces"
    echo "  interface [id]       - Show components for specific interface (or all if no id)"
    echo "  component [id]       - Show interfaces using specific component (or all if no id)"
    echo "  stats                - Show component usage statistics"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 interfaces                         # List all interfaces with components"
    echo "  $0 interface                          # Same as 'interfaces'"
    echo "  $0 interface fleet-dashboard          # Show specific interface's components"
    echo "  $0 -v interface fleet-dashboard       # Show with full dependency paths"
    echo "  $0 --name-only component              # List all components (names only)"
    echo "  $0 --id-only component websocket-mgr  # Show specific component (ID only)"
    echo "  $0 -v stats                           # Show detailed statistics"
}

# Format entity display based on options
format_entity() {
    local entity_ref="$1"  # e.g., "component:websocket-manager"
    local entity_type="${entity_ref%%:*}"
    local entity_id="${entity_ref#*:}"

    # Get entity details based on type
    local plural_type=""
    case "$entity_type" in
        "interface") plural_type="interfaces" ;;
        "component") plural_type="components" ;;
        "feature") plural_type="features" ;;
        "action") plural_type="actions" ;;
        *) plural_type="${entity_type}s" ;;
    esac

    local entity_name=$(jq -r --arg type "$plural_type" --arg id "$entity_id" \
        '.entities[$type][$id].name // $id' "$GRAPH_FILE" 2>/dev/null)

    if [[ "$ID_ONLY" == "true" ]]; then
        echo "$entity_id"
    elif [[ "$NAME_ONLY" == "true" ]]; then
        echo "$entity_name"
    else
        # Default format: Full Name (id-name)
        echo "$entity_name ($entity_id)"
    fi
}

# Get all components used by an interface (through features)
get_interface_components() {
    local interface="$1"
    local return_paths="${2:-false}"

    # Get features that the interface depends on
    local features=$(jq -r --arg interface "interface:$interface" '
        .graph[$interface].depends_on[]? |
        select(startswith("feature:"))
    ' "$GRAPH_FILE" 2>/dev/null)

    local components=()
    local component_paths=()

    # For each feature, get its components
    while IFS= read -r feature; do
        if [[ -n "$feature" ]]; then
            local feature_id="${feature#feature:}"
            local feature_name=$(jq -r --arg id "$feature_id" '.entities.features[$id].name // $id' "$GRAPH_FILE")

            # Get components that this feature depends on
            local feature_components=$(jq -r --arg feature "$feature" '
                .graph[$feature].depends_on[]? |
                select(startswith("component:"))
            ' "$GRAPH_FILE" 2>/dev/null)

            while IFS= read -r component; do
                if [[ -n "$component" ]]; then
                    components+=("$component")
                    if [[ "$return_paths" == "true" ]]; then
                        # Store full path with names
                        local comp_id="${component#component:}"
                        local comp_name=$(jq -r --arg id "$comp_id" '.entities.components[$id].name // $id' "$GRAPH_FILE")
                        local int_name=$(jq -r --arg id "$interface" '.entities.interfaces[$id].name // $id' "$GRAPH_FILE")
                        component_paths+=("$int_name ($interface)|$feature_name ($feature_id)|$comp_name ($comp_id)")
                    fi
                fi
            done <<< "$feature_components"
        fi
    done <<< "$features"

    # Return results
    if [[ "$return_paths" == "true" ]]; then
        printf "%s\n" "${component_paths[@]}"
    else
        printf "%s\n" "${components[@]}" | sort -u
    fi
}

# Get all interfaces that use a component (through features)
get_component_interfaces() {
    local component="$1"
    local return_paths="${2:-false}"

    # Find features that depend on this component
    local features=$(jq -r --arg component "component:$component" '
        .graph | to_entries[] |
        select(.value.depends_on[]? == $component) |
        select(.key | startswith("feature:")) |
        .key
    ' "$GRAPH_FILE" 2>/dev/null)

    local interfaces=()
    local interface_paths=()

    # For each feature, find interfaces that depend on it
    while IFS= read -r feature; do
        if [[ -n "$feature" ]]; then
            local feature_id="${feature#feature:}"
            local feature_name=$(jq -r --arg id "$feature_id" '.entities.features[$id].name // $id' "$GRAPH_FILE")

            # Find interfaces that depend on this feature
            local feature_interfaces=$(jq -r --arg feature "$feature" '
                .graph | to_entries[] |
                select(.value.depends_on[]? == $feature) |
                select(.key | startswith("interface:")) |
                .key
            ' "$GRAPH_FILE" 2>/dev/null)

            while IFS= read -r interface; do
                if [[ -n "$interface" ]]; then
                    interfaces+=("$interface")
                    if [[ "$return_paths" == "true" ]]; then
                        # Store full path with names
                        local int_id="${interface#interface:}"
                        local int_name=$(jq -r --arg id "$int_id" '.entities.interfaces[$id].name // $id' "$GRAPH_FILE")
                        local comp_name=$(jq -r --arg id "$component" '.entities.components[$id].name // $id' "$GRAPH_FILE")
                        interface_paths+=("$int_name ($int_id)|$feature_name ($feature_id)|$comp_name ($component)")
                    fi
                fi
            done <<< "$feature_interfaces"
        fi
    done <<< "$features"

    # Return results
    if [[ "$return_paths" == "true" ]]; then
        printf "%s\n" "${interface_paths[@]}"
    else
        printf "%s\n" "${interfaces[@]}" | sort -u
    fi
}

# List all interfaces with their components
list_interfaces() {
    echo "🖥️  Interface Component Map:"
    echo ""

    # Get all interfaces
    local interfaces=$(jq -r '.entities.interfaces | keys[]' "$GRAPH_FILE" 2>/dev/null)

    while IFS= read -r interface; do
        if [[ -n "$interface" ]]; then
            echo "📋 $(format_entity "interface:$interface")"

            if [[ "$VERBOSE" == "true" ]]; then
                # Show full paths
                local paths=$(get_interface_components "$interface" "true")
                if [[ -z "$paths" ]]; then
                    echo "  ⚠️  No components found"
                else
                    while IFS= read -r path; do
                        if [[ -n "$path" ]]; then
                            # Split path and display with arrows
                            IFS='|' read -r int feat comp <<< "$path"
                            echo "  └─ $int → $feat → $comp"
                        fi
                    done <<< "$paths"
                fi
            else
                # Show just components
                local components=$(get_interface_components "$interface")
                if [[ -z "$components" ]]; then
                    echo "  ⚠️  No components found"
                else
                    while IFS= read -r component; do
                        if [[ -n "$component" ]]; then
                            echo "  └─ $(format_entity "$component")"
                        fi
                    done <<< "$components"
                fi
            fi
            echo ""
        fi
    done <<< "$interfaces"
}

# List all components with their interfaces
list_components() {
    echo "🔧 Component Interface Map:"
    echo ""

    # Get all components
    local components=$(jq -r '.entities.components | keys[]' "$GRAPH_FILE" 2>/dev/null)

    while IFS= read -r component; do
        if [[ -n "$component" ]]; then
            echo "⚙️  $(format_entity "component:$component")"

            if [[ "$VERBOSE" == "true" ]]; then
                # Show full paths
                local paths=$(get_component_interfaces "$component" "true")
                if [[ -z "$paths" ]]; then
                    echo "  ⚠️  Not used by any interface"
                else
                    while IFS= read -r path; do
                        if [[ -n "$path" ]]; then
                            # Split path and display with arrows
                            IFS='|' read -r int feat comp <<< "$path"
                            echo "  └─ $int → $feat → $comp"
                        fi
                    done <<< "$paths"
                fi
            else
                # Show just interfaces
                local interfaces=$(get_component_interfaces "$component")
                if [[ -z "$interfaces" ]]; then
                    echo "  ⚠️  Not used by any interface"
                else
                    while IFS= read -r interface; do
                        if [[ -n "$interface" ]]; then
                            echo "  └─ $(format_entity "$interface")"
                        fi
                    done <<< "$interfaces"
                fi
            fi
            echo ""
        fi
    done <<< "$components"
}

# Show components for a specific interface
show_interface_components() {
    local interface="$1"

    # Check if interface exists
    if ! jq -e --arg id "$interface" '.entities.interfaces | has($id)' "$GRAPH_FILE" > /dev/null 2>&1; then
        echo "❌ Interface not found: $interface"
        exit 1
    fi

    echo "📋 Components for $(format_entity "interface:$interface"):"
    echo ""

    if [[ "$VERBOSE" == "true" ]]; then
        # Show with full paths
        local paths=$(get_interface_components "$interface" "true")

        if [[ -z "$paths" ]]; then
            echo "  ⚠️  No components found"
        else
            while IFS= read -r path; do
                if [[ -n "$path" ]]; then
                    # Split path and display with arrows
                    IFS='|' read -r int feat comp <<< "$path"
                    echo "  🔗 Path: $int → $feat → $comp"

                    # Extract component details
                    local comp_id=$(echo "$comp" | sed 's/.*(\(.*\))/\1/')
                    local comp_type=$(jq -r --arg id "$comp_id" '.entities.components[$id].type // ""' "$GRAPH_FILE")
                    [[ -n "$comp_type" ]] && echo "     Type: $comp_type"
                    echo ""
                fi
            done <<< "$paths"
        fi
    else
        # Simple component list
        local components=$(get_interface_components "$interface")

        if [[ -z "$components" ]]; then
            echo "  ⚠️  No components found"
        else
            while IFS= read -r component; do
                if [[ -n "$component" ]]; then
                    echo "  └─ $(format_entity "$component")"
                fi
            done <<< "$components"
        fi
    fi
}

# Show interfaces for a specific component
show_component_interfaces() {
    local component="$1"

    # Check if component exists
    if ! jq -e --arg id "$component" '.entities.components | has($id)' "$GRAPH_FILE" > /dev/null 2>&1; then
        echo "❌ Component not found: $component"
        exit 1
    fi

    echo "⚙️  Interfaces using $(format_entity "component:$component"):"
    echo ""

    if [[ "$VERBOSE" == "true" ]]; then
        # Show with full paths
        local paths=$(get_component_interfaces "$component" "true")

        if [[ -z "$paths" ]]; then
            echo "  ⚠️  Not used by any interface"
        else
            while IFS= read -r path; do
                if [[ -n "$path" ]]; then
                    # Split path and display with arrows
                    IFS='|' read -r int feat comp <<< "$path"
                    echo "  🔗 Path: $int → $feat → $comp"

                    # Extract interface details
                    local int_id=$(echo "$int" | sed 's/.*(\(.*\))/\1/')
                    local int_type=$(jq -r --arg id "$int_id" '.entities.interfaces[$id].type // ""' "$GRAPH_FILE")
                    [[ -n "$int_type" ]] && echo "     Type: $int_type"
                    echo ""
                fi
            done <<< "$paths"
        fi
    else
        # Simple interface list
        local interfaces=$(get_component_interfaces "$component")

        if [[ -z "$interfaces" ]]; then
            echo "  ⚠️  Not used by any interface"
        else
            while IFS= read -r interface; do
                if [[ -n "$interface" ]]; then
                    echo "  └─ $(format_entity "$interface")"
                fi
            done <<< "$interfaces"
        fi
    fi
}

# Show usage statistics
show_stats() {
    echo "📊 Component Usage Statistics:"
    echo ""

    # Total counts
    local total_interfaces=$(jq '.entities.interfaces | length' "$GRAPH_FILE")
    local total_components=$(jq '.entities.components | length' "$GRAPH_FILE")

    echo "  📈 Total interfaces: $total_interfaces"
    echo "  🔧 Total components: $total_components"
    echo ""

    # Most used components
    echo "  🏆 Most used components:"

    # Build usage count for each component
    declare -A component_usage

    local components=$(jq -r '.entities.components | keys[]' "$GRAPH_FILE" 2>/dev/null)
    while IFS= read -r component; do
        if [[ -n "$component" ]]; then
            local count=$(get_component_interfaces "$component" | grep -c "interface:" || true)
            if [[ $count -gt 0 ]]; then
                component_usage["$component"]=$count
            fi
        fi
    done <<< "$components"

    # Sort and display top 5
    for comp in "${!component_usage[@]}"; do
        echo "${component_usage[$comp]} $comp"
    done | sort -rn | head -5 | while read count comp; do
        echo "    $(format_entity "component:$comp"): used by $count interfaces"
    done

    echo ""

    # Unused components
    echo "  ⚠️  Unused components:"
    local unused_count=0
    while IFS= read -r component; do
        if [[ -n "$component" ]]; then
            local interfaces=$(get_component_interfaces "$component")
            if [[ -z "$interfaces" ]]; then
                echo "    $(format_entity "component:$component")"
                ((unused_count++))
            fi
        fi
    done <<< "$components"

    if [[ $unused_count -eq 0 ]]; then
        echo "    ✅ All components are in use"
    fi

    echo ""

    # Interfaces without components
    echo "  📋 Interfaces without components:"
    local interfaces=$(jq -r '.entities.interfaces | keys[]' "$GRAPH_FILE" 2>/dev/null)
    local no_comp_count=0

    while IFS= read -r interface; do
        if [[ -n "$interface" ]]; then
            local components=$(get_interface_components "$interface")
            if [[ -z "$components" ]]; then
                echo "    $(format_entity "interface:$interface")"
                ((no_comp_count++))
            fi
        fi
    done <<< "$interfaces"

    if [[ $no_comp_count -eq 0 ]]; then
        echo "    ✅ All interfaces have components"
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        echo ""
        echo "  📊 Component sharing analysis:"

        # Find components used by multiple interfaces
        declare -A shared_components

        while IFS= read -r component; do
            if [[ -n "$component" ]]; then
                local interface_list=$(get_component_interfaces "$component")
                local count=$(echo "$interface_list" | grep -c "interface:" || true)
                if [[ $count -gt 1 ]]; then
                    echo ""
                    echo "    🔄 $(format_entity "component:$component") is shared by:"
                    echo "$interface_list" | while IFS= read -r interface; do
                        if [[ -n "$interface" ]]; then
                            echo "       - $(format_entity "$interface")"
                        fi
                    done
                fi
            fi
        done <<< "$components"
    fi
}

# Parse command line options
while [[ $# -gt 0 ]]; do
    case $1 in
        --file|-f)
            GRAPH_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --name-only)
            NAME_ONLY=true
            shift
            ;;
        --id-only)
            ID_ONLY=true
            shift
            ;;
        -h|--help|help)
            show_help
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

# Check for conflicting options
if [[ "$NAME_ONLY" == "true" && "$ID_ONLY" == "true" ]]; then
    echo "❌ Error: --name-only and --id-only cannot be used together"
    exit 1
fi

# Check if file exists
if [[ ! -f "$GRAPH_FILE" ]]; then
    echo "❌ Graph file not found: $GRAPH_FILE"
    exit 1
fi

# Main command processing
case "${1:-}" in
    "interfaces")
        list_interfaces
        ;;
    "components")
        list_components
        ;;
    "interface")
        if [[ $# -lt 2 ]]; then
            # No ID provided, list all interfaces
            list_interfaces
        else
            show_interface_components "$2"
        fi
        ;;
    "component")
        if [[ $# -lt 2 ]]; then
            # No ID provided, list all components
            list_components
        else
            show_component_interfaces "$2"
        fi
        ;;
    "stats")
        show_stats
        ;;
    "")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac