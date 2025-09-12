#!/bin/bash

# api-spec.sh - API specification generator

set -euo pipefail

# Get script directory for template location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/../templates/api.yaml"

# Load library functions
source "$LIB_DIR/utils.sh"
source "$LIB_DIR/resolve.sh"
source "$LIB_DIR/query.sh"
source "$LIB_DIR/render.sh"

# Generate API specification
generate_api_spec() {
    local entity_ref="$1"
    local format="${2:-yaml}"
    
    # Validate entity type (schema entities for APIs)
    if [[ ! "$entity_ref" =~ ^schema: ]]; then
        error "Expected schema entity for API generation, got: $entity_ref"
    fi
    
    # Render template
    render_template "$TEMPLATE_FILE" "$entity_ref" "$format"
}

# Main entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    generate_api_spec "$@"
fi