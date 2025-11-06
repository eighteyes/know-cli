#!/usr/bin/env bash

# Know Tool System Installation Script
# Installs the know tool as a system-wide CLI command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Installation directories
INSTALL_DIR="/usr/local/lib/know"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/know"

# Check if running as root/sudo
check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}This script must be run as root or with sudo${NC}"
        exit 1
    fi
}

# Check Python 3 availability
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is required but not installed${NC}"
        echo "Please install Python 3 first:"
        echo "  Ubuntu/Debian: sudo apt-get install python3"
        echo "  RHEL/CentOS: sudo yum install python3"
        echo "  macOS: brew install python3"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
}

# Install Python dependencies in a system venv
install_dependencies() {
    echo "Installing Python dependencies..."

    # Create system venv
    VENV_DIR="/usr/local/lib/know-venv"

    if ! python3 -m venv "$VENV_DIR" 2>/dev/null; then
        echo -e "${YELLOW}Warning: Could not create venv - using system Python${NC}"
        return
    fi

    # Install dependencies in venv
    if "$VENV_DIR/bin/pip" install --quiet click pydantic networkx rich aiofiles python-dotenv 2>/dev/null; then
        echo -e "${GREEN}✓ Dependencies installed in system venv${NC}"
    else
        echo -e "${YELLOW}Warning: Some optional dependencies couldn't be installed${NC}"
        echo "The tool will work with reduced features"
    fi
}

# Install know tool files
install_know() {
    echo "Installing know tool..."

    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"

    # Copy Python files
    cp -r know_lib "$INSTALL_DIR/"
    cp know.py "$INSTALL_DIR/know.py"

    # Create the main executable wrapper
    cat > "$BIN_DIR/know" << 'EOF'
#!/usr/bin/env bash

# Know Tool - System CLI Wrapper
# This wrapper enables know to work from any directory

# Default graph location (can be overridden)
DEFAULT_GRAPH="${KNOW_GRAPH_PATH:-$PWD/.ai/spec-graph.json}"

# Find the installation directory and venv
KNOW_INSTALL_DIR="/usr/local/lib/know"
VENV_PYTHON="/usr/local/lib/know-venv/bin/python3"

# Use venv Python if available, otherwise system Python
if [ -f "$VENV_PYTHON" ]; then
    PYTHON="$VENV_PYTHON"
else
    PYTHON="python3"
fi

# Check for local .ai/spec-graph.json or use specified path
if [ -f ".ai/spec-graph.json" ]; then
    GRAPH_PATH=".ai/spec-graph.json"
elif [ -f "$DEFAULT_GRAPH" ]; then
    GRAPH_PATH="$DEFAULT_GRAPH"
else
    # Try to find a graph file in parent directories
    SEARCH_DIR="$PWD"
    while [ "$SEARCH_DIR" != "/" ]; do
        if [ -f "$SEARCH_DIR/.ai/spec-graph.json" ]; then
            GRAPH_PATH="$SEARCH_DIR/.ai/spec-graph.json"
            break
        fi
        SEARCH_DIR=$(dirname "$SEARCH_DIR")
    done
fi

# If no graph found and not creating one, show help
if [ -z "$GRAPH_PATH" ] && [ "$1" != "init" ]; then
    echo "No spec-graph.json found. Use 'know init' to create one."
    GRAPH_PATH="/tmp/empty-graph.json"
fi

# Run the Python implementation
exec "$PYTHON" "$KNOW_INSTALL_DIR/know.py" --graph-path "${GRAPH_PATH}" "$@"
EOF

    # Make executable
    chmod +x "$BIN_DIR/know"

    echo -e "${GREEN}✓ Know tool installed to $BIN_DIR/know${NC}"
}

