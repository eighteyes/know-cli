# Virtual Environment Setup

## Overview

The `know` tool now uses system-level virtual environments instead of project-local venvs to avoid conflicts between different environments (Docker, macOS, Linux, etc.).

## Locations

### User Installation
- **Venv**: `~/.local/venvs/know`
- **Binary**: `~/.local/bin/know`
- **Library**: `~/.local/lib/know`

### System Installation (requires sudo)
- **Venv**: `/usr/local/lib/know-venv`
- **Binary**: `/usr/local/bin/know`
- **Library**: `/usr/local/lib/know`

### Development Setup
- **Venv**: `~/.local/venvs/know`
- **Script**: `./know/know` (in project directory)

## Why System Venv?

1. **Cross-environment compatibility**: Venvs created on different platforms (Docker vs macOS) are not compatible
2. **No project pollution**: Keeps the project directory clean
3. **Centralized dependencies**: One venv can be used by multiple projects
4. **Easy management**: Simple to update or remove

## Installation Methods

### Method 1: User Install (Recommended for Development)
```bash
cd /Users/god/work/lb-www/know
make user-install
```

This creates:
- `~/.local/venvs/know` - Virtual environment with all dependencies
- `~/.local/bin/know` - Executable wrapper that uses the venv

### Method 2: System Install (Requires sudo)
```bash
cd /Users/god/work/lb-www/know
sudo make install
```

This creates:
- `/usr/local/lib/know-venv` - System-wide virtual environment
- `/usr/local/bin/know` - System command available to all users

### Method 3: Local Install Script
```bash
cd /Users/god/work/lb-www/know
./install-local.sh
```

Same as Method 1 but with more verbose output.

## Fallback Behavior

All wrapper scripts follow this priority:

1. **System venv** (`~/.local/venvs/know/bin/python3` or `/usr/local/lib/know-venv/bin/python3`)
2. **Local venv** (if `./venv/bin/python3` exists - for backwards compatibility)
3. **System Python** (`python3` in PATH)

## Testing the Setup

```bash
# Check which Python is being used
which know

# Verify it's using the venv
head -20 $(which know)

# Test that it works
know --help
know -g .ai/spec-graph.json stats
```

## Updating Dependencies

### User venv:
```bash
~/.local/venvs/know/bin/pip install --upgrade click rich pydantic networkx
```

### System venv (requires sudo):
```bash
sudo /usr/local/lib/know-venv/bin/pip install --upgrade click rich pydantic networkx
```

## Removing/Reinstalling

### Remove user installation:
```bash
rm -rf ~/.local/venvs/know ~/.local/bin/know ~/.local/lib/know
```

### Remove system installation:
```bash
sudo know-uninstall
# or manually:
sudo rm -rf /usr/local/lib/know /usr/local/lib/know-venv /usr/local/bin/know
```

### Fresh reinstall:
```bash
# Remove old installation
rm -rf ~/.local/venvs/know ~/.local/bin/know ~/.local/lib/know

# Remove any local venv in project
cd /Users/god/work/lb-www/know
rm -rf venv

# Reinstall
make user-install

# or if you prefer the installer script
./install-local.sh
```

## Files Modified

The following files were updated to support system venv:

1. **`know/know`** - Launcher script (checks for system venv first)
2. **`install.sh`** - System installer (creates `/usr/local/lib/know-venv`)
3. **`install-local.sh`** - User installer (creates `~/.local/venvs/know`)
4. **`Makefile`** - Build targets (updated `user-install`)
5. **`CONTRIBUTING.md`** - Developer docs (updated setup instructions)
6. **`.gitignore`** - Added venv patterns

## Troubleshooting

### Command not found
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Module not found errors
```bash
# Reinstall dependencies
~/.local/venvs/know/bin/pip install click rich pydantic networkx
```

### Using wrong Python
```bash
# Check which Python know is using
grep -A 5 "PYTHON=" $(which know)

# Should show something like:
# VENV_PYTHON="$HOME/.local/venvs/know/bin/python3"
```

### Venv doesn't exist
```bash
# Recreate it
python3 -m venv ~/.local/venvs/know
~/.local/venvs/know/bin/pip install click rich pydantic networkx
```

## Benefits

✅ No conflicts between Docker and macOS venvs
✅ Clean project directory
✅ One venv for all projects using `know`
✅ Easy to update dependencies centrally
✅ Works with all installation methods
✅ Automatic fallback to system Python if venv missing

## Migration from Old Setup

If you previously had a local venv in the project:

```bash
# 1. Remove old venv
cd /Users/god/work/lb-www/know
rm -rf venv

# 2. Install using new method
make user-install

# 3. Verify it works
./know/know -g ../.ai/spec-graph.json stats
```

The old venv was platform-specific and won't work across different environments. The new system venv is created fresh on your machine.
