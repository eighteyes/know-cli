#!/usr/bin/env bash

# Know Tool Local Installation Script
# Installs the know tool to user's local bin directory

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"
KNOW_LIB_DIR="${HOME}/.local/lib/know"

echo "================================"
echo "Know Tool Local Installation"
echo "================================"
echo

# Create directories
echo "📁 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$KNOW_LIB_DIR"
mkdir -p "${HOME}/.local/venvs"

# Create venv and install dependencies
echo "🐍 Creating virtual environment..."
VENV_DIR="${HOME}/.local/venvs/know"
if python3 -m venv "$VENV_DIR" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    "$VENV_DIR/bin/pip" install --quiet click pydantic networkx rich aiofiles python-dotenv 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Warning: Some dependencies couldn't be installed${NC}"
    }
else
    echo -e "${YELLOW}⚠️  Warning: Could not create venv - using system Python${NC}"
fi

# Copy the know library
echo "📦 Copying know library..."
cp -r "$SCRIPT_DIR/know_lib" "$KNOW_LIB_DIR/"

# Copy the Python implementation
echo "📦 Copying know tool..."
cp "$SCRIPT_DIR/know.py" "$KNOW_LIB_DIR/know.py"

# Create the wrapper script
echo "🔗 Creating wrapper script..."
cat > "$INSTALL_DIR/know" << 'EOF'
#!/usr/bin/env bash

# Know Tool - Local CLI Wrapper
# This wrapper enables know to work from any directory

# Default graph location (can be overridden)
DEFAULT_GRAPH="${KNOW_GRAPH_PATH:-$PWD/.ai/spec-graph.json}"

# Find the installation directory and venv
KNOW_LIB_DIR="${HOME}/.local/lib/know"
VENV_PYTHON="${HOME}/.local/venvs/know/bin/python3"

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

# If no graph found, show error
if [ -z "$GRAPH_PATH" ]; then
    echo "Error: No spec-graph.json found in current directory or parents"
    echo "Looking for: .ai/spec-graph.json"
    exit 1
fi

# Run the Python implementation with graph path
cd "$PWD"
exec "$PYTHON" "$KNOW_LIB_DIR/know.py" "$@"
EOF

# Make executable
chmod +x "$INSTALL_DIR/know"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo
    echo -e "${YELLOW}⚠️  Warning: $INSTALL_DIR is not in your PATH${NC}"
    echo
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo
    echo "Then reload your shell:"
    echo "  source ~/.bashrc  # or source ~/.zshrc"
else
    echo -e "${GREEN}✅ $INSTALL_DIR is already in PATH${NC}"
fi

echo
echo "================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "================================"
echo

# Test the installation
if command -v know &> /dev/null; then
    echo -e "${GREEN}🎉 Know tool is ready to use!${NC}"
    echo
    echo "Try these commands:"
    echo "  know list           # List all entities"
    echo "  know list feature   # List features"
    echo "  know stats          # Show graph statistics"
    echo "  know --help         # Show help"
else
    echo "📝 To use know immediately, run:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "  know --help"
fi

echo
echo "To uninstall:"
echo "  rm -rf ~/.local/lib/know ~/.local/bin/know ~/.local/venvs/know"
echo
