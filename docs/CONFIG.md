# Chat Loop Configuration Guide

The AWS Strands chat loop supports comprehensive configuration via `.chatrc` files.

## Quick Start

1. Copy the example config:
   ```bash
   cp AWS_Strands/.chatrc.example ~/.chatrc
   ```

2. Edit for your preferences:
   ```bash
   nano ~/.chatrc  # or your preferred editor
   ```

3. Run chat loop - config loads automatically:
   ```bash
   python AWS_Strands/chat_loop.py --agent AWS_Strands/Product_Pete/agent.py
   ```

## Configuration Locations

Configs are loaded in this order (later overrides earlier):

1. **Built-in defaults** - Always available as fallback
2. **Global config** - `~/.chatrc` - Applies to all agents
3. **Project config** - `.chatrc` in current dir or up to 3 parents - Project-specific
4. **Explicit config** - `--config /path/to/config` - Highest priority

## Configuration Sections

### Colors

Customize ANSI escape codes for terminal output:

```yaml
colors:
  user: '\033[97m'      # Bright white (default)
  agent: '\033[94m'     # Bright blue
  system: '\033[33m'    # Yellow
  error: '\033[91m'     # Bright red
  success: '\033[92m'   # Bright green
  dim: '\033[2m'        # Dim
  reset: '\033[0m'      # Reset
```

**Alternative color schemes:**

Monochrome (for colorblind users):
```yaml
colors:
  user: '\033[1m'     # Bold
  agent: '\033[0m'    # Normal
  system: '\033[2m'   # Dim
```

High contrast:
```yaml
colors:
  user: '\033[97;1m'  # Bright white bold
  agent: '\033[96;1m' # Bright cyan bold
```

### Features

Toggle functionality on/off:

```yaml
features:
  auto_save: false              # Save conversations on exit
  rich_enabled: true            # Use rich library for formatting
  show_tokens: false            # Display token counts (future)
  show_metadata: true           # Show agent metadata on startup
  readline_enabled: true        # Command history
```

### Paths

File system locations:

```yaml
paths:
  save_location: ~/agent-conversations    # Conversation exports
  log_location: .logs                      # Log files
```

### Behavior

Runtime behavior:

```yaml
behavior:
  max_retries: 3               # Maximum retry attempts on failure
  retry_delay: 2.0             # Seconds between retries
  timeout: 120.0               # Request timeout (seconds)
  spinner_style: dots          # Thinking indicator style
```

**Available spinner styles:**
- dots, line, arc, arrow, arrow2, arrow3, balloonBox, betaWave, bouncingBall, bouncingBar, boxBounce, boxBounce2, christmas, circle, circleHalves, circleQuarters, clock, dots2-12, earth, grenade, growHorizontal, growVertical, hamburger, hearts, layer, line, line2, monkey, moon, noise, orangeBluePulse, orangePulse, pipe, point, pong, runner, sand, simpleDots, simpleDotsScrolling, smiley, soccerHeader, speaker, squareCorners, squish, star, star2, toggle, toggle2-13, triangle, weather

### UI

User interface preferences:

```yaml
ui:
  show_banner: true            # Welcome banner
  show_thinking_indicator: true  # "Thinking..." spinner
  show_duration: true          # Query duration
  show_status_bar: false       # Top status bar (agent, model, queries, time)
```

**Status Bar:**
When enabled, shows a persistent status bar at the top:
```
┌─────────────────────────────────────────────────┐
│ Clara │ Sonnet 4.5 │ 3 queries │ 12m 34s        │
└─────────────────────────────────────────────────┘
```
- Updates after each query
- Shows session time and query count
- Clean box drawing characters

## Per-Agent Configuration

Override settings for specific agents:

```yaml
agents:
  'Complex Coding Clara':
    features:
      auto_save: true
      show_tokens: true
    paths:
      save_location: ~/code-conversations/clara
    behavior:
      timeout: 300.0
    ui:
      show_metadata: false

  'Product Pete':
    colors:
      agent: '\033[95m'       # Magenta
    features:
      auto_save: true
```

Agent names must match exactly (as shown in banner).

## Usage Examples

### Global Configuration

Apply to all agents:

```bash
cp AWS_Strands/.chatrc.example ~/.chatrc
nano ~/.chatrc
```

### Project Configuration

For a specific project:

```bash
cd ~/my-project
cp ~/path/to/.chatrc.example .chatrc
nano .chatrc
```

### Explicit Configuration

Use a specific config file:

```bash
python AWS_Strands/chat_loop.py --agent <agent> --config /path/to/custom.chatrc
```

### Workflow-Specific Configs

Different configs for different workflows:

