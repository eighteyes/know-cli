#!/bin/bash

# mod-graph-enhanced.sh - Enhanced graph modifications with dependency rule enforcement

set -euo pipefail

# Source the original mod-graph and dynamic commands
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/dynamic-commands.sh"

# Original mod-graph location
ORIG_MOD_GRAPH="$SCRIPT_DIR/mod-graph.sh"

# Enhanced connect function with rule validation
connect_with_validation() {
    local from_ref="$1"
    local to_ref="$2"

    # Validate the connection against rules
    if ! enforce_connection_rules "$from_ref" "$to_ref"; then
        echo ""
        echo "Connection blocked by dependency rules."
        echo "Use 'know rules' to see allowed dependencies."
        return 1
    fi

    # If valid, proceed with original connect
    "$ORIG_MOD_GRAPH" connect "$from_ref" "$to_ref"
}

# Main dispatcher
case "${1:-}" in
    connect)
        shift
        connect_with_validation "$@"
        ;;
    *)
        # Pass through to original mod-graph
        exec "$ORIG_MOD_GRAPH" "$@"
        ;;
esac