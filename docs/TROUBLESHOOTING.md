# Troubleshooting Guide

Common issues and solutions for **Basic Agent Chat Loop**.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Command Not Found](#command-not-found)
- [Import and Module Errors](#import-and-module-errors)
- [Agent Loading Issues](#agent-loading-issues)
- [Configuration Issues](#configuration-issues)
- [Terminal and Display Issues](#terminal-and-display-issues)
- [Command History Issues](#command-history-issues)
- [Performance Issues](#performance-issues)
- [Platform-Specific Issues](#platform-specific-issues)

---

## Installation Issues

### Package not found on PyPI

**Symptom:** `ERROR: Could not find a version that satisfies the requirement basic-agent-chat-loop`

**Solutions:**
```bash
# Update pip to latest version
pip install --upgrade pip

# Try with explicit package name
pip install basic-agent-chat-loop

# Check if you have internet connectivity
ping pypi.org
```

### Permission denied during installation

**Symptom:** `ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied`

**Solutions:**
```bash
# Use user install (recommended)
pip install --user basic-agent-chat-loop

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install basic-agent-chat-loop

# As last resort, use sudo (not recommended)
sudo pip install basic-agent-chat-loop
```

### SSL certificate errors

**Symptom:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions:**
```bash
# Update certificates (macOS)
/Applications/Python*/Install\ Certificates.command

# Or temporarily bypass SSL (not recommended for production)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org basic-agent-chat-loop
```

### Dependency conflicts

**Symptom:** `ERROR: pip's dependency resolver does not currently take into account all the packages that are installed`

**Solutions:**
```bash
# Install in isolated environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install basic-agent-chat-loop

# Or force reinstall
pip install --force-reinstall --no-cache-dir basic-agent-chat-loop
```

---

## Command Not Found

### "chat_loop: command not found" on macOS/Linux

**Symptom:** Shell cannot find the `chat_loop` command after installation

**Diagnosis:**
```bash
# Check if package is installed
pip show basic-agent-chat-loop

# Find where pip installed scripts
pip show -f basic-agent-chat-loop | grep -E "bin/|Scripts/"

# Check your PATH
echo $PATH
```

**Solutions:**

1. **Add pip's bin directory to PATH:**
   ```bash
   # For bash (add to ~/.bashrc)
   export PATH="$HOME/.local/bin:$PATH"

   # For zsh (add to ~/.zshrc)
   export PATH="$HOME/.local/bin:$PATH"

   # Reload shell
   source ~/.bashrc  # or source ~/.zshrc
   ```

2. **Use full path temporarily:**
   ```bash
   ~/.local/bin/chat_loop
   ```

3. **Reinstall with system-wide access:**
   ```bash
   sudo pip install basic-agent-chat-loop
   ```

### "chat_loop: command not found" on Windows

**Symptom:** PowerShell or CMD cannot find the command

**Solutions:**

1. **Check if Scripts directory is in PATH:**
   ```powershell
   # PowerShell
   $env:PATH -split ';' | Select-String Python

   # Add to PATH if missing
   $env:PATH += ";$env:APPDATA\Python\Python3X\Scripts"
   ```

2. **Use py launcher:**
   ```cmd
   py -m basic_agent_chat_loop.cli
   ```

3. **Run as module:**
   ```cmd
   python -m basic_agent_chat_loop.cli
   ```

---

## Import and Module Errors

### "No module named 'basic_agent_chat_loop'"

**Symptom:** Python cannot find the package

**Diagnosis:**
```bash
# Check what Python is being used
which python
python --version

# Check installed packages
pip list | grep basic-agent-chat-loop

# Check sys.path
python -c "import sys; print('\n'.join(sys.path))"
```

**Solutions:**

1. **Reinstall the package:**
   ```bash
   pip install --force-reinstall basic-agent-chat-loop
   ```

2. **Ensure using correct Python:**
   ```bash
   # Use specific Python version
   python3 -m pip install basic-agent-chat-loop
   ```

3. **Check virtual environment:**
   ```bash
   # Activate the correct venv
   source venv/bin/activate
   pip install basic-agent-chat-loop
   ```

### "ModuleNotFoundError: No module named 'anthropic_bedrock'"

**Symptom:** Missing AWS Bedrock dependency

**Solution:**
```bash
# Install with bedrock support
pip install basic-agent-chat-loop[bedrock]
```

### "ModuleNotFoundError: No module named 'readline'"

**Symptom:** Windows missing readline support

**Solution:**
```bash
# Install with Windows support
pip install basic-agent-chat-loop[windows]
```

---

## Agent Loading Issues

### Agent file not found

**Symptom:** `Error: Agent file not found: path/to/agent.py`

**Solutions:**

1. **Use absolute path:**
   ```bash
   chat_loop /full/path/to/agent.py
   ```

2. **Use relative path from current directory:**
   ```bash
   cd /directory/with/agent
   chat_loop agent.py
   ```

3. **Use alias system:**
   ```bash
   # Save as alias once
   chat_loop --save-alias myagent /full/path/to/agent.py

   # Use from anywhere
   chat_loop myagent
   ```

### Environment file (.env) not loaded

**Symptom:** Agent cannot access environment variables

**Solutions:**

1. **Place .env in project root or up to 3 parent directories**
2. **Check .env file format:**
   ```bash
   # .env file should have KEY=VALUE format (no spaces around =)
   API_KEY=your_key_here
   SECRET=your_secret
   ```

3. **Manually set environment variables:**
   ```bash
   export API_KEY=your_key
   chat_loop agent.py
   ```

### Agent import errors

**Symptom:** `ImportError` when loading agent module

**Solutions:**

1. **Ensure agent dependencies are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Python path includes agent directory:**
   ```bash
   export PYTHONPATH=/path/to/agent/directory:$PYTHONPATH
   ```

---

## Configuration Issues

### Config file not being read

**Symptom:** Settings in `~/.chatrc` are not applied

**Diagnosis:**
```bash
# Check if config exists
ls -la ~/.chatrc

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('$HOME/.chatrc'))"
```

**Solutions:**

1. **Recreate config file:**
   ```bash
   # Delete existing config
   rm ~/.chatrc

   # Package will recreate on next run
   python -c "from basic_agent_chat_loop.chat_config import get_config; get_config()"
   ```

2. **Fix YAML syntax errors:**
   ```yaml
   # Ensure proper indentation (spaces, not tabs)
   features:
     show_tokens: true  # Note: 2 spaces for indentation
     auto_save: false
   ```

3. **Use explicit config path:**
   ```bash
   chat_loop agent.py --config /path/to/custom.chatrc
   ```

### Colors not displaying correctly

**Symptom:** Terminal shows escape codes or wrong colors

**Solutions:**

1. **Check terminal supports ANSI colors:**
   ```bash
   echo -e "\033[94mBlue Text\033[0m"
   ```

2. **Use a modern terminal emulator:**
   - macOS: iTerm2, Terminal.app
   - Linux: GNOME Terminal, Konsole
   - Windows: Windows Terminal (recommended)

3. **Disable colors if needed:**
   ```yaml
   # In ~/.chatrc
   features:
     rich_enabled: false
   ```

---

## Terminal and Display Issues

### Formatting issues or broken output

**Symptom:** Markdown not rendering, or garbled text

**Solutions:**

1. **Ensure rich is installed:**
   ```bash
   pip install rich>=13.7.0
   ```

2. **Disable rich formatting:**
   ```yaml
   # In ~/.chatrc
   features:
     rich_enabled: false
   ```

3. **Update terminal:**
   - Windows: Use Windows Terminal instead of CMD
   - macOS: Update Terminal.app or use iTerm2
   - Linux: Use modern terminal with UTF-8 support

### Unicode/emoji display issues

**Symptom:** Boxes or question marks instead of emojis

**Solutions:**

1. **Ensure terminal uses UTF-8:**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export LANG=en_US.UTF-8
   export LC_ALL=en_US.UTF-8
   ```

2. **Install fonts with emoji support:**
   - macOS: System fonts support emojis
   - Linux: `sudo apt install fonts-noto-color-emoji`
   - Windows: Use Windows Terminal with modern fonts

### Screen not clearing properly

**Symptom:** `clear` command leaves artifacts

**Solutions:**

1. **Try alternate clear method:**
   - Type `exit` and restart
   - Or manually: Ctrl+L (Unix) or `cls` (Windows)

2. **Check terminal capabilities:**
   ```bash
   echo $TERM
   # Should show something like: xterm-256color
   ```

---

## Command History Issues

### History not persisting between sessions

**Symptom:** Up arrow doesn't recall previous commands

**Solutions:**

1. **Check if history file exists:**
   ```bash
   ls -la ~/.chat_history
   ```

2. **Ensure readline is enabled:**
   ```yaml
   # In ~/.chatrc
   features:
     readline_enabled: true
   ```

3. **Windows: Install pyreadline3:**
   ```bash
   pip install basic-agent-chat-loop[windows]
   ```

### History file permission errors

**Symptom:** `PermissionError: [Errno 13] Permission denied: '~/.chat_history'`

**Solutions:**
```bash
# Fix permissions
chmod 644 ~/.chat_history

# Or delete and recreate
rm ~/.chat_history
```

---

## Performance Issues

### Slow startup time

**Solutions:**

1. **Lazy load rich library** (future enhancement)
2. **Check agent initialization time** - may be agent-specific
3. **Profile slow operations:**
   ```bash
   python -m cProfile -m basic_agent_chat_loop.cli agent.py
   ```

### High memory usage

**Solutions:**

1. **Limit conversation history** (future feature)
2. **Monitor agent memory usage** - may be agent-specific
3. **Use system monitoring:**
   ```bash
   # macOS/Linux
   top -p $(pgrep -f chat_loop)

   # Windows
   tasklist | findstr python
   ```

---

## Platform-Specific Issues

### macOS: SSL Certificate Issues

**Symptom:** Certificate verification errors

**Solution:**
```bash
# Run certificate installer
/Applications/Python*/Install\ Certificates.command
```

### Linux: Missing dependencies

**Symptom:** Various import errors

**Solutions:**
```bash
# Debian/Ubuntu
sudo apt update
sudo apt install python3-pip python3-dev

# RHEL/CentOS/Fedora
sudo dnf install python3-pip python3-devel
```

### Windows: PowerShell Execution Policy

**Symptom:** Scripts blocked by execution policy

**Solution:**
```powershell
# Set policy for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Windows: ANSI color support

**Symptom:** No colors in older Windows terminals

**Solutions:**
1. **Use Windows Terminal** (recommended)
2. **Enable ANSI in PowerShell:**
   ```powershell
   Set-ItemProperty HKCU:\Console VirtualTerminalLevel -Type DWORD 1
   ```

---

## Getting More Help

If you're still experiencing issues:

1. **Check GitHub Issues**: [Existing Issues](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
2. **Search Discussions**: [GitHub Discussions](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/discussions)
3. **File a Bug Report**: [New Issue](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues/new)

When reporting issues, please include:
- Operating system and version
- Python version (`python --version`)
- Package version (`pip show basic-agent-chat-loop`)
- Full error message and traceback
- Steps to reproduce the issue

## See Also

- [Installation Guide](INSTALL.md) - Installation instructions
- [Configuration Reference](CONFIG.md) - Configuration options
- [README](../README.md) - Feature overview