```bash
# Coding workflow
python AWS_Strands/chat_loop.py --agent Clara --config ~/.chatrc-coding

# Research workflow
python AWS_Strands/chat_loop.py --agent Dave --config ~/.chatrc-research
```

## Configuration Tips

### 1. Start with Example

Copy `.chatrc.example` and modify incrementally:
```bash
cp AWS_Strands/.chatrc.example ~/.chatrc
```

### 2. Test Changes

Run with `info` command to verify settings:
```bash
python AWS_Strands/chat_loop.py --agent <agent>
> info
```

### 3. Per-Agent Overrides

Use agent-specific configs for specialized workflows:
- Clara: Auto-save, longer timeout, hide metadata
- Pete: Custom colors for product work
- Dave: Very long timeout for deep research

### 4. Color Accessibility

For colorblind users, use monochrome or high-contrast schemes.

### 5. Performance Tuning

Adjust for your use case:
- Research: Higher timeout, disable thinking indicator
- Quick queries: Lower retries, faster retry_delay
- Production: Enable auto_save, logging

### 6. Team Consistency

Commit `.chatrc` to project root for team consistency:
```bash
cp AWS_Strands/.chatrc.example .chatrc
# Edit for project
git add .chatrc
git commit -m "Add chat loop config"
```

## Configuration Priority

When the same setting exists in multiple configs:

1. Explicit `--config` (highest)
2. Per-agent override in project `.chatrc`
3. Project `.chatrc` (current dir or parents)
4. Per-agent override in global `~/.chatrc`
5. Global `~/.chatrc`
6. Built-in defaults (lowest)

Example:
```yaml
# ~/.chatrc (global)
behavior:
  max_retries: 3

# .chatrc (project)
behavior:
  max_retries: 5
agents:
  'Complex Coding Clara':
    behavior:
      max_retries: 10

# Result for Clara: max_retries = 10 (agent override wins)
# Result for Pete: max_retries = 5 (project config wins)
```

## Troubleshooting

### Config not loading?

1. Check YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('.chatrc'))"
   ```

2. Verify file location:
   ```bash
   ls -la ~/.chatrc
   ls -la .chatrc
   ```

3. Check for YAML library:
   ```bash
   python3 -c "import yaml; print('✓ YAML available')"
   ```

### Colors not working?

Ensure ANSI codes are quoted:
```yaml
colors:
  user: '\033[97m'  # Correct - quoted
  # user: \033[97m  # Wrong - unquoted
```

### Agent-specific config not applying?

Check agent name matches exactly:
```bash
# Run chat loop and check banner for exact name
python AWS_Strands/chat_loop.py --agent <agent>
# Look for: "COMPLEX CODING CLARA - Interactive Chat"
# Config should use: 'Complex Coding Clara'
```

## Advanced Usage

### Dynamic Config Loading

Config can be reloaded per agent in scripts:

```python
from AWS_Strands.chat_config import get_config, ChatConfig

# Load specific config
config = ChatConfig(config_path=Path('custom.chatrc'))

# Get values with agent overrides
timeout = config.get('behavior.timeout', 120.0, agent_name='Clara')

# Runtime changes (not persisted)
config.set('features.auto_save', True, agent_name='Pete')
```

### Config in Scripts

Integrate config in custom scripts:

```python
from AWS_Strands.chat_loop import ChatLoop
from AWS_Strands.chat_config import get_config

config = get_config()
chat = ChatLoop(agent, name, desc, config=config)
chat.run()
```

## Schema Reference

Full configuration schema:

```yaml
colors:
  user: string        # ANSI escape code
  agent: string
  system: string
  error: string
  success: string
  dim: string
  reset: string

features:
  auto_save: boolean
  rich_enabled: boolean
  show_tokens: boolean
  show_metadata: boolean
  readline_enabled: boolean

paths:
  save_location: string  # Path with ~ and $VAR expansion
  log_location: string

behavior:
  max_retries: integer   # 0-10 recommended
  retry_delay: float     # Seconds
  timeout: float         # Seconds
  spinner_style: string  # See spinner styles above

ui:
  show_banner: boolean
  show_thinking_indicator: boolean
  show_duration: boolean
  show_status_bar: boolean  # Top status bar with agent, model, queries, time

agents:
  '<agent_name>':
    # Any of the above sections can be overridden
    colors: {...}
    features: {...}
    paths: {...}
    behavior: {...}
    ui: {...}
```

## See Also

- `.chatrc.example` - Comprehensive example with all options
- `chat_config.py` - Configuration implementation
- `chat_loop.py` - Main chat loop using config
- `Chat_TODO.md` - Feature tracking and roadmap