# Create shell completions
install_completions() {
    echo "Installing shell completions..."

    # Detect OS for completion paths
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS paths
        BASH_COMPLETION_DIR="/usr/local/etc/bash_completion.d"
        ZSH_COMPLETION_DIR="/usr/local/share/zsh/site-functions"
    else
        # Linux paths
        BASH_COMPLETION_DIR="/etc/bash_completion.d"
        ZSH_COMPLETION_DIR="/usr/share/zsh/site-functions"
    fi

    # Bash completion
    mkdir -p "$BASH_COMPLETION_DIR"
    cat > "$BASH_COMPLETION_DIR/know" << 'EOF'
# Bash completion for know tool
_know_completions() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    commands="list get add deps dependents validate cycles stats build-order init help"

    # Entity types
    entity_types="users features interfaces components requirements objectives actions behavior"

    case "${prev}" in
        know)
            COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
            return 0
            ;;
        list)
            COMPREPLY=( $(compgen -W "${entity_types}" -- ${cur}) )
            return 0
            ;;
        get|deps|dependents)
            # Complete with existing entities (if graph exists)
            if [ -f ".ai/spec-graph.json" ]; then
                local entities=$(know list 2>/dev/null | grep ':' || true)
                COMPREPLY=( $(compgen -W "${entities}" -- ${cur}) )
            fi
            return 0
            ;;
    esac
}

complete -F _know_completions know
EOF

    # Zsh completion (basic)
    mkdir -p "$ZSH_COMPLETION_DIR" 2>/dev/null || true
    if [ -d "$ZSH_COMPLETION_DIR" ] && [ -w "$ZSH_COMPLETION_DIR" ]; then
        cat > "$ZSH_COMPLETION_DIR/_know" << 'EOF'
#compdef know

_know() {
    local -a commands
    commands=(
        'list:List entities'
        'get:Get entity details'
        'add:Add new entity'
        'deps:Show dependencies'
        'dependents:Show dependents'
        'validate:Validate graph'
        'cycles:Detect cycles'
        'stats:Show statistics'
        'build-order:Show build order'
        'init:Initialize new graph'
        'help:Show help'
    )

    _describe 'command' commands
}
EOF
        echo -e "${GREEN}✓ Zsh completions installed to $ZSH_COMPLETION_DIR${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping Zsh completions (directory not writable)${NC}"
    fi

    echo -e "${GREEN}✓ Bash completions installed to $BASH_COMPLETION_DIR${NC}"
}

# Create man page
install_man_page() {
    echo "Installing man page..."

    mkdir -p /usr/local/share/man/man1
    cat > /usr/local/share/man/man1/know.1 << 'EOF'
.TH KNOW 1 "2024" "Know Tool" "User Commands"
.SH NAME
know \- Manage specification graphs for software projects
.SH SYNOPSIS
.B know
[\fI\-g GRAPH_PATH\fR]
\fICOMMAND\fR
[\fIARGS\fR]
.SH DESCRIPTION
Know is a high-performance tool for managing specification graphs that define
relationships between users, features, components, and other project entities.
.PP
It provides efficient graph operations, dependency resolution, and validation
capabilities for complex software projects.
.SH COMMANDS
.TP
.B list \fR[\fITYPE\fR]
List all entities or entities of a specific type
.TP
.B get \fIENTITY\fR
Display details of a specific entity
.TP
.B deps \fIENTITY\fR
Show dependencies of an entity
.TP
.B dependents \fIENTITY\fR
Show what depends on an entity
.TP
.B add \fITYPE\fR \fIKEY\fR \fIDATA\fR
Add a new entity to the graph
.TP
.B validate
Validate graph structure and dependencies
.TP
.B cycles
Detect circular dependencies
.TP
.B stats
Display graph statistics
.TP
.B build\-order
Show topological build order
.TP
.B init
Initialize a new specification graph
.SH OPTIONS
.TP
.B \-g, \-\-graph\-path \fIPATH\fR
Specify path to spec-graph.json (default: .ai/spec-graph.json)
.SH ENVIRONMENT
.TP
.B KNOW_GRAPH_PATH
Default path to specification graph file
.SH FILES
.TP
.I .ai/spec-graph.json
Default specification graph location
.TP
.I /usr/local/lib/know/
Installation directory
.TP
.I /etc/know/
Configuration directory
.SH EXAMPLES
.TP
List all entities:
.B know list
.TP
Get user details:
.B know get user:owner
.TP
Show feature dependencies:
.B know deps feature:auth
.TP
Validate the graph:
.B know validate
.SH AUTHOR
Written for the LB project.
.SH SEE ALSO
Full documentation at: https://github.com/yourproject/know
EOF

    # Update man database
    if command -v mandb &> /dev/null; then
        mandb -q
    fi

    echo -e "${GREEN}✓ Man page installed (use 'man know' to view)${NC}"
}

