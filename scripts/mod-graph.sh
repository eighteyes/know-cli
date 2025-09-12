#!/bin/bash

# Knowledge Graph Modifier - Clean CLI Interface
# Fast, intuitive commands for managing knowledge-map-cmd.json

set -e

KNOWLEDGE_MAP_FILE="knowledge-map-cmd.json"
TEMP_FILE="/tmp/km_temp.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

check_file() {
    if [[ ! -f "$KNOWLEDGE_MAP_FILE" ]]; then
        echo -e "${RED}✗ $KNOWLEDGE_MAP_FILE not found${NC}"
        exit 1
    fi
}

backup() {
    cp "$KNOWLEDGE_MAP_FILE" "${KNOWLEDGE_MAP_FILE}.backup.$(date +%s)"
    echo -e "${GREEN}✓ Backup created${NC}"
}

show_usage() {
    echo -e "${BOLD}Knowledge Graph Modifier${NC}"
    echo -e "${CYAN}Fast CLI for managing knowledge-map-cmd.json${NC}"
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 <command> [args...]"
    echo
    echo -e "${YELLOW}Entity Commands:${NC}"
    echo "  list [type]              List entities (optionally by type)"
    echo "  add <type> <id> <name>   Add new entity"
    echo "  set <type> <id> <key> <value>   Set entity property"
    echo "  edit <type> <id>         Edit entity (interactive)"
    echo "  remove <type> <id>       Remove entity"
    echo "  show <type> <id>         Show entity details"
    echo
    echo -e "${YELLOW}Graph Commands:${NC}"
    echo "  connect <from> <to>      Add dependency: from -> to"
    echo "  disconnect <from> <to>   Remove dependency"
    echo "  deps <entity>            Show dependencies for entity"
    echo "  dependents <entity>      Show what depends on entity"
    echo "  validate                 Validate graph structure"
    echo
    echo -e "${YELLOW}Utility Commands:${NC}"
    echo "  stats                    Show statistics"
    echo "  backup                   Create backup"
    echo "  types                    List entity types"
    echo "  search <term>            Search entities by name/id"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 add features new-telemetry \"Real-time Telemetry v2\""
    echo "  $0 set features new-telemetry priority P0"
    echo "  $0 connect feature:new-telemetry platform:aws-infrastructure"
    echo "  $0 deps user:owner"
    echo "  $0 search telemetry"
}

get_entity_types() {
    jq -r '.entities | keys[]' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "users platforms screens components features functionality requirements schema ui_components"
}

list_entities() {
    local type="$1"
    
    if [[ -n "$type" ]]; then
        echo -e "${CYAN}📋 Entities in $type:${NC}"
        jq -r ".entities.$type | to_entries[] | \"  \(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || {
            echo -e "${RED}✗ Invalid entity type: $type${NC}"
            return 1
        }
    else
        echo -e "${CYAN}📋 All Entities:${NC}"
        for entity_type in $(get_entity_types); do
            local count=$(jq -r ".entities.$entity_type | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
            if [[ "$count" -gt 0 ]]; then
                echo -e "${YELLOW}$entity_type ($count):${NC}"
                jq -r ".entities.$entity_type | to_entries[] | \"  \(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE"
            fi
        done
    fi
}

add_entity() {
    local type="$1" id="$2" name="$3"
    
    if [[ -z "$type" || -z "$id" || -z "$name" ]]; then
        echo -e "${RED}✗ Usage: add <type> <id> <name>${NC}"
        return 1
    fi
    
    # Validate type
    if ! echo "$(get_entity_types)" | grep -qw "$type"; then
        echo -e "${RED}✗ Invalid entity type: $type${NC}"
        echo -e "${YELLOW}Valid types: $(get_entity_types)${NC}"
        return 1
    fi
    
    # Check if exists
    if jq -e ".entities.$type.\"$id\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Entity $id already exists in $type${NC}"
        return 1
    fi
    
    backup
    
    # Create entity
    local entity_obj="{\"id\": \"$id\", \"type\": \"$type\", \"name\": \"$name\"}"
    jq ".entities.$type.\"$id\" = $entity_obj" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    # Initialize graph entry if it doesn't exist
    jq ".graph.\"$type:$id\" = (.graph.\"$type:$id\" // {\"depends_on\": []})" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    echo -e "${GREEN}✓ Added $type:$id - $name${NC}"
}

