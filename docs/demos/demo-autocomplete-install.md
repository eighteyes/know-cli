# Interactive Autocomplete Installation Demo

## What happens when you run `./know/know --install-completion`:

```
Installing know command autocomplete...

✅ Installed user completion to /home/user/.local/share/bash-completion/completions/know

🔧 Shell Configuration Setup

Detected shell: zsh
Configuration file: /home/user/.zshrc

Choose setup option:
  1) Add to /home/user/.zshrc automatically
  2) Show manual instructions
  3) Add to custom file
  4) Skip configuration

Enter choice [1-4]:
```

## Option Examples:

### Option 1: Automatic Setup
```
✅ Added autocomplete to /home/user/.zshrc
Restart your shell or run: source /home/user/.zshrc
```

### Option 2: Manual Instructions
```
📋 Manual Setup Instructions:

Add this line to your /home/user/.zshrc:
  autoload -U bashcompinit && bashcompinit && source /home/user/.local/share/bash-completion/completions/know

Then restart your shell or run:
  source /home/user/.zshrc
```

### Option 3: Custom File
```
Enter path to shell config file: ~/.config/my-shell-setup.sh

✅ Added autocomplete to /home/user/.config/my-shell-setup.sh
Source this file from your main shell config or restart your shell
```

### Option 4: Skip
```
⏭️  Skipped configuration. You can set up manually later:
  source /home/user/.local/share/bash-completion/completions/know
```

## Smart Shell Detection

- **Bash users**: Adds `source <completion-file>` to `~/.bashrc`
- **Zsh users**: Adds `autoload -U bashcompinit && bashcompinit && source <completion-file>` to `~/.zshrc`
- **Other shells**: Shows manual instructions

## Safety Features

- ✅ **Duplicate prevention**: Checks if autocomplete is already configured
- ✅ **File creation**: Creates config files if they don't exist
- ✅ **Path expansion**: Supports `~` in custom file paths
- ✅ **Fallback paths**: Multiple installation locations (system → user → fallback)