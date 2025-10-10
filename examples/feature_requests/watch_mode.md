---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] Add --watch flag for hot-reloading agent during development'
labels: enhancement
assignees: ''
---

## Feature Description
Add a `--watch` / `-w` flag that automatically reloads the agent when the agent file or its dependencies are modified, similar to nodemon for Node.js development.

## Problem/Motivation
**Is your feature request related to a problem?**
When developing and iterating on agents, I have to manually exit the chat loop and restart it every time I make a code change. This slows down the development cycle significantly.

Example: "I'm frustrated when I need to test changes to my agent because I have to exit the chat, restart `chat_loop`, and lose my conversation context every time."

## Proposed Solution
Add a watch mode that monitors the agent file and automatically reloads when changes are detected.

**Example:**
```bash
# Start in watch mode
chat_loop myagent --watch

# Or with short flag
chat_loop path/to/agent.py -w

# Output when changes detected:
# 🔄 Agent file modified, reloading...
# ✓ Agent reloaded successfully
```

## Alternatives Considered
1. **Manual restart** - Current approach, too slow
2. **External watcher script** - Could use entr/watchexec but requires additional setup
3. **Editor integration** - Would require per-editor plugins

## Benefits
Who would benefit from this feature and how?
- **Agent developers**: Significantly faster iteration cycle during development
- **QA testers**: Can test changes immediately without losing context
- **Anyone prototyping**: Enables rapid experimentation with agent behavior

## Implementation Ideas
- Use `watchdog` library to monitor file changes
- Watch the agent file itself plus any relative imports
- Option to watch entire directory: `--watch-dir path/`
- Debounce rapid changes (wait 500ms after last change)
- Preserve conversation history across reloads (optional)
- Show clear indication when reload happens

**Suggested implementation approach:**
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AgentReloader(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == agent_path:
            reload_agent()
```

## Additional Context
Similar to:
- `nodemon` for Node.js
- `cargo watch` for Rust
- Django's auto-reload
- Flask's debug mode

This is a common pattern in modern development tools and would align well with the project's focus on developer experience.

## Priority
How important is this feature to you?
- [ ] Critical - Blocking my workflow
- [x] High - Would significantly improve my experience
- [ ] Medium - Nice to have
- [ ] Low - Minor improvement
