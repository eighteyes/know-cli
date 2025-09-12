#!/bin/bash

# autocomplete.sh - Entity discovery and autocomplete for know CLI

# Generate bash completion script
generate_completion() {
    cat << 'EOF'
_know_completion() {
    local cur prev words cword
    _init_completion || return

    case $prev in
        --map)
            _filedir json
            return
            ;;
        --format)
            COMPREPLY=($(compgen -W "md json yaml" -- "$cur"))
            return
            ;;
        --output)
            _filedir
            return
            ;;
    esac

    case $cword in
        1)
            # First argument - commands
            COMPREPLY=($(compgen -W "feature component screen functionality requirement api deps impact order validate package test list search" -- "$cur"))
            ;;
        2)
            # Second argument - entity IDs based on command
            case ${words[1]} in
                feature)
                    COMPREPLY=($(compgen -W "$(know list features 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print $1}')" -- "$cur"))
                    ;;
                component)
                    COMPREPLY=($(compgen -W "$(know list components 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print $1}')" -- "$cur"))
                    ;;
                screen)
                    COMPREPLY=($(compgen -W "$(know list screens 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print $1}')" -- "$cur"))
                    ;;
                functionality)
                    COMPREPLY=($(compgen -W "$(know list functionality 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print $1}')" -- "$cur"))
                    ;;
                requirement)
                    COMPREPLY=($(compgen -W "$(know list requirements 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print $1}')" -- "$cur"))
                    ;;
                api)
                    COMPREPLY=($(compgen -W "$(know list schema 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print $1}')" -- "$cur"))
                    ;;
                deps|impact|package|test)
                    # For these commands, show all entity references
                    local all_entities=""
                    for type in features components screens functionality requirements schema; do
                        all_entities+=" $(know list $type 2>/dev/null | grep -E '^  [a-z-]+' | awk -v t=$type '{print t":"$1}')"
                    done
                    COMPREPLY=($(compgen -W "$all_entities" -- "$cur"))
                    ;;
            esac
            ;;
    esac

    # Handle global options
    if [[ $cur == -* ]]; then
        COMPREPLY=($(compgen -W "--format --output --map --ai --help" -- "$cur"))
    fi
}

complete -F _know_completion know
EOF
}

# Fuzzy search entities
search_entities() {
    local search_term="$1"
    local entity_type="${2:-}"
    
    echo "🔍 Searching for entities matching: '$search_term'"
    echo
    
    if [[ -n "$entity_type" ]]; then
        local normalized_type
        normalized_type=$(normalize_entity_type "$entity_type")
        
        echo "📋 Found in $normalized_type:"
        jq -r --arg type "$normalized_type" --arg search "$search_term" '
            .entities[$type] | to_entries[] |
            select(.key | contains($search) or (.value.name // "" | ascii_downcase | contains($search | ascii_downcase))) |
            "  \(.key) - \(.value.name // "No name")"
        ' "$KNOWLEDGE_MAP"
    else
        echo "📋 Found across all types:"
        for type in $(get_entity_types); do
            jq -r --arg type "$type" --arg search "$search_term" '
                .entities[$type] | to_entries[] |
                select(.key | contains($search) or (.value.name // "" | ascii_downcase | contains($search | ascii_downcase))) |
                "  \($type):\(.key) - \(.value.name // "No name")"
            ' "$KNOWLEDGE_MAP" 2>/dev/null || true
        done
    fi
    
    echo
    echo "💡 Use exact ID with: know <command> <entity_id>"
    echo "💡 Use full reference with: know <command> <type>:<entity_id>"
}

# Interactive entity picker
pick_entity() {
    local entity_type="$1"
    
    echo "📋 Available ${entity_type}s:"
    echo
    
    local entities
    entities=$(list_entities "$entity_type" | grep "^  " | nl -w2 -s") ")
    
    if [[ -z "$entities" ]]; then
        error "No entities found of type: $entity_type"
    fi
    
    echo "$entities"
    echo
    read -p "Select entity (number or ID): " selection
    
    if [[ "$selection" =~ ^[0-9]+$ ]]; then
        # Number selection
        local entity_id
        entity_id=$(echo "$entities" | sed -n "${selection}p" | awk '{print $2}')
        echo "$entity_type:$entity_id"
    else
        # Direct ID
        echo "$entity_type:$selection"
    fi
}

# Smart entity suggestions
suggest_entities() {
    local partial_id="$1"
    local entity_type="${2:-}"
    
    echo "🔍 Did you mean:"
    echo
    
    if [[ -n "$entity_type" ]]; then
        local normalized_type
        normalized_type=$(normalize_entity_type "$entity_type")
        
        jq -r --arg type "$normalized_type" --arg partial "$partial_id" '
            .entities[$type] | to_entries[] |
            select(.key | startswith($partial)) |
            "  \(.key) - \(.value.name // "No name")"
        ' "$KNOWLEDGE_MAP" | head -5
    else
        # Search across all types
        local count=0
        for type in $(get_entity_types); do
            jq -r --arg type "$type" --arg partial "$partial_id" '
                .entities[$type] | to_entries[] |
                select(.key | startswith($partial)) |
                "  \($type):\(.key) - \(.value.name // "No name")"
            ' "$KNOWLEDGE_MAP" 2>/dev/null | head -2
            ((count++))
            [[ $count -ge 3 ]] && break
        done
    fi
}