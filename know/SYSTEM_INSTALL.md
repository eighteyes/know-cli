# Know Tool - System CLI Installation Guide

## Quick Install Options

### 1. Script Install (Recommended)
```bash
# Download and run installer
sudo bash install.sh
```

### 2. Make Install
```bash
# System-wide installation
sudo make install

# User-only installation
make user-install

# Development mode
make dev
```

### 3. Manual Installation
```bash
# Copy files manually
sudo cp -r know_lib /usr/local/lib/know/
sudo cp know_minimal.py /usr/local/lib/know/know.py

# Create executable
sudo tee /usr/local/bin/know << 'EOF'
#!/usr/bin/env bash
exec python3 /usr/local/lib/know/know.py "$@"
EOF
sudo chmod +x /usr/local/bin/know
```

## Platform-Specific Installation

### macOS (Homebrew)
```bash
# Once published to Homebrew
brew install know-tool

# Or from local formula
brew install --build-from-source know.rb
```

### Ubuntu/Debian (apt)
```bash
# Add to PATH via update-alternatives
sudo update-alternatives --install /usr/bin/know know /usr/local/bin/know 100

# Or create .deb package
dpkg-deb --build know-package/
sudo dpkg -i know-tool_1.0.0_all.deb
```

### Fedora/RHEL (rpm)
```bash
# Create RPM package
rpmbuild -bb know.spec
sudo rpm -i know-tool-1.0.0.rpm
```

### Arch Linux (AUR)
```bash
# Create PKGBUILD
makepkg -si
```

### Python Package (pip)
```bash
# Install from PyPI (when published)
pip install know-tool

# Install from local
pip install .

# Install with all features
pip install know-tool[full]

# Development install
pip install -e .[dev]
```

## Docker Installation
```dockerfile
# Dockerfile
FROM python:3.11-slim
COPY know_lib /app/know_lib
COPY know_minimal.py /app/know.py
WORKDIR /app
ENTRYPOINT ["python3", "know.py"]
```

```bash
# Build and use
docker build -t know-tool .
docker run -v $(pwd):/workspace know-tool list
```

## PATH Configuration

### Option 1: System-wide
```bash
# Already in PATH after install
which know  # /usr/local/bin/know
```

### Option 2: User PATH
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

### Option 3: Alias
```bash
# Add to shell config
alias know='python3 /path/to/know.py'
```

### Option 4: Symlink
```bash
# Create symbolic link
ln -s /absolute/path/to/know.py /usr/local/bin/know
```

## Environment Configuration

### Graph Path Resolution
The tool searches for `spec-graph.json` in this order:

1. `--graph-path` command argument
2. `KNOW_GRAPH_PATH` environment variable
3. `.ai/spec-graph.json` in current directory
4. `.ai/spec-graph.json` in parent directories (recursive)
5. Creates new if `know init` is run

### Environment Variables
```bash
# Set default graph location
export KNOW_GRAPH_PATH="/path/to/spec-graph.json"

# Set for specific project
cd /my/project
export KNOW_GRAPH_PATH="$(pwd)/.ai/spec-graph.json"
```

### Per-Project Configuration
```bash
# .envrc (for direnv users)
export KNOW_GRAPH_PATH="${PWD}/.ai/spec-graph.json"

# Project script
#!/bin/bash
KNOW_GRAPH_PATH="$(git rev-parse --show-toplevel)/.ai/spec-graph.json" know "$@"
```

## Shell Integration

### Bash Completion
```bash
# Enable for session
source /etc/bash_completion.d/know

# Add to ~/.bashrc
if [ -f /etc/bash_completion.d/know ]; then
    . /etc/bash_completion.d/know
fi
```

### Zsh Completion
```bash
# Add to ~/.zshrc
fpath=(/usr/share/zsh/site-functions $fpath)
autoload -U compinit && compinit
```

### Fish Completion
```fish
# Save to ~/.config/fish/completions/know.fish
complete -c know -a "list get add deps validate stats"
complete -c know -f -n "__fish_seen_subcommand_from list" \
    -a "users features components interfaces"
```

## Advanced Setups

### Multi-Project Setup
```bash
# Create wrapper script: /usr/local/bin/know-project
#!/bin/bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
GRAPH_PATH="$PROJECT_ROOT/.ai/spec-graph.json"

if [ ! -f "$GRAPH_PATH" ]; then
    echo "No spec-graph.json found in $PROJECT_ROOT"
    echo "Run 'know init' to create one"
    exit 1
fi

exec know --graph-path "$GRAPH_PATH" "$@"
```

### CI/CD Integration
```yaml
# GitHub Actions
- name: Install Know Tool
  run: |
    curl -L https://github.com/project/know/releases/latest/download/know-linux-amd64 -o know
    chmod +x know
    sudo mv know /usr/local/bin/

# GitLab CI
before_script:
  - pip install know-tool
  - know validate

# Jenkins
sh '''
  python3 -m pip install know-tool
  know stats
  know validate
'''
```

### Systemd Service
```bash
# Enable graph watching service
sudo systemctl enable know-watcher
sudo systemctl start know-watcher

# Check status
systemctl status know-watcher
```

## Verification

### Test Installation
```bash
# Check version
know --version

# Test basic commands
know init
know list
know stats
know validate

# Check man page
man know

# Test completions
know <TAB><TAB>
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Command not found | Check PATH: `echo $PATH` |
| Python not found | Install Python 3: `apt install python3` |
| Permission denied | Use sudo or check permissions |
| No graph found | Run `know init` or set KNOW_GRAPH_PATH |
| Import errors | Install dependencies: `pip install -r requirements.txt` |

## Uninstallation

### Script Uninstall
```bash
sudo know-uninstall
```

### Make Uninstall
```bash
sudo make uninstall
```

### Manual Uninstall
```bash
sudo rm -rf /usr/local/lib/know
sudo rm /usr/local/bin/know
sudo rm /etc/bash_completion.d/know
sudo rm /usr/share/zsh/site-functions/_know
```

### Package Manager
```bash
# Homebrew
brew uninstall know-tool

# pip
pip uninstall know-tool

# apt
sudo apt remove know-tool

# rpm
sudo rpm -e know-tool
```

## Security Considerations

### File Permissions
```bash
# Secure installation
sudo chmod 755 /usr/local/bin/know
sudo chmod -R 644 /usr/local/lib/know/
sudo find /usr/local/lib/know -type d -exec chmod 755 {} \;
```

### Graph File Security
```bash
# Protect sensitive graphs
chmod 600 .ai/spec-graph.json  # Owner only
chmod 640 .ai/spec-graph.json  # Owner + group read
```

### Audit Installation
```bash
# Check what was installed
find /usr/local -name "*know*" 2>/dev/null
find ~/.local -name "*know*" 2>/dev/null
```

## Best Practices

1. **System Install**: Use for shared/production environments
2. **User Install**: Use for personal development
3. **Virtual Environment**: Use for project-specific versions
4. **Docker**: Use for CI/CD and isolated environments
5. **Symlinks**: Use for multiple versions/testing

## Support

- Check installation: `know --help`
- View logs: `journalctl -u know-watcher`
- Report issues: GitHub issues page
- Documentation: `man know` or this guide