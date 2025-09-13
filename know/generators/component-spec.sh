#!/bin/bash

# component-spec.sh - Component specification generator

set -euo pipefail

# Get script directory for template location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/../templates/component.md"
KNOW_DIR="$(dirname "$SCRIPT_DIR")"
LIB_DIR="$KNOW_DIR/lib"

# Source required libraries (order matters!)
source "$LIB_DIR/utils.sh"
source "$LIB_DIR/query.sh"
source "$LIB_DIR/resolve.sh"
source "$LIB_DIR/render.sh"

# Generate component specification
generate_component_spec() {
    local entity_ref="$1"
    local format="${2:-md}"
    
    # Validate entity type
    if [[ ! "$entity_ref" =~ ^component: ]]; then
        error "Expected component entity, got: $entity_ref"
    fi
    
    # Render template
    render_template "$TEMPLATE_FILE" "$entity_ref" "$format"
}

# Main entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    generate_component_spec "$@"
fi