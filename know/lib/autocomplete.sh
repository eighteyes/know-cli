#!/bin/bash

# autocomplete.sh - Entity discovery and autocomplete for know CLI

# Generate bash completion script
generate_completion() {
    cat << 'EOF'
_know_completion() {
    local cur prev words cword
    _init_completion || return

    # Cache directory for entity lists
    local cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/know"
    local cache_file="$cache_dir/entities.cache"
    local knowledge_map="${KNOWLEDGE_MAP:-spec-graph.json}"

    # Function to get cached entities
    _get_entities() {
        local entity_type="$1"

        # Check if cache exists and is newer than knowledge map
        if [[ -f "$cache_file" && "$cache_file" -nt "$knowledge_map" ]]; then
            grep "^$entity_type:" "$cache_file" 2>/dev/null | cut -d: -f2
        else
            # Rebuild cache
            mkdir -p "$cache_dir"
            {
                know list features 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print "features:" $1}'
                know list components 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print "components:" $1}'
                know list screens 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print "screens:" $1}'
                know list functionality 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print "functionality:" $1}'
                know list requirements 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print "requirements:" $1}'
                know list schema 2>/dev/null | grep -E '^  [a-z-]+' | awk '{print "schema:" $1}'
            } > "$cache_file" 2>/dev/null

            grep "^$entity_type:" "$cache_file" 2>/dev/null | cut -d: -f2
        fi
    }

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
            local commands="feature component screen functionality requirement api"
            commands="$commands deps impact gaps validate order blockers"
            commands="$commands list search check preview"
            commands="$commands create-feature complete implementation-chain priorities completeness ready-check todo"
            commands="$commands package test mod query"
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
        2)
            # Second argument - entity IDs based on command
            case ${words[1]} in
                feature)
                    COMPREPLY=($(compgen -W "$(_get_entities features)" -- "$cur"))
                    ;;
                component)
                    COMPREPLY=($(compgen -W "$(_get_entities components)" -- "$cur"))
                    ;;
                screen)
                    COMPREPLY=($(compgen -W "$(_get_entities screens)" -- "$cur"))
                    ;;
                functionality)
                    COMPREPLY=($(compgen -W "$(_get_entities functionality)" -- "$cur"))
                    ;;
                requirement)
                    COMPREPLY=($(compgen -W "$(_get_entities requirements)" -- "$cur"))
                    ;;
                api)
                    COMPREPLY=($(compgen -W "$(_get_entities schema)" -- "$cur"))
                    ;;
                check|preview)
                    # These need type as second arg, entity as third
                    if [[ $cword -eq 2 ]]; then
                        COMPREPLY=($(compgen -W "feature component screen functionality requirement api" -- "$cur"))
                    fi
                    ;;
                deps|impact|gaps|validate|package|test|complete|ready-check)
                    # For these commands, show all entity references with type prefixes
                    local all_entities=""
                    if [[ -f "$cache_file" && "$cache_file" -nt "$knowledge_map" ]]; then
                        all_entities=$(sed 's/:/ /g' "$cache_file" | awk '{print $1":"$2}')
                    else
                        for type in features components screens functionality requirements schema; do
                            all_entities+=" $(_get_entities $type | sed "s/^/$type:/")"
                        done
                    fi
                    COMPREPLY=($(compgen -W "$all_entities" -- "$cur"))
                    ;;
                list)
                    COMPREPLY=($(compgen -W "features components screens functionality requirements schema" -- "$cur"))
                    ;;
                search)
                    # No completion for search terms
                    ;;
            esac
            ;;
        3)
            # Third argument - for check/preview commands
            case ${words[1]} in
                check|preview)
                    local entity_type="${words[2]}"
                    case $entity_type in
                        feature)
                            COMPREPLY=($(compgen -W "$(_get_entities features)" -- "$cur"))
                            ;;
                        component)
                            COMPREPLY=($(compgen -W "$(_get_entities components)" -- "$cur"))
                            ;;
                        screen)
                            COMPREPLY=($(compgen -W "$(_get_entities screens)" -- "$cur"))
                            ;;
                        functionality)
                            COMPREPLY=($(compgen -W "$(_get_entities functionality)" -- "$cur"))
                            ;;
                        requirement)
                            COMPREPLY=($(compgen -W "$(_get_entities requirements)" -- "$cur"))
                            ;;
                        api)
                            COMPREPLY=($(compgen -W "$(_get_entities schema)" -- "$cur"))
                            ;;
                    esac
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

