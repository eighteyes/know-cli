# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Unix-like system (Linux, macOS, WSL)
- 10MB free disk space

## Quick Start

### Option 1: Automated Install (Recommended)
```bash
# Download and run installer
curl -fsSL https://raw.githubusercontent.com/yourproject/know/main/install.sh | sudo bash
```

### Option 2: Manual Install
```bash
# Clone repository
git clone https://github.com/yourproject/know.git
cd know/know_python

# Install system-wide
sudo make install

# Or install for current user only
make user-install
```

### Option 3: Python Package
```bash
# Install from PyPI (when available)
pip install know-tool

# Install from source
pip install git+https://github.com/yourproject/know.git#subdirectory=know_python
```

## Detailed Installation

### System-Wide Installation (Linux/macOS)

Installs `know` for all users on the system:

```bash
# Using installer script
sudo bash install.sh

# Using make
sudo make install

# Manual installation
sudo mkdir -p /usr/local/lib/know
sudo cp -r know_lib /usr/local/lib/know/
sudo cp know.py /usr/local/lib/know/know.py
sudo tee /usr/local/bin/know > /dev/null << 'EOF'
#!/usr/bin/env bash
exec python3 /usr/local/lib/know/know.py "$@"
EOF
sudo chmod +x /usr/local/bin/know
```

**Result**: `know` command available globally

### User Installation

Installs `know` for current user only (no sudo required):

```bash
# Using make
make user-install

# Manual installation
mkdir -p ~/.local/lib/know ~/.local/bin
cp -r know_lib ~/.local/lib/know/
cp know.py ~/.local/lib/know/know.py
cat > ~/.local/bin/know << 'EOF'
#!/usr/bin/env bash
exec python3 ~/.local/lib/know/know.py "$@"
EOF
chmod +x ~/.local/bin/know

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

**Result**: `know` command available for current user

### Development Installation

For contributing or testing:

```bash
# Clone repository
git clone https://github.com/yourproject/know.git
cd know/know_python

# Install in development mode
make dev

# Or use pip editable install (if pip available)
pip install -e .

# Run tests
make test
```

**Result**: `./know-dev` command for testing

### Docker Installation

For isolated environment:

```bash
# Pull image (when available)
docker pull yourproject/know-tool

# Or build locally
docker build -t know-tool .

# Create alias for easy use
alias know='docker run -v $(pwd):/workspace know-tool'
```

**Result**: `know` command via Docker

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Install Python if needed
sudo apt update
sudo apt install python3 python3-pip

# Install know
curl -fsSL https://raw.githubusercontent.com/yourproject/know/main/install.sh | sudo bash

# Enable completions
echo "source /etc/bash_completion.d/know" >> ~/.bashrc
```

### Fedora/RHEL/CentOS

```bash
# Install Python if needed
sudo dnf install python3

# Install know
curl -fsSL https://raw.githubusercontent.com/yourproject/know/main/install.sh | sudo bash
```

### macOS

```bash
# Using Homebrew (when formula is published)
brew install know-tool

# Or manual install
curl -fsSL https://raw.githubusercontent.com/yourproject/know/main/install.sh | bash

# If Python not installed
brew install python@3.11
```

### Windows (WSL2)

```bash
# In WSL2 terminal
sudo apt update
sudo apt install python3

# Install know
curl -fsSL https://raw.githubusercontent.com/yourproject/know/main/install.sh | sudo bash
```

### Arch Linux

```bash
# Install Python if needed
sudo pacman -S python

# Install know
git clone https://github.com/yourproject/know.git
cd know/know_python
sudo make install
```

## Configuration

### Setting Default Graph Location

```bash
# Set environment variable (add to ~/.bashrc or ~/.zshrc)
export KNOW_GRAPH_PATH="/path/to/your/spec-graph.json"

# Or use project-specific .envrc (with direnv)
echo 'export KNOW_GRAPH_PATH="${PWD}/.ai/spec-graph.json"' > .envrc
direnv allow
```

### Enabling Shell Completions

#### Bash
```bash
# Add to ~/.bashrc
if [ -f /etc/bash_completion.d/know ]; then
    source /etc/bash_completion.d/know
fi
```

#### Zsh
```bash
# Add to ~/.zshrc
fpath=(/usr/share/zsh/site-functions $fpath)
autoload -U compinit && compinit
```

#### Fish
```fish
# Create completion file
mkdir -p ~/.config/fish/completions
echo 'complete -c know -a "list get add deps validate stats"' > ~/.config/fish/completions/know.fish
```

## Verification

After installation, verify everything works:

```bash
# Check installation
know --version

# Initialize a test project
mkdir test-project && cd test-project
know init

# Test basic commands
know list
know stats
know validate

# Test completions (press TAB)
know <TAB><TAB>

# View documentation
man know  # If man page installed
know --help
```

## Upgrading

### From Bash Version

If upgrading from the original bash implementation:

```bash
# Backup existing graph
cp .ai/spec-graph.json .ai/spec-graph.json.backup

# Install Python version
sudo make install

# Verify compatibility
know validate
```

### Updating Python Version

```bash
# Using installer
sudo bash install.sh

# Using make
sudo make uninstall
sudo make install

# Using pip
pip install --upgrade know-tool
```

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| `know: command not found` | Add installation directory to PATH |
| `Python 3 is required` | Install Python: `sudo apt install python3` |
| `No module named 'know_lib'` | Reinstall: `sudo make install` |
| `Permission denied` | Use sudo for system install or try user install |
| `No spec-graph.json found` | Run `know init` or set `KNOW_GRAPH_PATH` |

### Debug Mode

```bash
# Run with Python directly for debugging
python3 /usr/local/lib/know/know.py --help

# Check Python version
python3 --version

# Verify installation files
ls -la /usr/local/lib/know/
ls -la /usr/local/bin/know

# Check environment
echo $PATH
echo $KNOW_GRAPH_PATH
```

### Getting Help

1. Check documentation: `know --help`
2. Read man page: `man know`
3. View online docs: [GitHub Documentation](https://github.com/yourproject/know)
4. Report issues: [GitHub Issues](https://github.com/yourproject/know/issues)

## Uninstallation

### Remove System Installation

```bash
# Using uninstaller
sudo know-uninstall

# Using make
sudo make uninstall

# Manual removal
sudo rm -rf /usr/local/lib/know
sudo rm -f /usr/local/bin/know
sudo rm -f /etc/bash_completion.d/know
sudo rm -f /usr/share/zsh/site-functions/_know
sudo rm -f /usr/local/share/man/man1/know.1
```

### Remove User Installation

```bash
rm -rf ~/.local/lib/know
rm -f ~/.local/bin/know
rm -f ~/.config/bash_completion.d/know
```

### Remove pip Installation

```bash
pip uninstall know-tool
```

## Optional Dependencies

The tool works without these, but they enhance functionality:

```bash
# Full feature set (when pip available)
pip install click pydantic networkx rich aiofiles python-dotenv

# Development dependencies
pip install pytest pytest-cov black mypy
```

## Security Notes

- The tool only reads/writes the specified graph file
- No network connections required
- No telemetry or data collection
- Runs with user permissions (sudo only for installation)

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: This guide and `know --help`
- **Issues**: [GitHub Issues](https://github.com/yourproject/know/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourproject/know/discussions)
- **Email**: support@yourproject.com