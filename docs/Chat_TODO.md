# Chat Loop Improvement TODO

This document tracks planned enhancements for the AWS Strands chat loop interface.

## Status Summary

**Recently Completed (11/27 features):**
- ✅ Command History with Readline (fully working with editing)
- ✅ Multi-line Input Support
- ✅ Automatic Error Recovery with Retry Logic
- ✅ Clear Command with Session Reset
- ✅ Streaming Progress Indicator
- ✅ Agent Metadata Display
- ✅ Improved Response Formatting with Rich
- ✅ Configuration File Support
- ✅ Status Bar (Minimal)
- ✅ Token/Cost Tracking
- ✅ Prompt Templates

**Next Up (High Priority):**
- ⏭️ Save Conversation - Export to markdown

**Total Progress:** 11 of 27 planned features completed (41%)

## High Priority - UX Enhancements

### 1. Command History with Readline ✅ COMPLETED
- [x] Add readline support for arrow key navigation
- [x] Persist history across sessions (.chat_history file)
- [x] Full editing support (arrow keys, backspace, Ctrl+A/E/K, etc.)
- [x] Search history with Ctrl+R (works automatically with readline)
- [x] Configure readline for better editing experience
- [ ] Auto-complete common commands (future enhancement)

### 2. Multi-line Input Support ✅ COMPLETED
- [x] Type `\\` to enter multi-line mode
- [x] Press Enter on empty line to submit
- [x] Visual indicator for multi-line mode

### 3. Token/Cost Tracking ✅ COMPLETED
- [x] Track input/output tokens per query
- [x] Display session totals
- [x] Estimate costs per model
- [x] Show running total in status line or summary

### 4. Clear Screen Command ✅ COMPLETED
- [x] Add `clear` command to clean terminal
- [x] Works cross-platform (Windows + Unix)
- [x] Reset agent session for fresh context

### 5. Save Conversation
- [ ] Export conversation to markdown
- [ ] Include timestamps and metadata
- [ ] Auto-save option on exit
- [ ] Format: `conversations/YYYY-MM-DD_HH-MM-SS_agent-name.md`

### 6. Better Error Recovery ✅ COMPLETED
- [x] Retry logic for network failures (3 attempts with 2s delay)
- [x] Rate limit detection with exponential backoff
- [x] Graceful degradation for timeouts
- [x] Show helpful error messages with suggestions

### 7. Streaming Progress Indicator ✅ COMPLETED
- [x] Show "Thinking..." while waiting for first token
- [x] Animated spinner with rich (dots animation)
- [x] Fallback to simple dots for terminals without rich
- [x] Hide when streaming starts (first token arrives)
- [x] Cleanup on errors and completion

### 8. Copy Last Response
- [ ] Add `copy` command to copy last response to clipboard
- [ ] Cross-platform clipboard support (pyperclip)
- [ ] Visual confirmation when copied

## Medium Priority - Features

### 9. Configuration File ✅ COMPLETED
- [x] Support `~/.chatrc` or `.chatrc` in project root
- [x] Configure: colors, behavior, paths, features, UI
- [x] Per-agent overrides with hierarchical merging
- [x] Example config with extensive comments (.chatrc.example)
- [x] YAML format with graceful fallback to defaults
- [x] Hierarchical precedence: project > global > defaults
- [x] Optional --config CLI argument

### 10. Improved Response Formatting ✅ COMPLETED
- [x] Better markdown rendering in terminal (rich library)
- [x] Syntax highlighting for code blocks (via rich markdown)
- [x] Tables rendered properly (via rich markdown)
- [x] Word wrap for long lines (automatic with rich)
- [x] Graceful fallback when rich not available

### 11. Agent Metadata Display ✅ COMPLETED
- [x] Show agent model, max_tokens on startup
- [x] Display available tools/capabilities
- [x] Add `info` command to show details
- [x] Extract metadata from agent configuration
- [x] Show tool count and list first 10 tools

