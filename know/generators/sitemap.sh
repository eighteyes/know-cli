#!/bin/bash

# Generate sitemap from spec-graph.json with proper screen-interface mapping
GRAPH_FILE="${1:-.ai/spec-graph.json}"

if [ ! -f "$GRAPH_FILE" ]; then
    echo "Error: Graph file not found: $GRAPH_FILE"
    exit 1
fi

echo "🗺️  Sitemap with Component Mapping"
echo "============================================"
echo

# Build a complete mapping of screens to interfaces
jq -r '
    # Get all screens with their URLs
    .references.screens | to_entries | .[] | 
    .key + "|" + .value.url + "|" + .value.name
' "$GRAPH_FILE" | sort -t'|' -k2 |
while IFS='|' read -r screen_id url name; do
    # Calculate indentation
    depth=$(echo "$url" | tr -cd '/' | wc -c)
    indent=""
    for ((i=1; i<$depth; i++)); do
        indent="  $indent"
    done
    
    # Print screen
    echo "${indent}📱 $url - $name"
    
    # Find interfaces that have this screen_id
    interfaces=$(jq -r --arg screen "$screen_id" '
        .entities.interfaces | to_entries | .[] |
        select(.key == $screen) | .key
    ' "$GRAPH_FILE")
    
    if [ -n "$interfaces" ]; then
        interface_name=$(jq -r --arg int "$interfaces" '.entities.interfaces[$int].name' "$GRAPH_FILE")
        echo "${indent}  └─ interface:$interfaces - $interface_name"
        
        # Get what this interface depends on from the graph
        deps=$(jq -r --arg int "interface:$interfaces" '
            .graph[$int].depends_on[]? | 
            select(startswith("feature:") or startswith("component:"))
        ' "$GRAPH_FILE" 2>/dev/null)
        
        if [ -n "$deps" ]; then
            echo "$deps" | while read -r dep; do
                if [[ $dep == feature:* ]]; then
                    feat_name=$(echo "$dep" | sed 's/feature://')
                    echo "${indent}      ⚡ $feat_name"
                elif [[ $dep == component:* ]]; then
                    comp_name=$(echo "$dep" | sed 's/component://')
                    echo "${indent}      📦 $comp_name"
                fi
            done
        fi
        
        # Get what depends on this interface
        dependents=$(jq -r --arg int "interface:$interfaces" '
            .graph | to_entries[] | 
            select(.value.depends_on[]? == $int) | 
            .key | select(startswith("component:") or startswith("action:"))
        ' "$GRAPH_FILE" 2>/dev/null)
        
        if [ -n "$dependents" ]; then
            echo "${indent}    Used by:"
            echo "$dependents" | while read -r dep; do
                if [[ $dep == action:* ]]; then
                    echo "${indent}      🎯 $(echo $dep | sed 's/action://')"
                elif [[ $dep == component:* ]]; then
                    echo "${indent}      🔧 $(echo $dep | sed 's/component://')"
                fi
            done
        fi
    fi
    echo
done

echo "============================================"
echo "Legend:"
echo "  📱 Screen (URL route)"
echo "  🖥️  Interface (entity)"  
echo "  ⚡ Feature dependency"
echo "  📦 Component dependency"
echo "  🎯 Action that uses this interface"
echo "  🔧 Component that uses this interface"
echo
echo "Statistics:"
echo "  Screens: $(jq '.references.screens | length' "$GRAPH_FILE")"
echo "  Interfaces: $(jq '.entities.interfaces | length' "$GRAPH_FILE")"
echo "  Mapped: $(jq -r '.entities.interfaces | keys[]' "$GRAPH_FILE" | 
    xargs -I{} sh -c "jq '.references.screens.\"{}\" // empty' \"$GRAPH_FILE\" > /dev/null && echo {}" | wc -l)"
