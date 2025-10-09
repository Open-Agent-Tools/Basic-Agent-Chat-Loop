# Basic Agent Chat Loop

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A feature-rich, interactive CLI for AI agents with token tracking, prompt templates, agent aliases, and extensive configuration options.

## Features

- 🏷️ **Agent Aliases** - Save agents as short names (`chat_loop pete` instead of full paths)
- 📜 **Command History** - Navigate previous queries with ↑↓ arrows (persisted to `~/.chat_history`)
- ✍️ **Multi-line Input** - Type `\\` to enter multi-line mode for code blocks
- 💰 **Token Tracking** - Track tokens and costs per query and session
- 📝 **Prompt Templates** - Reusable prompts from `~/.prompts/`
- ⚙️ **Configuration** - YAML-based config with per-agent overrides
- 📊 **Status Bar** - Real-time metrics (queries, tokens, duration)
- 📈 **Session Summary** - Full statistics displayed on exit
- 🎨 **Rich Formatting** - Enhanced markdown rendering with syntax highlighting
- 🔄 **Error Recovery** - Automatic retry logic with exponential backoff
- 🔍 **Agent Metadata** - Display model, tools, and capabilities

## Installation

### PyPI Install (Coming Soon)

```bash
pip install basic-agent-chat-loop
```

### From Source

**Recommended (editable install):**

```bash
git clone <repo-url> Basic-Agent-Chat-Loop
cd Basic-Agent-Chat-Loop
pip install -e .
```

**Windows users (for command history support):**

```bash
pip install -e ".[windows]"
```

**Development install:**

```bash
pip install -e ".[dev]"
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed installation instructions.

## Quick Start

### Basic Usage

```bash
# Run with agent path
chat_loop AWS_Strands/Product_Pete/agent.py

# Run with alias (after saving)
chat_loop pete
```

### Agent Aliases

Save frequently used agents for quick access:

```bash
# Save aliases
chat_loop --save-alias pete AWS_Strands/Product_Pete/agent.py
chat_loop --save-alias clara AWS_Strands/Complex_Coding_Clara/agent.py

# Use aliases from anywhere
chat_loop pete
chat_loop clara

# List all aliases
chat_loop --list-aliases

# Remove an alias
chat_loop --remove-alias pete
```

Aliases are stored in `~/.chat_aliases` and work from any directory.

### Prompt Templates

Create reusable prompt templates:

```bash
# Create template directory
mkdir -p ~/.prompts

# Create a code review template
cat > ~/.prompts/review.md <<'EOF'
# Code review
Please review the following code for:
- Best practices and design patterns
- Potential bugs or edge cases
{input}
EOF

# Use template in chat
chat_loop pete
You: /review my_code.py
```

## Configuration

Create a configuration file at `~/.chatrc`:

```bash
cp .chatrc.example ~/.chatrc
```

Example configuration:

```yaml
features:
  show_tokens: true           # Display token counts
  show_metadata: true         # Show agent model/tools info
  rich_enabled: true          # Enhanced formatting

ui:
  show_status_bar: true       # Top status bar
  show_duration: true         # Query duration

behavior:
  max_retries: 3              # Retry attempts on failure
  timeout: 120.0              # Request timeout (seconds)

# Per-agent overrides
agents:
  'Product Pete':
    features:
      show_tokens: false
```

See [CONFIG.md](CONFIG.md) for full configuration options.

## Commands

| Command | Description |
|---------|-------------|
| `help` | Show help message |
| `info` | Show agent details (model, tools) |
| `templates` | List available prompt templates |
| `/name` | Use prompt template from `~/.prompts/name.md` |
| `clear` | Clear screen and reset agent session |
| `exit`, `quit` | Exit chat (shows session summary) |

### Multi-line Input

Press `\\` to enter multi-line mode:

```
You: \\
... def factorial(n):
...     if n <= 1:
...         return 1
...     return n * factorial(n - 1)
...
[Press Enter on empty line to submit]
```

## Token Tracking

### During Chat

When `show_tokens: true` in config:

```
------------------------------------------------------------
Time: 6.3s │ 1 cycle │ Tokens: 4.6K (in: 4.4K, out: 237) │ Cost: $0.017
```

### Session Summary

Always shown on exit:

```
============================================================
Session Summary
------------------------------------------------------------
  Duration: 12m 34s
  Queries: 15
  Tokens: 67.8K (in: 45.2K, out: 22.6K)
  Total Cost: $0.475
============================================================
```

## Programmatic Usage

```python
from basic_agent_chat_loop import ChatLoop

# Create chat interface
chat = ChatLoop(
    agent=your_agent,
    name="My Agent",
    description="Agent description",
    config_path=Path("~/.chatrc")  # Optional
)

# Run interactive loop
chat.run()
```

## Requirements

### Core Dependencies

- `anthropic-bedrock>=0.8.0` - AWS Bedrock integration
- `pyyaml>=6.0.1` - Configuration file parsing

### Optional (Recommended)

- `rich>=13.7.0` - Enhanced terminal rendering
- `readline` (built-in on Unix) - Command history
- `pyreadline3` (Windows only) - Command history support

## Platform Support

- ✅ **macOS** - Full support with native readline
- ✅ **Linux** - Full support with native readline
- ✅ **Windows** - Full support (install via `install.bat` or `install.py`)

## Architecture

```
src/basic_agent_chat_loop/
├── chat_loop.py          # Main orchestration
├── chat_config.py        # Configuration management
├── cli.py                # CLI entry point
├── components/           # Modular components
│   ├── ui_components.py      # Colors, StatusBar
│   ├── token_tracker.py      # Token/cost tracking
│   ├── template_manager.py   # Prompt templates
│   ├── display_manager.py    # Display formatting
│   ├── agent_loader.py       # Agent loading
│   └── alias_manager.py      # Alias management
docs/
├── ALIASES.md            # Alias system guide
├── CONFIG.md             # Configuration reference
├── INSTALL.md            # Installation instructions
└── Chat_TODO.md          # Roadmap and future features
```

## Documentation

- [docs/ALIASES.md](docs/ALIASES.md) - Agent alias system guide
- [docs/CONFIG.md](docs/CONFIG.md) - Configuration reference
- [docs/INSTALL.md](docs/INSTALL.md) - Installation instructions
- [docs/Chat_TODO.md](docs/Chat_TODO.md) - Roadmap and future features

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Changelog

### v1.0.0 (2025-10-08)

- ✨ Initial release
- 🏷️ Agent alias system
- 📝 Prompt templates
- 💰 Token tracking and cost estimation
- ⚙️ YAML configuration with per-agent overrides
- 📊 Status bar and session summaries
- 🎨 Rich markdown rendering
- 🔄 Automatic error recovery
- 📜 Persistent command history
- 🌐 Cross-platform installers (macOS, Linux, Windows)

## Support

For issues, questions, or contributions, please visit the [repository](https://github.com/yourusername/Basic-Agent-Chat-Loop).