set_entity_property() {
    local type="$1" id="$2" key="$3" value="$4"
    
    if [[ -z "$type" || -z "$id" || -z "$key" || -z "$value" ]]; then
        echo -e "${RED}✗ Usage: set <type> <id> <key> <value>${NC}"
        echo -e "${YELLOW}Example: set features real-time-telemetry priority P0${NC}"
        return 1
    fi
    
    # Validate type
    if ! echo "$(get_entity_types)" | grep -qw "$type"; then
        echo -e "${RED}✗ Invalid entity type: $type${NC}"
        echo -e "${YELLOW}Valid types: $(get_entity_types)${NC}"
        return 1
    fi
    
    # Check if entity exists
    if ! jq -e ".entities.$type.\"$id\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Entity $id not found in $type${NC}"
        return 1
    fi
    
    backup
    
    # Set the property - handle different value types
    if [[ "$value" =~ ^[0-9]+$ ]]; then
        # Numeric value
        jq ".entities.$type.\"$id\".\"$key\" = $value" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    elif [[ "$value" == "true" || "$value" == "false" ]]; then
        # Boolean value
        jq ".entities.$type.\"$id\".\"$key\" = $value" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    elif [[ "$value" =~ ^\[.*\]$ ]]; then
        # Array value (JSON format)
        jq ".entities.$type.\"$id\".\"$key\" = $value" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    else
        # String value
        jq ".entities.$type.\"$id\".\"$key\" = \"$value\"" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    fi
    
    echo -e "${GREEN}✓ Set $type:$id.$key = $value${NC}"
}

remove_entity() {
    local type="$1" id="$2"
    
    if [[ -z "$type" || -z "$id" ]]; then
        echo -e "${RED}✗ Usage: remove <type> <id>${NC}"
        return 1
    fi
    
    # Check if exists
    if ! jq -e ".entities.$type.\"$id\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Entity $id not found in $type${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}⚠ This will remove $type:$id and all its connections${NC}"
    read -p "Continue? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        return 0
    fi
    
    backup
    
    # Remove entity
    jq "del(.entities.$type.\"$id\")" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    # Remove graph entry
    jq "del(.graph.\"$type:$id\")" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    # Remove references from other entities' depends_on arrays
    local entity_key="$type:$id"
    jq "(.graph // {}) | to_entries | map(.value.depends_on |= (. - [\"$entity_key\"])) | from_entries as \$cleaned_graph | . + {\"graph\": \$cleaned_graph}" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    echo -e "${GREEN}✓ Removed $type:$id${NC}"
}

show_entity() {
    local type="$1" id="$2"
    
    if [[ -z "$type" || -z "$id" ]]; then
        echo -e "${RED}✗ Usage: show <type> <id>${NC}"
        return 1
    fi
    
    if ! jq -e ".entities.$type.\"$id\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Entity $id not found in $type${NC}"
        return 1
    fi
    
    echo -e "${CYAN}📄 Entity Details: $type:$id${NC}"
    jq -C ".entities.$type.\"$id\"" "$KNOWLEDGE_MAP_FILE"
    
    echo -e "\n${CYAN}🔗 Dependencies:${NC}"
    # Handle entity type mapping (entities uses plurals, graph uses singular)
    local graph_key
    if [[ "$type" == "users" ]]; then graph_key="user:$id"
    elif [[ "$type" == "platforms" ]]; then graph_key="platform:$id"
    elif [[ "$type" == "screens" ]]; then graph_key="screen:$id"
    elif [[ "$type" == "components" ]]; then graph_key="component:$id"
    elif [[ "$type" == "features" ]]; then graph_key="feature:$id"
    elif [[ "$type" == "requirements" ]]; then graph_key="requirement:$id"
    elif [[ "$type" == "ui_components" ]]; then graph_key="ui_component:$id"
    else graph_key="$type:$id"; fi
    
    local deps=$(jq -r ".graph.\"$graph_key\".depends_on[]?" "$KNOWLEDGE_MAP_FILE" 2>/dev/null)
    if [[ -n "$deps" ]]; then
        echo "$deps" | sed 's/^/  → /'
    else
        echo "  None"
    fi
    
    echo -e "\n${CYAN}🔙 Dependents:${NC}"
    local dependents=$(jq -r ".graph | to_entries[] | select(.value.depends_on[]? == \"$graph_key\") | .key" "$KNOWLEDGE_MAP_FILE" 2>/dev/null)
    if [[ -n "$dependents" ]]; then
        echo "$dependents" | sed 's/^/  ← /'
    else
        echo "  None"
    fi
}

