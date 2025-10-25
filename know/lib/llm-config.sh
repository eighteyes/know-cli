#!/bin/bash

# LLM Configuration Management for Know tool
# Handles config set, get, list, and model selection

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/../config"
CONFIG_FILE="$CONFIG_DIR/llm-config.json"

# Colors (reuse if already defined)
if [[ -z "${RED:-}" ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m'
fi

# Ensure config file exists
ensure_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        mkdir -p "$CONFIG_DIR"
        cat > "$CONFIG_FILE" <<EOF
{
  "provider": "mock",
  "model": "claude-3-haiku-20240307",
  "api_key": "",
  "max_tokens": 1024,
  "temperature": 0.7,
  "lm_studio_url": "http://localhost:1234/v1/chat/completions",
  "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
    fi
}

# Get a config value
get_config() {
    local key="$1"
    ensure_config

    # Handle environment variable overrides
    case "$key" in
        provider)
            echo "${LLM_PROVIDER:-$(jq -r ".provider // \"mock\"" "$CONFIG_FILE")}"
            ;;
        model)
            echo "${LLM_MODEL:-$(jq -r ".model // \"claude-3-haiku-20240307\"" "$CONFIG_FILE")}"
            ;;
        api_key)
            # Don't use environment variable for API key (security)
            local stored_key=$(jq -r ".api_key // \"\"" "$CONFIG_FILE")
            if [[ -z "$stored_key" ]]; then
                echo "${ANTHROPIC_API_KEY:-}"
            else
                echo "$stored_key"
            fi
            ;;
        max_tokens)
            echo "${LLM_MAX_TOKENS:-$(jq -r ".max_tokens // 1024" "$CONFIG_FILE")}"
            ;;
        temperature)
            echo "${LLM_TEMPERATURE:-$(jq -r ".temperature // 0.7" "$CONFIG_FILE")}"
            ;;
        lm_studio_url)
            echo "${LM_STUDIO_URL:-$(jq -r ".lm_studio_url // \"http://localhost:1234/v1/chat/completions\"" "$CONFIG_FILE")}"
            ;;
        *)
            jq -r ".$key // null" "$CONFIG_FILE"
            ;;
    esac
}

# Set a config value
set_config() {
    local key="$1"
    local value="${2:-}"

    ensure_config

    # Special handling for model selection
    if [[ "$key" == "model" ]]; then
        if [[ -z "$value" ]]; then
            # Interactive model selection
            select_model
            return
        fi
    fi

    # Special handling for API key (mask it in display)
    if [[ "$key" == "api_key" ]]; then
        if [[ -z "$value" ]]; then
            echo -e "${YELLOW}Enter API key (input will be hidden):${NC}"
            read -s value
            echo
        fi

        if [[ -n "$value" ]]; then
            # Update config file
            local tmp_file=$(mktemp)
            jq --arg key "$key" --arg val "$value" --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
                '.[$key] = $val | .last_updated = $ts' "$CONFIG_FILE" > "$tmp_file"
            mv "$tmp_file" "$CONFIG_FILE"

            # Mask the API key for display
            local masked_key="${value:0:6}...${value: -4}"
            echo -e "${GREEN}✓${NC} Set $key to: $masked_key"
        else
            echo -e "${RED}✗${NC} API key cannot be empty"
            return 1
        fi
    else
        # Normal config update
        if [[ -n "$value" ]]; then
            local tmp_file=$(mktemp)
            jq --arg key "$key" --arg val "$value" --arg ts "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
                '.[$key] = $val | .last_updated = $ts' "$CONFIG_FILE" > "$tmp_file"
            mv "$tmp_file" "$CONFIG_FILE"
            echo -e "${GREEN}✓${NC} Set $key to: $value"
        else
            echo -e "${RED}✗${NC} Value cannot be empty"
            return 1
        fi
    fi
}

