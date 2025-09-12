#!/bin/bash

# screen-spec.sh - Screen specification generator

set -euo pipefail

# Get script directory for template location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Choose template based on AI mode
if [[ "${AI_MODE:-false}" == "true" ]]; then
    TEMPLATE_FILE="$SCRIPT_DIR/../templates/screen-ai.md"
else
    TEMPLATE_FILE="$SCRIPT_DIR/../templates/screen.md"
fi

# Load library functions
source "$LIB_DIR/utils.sh"
source "$LIB_DIR/resolve.sh"
source "$LIB_DIR/query.sh"
source "$LIB_DIR/render.sh"

# Generate screen specification
generate_screen_spec() {
    local entity_ref="$1"
    local format="${2:-md}"
    
    # Validate entity type
    if [[ ! "$entity_ref" =~ ^screens: ]]; then
        error "Expected screens entity, got: $entity_ref"
    fi
    
    # Render template
    render_template "$TEMPLATE_FILE" "$entity_ref" "$format"
}

# Main entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    generate_screen_spec "$@"
fi