### 12. Conversation Context Management
- [ ] Add `context` command to show conversation length
- [ ] Warn when approaching context limits
- [ ] Option to clear/truncate history
- [ ] Smart context window management

### 13. Session Management
- [ ] Resume previous conversations
- [ ] List available sessions
- [ ] Delete old sessions
- [ ] Search across sessions

### 14. Prompt Templates ✅ COMPLETED
- [x] Save reusable prompts (markdown files in ~/.prompts/)
- [x] Load template with `/template_name <context>`
- [x] Variable substitution in templates ({input} placeholder)
- [x] List templates with `templates` command
- [x] Share templates between agents (global ~/.prompts/ directory)

## Low Priority - Nice to Have

### 15. Response Streaming Enhancements
- [ ] Pause/resume streaming (space bar?)
- [ ] Adjust streaming speed
- [ ] Buffer responses for smoother display

### 16. Rich Terminal UI
- [x] Status bar with query count, time, model (minimal version)
- [x] Enhanced status bar with token count (available with token tracking enabled)
- [ ] Split screen for long responses
- [ ] Scrollback buffer
- [ ] TUI mode with panels (textual library?)

### 17. Voice Input/Output
- [ ] Speech-to-text for input
- [ ] Text-to-speech for responses
- [ ] Toggle with command

### 18. Agent Switching
- [ ] Switch between agents mid-session
- [ ] Compare responses from multiple agents
- [ ] Agent selector menu

### 19. Export Options
- [ ] Export to PDF
- [ ] Export to HTML with syntax highlighting
- [ ] Export to JSON for analysis

### 20. Collaboration Features
- [ ] Share conversation URL
- [ ] Collaborative sessions
- [ ] Comments/annotations on responses

## Additional Ideas

### 21. Performance & Monitoring
- [ ] Response time tracking per query
- [ ] Success/failure rate statistics
- [ ] Network latency monitoring
- [ ] Cache frequent queries

### 22. Safety & Validation
- [ ] Confirm before expensive operations
- [ ] Validate inputs for common issues
- [ ] Sanitize file paths in save operations
- [ ] Rate limiting on client side

### 23. Developer Tools
- [ ] Debug mode with verbose logging
- [ ] Inspect raw API responses
- [ ] Test mode with mock responses
- [ ] Performance profiling

### 24. Accessibility
- [ ] Screen reader support
- [ ] Configurable color schemes
- [ ] High contrast mode
- [ ] Font size adjustment

### 25. Integration
- [ ] Pipe input from files or commands
- [ ] Redirect output to files
- [ ] Integration with git for commit messages
- [ ] IDE plugin/extension

### 26. Advanced Features
- [ ] Batch mode (process multiple queries from file)
- [ ] Watch mode (re-run on file changes)
- [ ] Webhook support for notifications
- [ ] Scheduled queries

### 27. Quality of Life
- [ ] Aliases for common commands
- [ ] Auto-save drafts
- [ ] Undo/redo for queries
- [ ] Quick reply shortcuts

## Implementation Notes

### Dependencies to Consider
- `readline` - command history (built-in)
- `rich` - better terminal formatting
- `pyperclip` - clipboard support
- `textual` - TUI framework (if going that route)
- `click` - better CLI (already in requirements)

### Backward Compatibility
- Keep simple mode for users who don't want features
- All enhancements should be optional
- Graceful degradation when features unavailable

### Testing
- Test on macOS, Linux, Windows
- Test with different terminal emulators
- Test with different agent types
- Performance testing with long conversations

## Quick Wins (Start Here)
1. ✅ **DONE** - Add readline for command history (easy, huge impact)
2. ✅ **DONE** - Implement clear command (trivial, useful)
3. ⏭️ Add save conversation (medium effort, valuable)
4. ✅ **DONE** - Token tracking display (shows costs)
5. ✅ **DONE** - Multi-line input (essential for code)
6. ✅ **DONE** - Error recovery with retry logic

## Recently Completed