# List all config values
list_config() {
    ensure_config

    echo -e "${BLUE}═══ LLM Configuration ═══${NC}"
    echo

    # Provider
    local provider=$(get_config "provider")
    echo -e "${YELLOW}Provider:${NC}     $provider"

    # Model
    local model=$(get_config "model")
    echo -e "${YELLOW}Model:${NC}        $model"

    # API Key (masked)
    local api_key=$(get_config "api_key")
    if [[ -n "$api_key" ]]; then
        local masked_key="${api_key:0:6}...${api_key: -4}"
        echo -e "${YELLOW}API Key:${NC}      $masked_key"
    else
        echo -e "${YELLOW}API Key:${NC}      (not set)"
    fi

    # Max tokens
    local max_tokens=$(get_config "max_tokens")
    echo -e "${YELLOW}Max Tokens:${NC}   $max_tokens"

    # Temperature
    local temperature=$(get_config "temperature")
    echo -e "${YELLOW}Temperature:${NC}  $temperature"

    # LM Studio URL (if provider is lm_studio)
    if [[ "$provider" == "lm_studio" ]]; then
        local lm_url=$(get_config "lm_studio_url")
        echo -e "${YELLOW}LM Studio:${NC}    $lm_url"
    fi

    # Last updated
    local last_updated=$(jq -r ".last_updated // \"never\"" "$CONFIG_FILE")
    echo
    echo -e "${BLUE}Last updated:${NC} $last_updated"

    # Environment variable overrides
    echo
    echo -e "${BLUE}Environment Overrides:${NC}"
    [[ -n "${LLM_PROVIDER:-}" ]] && echo "  LLM_PROVIDER=$LLM_PROVIDER"
    [[ -n "${LLM_MODEL:-}" ]] && echo "  LLM_MODEL=$LLM_MODEL"
    [[ -n "${LLM_MAX_TOKENS:-}" ]] && echo "  LLM_MAX_TOKENS=$LLM_MAX_TOKENS"
    [[ -n "${LLM_TEMPERATURE:-}" ]] && echo "  LLM_TEMPERATURE=$LLM_TEMPERATURE"
    [[ -n "${ANTHROPIC_API_KEY:-}" ]] && echo "  ANTHROPIC_API_KEY=(set)"
    [[ -n "${LM_STUDIO_URL:-}" ]] && echo "  LM_STUDIO_URL=$LM_STUDIO_URL"

    # No overrides message
    if [[ -z "${LLM_PROVIDER:-}${LLM_MODEL:-}${LLM_MAX_TOKENS:-}${LLM_TEMPERATURE:-}${ANTHROPIC_API_KEY:-}${LM_STUDIO_URL:-}" ]]; then
        echo "  (none)"
    fi
}

# Query available models from provider
query_models() {
    local provider="${1:-$(get_config "provider")}"

    case "$provider" in
        anthropic)
            echo -e "${BLUE}Available Anthropic Models:${NC}"
            echo "  • claude-3-opus-20240229      (most capable, highest cost)"
            echo "  • claude-3-sonnet-20240229    (balanced performance)"
            echo "  • claude-3-haiku-20240307     (fastest, most affordable)"
            echo "  • claude-2.1                   (legacy model)"
            echo "  • claude-2.0                   (legacy model)"
            echo "  • claude-instant-1.2           (legacy fast model)"
            ;;
        lm_studio)
            # Query LM Studio for available models
            local lm_url=$(get_config "lm_studio_url")
            local base_url="${lm_url%/v1/chat/completions}"

            echo -e "${BLUE}Querying LM Studio for models...${NC}"

            # Try to get models from LM Studio
            local response=$(curl -s "${base_url}/v1/models" 2>/dev/null)

            if [[ $? -eq 0 ]] && [[ -n "$response" ]]; then
                # Parse the response
                local models=$(echo "$response" | jq -r '.data[]?.id // empty' 2>/dev/null)

                if [[ -n "$models" ]]; then
                    echo -e "${GREEN}Available LM Studio Models:${NC}"
                    echo "$models" | while read -r model; do
                        echo "  • $model"
                    done
                else
                    echo -e "${YELLOW}No models found. Make sure LM Studio is running and has models loaded.${NC}"
                    echo -e "URL: $base_url/v1/models"
                fi
            else
                echo -e "${RED}Could not connect to LM Studio at $base_url${NC}"
                echo "Make sure LM Studio is running and accessible."
            fi
            ;;
        mock)
            echo -e "${BLUE}Mock Provider (for testing):${NC}"
            echo "  • mock-model (default)"
            echo "  • mock-gpt-4"
            echo "  • mock-llama"
            ;;
        *)
            echo -e "${RED}Unknown provider: $provider${NC}"
            ;;
    esac
}

