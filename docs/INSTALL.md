# Installation Guide

Complete installation instructions for **Basic Agent Chat Loop** on macOS, Linux, and Windows.

## Quick Install

### Standard Installation

The easiest way to install:

```bash
pip install basic-agent-chat-loop
```

That's it! The CLI command `chat_loop` will be available immediately.

### Platform-Specific Installations

**Windows (with command history support):**
```bash
pip install basic-agent-chat-loop[windows]
```

**AWS Bedrock integration:**
```bash
pip install basic-agent-chat-loop[bedrock]
```

**Development install:**
```bash
pip install basic-agent-chat-loop[dev]
```

## Installation Methods

### Method 1: PyPI (Recommended)

Install from the Python Package Index:

```bash
# Latest stable release
pip install basic-agent-chat-loop

# Specific version
pip install basic-agent-chat-loop==0.1.0

# With all optional dependencies
pip install basic-agent-chat-loop[windows,bedrock,dev]
```

### Method 2: From Source

For development or to use the latest features:

```bash
# Clone the repository
git clone https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop.git
cd Basic-Agent-Chat-Loop

# Install in editable mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Method 3: User vs System Install

**User install (no sudo required):**
```bash
pip install --user basic-agent-chat-loop
```

**System install:**
```bash
# May require sudo on Unix systems
sudo pip install basic-agent-chat-loop
```

**Virtual environment (recommended for development):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install basic-agent-chat-loop
```

## Verification

After installation, verify everything works:

```bash
# Check installation
pip show basic-agent-chat-loop

# Verify CLI command is available
which chat_loop  # Unix/macOS
where chat_loop  # Windows

# Test the command (will show help)
chat_loop --help
```

## First Run Setup

On first run, the package automatically creates:

1. **`~/.chatrc`** - Configuration file with recommended defaults
2. **`~/.prompts/`** - Sample prompt templates (created on first template use)

These files are created with sensible defaults - no manual setup required!

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade basic-agent-chat-loop
```

## Uninstalling

To remove the package:

```bash
pip uninstall basic-agent-chat-loop
```

This removes:
- The `chat_loop` command
- All Python package files
- Installed dependencies (if no other packages use them)

This does NOT remove:
- `~/.chatrc` - Your configuration file
- `~/.prompts/` - Your prompt templates
- `~/.chat_aliases` - Your saved agent aliases
- `~/.chat_history` - Your command history

To fully clean up:

```bash
# Uninstall package
pip uninstall basic-agent-chat-loop

# Remove configuration (optional - will be recreated on next install)
rm -f ~/.chatrc
rm -rf ~/.prompts/
rm -f ~/.chat_aliases
rm -f ~/.chat_history
```

## Platform-Specific Notes

### macOS

**Using Homebrew Python:**
```bash
# Install with Homebrew's pip
python3 -m pip install basic-agent-chat-loop
```

**Command history works out of the box** - readline is built-in.

### Linux

**Debian/Ubuntu:**
```bash
# Ensure pip is installed
sudo apt update
sudo apt install python3-pip

# Install package
pip3 install basic-agent-chat-loop
```

**RHEL/CentOS/Fedora:**
```bash
# Ensure pip is installed
sudo dnf install python3-pip  # Fedora
sudo yum install python3-pip  # CentOS/RHEL

# Install package
pip3 install basic-agent-chat-loop
```

**Command history works out of the box** - readline is built-in.

### Windows

**Install with Windows extras:**
```bash
pip install basic-agent-chat-loop[windows]
```

This includes `pyreadline3` for command history support.

**Using Windows Terminal** (recommended) for best experience with colors and formatting.

**PowerShell execution policy:**
If you get execution policy errors, you may need to adjust:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Dependencies

### Core Dependencies
These are installed automatically:
- `pyyaml>=6.0.1` - Configuration parsing
- `rich>=13.7.0` - Terminal formatting
- `python-dotenv>=1.0.0` - Environment variable management

### Optional Dependencies

**Windows extras (`[windows]`):**
- `pyreadline3>=3.4.1` - Command history on Windows

**AWS Bedrock extras (`[bedrock]`):**
- `anthropic-bedrock>=0.8.0` - AWS Bedrock integration

**Development extras (`[dev]`):**
- `pytest>=7.0` - Testing framework
- `pytest-cov>=4.0` - Coverage reporting
- `black>=23.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0.0` - Type checking

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Common Issues

**"command not found: chat_loop"**

The pip bin directory is not in your PATH. Solutions:

```bash
# Find where pip installed it
pip show -f basic-agent-chat-loop | grep bin

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

**"No module named 'basic_agent_chat_loop'"**

Package not installed in current environment:

```bash
# Verify installation
pip list | grep basic-agent-chat-loop

# Reinstall if needed
pip install --force-reinstall basic-agent-chat-loop
```

**Import errors or missing dependencies**

Try reinstalling with force:

```bash
pip install --force-reinstall basic-agent-chat-loop
```

**Permission errors**

Use user install to avoid sudo:

```bash
pip install --user basic-agent-chat-loop
```

**Old version installed**

Upgrade to latest:

```bash
pip install --upgrade basic-agent-chat-loop
```

## Next Steps

After installation:

1. **Run your first agent:**
   ```bash
   chat_loop path/to/your/agent.py
   ```

2. **Save an alias for quick access:**
   ```bash
   chat_loop --save-alias myagent path/to/agent.py
   chat_loop myagent
   ```

3. **Customize your config:**
   ```bash
   # Edit ~/.chatrc to customize colors, features, behavior
   nano ~/.chatrc
   ```

4. **Explore sample templates:**
   ```bash
   # Templates are created in ~/.prompts/ on first use
   ls ~/.prompts/
   ```

5. **Read the docs:**
   - [README.md](../README.md) - Feature overview
   - [CONFIG.md](CONFIG.md) - Configuration options
   - [ALIASES.md](ALIASES.md) - Alias system guide
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

## Getting Help

- 📖 **Documentation**: [docs/](.)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/discussions)