### Status Bar (Minimal) ✅ (2025-01-08)
- Clean top-positioned status bar with box drawing characters
- Shows 4 key metrics:
  - Agent name
  - Model ID (shortened if too long)
  - Query count (tracks queries per session)
  - Session time (minutes and seconds)
- Configuration-controlled (ui.show_status_bar in .chatrc)
- Default: disabled (opt-in)
- Updates after each query
- Auto-clears screen and redraws for clean display
- No dependencies beyond Python stdlib
- Graceful fallback if disabled

**Design Decisions:**
- Minimal fields (not token/cost - those need tracking first)
- Top position (always visible)
- All-or-nothing config (no field picker)
- Config-only control (no CLI flag)
- Clean box drawing style with │ separators

**Example:**
```
┌─────────────────────────────────────────────────┐
│ Clara │ Sonnet 4.5 │ 3 queries │ 12m 34s        │
└─────────────────────────────────────────────────┘
```

### Token/Cost Tracking ✅ (2025-01-08)
- Track input and output tokens per query
- Display session totals with formatted numbers (K/M suffix)
- Cost estimation for Claude and GPT models
- Per-query breakdown showing input/output tokens
- Session cost running total
- Integration with status bar (shows token count when enabled)
- Configuration-controlled (features.show_tokens in .chatrc)
- Default: disabled (opt-in)
- Multiple response pattern support (Anthropic, OpenAI, etc.)
- Graceful handling of unknown models (shows tokens but no cost)

**Implementation:**
- TokenTracker class with pricing table for common models
- Pricing: per-million-token rates for input and output separately
- Token extraction from response objects (multiple attribute patterns)
- Per-query display: `Tokens: 1.2K (in: 234, out: 1.0K) │ Cost: $0.0123 │ Session: $0.0456`
- Status bar integration: shows running total when both status bar and token tracking enabled

