#!/bin/bash

# Knowledge Graph Modifier - Clean CLI Interface
# Fast, intuitive commands for managing spec-graph.json

set -e

KNOWLEDGE_MAP_FILE="${KNOWLEDGE_MAP:-./.ai/spec-graph.json}"
TEMP_FILE="/tmp/km_temp.json"
BACKUP_DIR=".backup-temp"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

check_file() {
    if [[ ! -f "$KNOWLEDGE_MAP_FILE" ]]; then
        echo -e "${RED}✗ $KNOWLEDGE_MAP_FILE not found${NC}"
        exit 1
    fi
}

backup() {
    mkdir -p "$BACKUP_DIR"
    cp "$KNOWLEDGE_MAP_FILE" "${BACKUP_DIR}/$(basename "$KNOWLEDGE_MAP_FILE").backup.$(date +%s)"
    echo -e "${GREEN}✓ Backup created in ${BACKUP_DIR}${NC}"
}

show_usage() {
    echo -e "${BOLD}Knowledge Graph Modifier${NC}"
    echo -e "${CYAN}Fast CLI for managing spec-graph.json${NC}"
    echo
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [--file|-f <graph-file>] <command> [args...]"
    echo
    echo -e "${YELLOW}Options:${NC}"
    echo "  --file, -f <file>        Use specified graph file (default: spec-graph.json)"
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
    echo "  resolve-cycles           Fix circular dependencies using canonical flow"
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
    jq -r '.entities | keys[]' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "users platforms screens components features objectives requirements schema ui_components"
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
        echo -e "${CYAN}📋 Knowledge Graph Entities${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo

        # WHAT: Business/Functional perspective (Project → User → Objectives → Actions)
        echo -e "${GREEN}🎯 WHAT (Business Perspective)${NC}"
        echo -e "${GREEN}═══════════════════════════════${NC}"
        echo -e "${CYAN}Flow: Project → User → Objectives → Actions${NC}"
        echo -e "${DIM}Integration: User→Requirements, Objectives→Features, Actions→Components${NC}"
        echo

        # Users define WHO uses the system
        local count=$(jq -r ".entities.users | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
        if [[ "$count" -gt 0 ]]; then
            echo -e "${YELLOW}├─ users ($count entities) - WHO uses the system${NC}"
            jq -r ".entities.users | to_entries[] | \"│  • \(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE"
        fi

        # Objectives defines WHAT the system does
        count=$(jq -r ".entities.objectives | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
        if [[ "$count" -gt 0 ]]; then
            echo -e "${YELLOW}├─ objectives ($count entities) - WHAT the system does${NC}"
            jq -r ".entities.objectives | to_entries[] | \"│  • \(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE"
        fi

        # Actions - User interactions that implement the objectives
        count=$(jq -r ".entities.actions | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
        if [[ "$count" -gt 0 ]]; then
            echo -e "${YELLOW}├─ actions ($count entities) - Actions users take${NC}"
            jq -r ".entities.actions | to_entries[] | \"│  • \(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE"
        fi

        echo
        # HOW: Technical/Implementation perspective (Platform → Requirements → Interface → Feature → Action → Component → UI → Data)
        echo -e "${GREEN}🔧 HOW (Technical Infrastructure)${NC}"
        echo -e "${GREEN}═════════════════════════════════${NC}"
        echo -e "${CYAN}Flow: Platform → Requirements → Interface → Feature → Action → Component → UI → Data${NC}"
        echo

        # Define HOW entity types in dependency order (actions are in WHAT)
        local how_types=("platforms" "requirements" "screens" "features" "components" "ui_components" "schema")
        local how_descriptions=("Infrastructure foundation" "System constraints" "User interfaces" "System capabilities" "Technical components" "UI building blocks" "Data structures")

        local i=0
        for entity_type in "${how_types[@]}"; do
            count=$(jq -r ".entities.$entity_type | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
            if [[ "$count" -gt 0 ]]; then
                echo -e "${YELLOW}├─ $entity_type ($count entities) - ${how_descriptions[$i]}${NC}"
                jq -r ".entities.$entity_type | to_entries[] | \"│  • \(.key) - \(.value.name // \"No name\")\"" "$KNOWLEDGE_MAP_FILE"
            fi
            i=$((i + 1))
        done

        echo
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

        # Summary statistics with WHAT vs HOW breakdown
        local what_count=$(($(jq -r '.entities.users | length' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0") + \
                           $(jq -r '.entities.objectives | length' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0") + \
                           $(jq -r '.entities.actions | length' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")))

        local how_count=0
        for entity_type in "${how_types[@]}"; do
            how_count=$((how_count + $(jq -r ".entities.$entity_type | length" "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")))
        done

        local total_entities=$(jq -r '[.entities | to_entries[] | .value | length] | add' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")
        local total_connections=$(jq -r '.connections | length' "$KNOWLEDGE_MAP_FILE" 2>/dev/null || echo "0")

        echo -e "${CYAN}📊 Summary:${NC}"
        echo -e "${CYAN}   Total: $total_entities entities, $total_connections connections${NC}"
        echo -e "${CYAN}   WHAT: $what_count entities (business perspective)${NC}"
        echo -e "${CYAN}   HOW: $how_count entities (technical implementation)${NC}"
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

resolve_circular_dependencies() {
    echo -e "${CYAN}🔄 Resolving circular dependencies using canonical flow...${NC}"
    echo -e "${YELLOW}HOW: Project → Platform → Requirements → Interface → Feature → Action → Component → UI → Data Models${NC}"
    echo -e "${YELLOW}WHAT: Project → User → Objectives → Implementation${NC}"
    echo -e "${YELLOW}Integration: User → Requirements, Objectives → Features, Implementation → Action/Component${NC}"
    echo
    
    # Define the canonical dependency hierarchy using a function (lower number = higher in hierarchy, can't depend on higher numbers)
    get_hierarchy_level() {
        local entity_type="$1"
        case "$entity_type" in
            "project") echo "1" ;;
            "platform") echo "2" ;;
            "requirement") echo "3" ;;
            "user") echo "35" ;;          # 3.5 - Parallel to requirements, feeds into interface
            "screen") echo "4" ;;         # Interface layer
            "interface") echo "4" ;;      # Interface layer (same as screen)
            "objectives") echo "45" ;; # 4.5 - Between interface and features
            "feature") echo "5" ;;
            "action") echo "6" ;;         # Actions come after features
            "component") echo "7" ;;
            "ui_component") echo "8" ;;
            "ui") echo "8" ;;             # Same as ui_component
            "model") echo "9" ;;          # Data models at the bottom
            "data_model") echo "9" ;;     # Same as model
            "implementation") echo "75" ;; # 7.5 - Between component and UI
            *) echo "999" ;;              # Unknown types get lowest priority
        esac
    }
    
    local violations_found=0
    local violations_fixed=0
    
    backup
    
    # Check all dependencies for violations
    local all_deps=$(jq -r '.graph | to_entries[] | "\(.key):\(.value.depends_on[]?)"' "$KNOWLEDGE_MAP_FILE" 2>/dev/null | grep -v ':$')
    
    while IFS= read -r dep_line; do
        if [[ -n "$dep_line" ]]; then
            local from_entity=$(echo "$dep_line" | cut -d':' -f1,2)  # Get type:id
            local to_entity=$(echo "$dep_line" | cut -d':' -f3-)     # Get the dependency
            
            local from_type=$(echo "$from_entity" | cut -d':' -f1)
            local to_type=$(echo "$to_entity" | cut -d':' -f1)
            
            local from_level=$(get_hierarchy_level "$from_type")
            local to_level=$(get_hierarchy_level "$to_type")
            
            # Violation: higher level entity depending on lower level entity
            if [[ $from_level -lt $to_level ]]; then
                echo -e "${RED}✗ Circular violation: $from_entity → $to_entity${NC}"
                echo -e "  ${YELLOW}($from_type level $from_level) cannot depend on ($to_type level $to_level)${NC}"
                ((violations_found++))
                
                # Remove the violating dependency
                echo -e "${BLUE}  Removing dependency: $from_entity -/→ $to_entity${NC}"
                jq ".graph.\"$from_entity\".depends_on |= (. - [\"$to_entity\"])" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
                ((violations_fixed++))
            fi
        fi
    done <<< "$all_deps"
    
    # Special case: Check for direct circular references (A→B, B→A)
    local direct_cycles=$(jq -r '
        .graph | to_entries[] as $from |
        $from.value.depends_on[]? as $to |
        (.graph[$to].depends_on[]? // empty) as $back |
        select($back == $from.key) |
        "\($from.key) ↔ \($to)"
    ' "$KNOWLEDGE_MAP_FILE" 2>/dev/null | sort -u)
    
    while IFS= read -r cycle; do
        if [[ -n "$cycle" ]]; then
            local entity_a=$(echo "$cycle" | cut -d' ' -f1)
            local entity_b=$(echo "$cycle" | cut -d' ' -f3)
            
            local type_a=$(echo "$entity_a" | cut -d':' -f1)
            local type_b=$(echo "$entity_b" | cut -d':' -f1)
            
            local level_a=$(get_hierarchy_level "$type_a")
            local level_b=$(get_hierarchy_level "$type_b")
            
            echo -e "${RED}✗ Direct cycle detected: $cycle${NC}"
            ((violations_found++))
            
            # Remove the dependency from the higher level entity (lower number) to lower level entity (higher number)
            if [[ $level_a -lt $level_b ]]; then
                echo -e "${BLUE}  Removing: $entity_a -/→ $entity_b (preserving canonical flow)${NC}"
                jq ".graph.\"$entity_a\".depends_on |= (. - [\"$entity_b\"])" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
            else
                echo -e "${BLUE}  Removing: $entity_b -/→ $entity_a (preserving canonical flow)${NC}"
                jq ".graph.\"$entity_b\".depends_on |= (. - [\"$entity_a\"])" "$KNOWLEDGE_MAP_FILE" > "$TEMP_FILE" && mv "$TEMP_FILE" "$KNOWLEDGE_MAP_FILE"
            fi
            ((violations_fixed++))
        fi
    done <<< "$direct_cycles"
    
    echo
    if [[ $violations_found -eq 0 ]]; then
        echo -e "${GREEN}✓ No circular dependency violations found${NC}"
    else
        echo -e "${GREEN}✓ Fixed $violations_fixed of $violations_found circular dependency violations${NC}"
        echo -e "${YELLOW}💡 Tip: Use 'validate' command to verify graph structure${NC}"
    fi
    
    echo
    echo -e "${CYAN}📋 Canonical Dependency Hierarchy:${NC}"
    echo -e "${PURPLE}HOW (Technical Flow):${NC}"
    echo -e "  ${BOLD}1.${NC} project (infrastructure foundation)"
    echo -e "  ${BOLD}2.${NC} platform (AWS, deployment infrastructure)"
    echo -e "  ${BOLD}3.${NC} requirement (system constraints and needs)"
    echo -e "  ${BOLD}4.${NC} interface/screen (user interfaces)"
    echo -e "  ${BOLD}5.${NC} feature (business capabilities)"
    echo -e "  ${BOLD}6.${NC} action (behavioral layer)"
    echo -e "  ${BOLD}7.${NC} component (implementation modules)"
    echo -e "  ${BOLD}8.${NC} ui/ui_component (UI elements)"
    echo -e "  ${BOLD}9.${NC} model/data_model (data structures)"
    echo
    echo -e "${PURPLE}WHAT (Business Flow):${NC}"
    echo -e "  project → user → objectives → implementation"
    echo
    echo -e "${PURPLE}Integration Points:${NC}"
    echo -e "  user → requirements"
    echo -e "  objectives → features"
    echo -e "  implementation → action/component"
}

# Parse file option
while [[ $# -gt 0 ]]; do
    case $1 in
        --file|-f)
            KNOWLEDGE_MAP_FILE="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

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
    "resolve-cycles"|"fix-cycles"|"resolve")
        check_file
        resolve_circular_dependencies
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