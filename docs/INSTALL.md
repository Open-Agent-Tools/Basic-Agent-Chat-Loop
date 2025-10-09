# Installation Guide

This guide explains how to install the Strands Chat Loop as a global command on **Windows**, **macOS**, or **Linux**.

## Quick Install

### macOS / Linux

```bash
# Clone the repository
git clone <repo-url> agent-examples
cd agent-examples/scripts/strands_chat_loop

# Run the installer
./install.sh
```

### Windows

```cmd
# Clone the repository
git clone <repo-url> agent-examples
cd agent-examples\scripts\strands_chat_loop

# Run the installer
install.bat
```

### Cross-Platform (Python)

Works on all platforms:

```bash
# Clone the repository
git clone <repo-url> agent-examples
cd agent-examples/scripts/strands_chat_loop

# Run the Python installer
python install.py
```

After installation, you can run from anywhere:

```bash
chat_loop AWS_Strands/Product_Pete/agent.py
chat_loop path/to/your/agent.py --config ~/.chatrc-custom
```

## What the Installer Does

1. **Installs Python Dependencies**
   - Prompts you to choose installation method (user/system/skip)
   - Installs from `requirements.txt`

2. **Creates Global Command**
   - Installs `chat_loop` wrapper to `~/.local/bin`
   - Makes it executable and callable from anywhere

3. **Updates PATH**
   - Adds `~/.local/bin` to your PATH in `.bashrc`/`.zshrc`
   - Allows the command to be found by your shell

## Usage

### Basic Usage

```bash
# Run with an agent
chat_loop AWS_Strands/Product_Pete/agent.py

# With custom config
chat_loop AWS_Strands/Product_Pete/agent.py --config ~/.chatrc-custom
```

### From Any Directory

```bash
# Works from anywhere
cd ~/Documents
chat_loop ~/Development/agent-examples/AWS_Strands/Product_Pete/agent.py

cd ~/Projects
chat_loop ../agent-examples/AWS_Strands/Complex_Coding_Clara/agent.py
```

## Installation Options

### User Install (Recommended)

```bash
./install.sh
# Choose option 1 for user install
```

- Installs to `~/.local/bin` (no sudo required)
- Dependencies installed to user site-packages
- Only affects current user

### System Install

```bash
./install.sh
# Choose option 2 for system install
```

- May require sudo for dependencies
- Available to all users
- Modifies system Python packages

### Skip Dependencies

If you've already installed dependencies:

```bash
./install.sh
# Choose option 3 to skip dependency installation
```

## Uninstall

### macOS / Linux

```bash
cd scripts/strands_chat_loop
./install.sh --uninstall
```

### Windows

```cmd
cd scripts\strands_chat_loop
install.bat /uninstall
```

### Cross-Platform

```bash
python install.py --uninstall
```

This removes:
- The `chat_loop` command from `~/.local/bin`

This does NOT remove:
- Python dependencies (remove manually with pip if needed)
- PATH modifications in shell config files

### Manual Cleanup

To fully remove everything:

```bash
# Uninstall command
./install.sh --uninstall

# Remove dependencies
pip uninstall anthropic-bedrock pyyaml rich

# Remove PATH modification (edit manually)
nano ~/.bashrc  # or ~/.zshrc
# Remove the line: export PATH="$HOME/.local/bin:$PATH"
```

## Troubleshooting

### Command Not Found

If `chat_loop` command is not found after installation:

```bash
# Reload your shell configuration
source ~/.bashrc  # or source ~/.zshrc

# Or restart your terminal
```

### Python Import Errors

If you see import errors:

```bash
# Reinstall dependencies
cd scripts/strands_chat_loop
pip install --user -r requirements.txt

# Or with uv (faster)
uv pip install -r requirements.txt
```

### Permission Denied

If you see "Permission denied" errors:

```bash
# Make sure install.sh is executable
chmod +x install.sh

# Run installer again
./install.sh
```

### Wrong Python Version

The chat loop requires Python 3.8+:

```bash
# Check your Python version
python3 --version

# If too old, install a newer Python
# Then run install.sh again
```

## Development Mode

If you're actively developing the chat loop, you may want to run it directly instead of installing:

```bash
# Run directly from source
python scripts/strands_chat_loop/chat_loop.py --agent AWS_Strands/Product_Pete/agent.py

# Or create an alias
echo "alias chat_loop='python3 /full/path/to/scripts/strands_chat_loop/chat_loop.py'" >> ~/.bashrc
source ~/.bashrc
```

## Alternative: Manual Installation

If you prefer to install manually:

```bash
# 1. Install dependencies
pip install --user -r scripts/strands_chat_loop/requirements.txt

# 2. Create ~/.local/bin if needed
mkdir -p ~/.local/bin

# 3. Create wrapper script
cat > ~/.local/bin/chat_loop << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "Development/agent-examples/scripts/strands_chat_loop"))
from chat_loop import main
sys.exit(main())
EOF

# 4. Make executable
chmod +x ~/.local/bin/chat_loop

# 5. Add to PATH (if not already)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Features

Once installed, you get:
- ✅ Global `chat_loop` command
- ✅ Works from any directory
- ✅ Accepts relative or absolute agent paths
- ✅ All chat loop features available
- ✅ Configuration file support
- ✅ Command history persistence
- ✅ Prompt templates

## Next Steps

After installation:

1. **Configure your settings**: `cp scripts/strands_chat_loop/.chatrc.example ~/.chatrc`
2. **Create templates**: `mkdir ~/.prompts` and add your templates
3. **Try an agent**: `chat_loop AWS_Strands/Product_Pete/agent.py`

See [README.md](README.md) for full feature documentation.
