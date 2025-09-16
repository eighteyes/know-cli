#!/bin/bash

# Generate unified route map showing pages and API endpoints with their dependencies
GRAPH_FILE="${1:-.ai/spec-graph.json}"

if [ ! -f "$GRAPH_FILE" ]; then
    echo "Error: Graph file not found: $GRAPH_FILE"
    exit 1
fi

echo "🗺️  Complete Route Map (Pages & APIs)"
echo "============================================"
echo

echo "📱 USER INTERFACE PAGES"
echo "----------------------"
jq -r '.references.screens | to_entries | .[] | 
    select(.value.type == "page") | 
    .key + "|" + .value.url + "|" + .value.name' "$GRAPH_FILE" | 
sort -t'|' -k2 |
while IFS='|' read -r screen_id url name; do
    echo "  $url → $name"
    
    # Find interface that uses this screen
    interface=$(jq -r --arg screen "$screen_id" '
        .entities.interfaces | to_entries | .[] |
        select(.key == $screen) | .key
    ' "$GRAPH_FILE")
    
    if [ -n "$interface" ]; then
        # Get what depends on this interface
        deps=$(jq -r --arg int "interface:$interface" '
            .graph[$int].depends_on[]? | 
            select(startswith("screen:") and (. != ("screen:" + $screen)))
        ' "$GRAPH_FILE" 2>/dev/null | sed 's/screen://')
        
        if [ -n "$deps" ]; then
            echo "    API calls:"
            echo "$deps" | while read -r api; do
                api_info=$(jq -r --arg api "$api" '
                    .references.screens[$api] | 
                    select(.type == "api") | 
                    "      → \(.method) \(.url)"
                ' "$GRAPH_FILE")
                [ -n "$api_info" ] && echo "$api_info"
            done
        fi
    fi
done

echo
echo "🔌 API ENDPOINTS"
echo "----------------"
jq -r '.references.screens | to_entries | .[] | 
    select(.value.type == "api") | 
    .value.method + "|" + .value.url + "|" + .value.name + "|" + .key' "$GRAPH_FILE" | 
sort -t'|' -k2 |
while IFS='|' read -r method url name key; do
    printf "  %-8s %s\n" "$method" "$url"
    echo "           Name: $name"
    
    # Find what uses this endpoint
    users=$(jq -r --arg screen "screen:$key" '
        .graph | to_entries[] | 
        select(.value.depends_on[]? == $screen) | 
        .key
    ' "$GRAPH_FILE" 2>/dev/null)
    
    if [ -n "$users" ]; then
        echo "           Used by:"
        echo "$users" | while read -r user; do
            case "$user" in
                component:*)
                    echo "             🔧 $(echo $user | sed 's/component://')"
                    ;;
                action:*)
                    echo "             🎯 $(echo $user | sed 's/action://')"
                    ;;
                interface:*)
                    echo "             🖥️  $(echo $user | sed 's/interface://')"
                    ;;
            esac
        done
    fi
    echo
done

echo
echo "============================================"
echo "Summary:"
echo "  Pages: $(jq '[.references.screens[] | select(.type == "page")] | length' "$GRAPH_FILE")"
echo "  API Endpoints: $(jq '[.references.screens[] | select(.type == "api")] | length' "$GRAPH_FILE")"
echo "  Total Routes: $(jq '.references.screens | length' "$GRAPH_FILE")"
echo
echo "Legend:"
echo "  📱 Page (user-facing route)"
echo "  🔌 API (backend endpoint)"
echo "  🖥️  Interface entity"
echo "  🔧 Component"
echo "  🎯 Action"