# Create systemd service for graph watching (optional - Linux only)
install_systemd_service() {
    # Skip on macOS - systemd is Linux-only
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Skipping systemd service (not available on macOS)..."
        return 0
    fi

    echo "Creating optional systemd service..."

    cat > /etc/systemd/system/know-watcher.service << 'EOF'
[Unit]
Description=Know Graph File Watcher
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/know watch
Restart=on-failure
User=nobody
Environment="KNOW_GRAPH_PATH=/var/lib/know/spec-graph.json"

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${GREEN}✓ Systemd service created (not enabled by default)${NC}"
    echo "  To enable: systemctl enable know-watcher"
}

# Create init command for new projects
create_init_command() {
    # Add init command to the Python script
    cat >> "$INSTALL_DIR/know_init.py" << 'EOF'
#!/usr/bin/env python3
"""Initialize a new specification graph"""

import json
import os
import sys
from pathlib import Path

def init_graph(path=".ai/spec-graph.json"):
    """Create a new specification graph"""

    graph_path = Path(path)

    if graph_path.exists():
        print(f"Graph already exists at {graph_path}")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Create directory if needed
    graph_path.parent.mkdir(parents=True, exist_ok=True)

    # Create default graph structure
    default_graph = {
        "meta": {
            "version": "1.0.0",
            "project": os.path.basename(os.getcwd()),
            "created": str(Path.cwd()),
            "phases": {}
        },
        "references": {},
        "entities": {
            "users": {},
            "requirements": {},
            "interfaces": {},
            "features": {},
            "components": {},
            "behaviors": {},
            "objectives": {},
            "actions": {}
        },
        "graph": {}
    }

    # Write the graph
    with open(graph_path, 'w') as f:
        json.dump(default_graph, f, indent=2)

    print(f"✓ Created new specification graph at {graph_path}")
    print("\nQuick start:")
    print("  know add users owner '{\"name\": \"Owner\", \"role\": \"admin\"}'")
    print("  know add features auth '{\"description\": \"Authentication\"}'")
    print("  know add-dep features:auth users:owner")
    print("  know validate")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        init_graph(sys.argv[1])
    else:
        init_graph()
EOF
    chmod +x "$INSTALL_DIR/know_init.py"
}

# Uninstall function
create_uninstaller() {
    cat > /usr/local/bin/know-uninstall << 'EOF'
#!/bin/bash
echo "Uninstalling know tool..."
sudo rm -rf /usr/local/lib/know
sudo rm -rf /usr/local/lib/know-venv
sudo rm -f /usr/local/bin/know
sudo rm -f /usr/local/bin/know-uninstall
# macOS paths
sudo rm -f /usr/local/etc/bash_completion.d/know
sudo rm -f /usr/local/share/zsh/site-functions/_know
# Linux paths
sudo rm -f /etc/bash_completion.d/know
sudo rm -f /usr/share/zsh/site-functions/_know
sudo rm -f /usr/local/share/man/man1/know.1
sudo rm -f /etc/systemd/system/know-watcher.service
echo "✓ Know tool uninstalled"
EOF
    chmod +x /usr/local/bin/know-uninstall
    echo -e "${GREEN}✓ Uninstaller created at /usr/local/bin/know-uninstall${NC}"
}

# Main installation
main() {
    echo "================================"
    echo "Know Tool System Installation"
    echo "================================"
    echo

    check_root
    check_python
    install_dependencies
    install_know
    create_init_command
    install_completions
    install_man_page
    install_systemd_service
    create_uninstaller

    echo
    echo "================================"
    echo -e "${GREEN}Installation Complete!${NC}"
    echo "================================"
    echo
    echo "The 'know' command is now available system-wide."
    echo
    echo "Quick start:"
    echo "  know --help          # Show help"
    echo "  know init            # Initialize new project"
    echo "  know list            # List entities"
    echo "  know stats           # Show statistics"
    echo
    echo "Shell completion:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  Bash: Add to ~/.bash_profile:"
        echo "        [ -f /usr/local/etc/bash_completion.d/know ] && . /usr/local/etc/bash_completion.d/know"
        echo "  Zsh:  Completions auto-load from /usr/local/share/zsh/site-functions"
    else
        echo "  Bash: source /etc/bash_completion.d/know"
        echo "  Zsh: autoload -U compinit && compinit"
    fi
    echo
    echo "To uninstall:"
    echo "  sudo know-uninstall"
    echo
}

# Run installation
main "$@"