# Install bash completion
install_completion() {
    local completion_dir="/usr/share/bash-completion/completions"
    local user_completion_dir="$HOME/.local/share/bash-completion/completions"
    local bashrc_completion="$HOME/.bash_completion"

    echo "Installing know command autocomplete..."
    echo

    # Determine completion file location
    local completion_file=""

    # Try system-wide installation first (requires sudo)
    if [[ -w "$completion_dir" ]]; then
        completion_file="$completion_dir/know"
        generate_completion > "$completion_file"
        echo "✅ Installed system-wide completion to $completion_file"
        echo "Restart your shell or run: source /etc/bash_completion"
        return 0
    fi

    # Fall back to user installation
    if mkdir -p "$user_completion_dir" 2>/dev/null; then
        completion_file="$user_completion_dir/know"
        generate_completion > "$completion_file"
        echo "✅ Installed user completion to $completion_file"
    else
        # Fall back to ~/.bash_completion
        completion_file="$bashrc_completion"
        generate_completion > "$completion_file"
        echo "✅ Installed completion to $completion_file"
    fi

    echo
    echo "🔧 Shell Configuration Setup"
    echo

    # Offer to add to shell config
    setup_shell_config "$completion_file"
}

# Interactive shell configuration setup
setup_shell_config() {
    local completion_file="$1"
    local current_shell=$(basename "$SHELL")
    local config_file=""
    local source_line=""

    # Determine shell and config file
    case "$current_shell" in
        bash)
            config_file="$HOME/.bashrc"
            source_line="source $completion_file"
            ;;
        zsh)
            config_file="$HOME/.zshrc"
            source_line="autoload -U bashcompinit && bashcompinit && source $completion_file"
            ;;
        *)
            echo "⚠️  Unknown shell: $current_shell"
            echo "Manual setup required. Add this line to your shell config:"
            echo "  source $completion_file"
            return 0
            ;;
    esac

    # Check if already configured
    if [[ -f "$config_file" ]] && grep -q "source.*know" "$config_file" 2>/dev/null; then
        echo "✅ Autocomplete already configured in $config_file"
        return 0
    fi

    echo "Detected shell: $current_shell"
    echo "Configuration file: $config_file"
    echo

    # Interactive options
    echo "Choose setup option:"
    echo "  1) Add to $config_file automatically"
    echo "  2) Show manual instructions"
    echo "  3) Add to custom file"
    echo "  4) Skip configuration"
    echo
    read -p "Enter choice [1-4]: " choice

    case "$choice" in
        1)
            # Automatic setup
            if [[ -f "$config_file" ]]; then
                echo >> "$config_file"
                echo "# Know command autocomplete" >> "$config_file"
                echo "$source_line" >> "$config_file"
                echo "✅ Added autocomplete to $config_file"
                echo "Restart your shell or run: source $config_file"
            else
                echo "❌ $config_file not found. Creating it..."
                echo "# Know command autocomplete" > "$config_file"
                echo "$source_line" >> "$config_file"
                echo "✅ Created $config_file with autocomplete"
                echo "Restart your shell or run: source $config_file"
            fi
            ;;
        2)
            # Manual instructions
            echo
            echo "📋 Manual Setup Instructions:"
            echo
            echo "Add this line to your $config_file:"
            echo "  $source_line"
            echo
            echo "Then restart your shell or run:"
            echo "  source $config_file"
            ;;
        3)
            # Custom file
            echo
            read -p "Enter path to shell config file: " custom_file
            if [[ -n "$custom_file" ]]; then
                custom_file="${custom_file/#\~/$HOME}"  # Expand ~ to HOME
                echo >> "$custom_file"
                echo "# Know command autocomplete" >> "$custom_file"
                echo "$source_line" >> "$custom_file"
                echo "✅ Added autocomplete to $custom_file"
                echo "Source this file from your main shell config or restart your shell"
            else
                echo "❌ No file specified"
            fi
            ;;
        4)
            # Skip
            echo "⏭️  Skipped configuration. You can set up manually later:"
            echo "  source $completion_file"
            ;;
        *)
            echo "❌ Invalid choice. Run 'know --install-completion' again to retry"
            ;;
    esac
}

# Show current completion status
completion_status() {
    echo "🔍 Checking autocomplete status..."
    echo

    if type _know_completion &>/dev/null; then
        echo "✅ Autocomplete is active"
        echo "Try: know <TAB> or know list <TAB>"
    else
        echo "❌ Autocomplete not active"
        echo "Run: know --install-completion"
    fi

    local cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/know"
    local cache_file="$cache_dir/entities.cache"

    if [[ -f "$cache_file" ]]; then
        local count=$(wc -l < "$cache_file")
        echo "📋 Entity cache: $count entities cached"
        echo "   Cache file: $cache_file"
    else
        echo "📋 Entity cache: Not created yet"
        echo "   Will be created on first tab completion"
    fi
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