connect_entities() {
    local from="$1" to="$2"
    
    if [[ -z "$from" || -z "$to" ]]; then
        echo -e "${RED}✗ Usage: connect <from> <to>${NC}"
        echo -e "${YELLOW}Example: connect user:owner feature:real-time-telemetry${NC}"
        return 1
    fi
    
    # Validate entities exist in graph
    if ! jq -e ".graph.\"$from\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Source entity not found: $from${NC}"
        return 1
    fi
    
    if ! jq -e ".graph.\"$to\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Target entity not found: $to${NC}"
        return 1
    fi
    
    backup
    
    # Add connection - ensure depends_on exists and add dependency
    jq ".graph.\"$from\" = (.graph.\"$from\" // {}) | .graph.\"$from\".depends_on = ((.graph.\"$from\".depends_on // []) + [\"$to\"] | unique)" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    echo -e "${GREEN}✓ Connected: $from → $to${NC}"
}

disconnect_entities() {
    local from="$1" to="$2"
    
    if [[ -z "$from" || -z "$to" ]]; then
        echo -e "${RED}✗ Usage: disconnect <from> <to>${NC}"
        return 1
    fi
    
    # Check if connection exists
    if ! jq -e ".graph.\"$from\".depends_on[]? | select(. == \"$to\")" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
        echo -e "${RED}✗ Connection not found: $from → $to${NC}"
        return 1
    fi
    
    backup
    
    # Remove connection
    jq ".graph.\"$from\".depends_on |= (. - [\"$to\"])" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
    
    echo -e "${GREEN}✓ Disconnected: $from -/→ $to${NC}"
}

show_dependencies() {
    local entity="$1"
    
    if [[ -z "$entity" ]]; then
        echo -e "${RED}✗ Usage: deps <entity>${NC}"
        return 1
    fi
    
    echo -e "${CYAN}🔗 Dependencies for $entity:${NC}"
    local deps=$(jq -r ".graph.\"$entity\".depends_on[]?" "$KNOWLEDGE_MAP_FILE" 2>/dev/null)
    if [[ -n "$deps" ]]; then
        echo "$deps" | sed 's/^/  → /'
    else
        echo "  None"
    fi
}

show_dependents() {
    local entity="$1"
    
    if [[ -z "$entity" ]]; then
        echo -e "${RED}✗ Usage: dependents <entity>${NC}"
        return 1
    fi
    
    echo -e "${CYAN}🔙 Entities depending on $entity:${NC}"
    local dependents=$(jq -r ".graph | to_entries[] | select(.value.depends_on[]? == \"$entity\") | .key" "$KNOWLEDGE_MAP_FILE" 2>/dev/null)
    if [[ -n "$dependents" ]]; then
        echo "$dependents" | sed 's/^/  ← /'
    else
        echo "  None"
    fi
}

