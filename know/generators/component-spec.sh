#!/bin/bash

# component-spec.sh - Component specification generator

set -euo pipefail

# Get script directory for template location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/../templates/component.md"

# Generate component specification
generate_component_spec() {
    local entity_ref="$1"
    local format="${2:-md}"
    
    # Validate entity type
    if [[ ! "$entity_ref" =~ ^components: ]]; then
        error "Expected components entity, got: $entity_ref"
    fi
    
    # Render template
    render_template "$TEMPLATE_FILE" "$entity_ref" "$format"
}

# Main entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    generate_component_spec "$@"
fi