# Interactive model selection
select_model() {
    local provider=$(get_config "provider")

    echo -e "${BLUE}═══ Model Selection ═══${NC}"
    echo -e "Current provider: ${YELLOW}$provider${NC}"
    echo

    case "$provider" in
        anthropic)
            echo "Select an Anthropic model:"
            echo "1) claude-3-opus-20240229      (most capable)"
            echo "2) claude-3-sonnet-20240229    (balanced)"
            echo "3) claude-3-haiku-20240307     (fast & affordable)"
            echo "4) claude-2.1                  (legacy)"
            echo "5) claude-instant-1.2          (legacy fast)"
            echo
            read -p "Choice (1-5): " choice

            case "$choice" in
                1) set_config "model" "claude-3-opus-20240229" ;;
                2) set_config "model" "claude-3-sonnet-20240229" ;;
                3) set_config "model" "claude-3-haiku-20240307" ;;
                4) set_config "model" "claude-2.1" ;;
                5) set_config "model" "claude-instant-1.2" ;;
                *) echo -e "${RED}Invalid choice${NC}" ;;
            esac
            ;;
        lm_studio)
            # Query and list available models
            local lm_url=$(get_config "lm_studio_url")
            local base_url="${lm_url%/v1/chat/completions}"

            echo "Fetching models from LM Studio..."
            local response=$(curl -s "${base_url}/v1/models" 2>/dev/null)

            if [[ $? -eq 0 ]] && [[ -n "$response" ]]; then
                local models=$(echo "$response" | jq -r '.data[]?.id // empty' 2>/dev/null)

                if [[ -n "$models" ]]; then
                    echo "Available models:"
                    local i=1
                    local model_array=()

                    while IFS= read -r model; do
                        echo "$i) $model"
                        model_array+=("$model")
                        ((i++))
                    done <<< "$models"

                    echo
                    read -p "Choice (1-$((i-1))): " choice

                    if [[ "$choice" -ge 1 ]] && [[ "$choice" -lt "$i" ]]; then
                        set_config "model" "${model_array[$((choice-1))]}"
                    else
                        echo -e "${RED}Invalid choice${NC}"
                    fi
                else
                    echo -e "${YELLOW}No models found in LM Studio${NC}"
                    echo "Please load a model in LM Studio first."
                fi
            else
                echo -e "${RED}Could not connect to LM Studio${NC}"
                echo "Enter model name manually:"
                read -p "Model: " model_name
                [[ -n "$model_name" ]] && set_config "model" "$model_name"
            fi
            ;;
        mock)
            echo "Mock models (for testing):"
            echo "1) mock-model (default)"
            echo "2) mock-gpt-4"
            echo "3) mock-llama"
            echo
            read -p "Choice (1-3): " choice

            case "$choice" in
                1) set_config "model" "mock-model" ;;
                2) set_config "model" "mock-gpt-4" ;;
                3) set_config "model" "mock-llama" ;;
                *) echo -e "${RED}Invalid choice${NC}" ;;
            esac
            ;;
    esac
}

# Export config as environment variables
export_config() {
    ensure_config

    export LLM_PROVIDER=$(get_config "provider")
    export LLM_MODEL=$(get_config "model")
    export LLM_MAX_TOKENS=$(get_config "max_tokens")
    export LLM_TEMPERATURE=$(get_config "temperature")

    # Only export API key if set in config
    local api_key=$(jq -r ".api_key // \"\"" "$CONFIG_FILE")
    [[ -n "$api_key" ]] && export ANTHROPIC_API_KEY="$api_key"

    export LM_STUDIO_URL=$(get_config "lm_studio_url")

    echo -e "${GREEN}✓${NC} Configuration exported to environment"
}

# Main command handler
main() {
    local command="${1:-list}"
    shift || true

    case "$command" in
        get)
            if [[ $# -eq 0 ]]; then
                list_config
            else
                get_config "$1"
            fi
            ;;
        set)
            if [[ $# -eq 0 ]]; then
                echo -e "${RED}Usage: know llm config set <key> [value]${NC}"
                echo "Keys: provider, model, api_key, max_tokens, temperature, lm_studio_url"
                echo
                echo "Special commands:"
                echo "  know llm config set model     # Interactive model selection"
                echo "  know llm config set api_key   # Secure input"
                exit 1
            fi
            set_config "$@"
            ;;
        list|show)
            list_config
            ;;
        models)
            query_models "$@"
            ;;
        export)
            export_config
            ;;
        reset)
            echo -e "${YELLOW}Resetting configuration to defaults...${NC}"
            rm -f "$CONFIG_FILE"
            ensure_config
            echo -e "${GREEN}✓${NC} Configuration reset"
            ;;
        help|--help)
            echo -e "${BLUE}═══ LLM Configuration Help ═══${NC}"
            echo
            echo "Commands:"
            echo "  know llm config                    # Show current configuration"
            echo "  know llm config list               # Same as above"
            echo "  know llm config get <key>          # Get specific value"
            echo "  know llm config set <key> [value]  # Set configuration value"
            echo "  know llm config set model          # Interactive model selection"
            echo "  know llm config set api_key        # Secure API key input"
            echo "  know llm config models [provider]  # List available models"
            echo "  know llm config export             # Export to environment"
            echo "  know llm config reset              # Reset to defaults"
            echo
            echo "Configuration keys:"
            echo "  provider       - LLM provider (anthropic, lm_studio, mock)"
            echo "  model          - Model name/ID"
            echo "  api_key        - API key for provider"
            echo "  max_tokens     - Maximum response tokens"
            echo "  temperature    - Response randomness (0-1)"
            echo "  lm_studio_url  - LM Studio server URL"
            echo
            echo "Examples:"
            echo "  know llm config set provider anthropic"
            echo "  know llm config set model                    # Interactive"
            echo "  know llm config set api_key                  # Secure input"
            echo "  know llm config set temperature 0.5"
            echo "  know llm config models                       # List models"
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo "Use: know llm config help"
            exit 1
            ;;
    esac
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi