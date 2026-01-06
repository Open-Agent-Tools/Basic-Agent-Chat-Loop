# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.8.0-beta.1] - 2026-01-06

### Changed - Major Architectural Simplification
- **Single Output Path** - Completely redesigned output handling for simplicity and reliability
  - Removed all bifurcated rendering paths (Rich/plain, Harmony/not, streaming/buffering)
  - Agent library now handles all output naturally - we just collect text for history
  - Eliminates double-output issue permanently
  - Tool prompts (Y/n confirmations) work naturally without interception
  - Removed 361 lines of complex rendering logic

### Removed
- **HarmonyProcessor** - Removed entire harmony processing system
  - Removed HarmonyProcessor import and instantiation
  - Removed 62-line harmony config logic
  - Removed _normalize_harmony_config() method
  - Removed harmony config sections from chat_config.py
- **ResponseRenderer Simplification** - Reduced from 165 to 45 lines (73% reduction)
  - Removed render_streaming_text(), render_final_response(), should_skip_streaming_display()
  - Removed _render_rich_markdown(), _render_plain_text() methods
  - Removed console and harmony_processor parameters
  - Now only handles agent name header display
- **OutputState** - Deleted components/output_mode.py (no longer needed)
- **Rich Console** - Removed Rich Console instantiation and rendering
- **suppress_agent_stdout** - Removed configuration option (no longer needed)

### Technical Details
The 1.8.0 release represents a fundamental shift in philosophy. Instead of trying to intercept, process, and re-render agent output (which caused double-output and hid tool prompts), we now let the agent library handle output naturally. We silently collect text for session history while the agent prints directly to terminal. This creates a single, simple output path that just works.

**Before (1.7.x)**: Agent → Our Interceptor → Rich/Harmony Processing → Render
**After (1.8.0)**: Agent → Terminal (we collect silently for history)

Benefits:
- No double-output (agent prints once)
- Tool prompts visible (no interception)
- Much simpler codebase (-361 lines)
- Easier to maintain and understand

Breaking Changes:
- Harmony processing no longer applies
- Rich markdown rendering no longer applies to agent output
- Agent output appears exactly as library provides it

## [1.7.1-beta.2] - 2026-01-05

### Fixed
- **Duplicate Text Output** - Resolved text appearing twice in terminal (streaming + final render)
  - Changed `render_streaming_text()` to check console object directly instead of `use_rich` flag
  - The `use_rich` flag could be incorrectly set or out of sync with actual console state
  - Now checks if `console is not None` as single source of truth for Rich availability
  - If console exists → skip streaming output (Rich will render later)
  - If console is None → print streaming text (plain text mode)
  - Updated `chat_loop.py` to use renderer's `should_skip_streaming_display()` method for consistency
  - Fixes user-reported issue: "text is still double printing to the terminal"
  - Changes in response_renderer.py (lines 89-97, 105) and chat_loop.py (lines 1870-1876)

### Technical Details
The root cause was using the `use_rich` flag to determine whether to skip streaming output. This flag is set during initialization and could become out of sync with the actual console object state. By checking the console object directly (`self.console is not None`), we ensure the decision is based on the actual availability of Rich rendering, not a potentially stale flag value.

## [1.7.1-beta.1] - 2026-01-05

### Fixed
- **Template Command Bug** - Fixed template commands (/) completely failing due to incorrect argument parsing
  - `CommandRouter` encodes template info as `"name|input"` using pipe delimiter
  - `chat_loop.py` was incorrectly splitting on whitespace instead of pipe
  - This caused templates like `/explain some code` to look for template `"explain|some"` instead of `"explain"`
  - Now uses `CommandRouter.extract_template_info()` helper method for correct parsing
  - Fixes user-reported issue: "prompt template using '/' are all failing"
  - All template functionality restored (lines 2498-2508 in chat_loop.py)

### Improved
- **Windows Rich Console Support** - Enhanced terminal compatibility for Windows systems
  - Added `force_terminal=True` to force Rich into terminal mode even if auto-detection fails
  - Added `legacy_windows=False` to use modern Windows Terminal features
  - Added comprehensive debug logging for terminal capability detection
  - Logs Rich Console state (is_terminal, color_system, legacy_windows)
  - Logs ResponseRenderer initialization values for troubleshooting
  - Addresses potential duplicate output issues on Windows terminals
  - Changes in chat_loop.py (lines 519-535) and response_renderer.py (lines 62-70)

### Technical Details
The template command bug was a simple but critical parsing error. The `CommandRouter` properly encodes template name and input as a pipe-delimited string (`"name|input"`), but the chat loop was splitting on whitespace instead of using the existing `extract_template_info()` helper. This meant commands like `/explain some code` would try to load a template called `"explain|some"` (with the pipe character) instead of `"explain"`.

The Windows improvements add better terminal detection and logging to help diagnose why Rich markdown rendering might show duplicate output on Windows systems. The `force_terminal=True` flag ensures Rich doesn't fall back to plain text mode when it can't detect terminal capabilities.

## [1.7.0] - 2026-01-02

### Changed
- **Internal Refactoring** - Improved code organization and maintainability
  - Integrated `SessionState` component to centralize session management
    - Replaced 8 scattered instance variables with single cohesive component
    - Single source of truth for query count, conversation history, timing, and accumulated usage
    - Cleaner delta calculation for AWS Strands cumulative token tracking
  - Integrated `CommandRouter` component for type-safe command parsing
    - Replaced 330+ lines of manual string parsing with enum-based routing
    - All commands now use `CommandType` enum for type safety
    - Easier to add new commands and maintain existing ones
    - Better separation of command parsing from command handling
  - Extracted 5 new components for better modularity:
    - `StreamingEventParser` - Event parsing logic
    - `ResponseRenderer` - Response formatting and display
    - `UsageExtractor` - Token/metadata extraction
    - `CommandRouter` - Command parsing and routing
    - `SessionState` - Session state management
  - Reduced `chat_loop.py` from 3,188 to 2,948 lines (-240 lines)
  - All 510 tests passing, 100% mypy type coverage, ruff compliant
  - No user-facing changes - purely internal code quality improvements

## [1.6.1] - 2025-12-31

### Added
- **Incremental Autosave** - Conversations now save automatically after each message
  - Removed `auto_save` configuration option (feature is always enabled)
  - Save happens immediately after each query-response cycle
  - Prevents data loss from crashes or force quits
  - All conversations saved to `./.chat-sessions` (project-local)
  - Removed manual `#save` command (no longer needed)

### Changed
- **Breaking Change**: Removed `features.auto_save` from configuration
  - Auto-save is now always enabled and cannot be disabled
  - Updated help text to reflect always-on autosave
  - Updated configuration examples and documentation

### Fixed
- Test suite updated to match removed auto_save configuration
  - All 318 tests passing with new autosave behavior

## [1.6.0-beta.7] - 2025-12-30

### Added
- **Context Monitoring Features** - Enhanced token usage tracking and warnings
  - Added `#context` command to display detailed token usage statistics
  - Status bar now shows context percentage when max_tokens is known
  - Configurable warning thresholds via `context.warning_thresholds` in config
  - Default thresholds at 80%, 90%, and 95% with appropriate messaging
  - Special treatment for highest threshold (includes suggestion to use `#compact`)
  - Supports custom threshold configurations per agent

### Fixed
- **AWS Strands Token Accumulation Bug** - Corrected cumulative token counting
  - AWS Strands `accumulated_usage` is cumulative across entire session
  - Implemented delta calculation to track only per-query token usage
  - Added `last_accumulated_input/output` tracking variables
  - Modified `_extract_token_usage()` to return `(usage_dict, is_accumulated)` tuple
  - Prevents token counts from growing beyond actual context limits
  - Related: User-reported issue of "70.6M tokens" appearing in status bar

## [1.6.0-beta.6] - 2025-12-30

### Changed
- **Command Prefix Update** - All in-chat commands now require `#` prefix to avoid collisions with regular conversation
  - Commands updated: `#help`, `#info`, `#compact`, `#sessions`, `#save`, `#copy`, `#resume`, `#clear`, `#quit`, `#exit`
  - Template commands still use `/` prefix (intentional)
  - Multi-line input still uses `\\` (intentional)
  - Added helpful error message for unknown `#` commands
  - Updated all help text and README documentation

### Fixed
- **Exit Command Hanging** - Added explicit `sys.exit(0)` to ensure clean terminal return
  - Fixed issue where `#exit` would show "[Process Completed]" but not return to prompt
  - Process now terminates cleanly and returns control immediately

## [1.6.0] - 2025-12-30

### Added
- **Session Compaction and Summary-Based Resume** - Complete redesign of conversation management
  - Auto-generate structured summaries when saving conversations (Phase 1)
  - New `compact` command to save current session and continue with context preserved (Phase 2)
  - Rewritten `resume` command using summary-based restoration instead of query replay (Phase 3)
  - Progressive summarization with n-1 chain model (each session references only parent)
  - HTML comment markers for easy summary extraction (`<!-- SESSION_SUMMARY_START/END -->`)
  - Fast, token-efficient session restoration without replaying all queries
  - Graceful error handling for missing summaries, agent mismatches, and edge cases
  - Session metadata tracking (agent_path, resumed_from, query_count, tokens)
  - Restoration exchange tracked but not counted as user query
  - Related: Issue #48 (Conversation compaction to manage context limits)

### Changed
- **Conversation Saving Made Async** - `save_conversation()` now async to support summary generation
- **Session Files Include Agent Path** - Markdown files now store agent file path instead of description
- **Resume Command Re-enabled** - Was temporarily disabled, now working with new summary-based approach
- **README Documentation Updated** - Added comprehensive examples for `resume` and `compact` commands

### Technical Details
The session resume system was completely redesigned to use summaries instead of query replay:

**Phase 1 - Auto-Summary Generation:**
- `_generate_session_summary()` method generates structured summaries on exit (lines 1160-1232)
- Summaries use hybrid instruction format with progressive compression
- Background context condenses previous summary to 1-2 sentences
- Current session details: topics discussed, decisions made, pending items
- Summary appended to markdown files with HTML comment markers
- Graceful handling if summary generation fails (saves without summary, warns user)

**Phase 2 - Compact Command:**
- `_handle_compact_command()` method (lines 1391-1566)
- Saves current session with summary
- Extracts summary and creates new session
- Agent reads summary and acknowledges context
- User continues in new session with compressed history
- Session chain tracked via `_resumed_from` and `_previous_summary` attributes

**Phase 3 - Summary-Based Resume:**
- `_extract_metadata_from_markdown()` utility (lines 1113-1151) parses session headers with regex
- Complete rewrite of `restore_session()` method (lines 874-1090)
- Loads markdown file, extracts summary using `_extract_summary_from_markdown()`
- Sends restoration prompt with summary to agent
- Agent provides brief acknowledgment (2-6 sentences)
- Creates new session with restoration exchange tracked
- Supports both session number (`resume 1`) and full ID

**Benefits:**
- Fast: No query replay, just summary injection
- Token-efficient: Summaries are compact vs full transcripts
- Traceable: File paths create clear session lineage
- Progressive: Old context compresses naturally over time
- Graceful: Errors don't block saving or resuming

**Markdown Format Changes:**
```markdown
**Session ID:** session_3
**Agent Path:** /path/to/agent.py
**Resumed From:** session_2

<!-- SESSION_SUMMARY_START -->
**Background Context:** [condensed previous context]

**Current Session Summary:**
**Topics Discussed:**
- [bullet points]

**Decisions Made:**
- [bullet points]

**Pending:**
- [bullet points]
<!-- SESSION_SUMMARY_END -->
```

## [1.5.1] - 2025-12-29

### Fixed
- **Empty Agent Responses in Saved Conversations** - Critical bugfix for conversation saving
  - Fixed streaming event parser to handle AWS Strands `.delta` events (Claude Sonnet 4.5)
  - Fixed conversation history tracking to work regardless of `auto_save` setting
  - Fixed Harmony processor overwriting responses with empty channels
  - Added comprehensive test suite (test_conversation_saving.py, 608 lines)
  - 9/9 core functionality tests passing for streaming formats and history tracking

### Technical Details
Three critical bugs were causing saved conversation files (.md and .json) to show only user queries without agent responses:

1. **Streaming Event Parser**: Only handled `.data` attribute events, missing AWS Strands `.delta` events. Added fallback handling for multiple event formats (.delta, .text, string events) in chat_loop.py:1369-1415.

2. **Conversation History Tracking**: History was only tracked when `auto_save=True`, breaking manual saves and copy commands. Removed conditional tracking in chat_loop.py:1595-1606.

3. **Harmony Processor**: Empty channels would overwrite actual response text. Fixed to preserve original text when channels are empty (harmony_processor.py:219-226, 463-467, 502).

Impact: Universal support for all streaming formats, reliable conversation saving regardless of configuration, complete conversation history in saved files, all manual commands work as expected. Fixes user reports of "saved conversations only show my questions".

## [1.5.0] - 2024-12-29

### Changed
- **Removed Google ADK Support** - Focused exclusively on AWS Strands agents
  - Removed all Google ADK/Gemini-related code and dependencies
  - Simplified codebase by removing unused agent framework
  - Updated documentation to specify AWS Strands only
  - Cleaned up imports and removed adk-specific utilities

### Technical Details
The project initially supported both Google ADK and AWS Strands agent frameworks. Since the focus is exclusively on AWS Strands (using Claude models via Anthropic/Bedrock), all Google ADK support has been removed to simplify the codebase and reduce maintenance overhead. All existing functionality for AWS Strands agents remains unchanged.

## [1.4.1] - 2024-12-24

### Fixed
- **Verbose Payload Logging Level** - Changed from INFO to DEBUG level
  - All verbose payload logging now uses `logger.debug()` instead of `logger.info()`
  - Keeps standard logs clean while preserving diagnostic capabilities
  - Users can enable verbose logging by setting logger level to DEBUG
  - Prevents log clutter in production environments

### Technical Details
The verbose payload logging introduced in v1.4.0 was initially set to INFO level, which could clutter standard logs with detailed diagnostic information. This hotfix moves all payload logging to DEBUG level, following standard logging practices where detailed diagnostic information belongs at DEBUG level. To enable verbose payload logging, set the logger level to DEBUG before initializing the chat loop.

## [1.4.0] - 2024-12-24

### Added
- **Verbose Payload Logging** - Comprehensive logging of request/response data at DEBUG level
  - Added `_serialize_for_logging()` helper to serialize objects to JSON with repr() fallback
  - Logs request query before sending to agent
  - Logs each streaming event received from agent during streaming responses
  - Logs final response object after streaming completes
  - Logs complete response for non-streaming agents
  - All logs include clear separators for easy parsing in agent log files
  - Enables detailed debugging and monitoring of agent communication
  - DEBUG level keeps logs clean by default, enable with logger.setLevel(logging.DEBUG)

### Technical Details
This feature adds comprehensive visibility into the data exchanged between the chat loop and agent. All request/response payloads are logged at DEBUG level in the agent log files (~/.chat_loop_logs/*_chat.log). The serialization helper attempts JSON formatting first (with pretty printing and default=str for common types), falling back to repr() for non-serializable objects. This makes it easy to debug agent behavior, track API changes, and monitor system health. To enable verbose logging, set the logger level to DEBUG before initializing the chat loop.

## [1.3.9] - 2024-12-24

### Fixed
- **Multipart Response Formatting** - Added newline separator when joining multiple response chunks
  - Prevents sentences from running together when agents return structured/multipart responses
  - Changed from empty string join to newline join in response text assembly
  - Improves readability for harmony multi-channel responses and structured content blocks
  - Example: `"Analysis.Conclusion."` → `"Analysis.\nConclusion."`

### Technical Details
When agents return responses as multiple content blocks or text chunks (common with streaming responses and harmony format), the code was concatenating them with no separator. This caused sentences to run together without proper spacing. The fix adds a newline separator (`"\n".join()` instead of `"".join()`) to ensure proper formatting and readability in both display and saved logs.

## [1.3.8] - 2024-12-24

### Fixed
- **Session Logging Bug** - Fixed conversation logs only saving user input, missing agent responses
  - Was saving `full_response` (raw text) instead of `display_text` (what user sees)
  - With harmony processing, if token extraction fails, `full_response` could be empty while `display_text` has content
  - Now saves `display_text` to ensure logs match what's displayed on screen
  - Also updated `self.last_response` to use `display_text` for clipboard copy commands
  - Ensures "what you see is what gets saved" consistency across display, logs, and clipboard

### Technical Details
This fixes a bug introduced with harmony processing where the conversation history was saving the raw response text before harmony formatting, while displaying the formatted version to the user. When harmony's token-level parsing wasn't available (missing logprobs), the raw text could be empty while the display text contained properly formatted content. The fix ensures session saves, clipboard copies, and display all use the same processed response text.

## [1.3.7] - 2024-12-24

### Fixed
- **CRITICAL: Harmony Detection Order Bug** - Fixed harmony detection running before model extraction
  - Harmony detection was being called before model_id was extracted from agent, causing auto-detection to fail
  - Now extracts model_id first, then passes it to `HarmonyProcessor.detect_harmony_agent()`
  - Resolves issue where "openai/gpt-oss-120b" models showed in banner but harmony wasn't enabled
  - Added model_id parameter to detect_harmony_agent() for more reliable detection

### Improved
- **Code Quality** - Comprehensive cleanup of harmony processor implementation
  - Removed 165 lines of excessive debug logging (25% reduction: 656→491 lines)
  - Removed duplicate harmony detection call (was being called twice)
  - Removed dead code: create_conversation() method and unused imports
  - Changed verbose INFO logging to DEBUG level for non-critical messages
  - Added clear documentation for weak fallback parsing method
- **Type Safety** - Fixed all mypy type checking errors
  - Fixed Collection indexing error in session_manager.py
  - Fixed optional type handling for session metadata
  - Added type ignore comments for untyped third-party imports (openai_harmony, pyperclip)
- **Enhanced Logging** - Added diagnostic logging for harmony detection
  - Added "Model Detected:" log message after agent load for debugging
  - Added "Harmony Detected:" log message to confirm detection status
  - Simplified detection logging to show only essential information

### Technical Details
This release fixes a critical bug where the harmony detection logic was executing before the model_id was extracted from the agent object. This caused the detection to fail even when the model was correctly identified as "openai/gpt-oss-120b" and shown in the status banner. The fix ensures model extraction happens first, then passes the extracted model_id to the detection function for reliable harmony format identification.

## [1.3.6] - 2024-12-24

### Fixed
- **Harmony Auto-Detection** - Fixed harmony processor not auto-detecting gpt-oss models
  - Now properly calls `HarmonyProcessor.detect_harmony_agent()` during initialization
  - Enhanced detection to check direct string attributes on agent (model, model_id, model_name)
  - Updated agent_loader to handle agents where model is stored as direct string attribute
  - Added comprehensive debug logging to show detection process
  - Resolves issue where "openai/gpt-oss-120b" models weren't being auto-detected

## [1.3.5] - 2024-12-24

### Fixed
- **Harmony Config Value Normalization** - Fixed harmony processor not being enabled when config set to "force" or other string values
  - Added `_normalize_harmony_config()` method to handle YAML string values ("auto", "yes", "no", "force", "true", "false", etc.)
  - Config values now properly normalized to boolean True/False or None
  - Enhanced logging shows both raw and normalized config values for debugging
  - Resolves issue where `harmony.enabled: force` wasn't being recognized

### Improved
- **Harmony Error Handling** - Enhanced error reporting for harmony token parsing failures
  - Added comprehensive error logging with token samples when parsing fails
  - Shows token count and first 50 tokens for debugging malformed harmony responses
  - Provides helpful error messages about common issues (e.g., missing logprobs)
  - Falls back gracefully to text-based parsing when token parsing fails
- **Harmony Documentation** - Clarified all acceptable config values
  - Updated config example to show all valid values: "auto", "yes/true/force/on", "no/false/off"
  - Added note about requiring logprobs=True in API calls for proper token parsing
  - Better documentation of harmony configuration options

## [1.3.4] - 2024-12-24

### Added
- **Enhanced Harmony Token Extraction** - Improved debugging for harmony response parsing
  - Added comprehensive logging for response object structure analysis
  - Token extraction now handles multiple response formats (OpenAI, Anthropic, custom)
  - Detailed logging of token counts, samples, and parsing results
  - Better error messages when logprobs are missing or malformed

### Improved
- **Harmony Channel Processing** - Better separation and display of harmony channels
  - Messages now properly grouped by channel (reasoning, analysis, commentary, final)
  - Improved logging shows channel detection and content extraction
  - Enhanced format_for_display() with detailed thinking prefixes

## [1.3.3] - 2024-12-24

### Changed
- **Default Features Enabled** - All wizard options now default to enabled
  - `features.auto_save: true` (was false)
  - `features.show_tokens: true` (was false)
  - `ui.show_status_bar: true` (was false)
  - `harmony.show_detailed_thinking: true` (was false)
  - Provides better out-of-the-box experience for new users

### Fixed
- **Status Bar Display** - Fixed status bar not showing between messages
  - Status bar now displays by default with agent name, model, query count, and session time
  - Resolves issue where status bar was hidden due to false default
- **Harmony Detection Improvements** - Enhanced logging and documentation
  - Added detailed logging for harmony auto-detection process
  - Better documentation of `harmony.enabled` config options in example config
  - Fixed model_info type handling to prevent TypeError with status bar display

## [1.3.2] - 2024-12-24

### Added
- **Harmony Config Override** - Manual control for harmony processing
  - New `harmony.enabled` config option with tri-state values (auto/yes/no)
  - `auto` (default) - Auto-detect harmony agents
  - `yes` - Force enable harmony processing for all agents
  - `no` - Disable harmony processing entirely
  - Added to config wizard with validation
  - Fixes issue where harmony wasn't activating despite being configured

### Fixed
- **Model Detection for Strands Agents** - Correctly extract model metadata
  - Fixed "Unknown Model" display for Strands-based agents
  - Now checks `model.config` dict for Strands-style configuration
  - Properly extracts `model_id`, `max_tokens`, and `temperature` from config
  - Agent metadata now displays correctly for all Strands agents

### Changed
- Harmony processor initialization now respects config override priority
- Improved logging for harmony enablement (shows whether forced or auto-detected)

## [1.3.1] - 2024-12-24

### Fixed
- **Package Metadata** - Removed setuptools deprecation warnings
  - Removed deprecated `license = "MIT"` table format
  - Removed deprecated "License :: OSI Approved :: MIT License" classifier
  - Added modern `license-files = ["LICENSE"]` reference
  - Added `maintainers` field
  - Fixes "invalid distribution" warning on Windows

## [1.3.0] - 2024-12-24

### Added
- **OpenAI Harmony Support** - Full integration for gpt-oss models
  - Automatic detection of harmony-formatted agents
  - Specialized `HarmonyProcessor` for parsing structured responses
  - Multi-channel output support (reasoning, analysis, commentary, final)
  - Configurable detailed thinking mode with labeled prefixes
  - New `harmony.show_detailed_thinking` config option
  - Added to config wizard
  - Now a core dependency (openai-harmony>=0.0.8)

### Changed
- **Python 3.9+ Required** - Upgraded from Python 3.8
  - Required by openai-harmony dependency (pydantic>=2.11.7)
  - Updated all documentation and classifiers
  - Modernized type annotations (Dict→dict, List→list, Tuple→tuple)

## [0.3.7] - 2025-10-20

### Fixed
- **Windows Command History** - pyreadline3 now installed automatically on Windows
  - No longer requires manual installation with `[windows]` extras
  - Ensures consistent UX across all platforms
  - Added warning message if readline is unavailable on Windows
  - Resolves long-standing usability issue for Windows users

### Changed
- pyreadline3 moved from optional to core dependency (Windows only)
- Updated installation documentation to reflect automatic Windows support

## [0.3.6] - 2025-10-20

### Added
- **Named Color Palette** - User-friendly color configuration
  - 12 predefined colors: black, red, green, yellow, blue, magenta, cyan, white, bright_red, bright_green, bright_blue, bright_white
  - Color wizard now uses color names instead of ANSI escape codes
  - Backward compatibility with existing ANSI code configs
  - New `Colors._resolve_color()` method for flexible color resolution

- **Agent Tool Message Highlighting** - Better visibility for agent operations
  - Lines starting with `[` or `Tool #` now display in bright_green
  - Works in both streaming and non-streaming modes
  - Automatic detection and colorization of agent tool usage
  - New `Colors.format_agent_response()` method

- **Configuration Reset** - Easy restoration of default settings
  - New `--reset-config` flag to reset .chatrc to defaults
  - Interactive prompt with confirmation
  - Supports both global (~/.chatrc) and project (./.chatrc) configs
  - Comprehensive default values for all configuration sections

### Changed
- Config wizard now prompts for color names instead of raw ANSI codes
- Improved color configuration user experience
- Enhanced test coverage (276 tests passing, +8 new tests)

### Fixed
- Removed unused `scope` variable in reset_config_to_defaults
- Fixed line length violations in config_wizard.py and ui_components.py
- Type hints added to default_config dictionary

## [0.3.5] - 2025-10-16

### Added
- **Audio Notifications** - Play sound when agent completes a turn
  - New `audio.enabled` config option (default: true)
  - Custom WAV file support via `audio.notification_sound` config
  - Bundled notification.wav included in package
  - Cross-platform support (macOS: afplay, Linux: aplay/paplay, Windows: winsound)
  - Per-agent audio override support

- **Configuration Wizard** - Interactive setup for .chatrc files
  - New `--wizard` / `-w` flag to launch interactive configuration wizard
  - Walks through all available settings section by section
  - Loads and displays current values when editing existing configs
  - Supports both global (`~/.chatrc`) and project-level (`./.chatrc`) configs
  - Input validation for all setting types (bool, int, float, string)
  - Generates well-formatted YAML with helpful comments
  - Secure file permissions (0o600) on created configs

### Changed
- Code quality improvements with ruff formatting
- Enhanced type annotations for winsound and yaml imports

### Fixed
- Line length warnings in config wizard (addressed via formatting)
- Type checking issues with platform-specific imports

## [0.3.0] - 2025-10-15

### Added
- **Conversation Auto-Save** - Automatically save conversations on exit
  - New `--auto-save` / `-s` flag to enable automatic saving
  - Config option `features.auto_save` for persistent setting
  - Per-agent config override support
  - Conversations saved to `~/agent-conversations/` by default
  - Filenames include agent name, timestamp, and first query snippet
  - JSON format with metadata (agent, model, tokens, duration)
  - 181 tests passing (maintained from 0.2.1)

### Changed
- Minor version bump to reflect new auto-save feature

## [0.2.1] - 2025-10-13

### Fixed
- **Code Quality** - Cleanup for release standards
  - Fixed all line-length violations (E501) - 88 character limit
  - Fixed mypy type checking issues
  - Improved type hints throughout codebase
  - All 181 tests passing

## [0.2.0] - 2025-10-10

### Added
- **Automatic Dependency Installation** - New `--auto-setup` / `-a` flag to automatically install agent dependencies
  - Supports `requirements.txt`, `pyproject.toml`, and `setup.py`
  - Smart detection: Suggests using `--auto-setup` when dependency files are found
  - Helpful feedback with installation progress and errors
  - 20 new tests for dependency management (181 total tests)
- **Community Roadmap** - Created 37 feature request issues for community discussion
  - CLI enhancements (watch, budget, pipe, resume, inspect, validate, export, quiet, test-suite, benchmark, compare, context, preset, profile, dry-run, max-turns)
  - Documentation & learning (tutorial, example agents, videos)
  - Integrations (VS Code, Web UI, API server, Slack/Discord)
  - Quality of life (better errors, keyboard shortcuts, tab completion, conversation management)
  - Advanced features (multi-agent, RAG, persistent memory, marketplace)
  - Developer experience (debug mode, config wizard, scaffolding, hot reload)
  - Testing & quality (integration tests, fuzzing, performance benchmarks)
  - Community & sharing (plugin system, templates, import/export)
  - Security & safety (sandboxing, audit logging, secret detection)

### Changed
- Minor version bump to reflect new auto-setup feature

## [0.1.3] - 2025-10-09

### Fixed
- **Eliminated Import Error Messages During Startup**
  - Completely removed "No module named" errors when using fully qualified agent paths
  - Parent package `__init__.py` files are no longer executed during agent loading
  - Register parent packages as stub modules (sufficient for Python's import machinery)
  - Added sys.stderr suppression during agent module execution as defense-in-depth
  - Fixes issue with paths like `/agents/local/timmy/agent.py` where parent `agents/__init__.py` tries to import sibling modules

### Impact
- Clean startup experience with no confusing error messages
- Agent functionality unchanged (absolute imports still work)
- All 161 tests passing

## [0.1.2] - 2025-10-09

### Fixed
- **Configuration System Bugs** - Fixed three critical config bugs
  - Fixed config loading precedence (explicit path now has highest priority)
  - Fixed NoneType handling in config merge (skips None values from YAML)
  - Fixed default template to use `agents: {}` instead of `agents:`
  - Resolves "NoneType not iterable" errors
- **Enhanced Relative Import Support** - Improved multi-module imports
  - Added proper parent package registration in sys.modules
  - Agents can now import from multiple sibling modules
  - Fixed: `from .utils import X` followed by `from .helpers import Y`

### Testing
- All 161 tests passing (up from 160)
- Added test for multiple sibling imports
- All 24 config tests now pass (was 20/24)

## [0.1.1] - 2025-10-09

### Fixed
- **Relative Import Support** - Agents with relative imports (from .module or from ..module) now work correctly on all platforms
  - Added package root detection by walking up directory tree for __init__.py files
  - Set proper __package__ attribute for Python import system
  - Support for both same-level and parent-level relative imports
  - Added comprehensive tests for relative import scenarios

### Added
- Comprehensive documentation updates:
  - PyPI, tests, and coverage badges in README
  - Complete INSTALL.md rewrite with platform-specific instructions
  - New TROUBLESHOOTING.md with common issues and solutions
  - Auto-setup documentation for .chatrc and ~/.prompts/

### Testing
- Added 2 new tests for relative imports (156 total tests passing)
- Verified Windows installation and compatibility

## [0.1.0] - 2025-10-09

### Added
- **Agent Alias System** - Save agents as short names for quick access
- **Command History** - Navigate previous queries with ↑↓ arrows (persisted to `~/.chat_history`)
- **Multi-line Input** - Type `\\` to enter multi-line mode for code blocks
- **Token Tracking** - Track tokens and costs per query and session
- **Prompt Templates** - Reusable prompts from `~/.prompts/` with variable substitution
- **Configuration System** - YAML-based config with per-agent overrides
- **Status Bar** - Real-time metrics (queries, tokens, duration)
- **Session Summary** - Full statistics displayed on exit
- **Rich Formatting** - Enhanced markdown rendering with syntax highlighting
- **Error Recovery** - Automatic retry logic with exponential backoff
- **Agent Metadata Display** - Show model, tools, and capabilities
- **Async Streaming Support** - Real-time response display with streaming
- **Cross-Platform Installers** - Support for macOS, Linux, and Windows
- **Comprehensive Test Suite** - 158 tests with 61% code coverage
- **Type Hints** - Full type annotations throughout codebase

### Fixed
- Logging configuration no longer interferes with other libraries
- Cost display duplication removed (was showing same value twice)
- Error messages sanitized to prevent path information leakage
- Magic numbers extracted to named constants for maintainability
- All linting issues resolved (ruff, black, mypy)

### Changed
- Renamed from "AWS Strands Chat Loop" to "Basic Agent Chat Loop" (framework-agnostic)
- Made `anthropic-bedrock` an optional dependency (moved to `[bedrock]` extra)
- Added `python-dotenv` as core dependency
- Improved error handling with more informative messages

### Security
- Error messages now show only filenames, not full system paths
- Environment variable loading limited to 3 parent directories
- Log files created with secure behavior

### Documentation
- Complete README with installation and usage examples
- Configuration reference (CONFIG.md)
- Alias system guide (ALIASES.md)
- Installation instructions (INSTALL.md)
- Comprehensive QA report with all issues documented

### Testing
- 158 unit tests covering all components
- Test coverage: 61% overall
  - TokenTracker: 100%
  - UIComponents: 100%
  - DisplayManager: 98%
  - AgentLoader: 93%
  - ChatConfig: 91%
  - TemplateManager: 86%
  - AliasManager: 83%

### Infrastructure
- GitHub-ready project structure
- PyPI-ready package configuration
- Development tooling (pytest, ruff, black, mypy)
- Comprehensive .gitignore

## [Unreleased]

### Planned Features
- Integration tests with mock agents
- Platform-specific testing (Windows, Linux)
- CI/CD pipeline with GitHub Actions
- Additional agent framework support (LangChain, CrewAI)
- Plugin system for extensions
- Web interface option

---

## Release Notes

### v0.1.0 - Initial Release

This is the first public release of Basic Agent Chat Loop, a feature-rich interactive CLI for AI agents. The project provides a unified interface for any AI agent with token tracking, prompt templates, and extensive configuration options.

**Key Highlights:**
- 🏷️ Save agents as aliases for quick access
- 💰 Track token usage and costs
- 📝 Reusable prompt templates
- ⚙️ Flexible YAML configuration
- 🎨 Rich markdown rendering
- 🔄 Automatic error recovery
- 📊 Real-time status updates
- ✅ Comprehensive test coverage

**Installation:**
```bash
pip install basic-agent-chat-loop
```

**Quick Start:**
```bash
# Save an alias
chat_loop --save-alias myagent path/to/agent.py

# Run chat
chat_loop myagent
```

For detailed documentation, see [README.md](README.md) and [docs/](docs/).

---

[1.7.1-beta.2]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.7.1-beta.2
[1.7.1-beta.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.7.1-beta.1
[1.7.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.7.0
[1.6.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.6.1
[1.6.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.6.0
[1.6.0-beta.7]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.6.0-beta.7
[1.6.0-beta.6]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.6.0-beta.6
[1.5.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.5.1
[1.5.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.5.0
[1.4.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.4.1
[1.4.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.4.0
[1.3.9]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.9
[1.3.8]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.8
[1.3.7]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.7
[1.3.6]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.6
[1.3.5]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.5
[1.3.4]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.4
[1.3.3]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.3
[1.3.2]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.2
[1.3.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.1
[1.3.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.3.0
[0.3.7]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.7
[0.3.6]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.6
[0.3.5]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.5
[0.3.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.0
[0.2.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.2.1
[0.2.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.2.0
[0.1.3]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.3
[0.1.2]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.2
[0.1.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.1
[0.1.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.0
