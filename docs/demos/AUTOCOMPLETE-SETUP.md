# Know Command Autocomplete Setup

## Quick Setup

```bash
# Install autocomplete
./know/know --install-completion

# For Bash users - add to ~/.bashrc:
source ~/.local/share/bash-completion/completions/know

# For Zsh users - add to ~/.zshrc:
autoload -U bashcompinit && bashcompinit
source ~/.local/share/bash-completion/completions/know
```

## Features

✅ **Command Completion**: All know commands (feature, component, deps, etc.)
✅ **Entity Completion**: Tab-complete entity IDs based on command type
✅ **Smart Caching**: Entity lists cached for performance
✅ **Type-Aware**: Different entities for different commands
✅ **Multi-Argument**: Supports complex command patterns like `know check feature <TAB>`

## Supported Completions

### Commands
- **Generation**: `feature`, `component`, `screen`, `functionality`, `requirement`, `api`
- **Analysis**: `deps`, `impact`, `gaps`, `validate`, `order`, `blockers`
- **Discovery**: `list`, `search`, `check`, `preview`
- **Workflows**: `create-feature`, `complete`, `implementation-chain`, `priorities`
- **Graph**: `mod`, `query`

### Entity Types
- **features**: real-time-telemetry, predictive-maintenance, etc.
- **components**: fleet-status-map, robot-controls, etc.
- **screens**: fleet-dashboard, mission-control, etc.
- **functionality**: fleet-management, analytics-insights, etc.
- **requirements**: multi-tenant-security, system-reliability, etc.
- **schema**: robot-fleet-model, telemetry-stream-model, etc.

### Examples
```bash
know <TAB>                          # Shows all commands
know feature <TAB>                  # Shows all features
know deps feature:<TAB>             # Shows all entity references
know check <TAB>                    # Shows entity types
know check feature <TAB>            # Shows features for checking
know list <TAB>                     # Shows listable entity types
```

## Performance

- **Caching**: Entity lists cached in `~/.cache/know/entities.cache`
- **Auto-refresh**: Cache rebuilds when knowledge graph changes
- **Fast lookup**: Avoids repeated `jq` calls during completion

## Status Check

```bash
./know/know --completion-status
```

Shows:
- ✅ Autocomplete is active / ❌ Autocomplete not active
- 📋 Entity cache status and location
- Installation instructions if needed

## Manual Installation Paths

1. **System-wide** (requires sudo): `/usr/share/bash-completion/completions/know`
2. **User-specific**: `~/.local/share/bash-completion/completions/know`
3. **Fallback**: `~/.bash_completion`

The installer tries these in order and picks the first writable location.