**Design Decisions:**
- Separate input/output pricing (more accurate than blended)
- K/M formatting for readability (1234 → 1.2K, 1234567 → 1.2M)
- Cost only shown if > $0 (unknown models don't show "$0.00")
- Session total tracks across queries (resets on clear)

**Example Output:**
```
------------------------------------------------------------
Time: 2.3s │ Tokens: 1.5K (in: 234, out: 1.3K) │ Cost: $0.0213 │ Session: $0.0789
```

### Prompt Templates ✅ (2025-01-08)
- Markdown-based templates stored in `~/.prompts/` directory
- Call templates with `/template_name <optional context>`
- Variable substitution using `{input}` placeholder
- List available templates with `templates` command
- First line markdown heading used as template description
- Shared across all agents (global directory)
- Auto-creates directory on first use

**Implementation:**
- Templates are standard markdown files with `.md` extension
- Variable `{input}` replaced with provided context
- If no `{input}` placeholder, context appended to template
- Templates listed with descriptions from first `#` line

**Example Templates:**
```markdown
# Code review
Please review the following code for:
- Best practices and design patterns
- Potential bugs or edge cases
{input}
```

**Usage:**
```
You: templates
Available Prompt Templates (3):
  /review - Code review
  /explain - Explain code
  /debug - Debug assistance

You: /review def foo(): return bar
✓ Loaded template: review
[Sends "Please review the following code for... def foo(): return bar"]
```

**Design Decisions:**
- Markdown format for rich formatting and readability
- Global `~/.prompts/` location for sharing across projects
- Simple `/name` syntax (no `/template` prefix needed)
- Automatic variable substitution with fallback to appending

### Configuration File Support ✅ (2025-01-08)
- Comprehensive configuration system with YAML format
- Hierarchical loading: project .chatrc > global ~/.chatrc > built-in defaults
- Configurable sections:
  - **Colors**: All ANSI color codes (user, agent, system, error, success, dim)
  - **Features**: auto_save, rich_enabled, show_tokens, show_metadata, readline_enabled
  - **Paths**: save_location, log_location
  - **Behavior**: max_retries, retry_delay, timeout, spinner_style
  - **UI**: show_banner, show_thinking_indicator, show_duration
- Per-agent overrides: Customize settings for specific agents by name
- Example config file with detailed comments and alternative color schemes
- Optional --config CLI argument for explicit config path
- Graceful fallback when YAML not available or config missing
- Dot-notation access (e.g., 'features.auto_save')
- Deep merge for nested configurations

**Files Created:**
- `AWS_Strands/chat_config.py` - Configuration loader and manager (280 lines)
- `AWS_Strands/.chatrc.example` - Comprehensive example config with docs

**Integration Points:**
- Colors applied from config on startup
- All behavior settings configurable
- Banner shows config status and auto-save location
- Info command shows config-enabled features

### Streaming Progress Indicator ✅ (2025-01-08)
- Animated thinking indicator while waiting for first token
- Rich spinner with "dots" animation for terminals with rich library
- Fallback to simple animated dots (...) for basic terminals
- Automatically hides when first token arrives
- Proper cleanup on errors and completion
- Non-blocking async implementation

### Agent Metadata Display ✅ (2025-01-08)
- Automatically extracts agent configuration on startup
- Shows model ID, max_tokens, temperature in banner
- Displays tool count
- New `info` command for detailed information
- Lists available tools (first 10, with count of remaining)
- Shows enabled features (rich, readline, etc.)

### Improved Response Formatting with Rich ✅ (2025-01-08)
- Integrated rich library for beautiful markdown rendering
- Automatic syntax highlighting for code blocks
- Proper table rendering
- Smart word wrapping for long lines
- Collects streaming response and renders at end for better formatting
- Graceful fallback to plain text when rich not available
- Works seamlessly with streaming and non-streaming agents

### Clear Command with Session Reset ✅ (2025-01-08)
- Type `clear` to clear terminal and reset agent session
- Cross-platform support (Unix `clear` and Windows `cls`)
- Gracefully cleans up old agent if cleanup method exists
- Creates fresh agent instance using agent factory
- Re-displays banner after clear
- Maintains command history across session resets

## Completed Earlier (2025-01-08)

### Command History with Full Readline Support ✅
- ↑↓ arrow keys navigate through command history
- Full line editing with ←→ arrow keys, backspace, delete
- Standard emacs keybindings (Ctrl+A, Ctrl+E, Ctrl+K, etc.)
- Ctrl+R for reverse history search
- Persistent history saved to `~/.chat_history` (1000 commands)
- Fixed: Direct input() calls instead of executor to preserve readline functionality

### Multi-line Input Support ✅
- Type `\\` to enter multi-line mode
- Continue entering lines with `...` prompt
- Press Enter on empty line to submit
- Full readline editing works in multi-line mode too
- Perfect for pasting code blocks or long prompts

### Automatic Error Recovery ✅
- **Timeout handling**: 3 retry attempts with 2s delay between tries
- **Connection errors**: Automatic retry with clear status messages
- **Rate limiting**: Smart detection with exponential backoff (2s → 4s → 8s)
- Color-coded error messages (red) with helpful suggestions
- All errors logged for debugging
- Non-retryable errors fail fast with actionable messages

---

## Implementation Notes & Lessons Learned

### Command History
- **Key Learning:** Using `asyncio.run_in_executor()` breaks readline's terminal access
- **Solution:** Use direct `input()` calls - blocking on user input is fine
- **Benefit:** Full readline functionality preserved (editing, search, keybindings)

### Multi-line Input
- **Design Choice:** `\\` trigger is clear and doesn't conflict with normal input
- **Alternative Considered:** Press Enter twice (rejected - too easy to accidentally submit)
- **Works Well With:** Readline editing works in multi-line mode seamlessly

### Error Recovery
- **Retry Strategy:** 3 attempts for transient errors, fail fast for others
- **Rate Limits:** Exponential backoff prevents hammering the API
- **User Experience:** Show attempt count and clear error messages

---

## Known Issues

None currently - all implemented features working as expected.

---

**Note:** This is a living document. Add ideas as they come up and prioritize based on user feedback.