validate_graph() {
    echo -e "${CYAN}🔍 Validating graph...${NC}"
    
    # JSON syntax
    if jq empty "$KNOWLEDGE_MAP_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ JSON syntax valid${NC}"
    else
        echo -e "${RED}✗ JSON syntax errors${NC}"
        return 1
    fi
    
    # Check for broken references
    local broken=0
    local all_refs=$(jq -r '.graph | to_entries[] | .value.depends_on[]?' "$KNOWLEDGE_MAP_FILE" 2>/dev/null | sort -u)
    
    while IFS= read -r ref; do
        if [[ -n "$ref" ]]; then
            # Check if the referenced entity exists in entities section
            ref_type=$(echo "$ref" | cut -d':' -f1)
            ref_id=$(echo "$ref" | cut -d':' -f2)
            if ! jq -e ".entities.$ref_type.\"$ref_id\"" "$KNOWLEDGE_MAP_FILE" > /dev/null 2>&1; then
                echo -e "${RED}✗ Broken reference: $ref (entity not found)${NC}"
                ((broken++))
            fi
        fi
    done <<< "$all_refs"
    
    if [[ $broken -eq 0 ]]; then
        echo -e "${GREEN}✓ All references valid${NC}"
    else
        echo -e "${RED}✗ Found $broken broken references${NC}"
    fi
    
    echo -e "${GREEN}✓ Validation complete${NC}"
}

show_stats() {
    echo -e "${PURPLE}📊 Knowledge Graph Statistics${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    for entity_type in $(get_entity_types); do
        local count=$(jq -r ".entities.$entity_type | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
        printf "${YELLOW}%-15s${NC} %s entities\n" "$entity_type:" "$count"
    done
    
    local total_entities=$(jq -r '.entities | to_entries | map(.value | length) | add' "$KNOWLEDGE_MAP_FILE")
    local total_connections=$(jq -r '.graph | to_entries | map(.value.depends_on | length) | add' "$KNOWLEDGE_MAP_FILE")
    local total_descriptions=$(jq -r '.references.descriptions | length' "$KNOWLEDGE_MAP_FILE")
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}Total entities:${NC}     $total_entities"
    echo -e "${BOLD}Total connections:${NC}  $total_connections"
    echo -e "${BOLD}Total descriptions:${NC} $total_descriptions"
}

search_entities() {
    local term="$1"
    
    if [[ -z "$term" ]]; then
        echo -e "${RED}✗ Usage: search <term>${NC}"
        return 1
    fi
    
    echo -e "${CYAN}🔍 Search results for: $term${NC}"
    
    for entity_type in $(get_entity_types); do
        local matches=$(jq -r ".entities.$entity_type | to_entries[] | select(.key | test(\"$term\"; \"i\")) | \"$entity_type:\(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE" 2>/dev/null)
        local name_matches=$(jq -r ".entities.$entity_type | to_entries[] | select(.value.name // \"\" | test(\"$term\"; \"i\")) | \"$entity_type:\(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE" 2>/dev/null)
        
        if [[ -n "$matches" || -n "$name_matches" ]]; then
            echo -e "${YELLOW}$entity_type:${NC}"
            (echo "$matches"; echo "$name_matches") | sort -u | sed 's/^/  /'
        fi
    done
}

# Main command dispatcher
case "${1:-}" in
    "list"|"ls")
        check_file
        list_entities "$2"
        ;;
    "add")
        check_file
        add_entity "$2" "$3" "$4"
        ;;
    "set")
        check_file
        set_entity_property "$2" "$3" "$4" "$5"
        ;;
    "remove"|"rm")
        check_file
        remove_entity "$2" "$3"
        ;;
    "show"|"info")
        check_file
        show_entity "$2" "$3"
        ;;
    "connect"|"link")
        check_file
        connect_entities "$2" "$3"
        ;;
    "disconnect"|"unlink")
        check_file
        disconnect_entities "$2" "$3"
        ;;
    "deps"|"dependencies")
        check_file
        show_dependencies "$2"
        ;;
    "dependents"|"rdeps")
        check_file
        show_dependents "$2"
        ;;
    "validate"|"check")
        check_file
        validate_graph
        ;;
    "stats"|"statistics")
        check_file
        show_stats
        ;;
    "backup")
        check_file
        backup
        ;;
    "types")
        echo "$(get_entity_types)"
        ;;
    "search"|"find")
        check_file
        search_entities "$2"
        ;;
    "help"|"--help"|"-h"|"")
        show_usage
        ;;
    *)
        echo -e "${RED}✗ Unknown command: $1${NC}"
        echo -e "${YELLOW}Run '$0 help' for usage${NC}"
        exit 1
        ;;
esac