# Agent Aliases Guide

Agent aliases let you save frequently used agents as short, memorable names instead of typing full paths every time.

## Quick Start

```bash
# Save an alias
chat_loop --save-alias pete AWS_Strands/Product_Pete/agent.py

# Use the alias
chat_loop pete
```

That's it! Now you can run `chat_loop pete` from any directory instead of typing the full path.

## Commands

### Save an Alias

```bash
chat_loop --save-alias <name> <path>
```

Example:
```bash
chat_loop --save-alias pete AWS_Strands/Product_Pete/agent.py
chat_loop --save-alias clara ~/projects/agents/clara/agent.py
```

**Notes:**
- Alias names must contain only letters, numbers, hyphens, and underscores
- Paths are automatically resolved to absolute paths
- The agent file must exist when you save the alias
- Aliases are globally unique (one alias = one path)

### List Aliases

```bash
chat_loop --list-aliases
```

Shows all saved aliases with their paths:

```
Saved Agent Aliases (3):
------------------------------------------------------------
  pete                 → /path/to/agent-examples/AWS_Strands/Product_Pete/agent.py
  clara                → /path/to/agent-examples/AWS_Strands/Complex_Coding_Clara/agent.py
  quinten              → /path/to/agent-examples/AWS_Strands/QuickResearch_Quinten/agent.py
------------------------------------------------------------

Usage: chat_loop <alias>
```

If an alias points to a missing file, it's marked with `(missing)` in red.

### Remove an Alias

```bash
chat_loop --remove-alias <name>
```

Example:
```bash
chat_loop --remove-alias pete
```

### Update an Alias

To change where an alias points:

```bash
chat_loop --save-alias pete NEW/PATH/agent.py --overwrite
```

Without `--overwrite`, you'll get an error if the alias already exists.

## Using Aliases

Once saved, use an alias just like a path:

```bash
# Instead of this:
chat_loop ~/Development/agent-examples/AWS_Strands/Product_Pete/agent.py

# Just type this:
chat_loop pete
```

Aliases work from **any directory** - no need to be in the agent directory!

```bash
cd ~/Documents
chat_loop pete        # Works!

cd ~/Projects
chat_loop clara       # Works!
```

## Path Resolution Priority

When you run `chat_loop <something>`, it checks in this order:

1. **Is it a valid file path?** (relative or absolute)
   - If yes, use that path
   - If no, continue...

2. **Is it a saved alias?**
   - If yes, use the alias's path
   - If no, show error

This means **file paths always take precedence** over aliases. If you have a file called `pete` in your current directory, it will use that file instead of the alias.

## Examples

### Common Workflow

```bash
# First time: save aliases for your frequently used agents
chat_loop --save-alias pete AWS_Strands/Product_Pete/agent.py
chat_loop --save-alias clara AWS_Strands/Complex_Coding_Clara/agent.py
chat_loop --save-alias quinten AWS_Strands/QuickResearch_Quinten/agent.py

# Daily use: just use the aliases
chat_loop pete
chat_loop clara
chat_loop quinten

# Check what aliases you have
chat_loop --list-aliases

# Remove one you don't use anymore
chat_loop --remove-alias quinten
```

### Project-Specific Agent

```bash
# Save a project-specific agent
cd ~/projects/myapp
chat_loop --save-alias myapp agent/custom_agent.py

# Use it from anywhere
cd ~/Documents
chat_loop myapp       # Works!
```

### Temporary vs Permanent

```bash
# Temporary: use path directly (no alias saved)
chat_loop path/to/experimental/agent.py

# Permanent: save as alias once you like it
chat_loop --save-alias experiment path/to/experimental/agent.py
chat_loop experiment
```

## Storage Location

Aliases are stored in a JSON file at:
```
~/.chat_aliases
```

**macOS/Linux:** `/Users/username/.chat_aliases`
**Windows:** `C:\Users\username\.chat_aliases`

The file looks like this:
```json
{
  "clara": "/path/to/agent-examples/AWS_Strands/Complex_Coding_Clara/agent.py",
  "pete": "/path/to/agent-examples/AWS_Strands/Product_Pete/agent.py",
  "quinten": "/path/to/agent-examples/AWS_Strands/QuickResearch_Quinten/agent.py"
}
```

You can edit this file manually if needed, but use the CLI commands for safety.

## Tips

### Good Alias Names

✅ **Good:**
- `pete` - Short and memorable
- `clara` - Matches agent name
- `product-mgr` - Descriptive with hyphens
- `research_v2` - Version with underscore

❌ **Bad:**
- `p` - Too short, hard to remember
- `my agent` - No spaces allowed
- `Pete's Agent` - No special characters
- `agent-123-final-v2-updated` - Too long

### Organize by Project

```bash
# Work agents
chat_loop --save-alias work-product AWS_Strands/Product_Pete/agent.py
chat_loop --save-alias work-research AWS_Strands/QuickResearch_Quinten/agent.py

# Personal agents
chat_loop --save-alias personal-code custom/agents/personal_coder.py
chat_loop --save-alias personal-writer custom/agents/writer.py
```

### Quick Alias Check

```bash
# Forgot if you saved an alias?
chat_loop --list-aliases | grep pete
```

## Troubleshooting

### Alias Not Found

```bash
$ chat_loop pete
Error: Agent not found: pete

Not found as:
  • File path: pete
  • Alias name: pete

Available aliases:
  • clara
  • quinten
```

**Solution:** The alias doesn't exist. Save it first:
```bash
chat_loop --save-alias pete AWS_Strands/Product_Pete/agent.py
```

### Agent File Moved

If you move an agent file after saving an alias, the alias will point to the old (now missing) location.

```bash
$ chat_loop --list-aliases
  pete                 → /old/path/agent.py (missing)
```

**Solution:** Update the alias with the new path:
```bash
chat_loop --save-alias pete /new/path/agent.py --overwrite
```

### Alias Name Conflict

```bash
$ chat_loop --save-alias pete another/agent.py
Error: Alias 'pete' already exists (points to: /existing/path/agent.py).
Use --overwrite to update.
```

**Solution:** Either choose a different name or use `--overwrite`:
```bash
chat_loop --save-alias pete another/agent.py --overwrite
```

## Best Practices

1. **Use descriptive names** that remind you what the agent does
2. **Keep it short** - the point is to save typing!
3. **Be consistent** - use the same naming pattern for all aliases
4. **List regularly** - use `--list-aliases` to see what you have
5. **Clean up** - remove aliases you no longer use
6. **Backup** - if you have many aliases, backup `~/.chat_aliases`

## Integration with Other Features

Aliases work seamlessly with all other chat loop features:

```bash
# Use alias with custom config
chat_loop pete --config ~/.chatrc-work

# Use alias with template
chat_loop clara
You: /review my_code.py

# Use alias from any directory
cd ~/Documents
chat_loop quinten
You: research quantum computing papers
```

## See Also

- [README.md](README.md) - Main documentation
- [CONFIG.md](CONFIG.md) - Configuration guide
- [INSTALL.md](INSTALL.md) - Installation guide
