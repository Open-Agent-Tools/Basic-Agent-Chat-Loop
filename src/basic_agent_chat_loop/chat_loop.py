#!/usr/bin/env python3
"""
Basic Agent Chat Loop - Interactive CLI for AI Agents

A feature-rich, unified chat interface for any AI agent with token tracking,
prompt templates, configuration management, and extensive UX enhancements.

Features:
- Async streaming support with real-time response display
- Command history with readline (↑↓ to navigate, saved to ~/.chat_history)
- Agent logs with rotation and secure permissions (0600) in ~/.chat_loop_logs/
- Multi-line input support (type \\\\ to enter multi-line mode)
  - Ctrl+D to cancel, ↑ arrow to edit previous line
  - Saves full block to history for later recall
- Token tracking per query and session
- Prompt templates from ~/.prompts/ with variable substitution
- Configuration file support (~/.chatrc or .chatrc in project root)
- Status bar with real-time metrics (queries, tokens, duration)
- Session summary on exit with full statistics
- Automatic error recovery with retry logic
- Rich markdown rendering with syntax highlighting
- Agent metadata display (model, tools, capabilities)

Privacy Note:
- Logs may contain user queries (truncated) and should be treated as sensitive
- See SECURITY.md for details on what gets logged and privacy considerations

Usage:
    chat_loop path/to/agent.py
    chat_loop my_agent_alias
    chat_loop <agent_path> --config ~/.chatrc-custom
"""

import argparse
import asyncio
import json
import logging
import logging.handlers
import os
import re
import stat
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pyperclip  # type: ignore[import-untyped]

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

# Platform-specific imports for ESC key detection
# Note: imports are done inside functions to avoid unused import warnings
try:
    if sys.platform != "win32":
        TERMIOS_AVAILABLE = True
    else:
        TERMIOS_AVAILABLE = False
    ESC_KEY_SUPPORT = True
except Exception:
    ESC_KEY_SUPPORT = False
    TERMIOS_AVAILABLE = False


# Components
# Configuration management
from .chat_config import ChatConfig, get_config
from .components import (
    AliasManager,
    AudioNotifier,
    Colors,
    ConfigWizard,
    DependencyManager,
    DisplayManager,
    ErrorMessages,
    HarmonyProcessor,
    SessionManager,
    StatusBar,
    TemplateManager,
    TokenTracker,
    extract_agent_metadata,
    load_agent_module,
)

# Rich library for better formatting
try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner

    RICH_AVAILABLE = True
    ConsoleType = Console
    MarkdownType = Markdown
except ImportError:
    RICH_AVAILABLE = False
    ConsoleType = None  # type: ignore
    MarkdownType = None  # type: ignore

# Setup logging directory in home directory for easy access
# Default: ~/.chat_loop_logs/
log_dir = Path.home() / ".chat_loop_logs"

# Command history configuration
READLINE_HISTORY_LENGTH = 1000

# Token estimation configuration
# Approximate token-to-word ratio for English text
# Based on empirical analysis of GPT tokenization (1 token ≈ 0.75 words)
TOKEN_TO_WORD_RATIO = 1.3

# Use a single consistent logger throughout the module
logger = logging.getLogger("basic_agent_chat_loop")


def _serialize_for_logging(obj: Any) -> str:
    """
    Serialize an object to JSON string for logging, with repr() fallback.

    Args:
        obj: The object to serialize

    Returns:
        JSON string if serializable, otherwise repr() string
    """
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        # Fallback to repr() for non-serializable objects
        return repr(obj)


def setup_logging(agent_name: str) -> bool:
    """
    Setup logging with agent-specific filename, rotation, and secure permissions.

    Log files are stored in ~/.chat_loop_logs/ with:
    - Rotating file handler (max 10MB per file, 5 backup files)
    - Restrictive permissions (0600 - owner read/write only)
    - UTF-8 encoding

    Args:
        agent_name: Name of the agent for the log file

    Returns:
        True if logging was successfully configured, False otherwise
    """
    try:
        # Ensure log directory exists with secure permissions
        log_dir.mkdir(exist_ok=True, mode=0o700)

        # Create log file path with sanitized agent name
        safe_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        log_file = log_dir / f"{safe_name}_chat.log"

        # Configure our logger
        logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        logger.handlers = []

        # Add rotating file handler with formatting
        # maxBytes=10MB, backupCount=5 keeps last ~50MB of logs
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

        # Set restrictive permissions on log file (owner read/write only)
        if log_file.exists():
            os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)  # 0600

        # Also add console handler for errors (stderr only)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)

        logger.info(f"Logging initialized for agent: {agent_name}")
        logger.info(f"Log file: {log_file}")
        return True

    except Exception as e:
        # Fallback: print to stderr if logging setup fails
        print(f"Warning: Could not setup logging: {e}", file=sys.stderr)
        # Set up minimal console-only logging as fallback
        logger.setLevel(logging.WARNING)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)
        return False


def set_terminal_title(title: str) -> None:
    """
    Set the terminal window/tab title.

    Uses ANSI escape sequences to update the terminal title.
    Works on macOS Terminal, iTerm2, Linux terminals, Windows Terminal, etc.

    Args:
        title: The title to set
    """
    try:
        # \033]0; sets both icon and window title
        # \033\\ is ST (String Terminator) - more compatible than BEL (\007)
        # ST works better with Mac Terminal and VSCode's integrated terminal
        print(f"\033]0;{title}\033\\", end="", flush=True)
    except Exception:
        # Silently fail if terminal doesn't support it
        pass


def setup_readline_history() -> Optional[Path]:
    """
    Setup readline command history with persistence.

    Returns:
        Path to history file if successful, None otherwise
    """
    if not READLINE_AVAILABLE:
        logger.debug("Readline not available, history will not be saved")
        # Show warning on Windows if readline is not available
        if sys.platform == "win32":
            print(
                Colors.system(
                    "⚠️  Command history not available. "
                    "This should not happen on Windows.\n"
                    "   Try reinstalling: "
                    "pip install --force-reinstall basic-agent-chat-loop"
                )
            )
        return None

    try:
        # History file in user's home directory
        history_file = Path.home() / ".chat_history"

        # Set history length
        readline.set_history_length(READLINE_HISTORY_LENGTH)

        # Enable tab completion and better editing
        try:
            # Suppress CPR warning by redirecting stderr temporarily
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

            try:
                # Parse readline init file if it exists
                readline.parse_and_bind("tab: complete")

                # Enable vi or emacs mode (emacs is default)
                readline.parse_and_bind("set editing-mode emacs")

                # Disable horizontal scroll to prevent CPR check
                readline.parse_and_bind("set horizontal-scroll-mode off")

                # Enable better line editing
                readline.parse_and_bind("set show-all-if-ambiguous on")
                readline.parse_and_bind("set completion-ignore-case on")
            finally:
                # Restore stderr
                sys.stderr.close()
                sys.stderr = old_stderr
        except Exception as e:
            logger.debug(f"Could not configure readline bindings: {e}")
            # Continue anyway, basic history will still work

        # Load existing history
        if history_file.exists():
            try:
                readline.read_history_file(str(history_file))
                count = readline.get_current_history_length()
                logger.debug(f"Loaded {count} history entries")
            except Exception as e:
                logger.warning(f"Could not load history from {history_file}: {e}")
                # Continue anyway, we'll create new history

        logger.debug(f"Command history will be saved to: {history_file}")
        return history_file

    except Exception as e:
        logger.warning(f"Could not setup command history: {e}")
        return None


def save_readline_history(history_file: Optional[Path]) -> bool:
    """
    Save readline command history.

    Args:
        history_file: Path to history file

    Returns:
        True if history was successfully saved, False otherwise
    """
    if not history_file:
        return False

    if not READLINE_AVAILABLE:
        return False

    try:
        # Ensure parent directory exists
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Save history
        readline.write_history_file(str(history_file))

        # Set secure permissions (readable/writable by owner only)
        history_file.chmod(0o600)

        count = readline.get_current_history_length()
        logger.debug(f"Saved {count} history entries to {history_file}")
        return True

    except Exception as e:
        logger.warning(f"Could not save command history to {history_file}: {e}")
        return False


def get_char_with_esc_detection() -> Optional[str]:
    """
    Get a single character from stdin with ESC and arrow key detection.

    Returns:
        The character typed, None if ESC was pressed,
        "UP_ARROW" if up arrow was pressed, or "" if detection failed
    """
    if not ESC_KEY_SUPPORT:
        return ""  # Fall back to regular input

    try:
        if sys.platform == "win32":
            # Windows implementation
            import msvcrt

            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\xe0":  # Extended key prefix on Windows
                    if msvcrt.kbhit():
                        extended = msvcrt.getch()
                        if extended == b"H":  # Up arrow
                            return "UP_ARROW"
                    return ""
                elif char == b"\x1b":  # ESC key
                    return None
                return char.decode("utf-8", errors="ignore")
            return ""
        else:
            # Unix/Linux/Mac implementation
            import select
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
                if char == "\x1b":  # ESC or arrow key sequence
                    # Check if more characters follow (within 100ms)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq = sys.stdin.read(2)
                        if seq == "[A":  # Up arrow
                            return "UP_ARROW"
                        # Other arrow keys would be [B, [C, [D
                    # Just ESC pressed
                    return None
                return char
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        logger.debug(f"Key detection failed: {e}")
        return ""  # Fall back to regular input


def input_with_esc(prompt: str) -> Optional[str]:
    """
    Enhanced input() that detects ESC and arrow key presses.

    Args:
        prompt: The prompt to display

    Returns:
        The user's input string, None if ESC was pressed,
        or "UP_ARROW" if up arrow was pressed
    """
    if not ESC_KEY_SUPPORT:
        # Fall back to regular input
        return input(prompt)

    # Print the prompt
    print(prompt, end="", flush=True)

    # Try to detect ESC/arrows on first character
    first_char = get_char_with_esc_detection()

    if first_char is None:
        # ESC was pressed
        print()  # New line after ESC
        return None
    elif first_char == "UP_ARROW":
        # Up arrow was pressed
        print()  # New line
        return "UP_ARROW"
    elif first_char == "":
        # Detection not available or failed, use regular input
        # But we already printed the prompt, so use empty prompt
        return input("")
    else:
        # Got a character, print it and continue with regular input
        print(first_char, end="", flush=True)
        rest_of_line = input("")
        return first_char + rest_of_line


class ChatLoop:
    """Generic chat loop for any AI agent with async streaming support."""

    def __init__(
        self,
        agent,
        agent_name: str,
        agent_description: str,
        agent_factory=None,
        agent_path: Optional[str] = None,
        config: Optional["ChatConfig"] = None,
    ):
        self.agent = agent
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_factory = agent_factory  # Function to create fresh agent instance
        self.agent_path = agent_path or "unknown"  # Store for session metadata
        self.history_file = None
        self.last_response = ""  # Track last response for copy command
        self.last_query = ""  # Track last user query for copy command

        # Conversation tracking - simple markdown buffer
        self.conversation_markdown: list[str] = []
        self.query_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Generate session ID for this chat session
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_agent_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        self.session_id = f"{safe_agent_name}_{timestamp}"

        # Load or use provided config
        self.config = config if config else get_config()

        # Apply configuration values (with agent-specific overrides)
        if self.config:
            self.max_retries = int(
                self.config.get("behavior.max_retries", 3, agent_name=agent_name)
            )
            self.retry_delay = float(
                self.config.get("behavior.retry_delay", 2.0, agent_name=agent_name)
            )
            self.timeout = float(
                self.config.get("behavior.timeout", 120.0, agent_name=agent_name)
            )
            self.spinner_style = self.config.get(
                "behavior.spinner_style", "dots", agent_name=agent_name
            )

            # Feature flags
            self.show_metadata = self.config.get(
                "features.show_metadata", True, agent_name=agent_name
            )
            self.show_thinking = self.config.get(
                "ui.show_thinking_indicator", True, agent_name=agent_name
            )
            self.show_duration = self.config.get(
                "ui.show_duration", True, agent_name=agent_name
            )
            self.show_banner = self.config.get(
                "ui.show_banner", True, agent_name=agent_name
            )
            self.update_terminal_title = self.config.get(
                "ui.update_terminal_title", True, agent_name=agent_name
            )

            # Rich override
            rich_enabled = self.config.get(
                "features.rich_enabled", True, agent_name=agent_name
            )
            self.use_rich = RICH_AVAILABLE and rich_enabled

            # Context warning thresholds
            self.context_warning_thresholds = self.config.get(
                "context.warning_thresholds", [80, 90, 95], agent_name=agent_name
            )
        else:
            # Defaults when no config
            self.max_retries = 3
            self.retry_delay = 2.0
            self.timeout = 120.0
            self.spinner_style = "dots"
            self.show_metadata = True
            self.show_thinking = True
            self.show_duration = True
            self.show_banner = True
            self.update_terminal_title = True
            self.use_rich = RICH_AVAILABLE
            self.context_warning_thresholds = [80, 90, 95]

        # Setup rich console if available and enabled
        self.console: Optional[Console] = Console() if self.use_rich else None

        # Extract agent metadata
        self.agent_metadata = extract_agent_metadata(self.agent)

        # Log model detection for debugging
        detected_model = self.agent_metadata.get("model_id", "Unknown")
        uses_harmony = self.agent_metadata.get("uses_harmony", False)
        logger.info(f"Model Detected: {detected_model}")
        logger.info(f"Harmony Detected: {uses_harmony}")

        # Setup prompt templates directory
        self.prompts_dir = Path.home() / ".prompts"

        # Create template manager
        self.template_manager = TemplateManager(self.prompts_dir)

        # Setup token tracking (always enabled for session summary)
        self.show_tokens = (
            self.config.get("features.show_tokens", False, agent_name=agent_name)
            if self.config
            else False
        )
        model_for_pricing = self.agent_metadata.get("model_id", "Unknown")

        # Check for config override
        if self.config:
            model_override = self.config.get(
                "agents." + agent_name + ".model_display_name", None
            )
            if model_override:
                model_for_pricing = model_override

        # Always create token tracker for session summary
        # (not just when show_tokens is true)
        self.token_tracker = TokenTracker(model_for_pricing)

        # Track previous accumulated usage for delta calculation
        # (AWS Strands agents report cumulative usage, we need the delta)
        self.last_accumulated_input = 0
        self.last_accumulated_output = 0

        # Track session start time for summary
        self.session_start_time = time.time()
        self.query_count = 0

        # Setup status bar if enabled
        self.show_status_bar_enabled = (
            self.config.get("ui.show_status_bar", False, agent_name=agent_name)
            if self.config
            else False
        )
        self.status_bar = None
        if self.show_status_bar_enabled:
            model_info = self.agent_metadata.get("model_id", "Unknown Model")

            # Check for config override
            if self.config:
                model_override = self.config.get(
                    "agents." + agent_name + ".model_display_name", None
                )
                if model_override:
                    model_info = model_override

            # Shorten long model IDs (ensure it's a string first)
            model_info = str(model_info) if model_info else "Unknown Model"
            if len(model_info) > 30:
                model_info = model_info[:27] + "..."

            # Get max_tokens for percentage display in status bar
            max_tokens_for_bar = self.agent_metadata.get("max_tokens", None)
            if max_tokens_for_bar == "Unknown":
                max_tokens_for_bar = None

            self.status_bar = StatusBar(
                agent_name,
                model_info,
                show_tokens=self.show_tokens,
                max_tokens=max_tokens_for_bar,
            )

            # Log for debugging
            logger.debug(
                f"Status bar initialized: agent={agent_name}, "
                f"model={model_info}, show_tokens={self.show_tokens}"
            )

        # Create display manager
        self.display_manager = DisplayManager(
            agent_name=self.agent_name,
            agent_description=self.agent_description,
            agent_metadata=self.agent_metadata,
            show_banner=self.show_banner,
            show_metadata=self.show_metadata,
            use_rich=self.use_rich,
            config=self.config,
            status_bar=self.status_bar,
        )

        # Setup audio notifications
        audio_enabled = (
            self.config.get("audio.enabled", True, agent_name=agent_name)
            if self.config
            else True
        )
        audio_sound_file = (
            self.config.get("audio.notification_sound", None, agent_name=agent_name)
            if self.config
            else None
        )
        self.audio_notifier = AudioNotifier(
            enabled=audio_enabled, sound_file=audio_sound_file
        )

        # Setup session manager for conversation persistence
        # Sessions are saved to ./.chat-sessions in current directory
        self.session_manager = SessionManager()

        # Setup Harmony processor if agent uses Harmony format
        self.harmony_processor = None

        # Check if harmony should be enabled
        # Priority: config override > auto-detection
        harmony_enabled_config_raw = (
            self.config.get("harmony.enabled", None) if self.config else None
        )

        # Auto-detect harmony support
        # Detection already performed by extract_agent_metadata()
        uses_harmony = self.agent_metadata.get("uses_harmony", False)

        # Normalize config value to handle string values from YAML
        # "auto"/None → None (auto-detect)
        # "yes"/"true"/"force"/True → True (force enable)
        # "no"/"false"/False → False (force disable)
        harmony_enabled_config = self._normalize_harmony_config(
            harmony_enabled_config_raw
        )

        logger.debug(f"Harmony config value (raw): {harmony_enabled_config_raw!r}")
        logger.debug(f"Harmony config value (normalized): {harmony_enabled_config!r}")
        logger.debug(f"Auto-detected harmony: {uses_harmony}")

        # Determine if harmony should be enabled
        # None = auto-detect, True = force enable, False = force disable
        should_enable_harmony = (
            harmony_enabled_config
            if harmony_enabled_config is not None
            else uses_harmony
        )

        logger.debug(f"Should enable harmony: {should_enable_harmony}")

        if should_enable_harmony:
            # Get detailed thinking config option
            show_detailed = (
                self.config.get("harmony.show_detailed_thinking", True)
                if self.config
                else True
            )
            self.harmony_processor = HarmonyProcessor(
                show_detailed_thinking=show_detailed
            )

            # Log how harmony was enabled
            if harmony_enabled_config is True:
                logger.info(
                    f"✓ Harmony ENABLED via config override "
                    f"(detailed_thinking={show_detailed})"
                )
            elif harmony_enabled_config is False:
                logger.info("✗ Harmony DISABLED via config override")
            else:
                logger.info(
                    f"✓ Harmony AUTO-DETECTED and enabled "
                    f"(detailed_thinking={show_detailed})"
                )
        else:
            logger.info(
                "✗ Harmony NOT enabled (agent not detected as harmony, config not set)"
            )

    def _normalize_harmony_config(self, value: Any) -> Optional[bool]:
        """
        Normalize harmony config value from YAML to proper type.

        Handles various string representations from YAML config files:
        - "auto", None, "" → None (auto-detect)
        - "yes", "true", "force", "on", True → True (force enable)
        - "no", "false", "off", False → False (force disable)

        Args:
            value: Raw config value from YAML

        Returns:
            None for auto-detect, True to force enable, False to force disable
        """
        if value is None or value == "":
            return None

        # Handle boolean values
        if isinstance(value, bool):
            return value

        # Handle string values (case-insensitive)
        if isinstance(value, str):
            value_lower = value.lower().strip()

            # Auto-detect
            if value_lower in ("auto", "detect"):
                return None

            # Force enable
            if value_lower in ("yes", "true", "force", "on", "enable", "enabled"):
                return True

            # Force disable
            if value_lower in ("no", "false", "off", "disable", "disabled"):
                return False

            # Unknown string - warn and default to auto-detect
            logger.warning(
                f"Unknown harmony.enabled value: {value!r} - "
                f"using auto-detect (valid: auto/yes/no)"
            )
            return None

        # Unknown type - warn and default to auto-detect
        logger.warning(
            f"Invalid harmony.enabled type: {type(value).__name__} - "
            f"using auto-detect (expected: bool or string)"
        )
        return None

    def _try_bedrock_token_extraction(
        self, response_obj: dict
    ) -> Optional[tuple[Any, bool]]:
        """
        Try to extract AWS Bedrock style accumulated usage.

        Args:
            response_obj: Response dict potentially containing Bedrock metrics

        Returns:
            Tuple of (usage_object, is_accumulated) or None if not found
        """
        if "result" in response_obj:
            result = response_obj["result"]
            if hasattr(result, "metrics") and hasattr(
                result.metrics, "accumulated_usage"
            ):
                return (result.metrics.accumulated_usage, True)
        return None

    def _try_standard_usage_extraction(self, response_obj) -> Optional[Any]:
        """
        Try to extract usage from common patterns.

        Args:
            response_obj: Response object to extract from

        Returns:
            Usage object or None if not found
        """
        # Pattern 1: response.usage (Anthropic/Claude style)
        if hasattr(response_obj, "usage"):
            return response_obj.usage

        # Pattern 2: response['usage'] (dict style)
        if isinstance(response_obj, dict) and "usage" in response_obj:
            return response_obj["usage"]

        # Pattern 3: response.metadata.usage
        if hasattr(response_obj, "metadata") and hasattr(
            response_obj.metadata, "usage"
        ):
            return response_obj.metadata.usage

        # Pattern 4: response.data.usage (streaming event)
        if hasattr(response_obj, "data") and hasattr(response_obj.data, "usage"):
            return response_obj.data.usage

        # Pattern 5: response.data['usage'] (streaming event dict)
        if (
            hasattr(response_obj, "data")
            and isinstance(response_obj.data, dict)
            and "usage" in response_obj.data
        ):
            return response_obj.data["usage"]

        return None

    def _extract_tokens_from_usage(self, usage) -> Optional[dict[str, int]]:
        """
        Extract input and output tokens from usage object.

        Args:
            usage: Usage object (dict or object with attributes)

        Returns:
            Dict with 'input_tokens' and 'output_tokens', or None if invalid
        """
        input_tokens: int = 0
        output_tokens: int = 0

        # Try different attribute names (check dict keys first, then attributes)
        if isinstance(usage, dict):
            # AWS Bedrock camelCase - explicit or chain with default
            input_tokens = (
                usage.get("inputTokens")
                or usage.get("input_tokens")
                or usage.get("prompt_tokens")
                or 0
            )
            output_tokens = (
                usage.get("outputTokens")
                or usage.get("output_tokens")
                or usage.get("completion_tokens")
                or 0
            )
        else:
            # Object attributes
            input_tokens = getattr(
                usage, "input_tokens", getattr(usage, "prompt_tokens", 0)
            )
            output_tokens = getattr(
                usage, "output_tokens", getattr(usage, "completion_tokens", 0)
            )

        # Ensure tokens are integers (handle mocks/test objects)
        try:
            input_tokens = int(input_tokens) if input_tokens is not None else 0
            output_tokens = int(output_tokens) if output_tokens is not None else 0
        except (TypeError, ValueError):
            return None

        if input_tokens > 0 or output_tokens > 0:
            return {"input_tokens": input_tokens, "output_tokens": output_tokens}

        return None

    def _extract_token_usage(
        self, response_obj
    ) -> Optional[tuple[dict[str, int], bool]]:
        """
        Extract token usage from response object.

        Args:
            response_obj: Response object from agent

        Returns:
            Tuple of (usage_dict, is_accumulated) where:
            - usage_dict: Dict with 'input_tokens' and 'output_tokens'
            - is_accumulated: True if usage is cumulative across session
            Returns None if no usage info available
        """
        if not response_obj:
            return None

        # Try AWS Bedrock accumulated usage first (cumulative)
        if isinstance(response_obj, dict):
            bedrock_result = self._try_bedrock_token_extraction(response_obj)
            if bedrock_result:
                usage, is_accumulated = bedrock_result
                tokens = self._extract_tokens_from_usage(usage)
                if tokens:
                    return (tokens, is_accumulated)

        # Try standard usage patterns (per-request)
        usage = self._try_standard_usage_extraction(response_obj)
        if usage:
            tokens = self._extract_tokens_from_usage(usage)
            if tokens:
                return (tokens, False)

        return None

    def _extract_code_blocks(self, text: str) -> list:
        """
        Extract code blocks from markdown text.

        Args:
            text: Markdown text containing code blocks

        Returns:
            List of code block contents (without fence markers)
        """
        # Match code blocks with triple backticks
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [match.strip() for match in matches]

    def _build_restoration_prompt(
        self,
        session_id: str,
        query_count: int,
        total_tokens: int,
        summary: str,
        session_file: Optional[Path] = None,
        resumed_from: Optional[str] = None,
    ) -> str:
        """
        Build restoration prompt for session resumption or compaction.

        Args:
            session_id: ID of the session being restored
            query_count: Number of queries in the session
            total_tokens: Total tokens used in the session
            summary: Summary text to include
            session_file: Optional path to the session file
            resumed_from: Optional ID of parent session (for resumed sessions)

        Returns:
            Formatted restoration prompt string
        """
        restoration_prompt_parts = [
            "CONTEXT RESTORATION: You are continuing a previous conversation "
            f"from {session_id}.\n\n",
            f"Previous session summary (Session ID: {session_id}, ",
            f"{query_count} queries, ",
            f"{self.token_tracker.format_tokens(total_tokens)}):\n\n",
        ]

        # Add resumed_from info if present
        if resumed_from:
            restoration_prompt_parts.append(
                f"This session was resumed from: {resumed_from}\n\n"
            )

        # Add session file path if provided
        if session_file:
            restoration_prompt_parts.append(
                f"Previous session file: {session_file}\n\n"
            )

        restoration_prompt_parts.append(summary)
        restoration_prompt_parts.append(
            "\n\nTask: Review the above and provide a brief acknowledgment "
            "(2-6 sentences or bullets) that includes:\n"
            "1. Main topics discussed\n"
            "2. Key decisions made\n"
            "3. Confirmation you're ready to continue\n\n"
            "Keep your response concise."
        )

        return "".join(restoration_prompt_parts)

    def _extract_text_from_event(self, event) -> str:
        """
        Extract text content from a streaming event.

        Handles various event formats from different agent implementations:
        - AWS Bedrock delta events: {"delta": {"text": "..."}}
        - Data attribute events: {"data": {"text": "..."}}
        - Simple text events: {"text": "..."}
        - String events: "..."

        Args:
            event: Streaming event from agent

        Returns:
            Extracted text string (empty if no text found)
        """
        if isinstance(event, str):
            return event
        if isinstance(event, dict):
            if "delta" in event and "text" in event["delta"]:
                return event["delta"]["text"]
            elif "data" in event and "text" in event["data"]:
                return event["data"]["text"]
            elif "text" in event:
                return event["text"]
        return ""

    async def _stream_response(self, prompt: str) -> str:
        """
        Stream response from agent and accumulate text.

        Args:
            prompt: Prompt to send to agent

        Returns:
            Complete accumulated response text
        """
        response = ""
        async for event in self.agent.stream_async(prompt):
            response += self._extract_text_from_event(event)
        return response

    def _resolve_session_id(self, session_id: str) -> Optional[str]:
        """
        Resolve session ID from numeric index or direct ID.

        Args:
            session_id: Session ID or numeric index (1-based)

        Returns:
            Actual session ID string, or None if invalid
        """
        # If session_id is a number, resolve it from the list
        if session_id.isdigit():
            session_num = int(session_id)
            sessions = self.session_manager.list_sessions(
                agent_name=self.agent_name, limit=20
            )

            if session_num < 1 or session_num > len(sessions):
                print(Colors.error(f"Invalid session number: {session_num}"))
                print(f"Valid range: 1-{len(sessions)}")
                return None

            # Get actual session_id from the list (1-indexed)
            session_info = sessions[session_num - 1]
            return session_info.session_id

        return session_id

    def _load_and_validate_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Load session data and validate it's restorable.

        Args:
            session_id: Session ID to load

        Returns:
            Dict with session data (metadata, summary, query_count, total_tokens,
            session_file), or None if validation fails
        """
        # Load markdown file
        sessions_dir = self.session_manager.sessions_dir
        session_file = sessions_dir / f"{session_id}.md"

        if not session_file.exists():
            print(Colors.error(f"⚠️  Session file not found: {session_id}"))
            return None

        # Extract metadata from markdown
        metadata = self._extract_metadata_from_markdown(session_file)
        if not metadata:
            print(Colors.error("Failed to parse session metadata"))
            return None

        # Extract summary
        summary = self._extract_summary_from_markdown(session_file)
        if not summary:
            print(
                Colors.error(
                    "⚠️  Session can't be resumed (no summary). "
                    "Starting fresh session..."
                )
            )
            return None

        # Get query count and tokens from metadata or session index
        query_count = metadata.get("query_count", 0)
        session_info_data = self.session_manager.get_session_metadata(session_id)
        total_tokens = session_info_data.total_tokens if session_info_data else 0

        # Display session info
        print(
            Colors.success(
                f"✓ Found: {metadata.get('agent_name', 'Unknown')} - {session_id}"
            )
        )
        print(
            Colors.system(
                f"  ({query_count} queries, "
                f"{self.token_tracker.format_tokens(total_tokens)})"
            )
        )

        return {
            "metadata": metadata,
            "summary": summary,
            "query_count": query_count,
            "total_tokens": total_tokens,
            "session_file": session_file,
        }

    def _validate_agent_compatibility(self, metadata: dict) -> bool:
        """
        Check if session agent matches current agent, prompt user if different.

        Args:
            metadata: Session metadata dict

        Returns:
            True if user confirms continuation, False otherwise
        """
        # Check if agent path matches (graceful warning)
        if "agent_path" in metadata and metadata["agent_path"] != self.agent_path:
            print(
                Colors.system(
                    f"\n⚠️  Different agent detected:\n"
                    f"  Session created with: {metadata['agent_path']}\n"
                    f"  Current agent:        {self.agent_path}"
                )
            )
            confirm = input(Colors.system("Continue? (y/n): "))
            if confirm.lower() != "y":
                print(Colors.system("Resume cancelled"))
                return False

        return True

    async def _send_restoration_prompt(
        self, restoration_prompt: str
    ) -> tuple[str, float]:
        """
        Send restoration prompt to agent and get response.

        Args:
            restoration_prompt: Prompt to send

        Returns:
            Tuple of (response_text, duration_seconds)
        """
        restoration_start = time.time()
        restoration_response = ""

        # Check if agent supports streaming
        if hasattr(self.agent, "stream_async"):
            # Display with spinner while streaming
            if self.use_rich and self.console:
                spinner = Spinner("dots", text="Restoring context...")
                with Live(spinner, console=self.console, refresh_per_second=10):
                    restoration_response = await self._stream_response(
                        restoration_prompt
                    )
            else:
                restoration_response = await self._stream_response(restoration_prompt)
        else:
            # Non-streaming agent
            restoration_response = await asyncio.get_event_loop().run_in_executor(
                None, self.agent, restoration_prompt
            )

        restoration_duration = time.time() - restoration_start
        return restoration_response, restoration_duration

    def _display_restoration_response(self, restoration_response: str) -> None:
        """
        Display agent's restoration acknowledgment.

        Args:
            restoration_response: Agent's response to display
        """
        print(Colors.agent(f"{self.agent_name}:"), end=" ")
        if self.use_rich and self.console:
            md = Markdown(restoration_response.strip())
            self.console.print(md)
        else:
            print(restoration_response.strip())
        print()

    def _initialize_restored_session(
        self,
        old_session_id: str,
        new_session_id: str,
        restoration_response: str,
        restoration_duration: float,
        restoration_input_tokens: float,
        restoration_output_tokens: float,
        session_data: dict,
    ) -> None:
        """
        Initialize new session with restored context.

        Args:
            old_session_id: Previous session ID
            new_session_id: New session ID for resumed session
            restoration_response: Agent's restoration response
            restoration_duration: Time taken for restoration
            restoration_input_tokens: Approximate input tokens
            restoration_output_tokens: Approximate output tokens
            session_data: Dict with query_count, total_tokens, summary, session_file
        """
        # Initialize new session
        self.session_id = new_session_id
        self._resumed_from = old_session_id  # Track parent session
        self._previous_summary = session_data["summary"]  # Store for next compaction

        # Reset conversation but add restoration exchange
        self.conversation_markdown = [
            f"\n## Session Restored ({datetime.now().strftime('%H:%M:%S')})\n",
            f"**Context:** Resumed from {old_session_id} "
            f"({session_data['query_count']} queries, "
            f"{self.token_tracker.format_tokens(session_data['total_tokens'])})\n",
            f"**Previous Session:** {session_data['session_file']}\n\n",
            f"**{self.agent_name}:** {restoration_response.strip()}\n\n",
            f"*Time: {restoration_duration:.1f}s | ",
            f"Tokens: {int(restoration_input_tokens + restoration_output_tokens)} ",
            f"(in: {int(restoration_input_tokens)}, "
            f"out: {int(restoration_output_tokens)})*\n\n",
            "---\n",
        ]

        # Reset counters (restoration tokens tracked separately)
        self.query_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_start_time = time.time()

        # Update status bar if enabled
        if self.status_bar:
            self.status_bar.query_count = 0
            self.status_bar.start_time = self.session_start_time

        print(Colors.success("✓ Session restored! Ready to continue."))
        print()

        logger.info(f"Successfully restored session: {old_session_id}")

    def _format_conversation_as_markdown(self) -> str:
        """
        Format entire conversation history as markdown.

        Returns:
            Markdown-formatted conversation
        """
        header = [
            f"# {self.agent_name} - Conversation\n\n",
            f"Session ID: {self.session_id}\n",
            f"Agent: {self.agent_name}\n",
            f"Queries: {self.query_count}\n\n",
            "---\n",
        ]
        return "".join(header + self.conversation_markdown)

    async def restore_session(self, session_id: str) -> bool:
        """
        Restore a previous session by loading its summary and creating a new session.

        Args:
            session_id: Session ID or number from sessions list

        Returns:
            True if successful, False otherwise
        """
        try:
            print(Colors.system("\n📋 Loading session..."))

            # Resolve numeric session IDs to actual IDs
            resolved_id = self._resolve_session_id(session_id)
            if not resolved_id:
                return False
            session_id = resolved_id

            # Load and validate session data
            session_data = self._load_and_validate_session(session_id)
            if not session_data:
                return False

            # Validate agent compatibility
            if not self._validate_agent_compatibility(session_data["metadata"]):
                return False

            # Build and send restoration prompt
            print(Colors.system("🔄 Restoring context..."))
            print()

            restoration_prompt = self._build_restoration_prompt(
                session_id=session_id,
                query_count=session_data["query_count"],
                total_tokens=session_data["total_tokens"],
                summary=session_data["summary"],
                session_file=session_data["session_file"],
                resumed_from=session_data["metadata"].get("resumed_from"),
            )

            (
                restoration_response,
                restoration_duration,
            ) = await self._send_restoration_prompt(restoration_prompt)

            # Display agent acknowledgment
            self._display_restoration_response(restoration_response)

            # Track restoration tokens (approximate - word count * ratio)
            restoration_input_tokens = (
                len(restoration_prompt.split()) * TOKEN_TO_WORD_RATIO
            )
            restoration_output_tokens = (
                len(restoration_response.split()) * TOKEN_TO_WORD_RATIO
            )

            # Create new session ID for resumed session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_agent_name = (
                self.agent_name.lower().replace(" ", "_").replace("/", "_")
            )
            new_session_id = f"{safe_agent_name}_{timestamp}"

            # Initialize new session with restored context
            self._initialize_restored_session(
                old_session_id=session_id,
                new_session_id=new_session_id,
                restoration_response=restoration_response,
                restoration_duration=restoration_duration,
                restoration_input_tokens=restoration_input_tokens,
                restoration_output_tokens=restoration_output_tokens,
                session_data=session_data,
            )

            return True

        except Exception as e:
            logger.error(f"Failed to restore session: {e}", exc_info=True)
            print(Colors.error(f"\n⚠️  Failed to restore session: {e}"))
            return False

    def _extract_summary_from_markdown(self, file_path: Path) -> Optional[str]:
        """
        Extract summary block from a markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            Summary text, or None if not found
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            start_marker = "<!-- SESSION_SUMMARY_START -->"
            end_marker = "<!-- SESSION_SUMMARY_END -->"

            if start_marker not in content or end_marker not in content:
                return None

            start_idx = content.index(start_marker) + len(start_marker)
            end_idx = content.index(end_marker)
            return content[start_idx:end_idx].strip()

        except Exception as e:
            logger.warning(f"Failed to extract summary: {e}")
            return None

    def _extract_metadata_from_markdown(self, file_path: Path) -> Optional[dict]:
        """
        Extract session metadata from markdown file headers.

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary with metadata, or None if parsing failed
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            metadata = {}

            # Extract session ID
            if match := re.search(r"\*\*Session ID:\*\* (.+)", content):
                metadata["session_id"] = match.group(1).strip()

            # Extract agent name
            if match := re.search(r"\*\*Agent:\*\* (.+)", content):
                metadata["agent_name"] = match.group(1).strip()

            # Extract agent path
            if match := re.search(r"\*\*Agent Path:\*\* (.+)", content):
                metadata["agent_path"] = match.group(1).strip()

            # Extract total queries
            if match := re.search(r"\*\*Total Queries:\*\* (\d+)", content):
                metadata["query_count"] = int(match.group(1))

            # Extract resumed from (if present)
            if match := re.search(r"\*\*Resumed From:\*\* (.+)", content):
                metadata["resumed_from"] = match.group(1).strip()

            return metadata if metadata else None

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return None

    async def _generate_session_summary(
        self, previous_summary: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a structured summary of the current session.

        Args:
            previous_summary: Optional summary from parent session for
                progressive summarization

        Returns:
            Summary text with HTML markers, or None if generation failed
        """
        try:
            # Build the summarization prompt
            prompt_parts = ["Generate a progressive session summary:\n\n"]

            # Add background context if there's a previous summary
            if previous_summary:
                prompt_parts.append(
                    "**Background Context:** Condense this previous summary to 1-2 "
                    "sentences:\n"
                )
                prompt_parts.append(previous_summary)
                prompt_parts.append("\n\n")

            # Add current session conversation
            prompt_parts.append("**Current Session:**\n")
            prompt_parts.extend(self.conversation_markdown)
            prompt_parts.append("\n\n")

            # Add instructions
            prompt_parts.append(
                "Create a structured summary:\n\n**Background Context:** "
            )
            if previous_summary:
                prompt_parts.append(
                    "[Condense the previous summary to 1-2 sentences]\n\n"
                )
            else:
                prompt_parts.append("Initial session.\n\n")

            prompt_parts.append(
                "**Current Session Summary:**\n"
                "**Topics Discussed:**\n"
                "- [bullet points about THIS session]\n\n"
                "**Decisions Made:**\n"
                "- [bullet points about THIS session]\n\n"
                "**Pending:**\n"
                "- [what's still open]\n\n"
                "Aim for less than 500 words, be complete but terse, no fluff.\n"
                "Use the exact format with HTML comment markers:\n\n"
                "<!-- SESSION_SUMMARY_START -->\n"
                "[your summary here]\n"
                "<!-- SESSION_SUMMARY_END -->"
            )

            summary_prompt = "".join(prompt_parts)

            # Call agent to generate summary
            print(
                Colors.system("📝 Generating session summary... "), end="", flush=True
            )

            summary_response = ""

            # Check if agent supports streaming
            if hasattr(self.agent, "stream_async"):
                # Use streaming
                summary_response = await self._stream_response(summary_prompt)
            else:
                # Non-streaming agent
                summary_response = await asyncio.get_event_loop().run_in_executor(
                    None, self.agent, summary_prompt
                )

            print("✓")

            # Validate that summary has the required markers
            if (
                "<!-- SESSION_SUMMARY_START -->" not in summary_response
                or "<!-- SESSION_SUMMARY_END -->" not in summary_response
            ):
                logger.warning("Summary missing required HTML markers")
                return None

            return summary_response.strip()

        except asyncio.TimeoutError:
            logger.warning("Summary generation timed out")
            print("⏱️ timeout")
            return None
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}", exc_info=True)
            print(f"⚠️ failed ({e})")
            return None

    async def save_conversation(
        self, session_id: Optional[str] = None, generate_summary: bool = False
    ) -> bool:
        """
        Save conversation as markdown file with optional auto-generated summary.

        Args:
            session_id: Optional custom session ID.
                Uses self.session_id if not provided.
            generate_summary: Whether to generate an AI summary of the session.
                Defaults to False to avoid generating summaries after every turn.
                Should be True when explicitly compacting or ending a session.

        Returns:
            True if save was successful, False otherwise
        """
        # Only save if there's conversation content
        if not self.conversation_markdown:
            logger.debug("No conversation to save")
            return False

        # Use provided session_id or fall back to self.session_id
        save_session_id = session_id or self.session_id

        try:
            # Generate summary for the session (only if requested)
            summary = None
            if generate_summary:
                summary = await self._generate_session_summary(
                    previous_summary=getattr(self, "_previous_summary", None)
                )

            # Ensure sessions directory exists
            sessions_dir = self.session_manager.sessions_dir
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Build full markdown with header
            md_path = sessions_dir / f"{save_session_id}.md"
            total_tokens = self.total_input_tokens + self.total_output_tokens

            markdown_content = [
                f"# {self.agent_name} Conversation\n\n",
                f"**Session ID:** {save_session_id}\n\n",
                f"**Date:** {datetime.now().isoformat()}\n\n",
                f"**Agent:** {self.agent_name}\n\n",
                f"**Agent Path:** {self.agent_path}\n\n",
                f"**Total Queries:** {self.query_count}\n\n",
            ]

            # Add "Resumed from" info if this session was resumed
            if hasattr(self, "_resumed_from") and self._resumed_from:
                markdown_content.append(f"**Resumed From:** {self._resumed_from}\n\n")

            markdown_content.append("---\n")

            # Add conversation content
            markdown_content.extend(self.conversation_markdown)

            # Add summary if generated successfully
            if summary:
                markdown_content.append("\n")
                markdown_content.append(summary)
                markdown_content.append("\n")
            elif generate_summary:
                # Only warn if we tried to generate a summary but it failed
                logger.warning("Session saved without summary - resume will not work")
                print(
                    Colors.system(
                        "  ⚠️  Summary generation failed - session cannot be resumed"
                    )
                )

            # Write markdown file
            with open(md_path, "w", encoding="utf-8") as f:
                f.writelines(markdown_content)

            # Set secure permissions (owner read/write only)
            md_path.chmod(0o600)

            # Update session index
            first_query = (
                self.conversation_markdown[1].replace("**You:** ", "").strip()
                if len(self.conversation_markdown) > 1
                else ""
            )
            preview = first_query[:100]
            if len(first_query) > 100:
                preview += "..."

            self.session_manager._update_index_simple(
                session_id=save_session_id,
                agent_name=self.agent_name,
                agent_path=self.agent_path,
                query_count=self.query_count,
                total_tokens=total_tokens,
                preview=preview,
            )

            logger.info(f"Conversation saved: {save_session_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save conversation: {e}", exc_info=True)
            print(Colors.error(f"\n⚠️  Could not save conversation: {e}"))
            return False

    def _show_save_confirmation(self, session_id: str):
        """Show user-friendly save confirmation with file paths."""
        save_dir = self.session_manager.sessions_dir
        md_path = save_dir / f"{session_id}.md"

        print()
        print(Colors.success("✓ Conversation saved successfully!"))
        print()
        print(Colors.system(f"  Session ID: {session_id}"))
        print(Colors.system(f"  File:       {md_path}"))
        print(Colors.system(f"  Queries:    {self.query_count}"))

        # Show token count if available
        total_tokens = self.total_input_tokens + self.total_output_tokens
        if total_tokens > 0:
            print(
                Colors.system(
                    f"  Tokens:     {self.token_tracker.format_tokens(total_tokens)}"
                )
            )
        print()

    async def _handle_compact_command(self):
        """
        Compact current session and continue in new session.

        This command:
        1. Saves current session with summary
        2. Extracts the summary
        3. Starts a new session with the summary as context
        4. Agent acknowledges the restored context
        """
        # Check if there's anything to compact
        if not self.conversation_markdown:
            print(
                Colors.system("No conversation to compact yet. Start chatting first!")
            )
            return

        try:
            # Save current session with summary
            print(Colors.system("\n📋 Compacting current session..."))
            old_session_id = self.session_id
            old_query_count = self.query_count
            old_total_tokens = self.total_input_tokens + self.total_output_tokens

            # Generate summary for compaction
            success = await self.save_conversation(generate_summary=True)
            if not success:
                print(Colors.error("Failed to save session for compaction"))
                return

            # Extract summary from saved file
            sessions_dir = self.session_manager.sessions_dir
            saved_file = sessions_dir / f"{old_session_id}.md"
            summary = self._extract_summary_from_markdown(saved_file)

            if not summary:
                print(
                    Colors.error(
                        "Failed to extract summary - session saved but cannot compact"
                    )
                )
                return

            # Show save confirmation
            print(Colors.success(f"✓ Saved session: {old_session_id}"))
            print(
                Colors.system(
                    f"  ({old_query_count} queries, "
                    f"{self.token_tracker.format_tokens(old_total_tokens)})"
                )
            )

            # Build and send restoration prompt
            print(Colors.system("🔄 Starting new session with summary..."))
            print()

            restoration_prompt = self._build_restoration_prompt(
                session_id=old_session_id,
                query_count=old_query_count,
                total_tokens=old_total_tokens,
                summary=summary,
                session_file=saved_file,
            )

            (
                restoration_response,
                restoration_duration,
            ) = await self._send_restoration_prompt(restoration_prompt)

            # Display agent acknowledgment
            self._display_restoration_response(restoration_response)

            # Track restoration tokens (approximate - word count * ratio)
            restoration_input_tokens = (
                len(restoration_prompt.split()) * TOKEN_TO_WORD_RATIO
            )
            restoration_output_tokens = (
                len(restoration_response.split()) * TOKEN_TO_WORD_RATIO
            )

            # Create new session ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_agent_name = (
                self.agent_name.lower().replace(" ", "_").replace("/", "_")
            )
            new_session_id = f"{safe_agent_name}_{timestamp}"

            # Initialize new session with compacted context
            session_data = {
                "query_count": old_query_count,
                "total_tokens": old_total_tokens,
                "summary": summary,
                "session_file": saved_file,
            }

            self._initialize_restored_session(
                old_session_id=old_session_id,
                new_session_id=new_session_id,
                restoration_response=restoration_response,
                restoration_duration=restoration_duration,
                restoration_input_tokens=restoration_input_tokens,
                restoration_output_tokens=restoration_output_tokens,
                session_data=session_data,
            )

            print(Colors.success("✓ Session compacted and ready to continue!"))
            print()

        except Exception as e:
            logger.error(f"Failed to compact session: {e}", exc_info=True)
            print(Colors.error(f"\n⚠️  Compaction failed: {e}"))
            print(Colors.system("Your previous session was saved successfully."))
            print(Colors.system("Continuing in current session..."))

    async def get_multiline_input(self) -> str:
        """
        Get multi-line input from user.

        Features:
        - Empty line submits
        - Ctrl+D or .cancel to cancel input
        - Up arrow or .back to edit previous line
        - Saves to history as single entry
        """
        lines: list[str] = []
        print(Colors.system("Multi-line mode:"))
        print(Colors.system("  • Empty line to submit"))
        print(Colors.system("  • Ctrl+D or .cancel to cancel"))
        if ESC_KEY_SUPPORT:
            print(Colors.system("  • ↑ or .back to edit previous line"))
        else:
            print(Colors.system("  • .back to edit previous line"))

        # Variable to hold text for pre-input hook
        prefill_text = None

        def startup_hook():
            """Readline startup hook to pre-fill input buffer."""
            nonlocal prefill_text
            if prefill_text is not None:
                readline.insert_text(prefill_text)
                readline.redisplay()

        # Set the startup hook if readline is available
        if READLINE_AVAILABLE:
            readline.set_startup_hook(startup_hook)

        try:
            while True:
                try:
                    # Show line number for context
                    line_num = len(lines) + 1
                    prompt = Colors.user(f"{line_num:2d}│ ")

                    # Use input_with_esc for ESC/arrow key detection
                    line = input_with_esc(prompt)

                    # Check if ESC was pressed (returns None)
                    if line is None:
                        print(Colors.system("✗ Multi-line input cancelled (ESC)"))
                        return ""

                    # Check if up arrow was pressed - edit previous line
                    if line == "UP_ARROW":
                        if lines:
                            # Pop the last line and let user edit it
                            prev_line = lines.pop()
                            print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                            # Set prefill text for next input
                            prefill_text = prev_line
                        else:
                            print(Colors.system("⚠ No previous line to edit"))
                        continue

                    # Clear prefill text after each input
                    prefill_text = None

                    # Check for cancel command
                    if line.strip() == ".cancel":
                        print(Colors.system("✗ Multi-line input cancelled"))
                        return ""

                    # Check for back command - edit previous line
                    if line.strip() == ".back":
                        if lines:
                            # Pop the last line and let user edit it
                            prev_line = lines.pop()
                            print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                            # Set prefill text for next input
                            prefill_text = prev_line
                        else:
                            print(Colors.system("⚠ No previous line to edit"))
                        continue

                    # Empty line submits (only if we have content)
                    if not line.strip():
                        if lines:
                            break
                        else:
                            # First line can't be empty
                            print(Colors.system("⚠ Enter some text or use .cancel"))
                            continue

                    # Add the line
                    lines.append(line)

                except EOFError:
                    # Ctrl+D cancels
                    print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+D)"))
                    return ""
                except KeyboardInterrupt:
                    # Ctrl+C cancels
                    print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+C)"))
                    return ""

            result = "\n".join(lines)

            # Save to readline history as single entry for later recall
            if result and READLINE_AVAILABLE:
                readline.add_history(result)

            print(Colors.success(f"✓ {len(lines)} lines captured"))
            return result

        finally:
            # Clean up the startup hook
            if READLINE_AVAILABLE:
                readline.set_startup_hook(None)

    async def _show_thinking_indicator(self, stop_event: asyncio.Event):
        """Show thinking indicator while waiting for response."""
        if not self.show_thinking:
            # Just wait silently
            while not stop_event.is_set():
                await asyncio.sleep(0.1)
            return

        if not self.use_rich:
            # Fallback to simple dots animation
            print(Colors.system("Thinking"), end="", flush=True)
            dot_count = 0
            while not stop_event.is_set():
                print(".", end="", flush=True)
                dot_count += 1
                if dot_count >= 3:
                    print("\b\b\b   \b\b\b", end="", flush=True)  # Clear dots
                    dot_count = 0
                await asyncio.sleep(0.5)
            print("\r" + " " * 15 + "\r", end="", flush=True)  # Clear line
        else:
            # Use rich spinner with configured style
            spinner_style = (
                self.spinner_style if hasattr(self, "spinner_style") else "dots"
            )
            with Live(
                Spinner(spinner_style, text=Colors.system("Thinking...")),
                console=self.console,
                refresh_per_second=10,
            ):
                while not stop_event.is_set():
                    await asyncio.sleep(0.1)

    async def _stream_agent_response(self, query: str) -> dict[str, Any]:
        """
        Stream agent response asynchronously.

        Returns:
            Dict with 'duration' and optional 'usage' (input_tokens, output_tokens)
        """
        start_time = time.time()
        response_text = []  # Collect response for rich rendering
        response_obj = None  # Store the response object for token extraction

        # Agent name in blue
        print(f"\n{Colors.agent(self.agent_name)}: ", end="", flush=True)

        # Setup thinking indicator
        stop_thinking = asyncio.Event()
        thinking_task = None

        try:
            # Start thinking indicator if enabled
            if self.show_thinking:
                thinking_task = asyncio.create_task(
                    self._show_thinking_indicator(stop_thinking)
                )

            first_token_received = False

            # Log request payload sent to agent
            logger.debug("=" * 60)
            logger.debug("REQUEST TO AGENT:")
            logger.debug(f"Query: {_serialize_for_logging(query)}")
            logger.debug("=" * 60)

            # Check if agent supports streaming
            if hasattr(self.agent, "stream_async"):
                async for event in self.agent.stream_async(query):
                    # Store last event for token extraction
                    response_obj = event

                    # Log streaming event received from agent
                    logger.debug("STREAMING EVENT FROM AGENT:")
                    logger.debug(_serialize_for_logging(event))

                    # Stop thinking indicator on first token
                    if not first_token_received:
                        stop_thinking.set()
                        if thinking_task:
                            await thinking_task
                        first_token_received = True

                    # Handle different event types
                    text_to_add = None  # Track text to add to response

                    # First check if event is a dict (AWS Strands format)
                    if isinstance(event, dict):
                        # AWS Strands dict format:
                        # {'event': {'contentBlockDelta': {'delta': {'text': '...'}}}}
                        if "event" in event and isinstance(event["event"], dict):
                            nested_event = event["event"]
                            if "contentBlockDelta" in nested_event:
                                delta_block = nested_event["contentBlockDelta"]
                                if (
                                    isinstance(delta_block, dict)
                                    and "delta" in delta_block
                                ):
                                    delta = delta_block["delta"]
                                    if isinstance(delta, dict) and "text" in delta:
                                        text_to_add = delta["text"]
                        # Fallback: check for direct text field
                        elif "text" in event:
                            text_to_add = event["text"]

                    elif hasattr(event, "data"):
                        data = event.data
                        if isinstance(data, str):
                            text_to_add = data
                        elif isinstance(data, dict):
                            # Handle structured data
                            if "text" in data:
                                text_to_add = data["text"]
                            elif "content" in data:
                                content = data["content"]
                                if isinstance(content, list):
                                    for block in content:
                                        if isinstance(block, dict) and "text" in block:
                                            text_to_add = block["text"]
                                            break
                                else:
                                    text_to_add = str(content)

                    # Fallback: Check for common streaming event patterns
                    # (AWS Strands object events, etc.)
                    elif hasattr(event, "delta"):
                        # AWS Strands/Anthropic delta events (object format)
                        delta = event.delta
                        if isinstance(delta, str):
                            text_to_add = delta
                        elif hasattr(delta, "text"):
                            text_to_add = delta.text
                        elif isinstance(delta, dict) and "text" in delta:
                            text_to_add = delta["text"]

                    elif hasattr(event, "text"):
                        # Direct text attribute
                        text_to_add = event.text

                    elif isinstance(event, str):
                        # Event is the text itself
                        text_to_add = event

                    # Append text if found and display it
                    if text_to_add:
                        response_text.append(text_to_add)
                        if not self.use_rich:
                            # Apply colorization for tool messages during streaming
                            formatted_text = Colors.format_agent_response(text_to_add)
                            print(formatted_text, end="", flush=True)
            else:
                # Fallback to non-streaming call if streaming not supported
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.agent, query
                )
                response_obj = response  # Store for token extraction

                # Log response received from agent
                logger.debug("RESPONSE FROM AGENT:")
                logger.debug(_serialize_for_logging(response))
                logger.debug("=" * 60)

                # Stop thinking indicator
                stop_thinking.set()
                if thinking_task:
                    await thinking_task

                # Format and display response
                if hasattr(response, "message"):
                    message = response.message
                    if isinstance(message, dict) and "content" in message:
                        content = message["content"]
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    response_text.append(block["text"])
                        else:
                            response_text.append(str(content))
                    else:
                        response_text.append(str(message))
                elif isinstance(response, str):
                    response_text.append(response)
                else:
                    response_text.append(str(response))

            # Log final response object (for streaming, this is the last event)
            if hasattr(self.agent, "stream_async"):
                logger.debug("FINAL RESPONSE OBJECT (last streaming event):")
                logger.debug(_serialize_for_logging(response_obj))
                logger.debug("=" * 60)

            # Render collected response
            # Concatenate streaming chunks directly (they may break mid-word)
            full_response = "".join(response_text)

            # Track if we already printed during streaming (to prevent duplicates)
            already_printed_streaming = first_token_received and not self.use_rich

            # Process through Harmony if available
            display_text = full_response
            if self.harmony_processor:
                # Debug: Log response object structure
                # (safely handle mocks/test objects)
                try:
                    logger.debug(f"Response object type: {type(response_obj)}")
                    logger.debug(f"Response object attrs: {dir(response_obj)[:20]}")
                    if response_obj and hasattr(response_obj, "choices"):
                        try:
                            logger.debug(
                                f"Response has choices: {len(response_obj.choices)}"
                            )
                        except TypeError:
                            logger.debug(
                                "Response has choices attribute (non-sequence)"
                            )

                        if response_obj.choices:
                            choice = response_obj.choices[0]
                            logger.debug(f"Choice type: {type(choice)}")
                            logger.debug(f"Choice attrs: {dir(choice)[:20]}")
                            if hasattr(choice, "logprobs"):
                                logger.debug(
                                    f"Has logprobs: {choice.logprobs is not None}"
                                )
                            if hasattr(choice, "message"):
                                logger.debug(f"Message type: {type(choice.message)}")
                except Exception as e:
                    logger.debug(
                        f"Error logging response structure (safe to ignore): {e}"
                    )

                processed = self.harmony_processor.process_response(
                    full_response, metadata=response_obj
                )
                display_text = self.harmony_processor.format_for_display(processed)

                # Log if Harmony-specific features detected
                if processed.get("has_reasoning"):
                    logger.debug("Harmony response contains reasoning")
                if processed.get("has_tools"):
                    logger.debug("Harmony response contains tool calls")

            # Store last response for copy commands (what user sees)
            self.last_response = display_text

            #  Render final response (only if not already printed during streaming)
            if not already_printed_streaming:
                if self.use_rich and display_text.strip() and self.console:
                    # Use rich markdown rendering
                    print()  # New line after agent name
                    md = Markdown(display_text)
                    self.console.print(md)
                elif display_text.strip():
                    # Non-streaming or non-rich: print plain text
                    formatted_response = Colors.format_agent_response(display_text)
                    print(formatted_response)

            duration = time.time() - start_time

            # Extract token usage if available
            usage_result = self._extract_token_usage(response_obj)

            # Extract additional metrics (framework-specific)
            cycle_count = None
            tool_count = None
            if isinstance(response_obj, dict) and "result" in response_obj:
                result = response_obj["result"]
                if hasattr(result, "metrics"):
                    metrics = result.metrics
                    if hasattr(metrics, "cycle_count"):
                        cycle_count = metrics.cycle_count
                    if hasattr(metrics, "tool_metrics") and metrics.tool_metrics:
                        # Count total tool calls across all tools
                        try:
                            if isinstance(metrics.tool_metrics, dict):
                                tool_count = sum(
                                    len(calls)
                                    for calls in metrics.tool_metrics.values()
                                )
                            elif hasattr(metrics.tool_metrics, "__len__"):
                                tool_count = len(metrics.tool_metrics)
                            elif hasattr(metrics.tool_metrics, "__dict__"):
                                # ToolMetrics object - count attributes
                                # that look like tool calls
                                tool_count = len(
                                    [
                                        k
                                        for k in metrics.tool_metrics.__dict__.keys()
                                        if not k.startswith("_")
                                    ]
                                )
                        except Exception as e:
                            logger.debug(f"Could not extract tool count: {e}")
                            tool_count = None

            # Track tokens (always, for session summary)
            if usage_result:
                usage_info, is_accumulated = usage_result

                if is_accumulated:
                    # AWS Strands accumulated_usage is cumulative across session
                    # Calculate delta from last query
                    current_input = usage_info["input_tokens"]
                    current_output = usage_info["output_tokens"]

                    delta_input = current_input - self.last_accumulated_input
                    delta_output = current_output - self.last_accumulated_output

                    # Update tracking
                    self.last_accumulated_input = current_input
                    self.last_accumulated_output = current_output

                    # Add only the delta
                    if delta_input > 0 or delta_output > 0:
                        self.token_tracker.add_usage(delta_input, delta_output)
                else:
                    # Non-accumulated usage - add directly
                    self.token_tracker.add_usage(
                        usage_info["input_tokens"], usage_info["output_tokens"]
                    )

                # Update status bar
                if self.status_bar:
                    self.status_bar.update_tokens(self.token_tracker.get_total_tokens())

            # Display duration and token info
            # Determine what to show
            show_info_line = (
                self.show_duration
                or (self.show_tokens and usage_info)
                or cycle_count
                or tool_count
            )

            if show_info_line:
                print(f"\n{Colors.DIM}{'-' * 60}{Colors.RESET}")

                info_parts = []
                if self.show_duration:
                    info_parts.append(f"Time: {duration:.1f}s")

                # Show agent metrics (cycles, tools) - always show if available
                if cycle_count is not None and cycle_count > 0:
                    cycle_word = "cycle" if cycle_count == 1 else "cycles"
                    info_parts.append(f"{cycle_count} {cycle_word}")

                if tool_count is not None and tool_count > 0:
                    tool_word = "tool" if tool_count == 1 else "tools"
                    info_parts.append(f"{tool_count} {tool_word}")

                # Only show tokens if show_tokens is enabled
                if self.show_tokens and usage_info:
                    input_tok = usage_info["input_tokens"]
                    output_tok = usage_info["output_tokens"]
                    total_tok = input_tok + output_tok

                    # Format tokens
                    token_str = (
                        f"Tokens: {self.token_tracker.format_tokens(total_tok)} "
                    )
                    token_str += f"(in: {self.token_tracker.format_tokens(input_tok)}, "
                    token_str += f"out: {self.token_tracker.format_tokens(output_tok)})"
                    info_parts.append(token_str)

                if info_parts:  # Only print if we have something to show
                    print(Colors.system(" │ ".join(info_parts)))

            logger.info(f"Query completed successfully in {duration:.1f}s")

            # Track conversation as markdown for saving
            self.query_count += 1
            entry_timestamp = datetime.now().strftime("%H:%M:%S")

            # Build markdown entry
            md_entry = [
                f"\n## Query {self.query_count} ({entry_timestamp})\n",
                f"**You:** {query}\n\n",
                f"**{self.agent_name}:** {display_text}\n\n",
            ]

            # Add metadata
            metadata_parts = [f"Time: {duration:.1f}s"]
            if usage_info:
                input_tok = usage_info.get("input_tokens", 0)
                output_tok = usage_info.get("output_tokens", 0)
                total_tok = input_tok + output_tok
                self.total_input_tokens += input_tok
                self.total_output_tokens += output_tok
                if total_tok > 0:
                    tok_str = (
                        f"Tokens: {total_tok:,} "
                        f"(in: {input_tok:,}, out: {output_tok:,})"
                    )
                    metadata_parts.append(tok_str)

            md_entry.append(f"*{' | '.join(metadata_parts)}*\n\n")
            md_entry.append("---\n")

            self.conversation_markdown.extend(md_entry)

            # Save conversation incrementally after each query-response
            await self.save_conversation()

            # Play audio notification on agent turn completion
            self.audio_notifier.play()

            return {"duration": duration, "usage": usage_info}

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(Colors.error(f"{self.agent_name}: Query failed - {e}"))
            print(
                Colors.system(
                    "Try rephrasing your question or check the logs for details."
                )
            )
            logger.error(
                f"Agent query failed after {duration:.1f}s: {e}", exc_info=True
            )

            return {"duration": duration, "usage": None}

        finally:
            # Always cleanup thinking indicator, even on KeyboardInterrupt
            stop_thinking.set()
            if thinking_task and not thinking_task.done():
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling

    async def process_query(self, query: str):
        """Process query through agent with streaming and error recovery."""
        for attempt in range(1, self.max_retries + 1):
            try:
                await self._stream_agent_response(query)
                return  # Success, exit retry loop

            except asyncio.TimeoutError:
                print(
                    ErrorMessages.query_timeout(
                        attempt, self.max_retries, int(self.timeout)
                    )
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    logger.warning(f"Timeout on attempt {attempt}, retrying...")
                else:
                    logger.error("Max retries reached after timeout")

            except ConnectionError as e:
                print(ErrorMessages.connection_error(e, attempt, self.max_retries))
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    logger.warning(
                        f"Connection error on attempt {attempt}, retrying..."
                    )
                else:
                    logger.error(f"Max retries reached after connection error: {e}")

            except Exception as e:
                # For other exceptions, don't retry - they're likely not transient
                error_msg = str(e)

                # Check for rate limit errors
                if "rate" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (
                            2 ** (attempt - 1)
                        )  # Exponential backoff
                        print(ErrorMessages.rate_limit_error(int(wait_time), attempt))
                        await asyncio.sleep(wait_time)
                        logger.warning(
                            f"Rate limit on attempt {attempt}, backing off..."
                        )
                    else:
                        print(
                            Colors.error(
                                "⚠️  Rate limit persists. Please wait and try again."
                            )
                        )
                        logger.error("Max retries reached due to rate limiting")
                else:
                    # Non-retryable error, log and exit
                    logger.error(f"Non-retryable error: {e}", exc_info=True)
                    raise

    async def _async_run(self):
        """Async implementation of the chat loop."""
        # Setup readline history
        self.history_file = setup_readline_history()

        # Set initial terminal title
        if self.update_terminal_title:
            set_terminal_title(f"{self.agent_name} - Idle")

        # Only show banner now if NOT resuming (will show after resume succeeds)
        will_resume = hasattr(self, "resume_session_ref") and self.resume_session_ref
        if not will_resume:
            self.display_manager.display_banner()

        # Handle --resume flag if specified
        if will_resume:
            session_ref = self.resume_session_ref

            # If "pick" mode, show session picker
            if session_ref == "pick":
                sessions = self.session_manager.list_sessions(
                    agent_name=self.agent_name, limit=20
                )

                if not sessions:
                    print(Colors.system("\nNo saved sessions found to resume."))
                    print("Continue with fresh session...\n")
                    self.display_manager.display_banner()
                else:
                    self.display_manager.display_sessions(
                        sessions, agent_name=self.agent_name
                    )
                    print()
                    try:
                        prompt = (
                            "Enter session number to resume (or press Enter to skip): "
                        )
                        choice = input(Colors.system(prompt)).strip()

                        if choice:
                            success = await self.restore_session(choice)
                            if success:
                                # Display banner after successful resume
                                self.display_manager.display_banner()
                            else:
                                # Resume failed, show banner for fresh session
                                self.display_manager.display_banner()
                        else:
                            # User pressed Enter to skip - show banner for fresh session
                            self.display_manager.display_banner()
                    except (KeyboardInterrupt, EOFError):
                        print()
                        print(
                            Colors.system("Skipping resume, starting fresh session...")
                        )
                        print()
                        # User cancelled - show banner for fresh session
                        self.display_manager.display_banner()
            else:
                # Direct resume with specific session ID/number
                success = await self.restore_session(session_ref)
                if success:
                    # Display banner after successful resume
                    self.display_manager.display_banner()
                else:
                    print(Colors.system("\nContinuing with fresh session...\n"))
                    # Resume failed, show banner for fresh session
                    self.display_manager.display_banner()

        try:
            while True:
                try:
                    # Get user input directly (blocking is fine for user input)
                    # Don't use executor as it breaks readline editing
                    user_input = input(f"\n{Colors.user('You')}: ").strip()

                    # Handle exit commands (with or without # or /)
                    # Support: exit, quit, bye, #exit, /exit, etc.
                    normalized_input = user_input.lstrip("#/").lower()
                    if normalized_input in ["exit", "quit", "bye"]:
                        print(
                            Colors.system(
                                f"\nGoodbye! Thanks for using {self.agent_name}!"
                            )
                        )
                        break

                    # Handle commands (commands start with #)
                    # Note: / prefix is reserved for templates (see below)
                    if user_input.startswith("#"):
                        # Strip # and get command
                        cmd_input = user_input[1:].strip()
                        cmd_lower = cmd_input.lower()

                        if cmd_lower in ["exit", "quit", "bye"]:
                            print(
                                Colors.system(
                                    f"\nGoodbye! Thanks for using {self.agent_name}!"
                                )
                            )
                            break
                        elif cmd_lower == "help":
                            self.display_manager.display_help()
                            continue
                        elif cmd_lower == "info":
                            self.display_manager.display_info()
                            continue
                        elif cmd_lower == "templates":
                            # List available prompt templates
                            templates = (
                                self.template_manager.list_templates_with_descriptions()
                            )
                            self.display_manager.display_templates(
                                templates, self.prompts_dir
                            )
                            continue
                        elif cmd_lower == "sessions":
                            # List saved sessions
                            sessions = self.session_manager.list_sessions(
                                agent_name=self.agent_name, limit=20
                            )
                            self.display_manager.display_sessions(
                                sessions, agent_name=self.agent_name
                            )
                            continue
                        elif cmd_lower == "compact":
                            # Compact session command
                            await self._handle_compact_command()
                            continue
                        elif cmd_lower.startswith("copy"):
                            # Copy command with variants
                            parts = cmd_lower.split(maxsplit=1)
                            copy_mode = parts[1] if len(parts) > 1 else ""

                            try:
                                content = None
                                description = ""

                                if copy_mode == "query":
                                    # Copy last user query
                                    if self.last_query:
                                        content = self.last_query
                                        description = "last query"
                                    else:
                                        print(Colors.system("No query to copy yet"))
                                        continue
                                elif copy_mode == "all":
                                    # Copy entire conversation as markdown
                                    if self.conversation_markdown:
                                        content = (
                                            self._format_conversation_as_markdown()
                                        )
                                        description = "entire conversation"
                                    else:
                                        print(
                                            Colors.system("No conversation to copy yet")
                                        )
                                        continue
                                elif copy_mode == "code":
                                    # Copy just code blocks from last response
                                    if self.last_response:
                                        code_blocks = self._extract_code_blocks(
                                            self.last_response
                                        )
                                        if code_blocks:
                                            content = "\n\n".join(code_blocks)
                                            description = (
                                                "code blocks from last response"
                                            )
                                        else:
                                            msg = (
                                                "No code blocks found in last response"
                                            )
                                            print(Colors.system(msg))
                                            continue
                                    else:
                                        print(Colors.system("No response to copy yet"))
                                        continue
                                else:
                                    # Default: copy last response
                                    if self.last_response:
                                        content = self.last_response
                                        description = "last response"
                                    else:
                                        print(Colors.system("No response to copy yet"))
                                        continue

                                # Copy to clipboard
                                pyperclip.copy(content)
                                print(
                                    Colors.success(
                                        f"✓ Copied {description} to clipboard"
                                    )
                                )

                            except Exception as e:
                                print(Colors.error(f"Failed to copy: {e}"))
                                logger.error(f"Copy command failed: {e}")
                            continue
                        elif cmd_lower == "resume" or cmd_lower.startswith("resume "):
                            # Resume a previous session
                            parts = cmd_input.split(maxsplit=1)

                            # If no session specified, show list of sessions
                            if len(parts) < 2:
                                sessions = self.session_manager.list_sessions(
                                    agent_name=self.agent_name, limit=20
                                )
                                self.display_manager.display_sessions(
                                    sessions, agent_name=self.agent_name
                                )
                                usage_msg = "Usage: #resume <number or session_id>"
                                print(f"\n{Colors.system(usage_msg)}")
                                continue

                            session_ref = parts[1].strip()
                            success = await self.restore_session(session_ref)

                            if success:
                                # Show banner after resume
                                self.display_manager.display_banner()
                            continue
                        elif cmd_lower == "context":
                            # Show context usage statistics
                            total_tokens = self.token_tracker.get_total_tokens()
                            input_tokens = self.token_tracker.total_input_tokens
                            output_tokens = self.token_tracker.total_output_tokens

                            # Get max tokens from agent metadata
                            max_tokens = self.agent_metadata.get(
                                "max_tokens", "Unknown"
                            )

                            # Calculate percentage if max_tokens is known
                            percentage_str = ""
                            if (
                                max_tokens != "Unknown"
                                and isinstance(max_tokens, (int, float))
                                and max_tokens > 0
                            ):
                                percentage = (total_tokens / max_tokens) * 100
                                percentage_str = f" ({percentage:.1f}%)"

                            # Calculate session duration
                            session_duration = time.time() - self.session_start_time
                            if session_duration < 60:
                                duration_str = f"{session_duration:.0f}s"
                            elif session_duration < 3600:
                                minutes = int(session_duration / 60)
                                seconds = int(session_duration % 60)
                                duration_str = f"{minutes}m {seconds}s"
                            else:
                                hours = int(session_duration / 3600)
                                minutes = int((session_duration % 3600) / 60)
                                duration_str = f"{hours}h {minutes}m"

                            # Display context information
                            print(f"\n{Colors.system('Context Usage')}")
                            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")

                            # Format max tokens display
                            if max_tokens == "Unknown":
                                max_str = "Unknown"
                            else:
                                max_str = self.token_tracker.format_tokens(max_tokens)

                            print(
                                f"  Total Tokens:   "
                                f"{self.token_tracker.format_tokens(total_tokens)} / "
                                f"{max_str}{percentage_str}"
                            )
                            print(
                                f"  Input Tokens:   "
                                f"{self.token_tracker.format_tokens(input_tokens)}"
                            )
                            print(
                                f"  Output Tokens:  "
                                f"{self.token_tracker.format_tokens(output_tokens)}"
                            )
                            print(f"  Queries:        {self.query_count}")
                            print(f"  Session Time:   {duration_str}")

                            # Show warning if approaching limits
                            if (
                                max_tokens != "Unknown"
                                and isinstance(max_tokens, (int, float))
                                and max_tokens > 0
                            ):
                                percentage = (total_tokens / max_tokens) * 100

                                # Sort thresholds in descending order
                                sorted_thresholds = sorted(
                                    self.context_warning_thresholds, reverse=True
                                )

                                # Check thresholds from highest to lowest
                                for threshold in sorted_thresholds:
                                    if percentage >= threshold:
                                        # Highest threshold gets special treatment
                                        if threshold == sorted_thresholds[0]:
                                            msg = (
                                                f"⚠️  Warning: {threshold}% "
                                                f"of context used!"
                                            )
                                            print(f"\n  {Colors.error(msg)}")
                                            msg2 = (
                                                "Consider using #compact "
                                                "to free up context."
                                            )
                                            print(f"  {Colors.system(msg2)}")
                                        # Second highest threshold
                                        elif (
                                            threshold == sorted_thresholds[1]
                                            if len(sorted_thresholds) > 1
                                            else False
                                        ):
                                            msg = (
                                                f"⚠️  Warning: {threshold}% "
                                                f"of context used"
                                            )
                                            print(f"\n  {Colors.error(msg)}")
                                        # Other thresholds
                                        else:
                                            msg = f"💡 Context usage: {threshold}%"
                                            print(f"\n  {Colors.system(msg)}")
                                        break  # Only show highest matched threshold

                            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
                            continue
                        elif cmd_lower == "clear":
                            # Clear screen (cross-platform)
                            os.system("clear" if os.name != "nt" else "cls")

                            # Reset agent session if factory available
                            if self.agent_factory:
                                try:
                                    # Cleanup old agent if possible
                                    if hasattr(self.agent, "cleanup"):
                                        try:
                                            if asyncio.iscoroutinefunction(
                                                self.agent.cleanup
                                            ):
                                                await self.agent.cleanup()
                                            else:
                                                self.agent.cleanup()
                                        except Exception as e:
                                            logger.debug(
                                                f"Error during agent cleanup: {e}"
                                            )

                                    # Create fresh agent instance
                                    self.agent = self.agent_factory()
                                    print(
                                        Colors.success(
                                            "✓ Screen cleared and agent session reset"
                                        )
                                    )
                                    logger.info("Agent session reset via clear command")
                                except Exception as e:
                                    print(
                                        Colors.error(
                                            f"⚠️  Could not reset agent session: {e}"
                                        )
                                    )
                                    logger.error(f"Failed to reset agent session: {e}")
                                    msg = "Screen cleared but agent session maintained"
                                    print(Colors.system(msg))
                            else:
                                print(Colors.success("✓ Screen cleared"))

                            self.display_manager.display_banner()
                            continue
                        else:
                            # Unknown # command
                            print(Colors.error(f"Unknown command: #{cmd_input}"))
                            print("Type '#help' for available commands")
                            continue

                    # Template command: /template_name <optional input>
                    elif user_input.startswith("/") and len(user_input) > 1:
                        parts = user_input[1:].split(maxsplit=1)
                        template_name = parts[0]
                        input_text = parts[1] if len(parts) > 1 else ""

                        # Try to load template
                        template = self.template_manager.load_template(
                            template_name, input_text
                        )
                        if template:
                            print(Colors.system(f"✓ Loaded template: {template_name}"))
                            # Use the template as the user input
                            user_input = template
                        else:
                            print(Colors.error(f"Template not found: {template_name}"))
                            templates = self.template_manager.list_templates()
                            tmpl_list = ", ".join(templates) or "none"
                            print(f"Available templates: {tmpl_list}")
                            print(f"Create at: {self.prompts_dir}/{template_name}.md")
                            continue

                    # Multi-line input trigger
                    elif user_input == "\\\\":  # Multi-line input trigger
                        user_input = await self.get_multiline_input()
                        if not user_input.strip():
                            continue
                    elif not user_input:
                        continue

                    # Process query through agent
                    logger.info(f"Processing query: {user_input[:100]}...")

                    # Track query for copy command
                    self.last_query = user_input

                    # Update terminal title to show processing
                    if self.update_terminal_title:
                        set_terminal_title(f"{self.agent_name} - Processing...")

                    # Update status bar before query
                    if self.status_bar:
                        self.status_bar.increment_query()
                        # Clear screen and redraw status bar
                        print("\033[2J\033[H", end="")  # Clear screen, move to top
                        print(self.status_bar.render())
                        print()  # Blank line after status bar

                    await self.process_query(user_input)

                    # Update terminal title back to idle
                    if self.update_terminal_title:
                        set_terminal_title(f"{self.agent_name} - Idle")

                except KeyboardInterrupt:
                    print(
                        Colors.system(
                            f"\n\nChat interrupted. Thanks for using {self.agent_name}!"
                        )
                    )
                    break
                except EOFError:
                    print(
                        Colors.system(
                            f"\n\nChat ended. Thanks for using {self.agent_name}!"
                        )
                    )
                    break

        finally:
            # Reset terminal title
            if self.update_terminal_title:
                set_terminal_title("Terminal")

            # Save command history
            save_readline_history(self.history_file)

            # Final save on exit with summary
            # (incremental saves happen after each query without summaries)
            success = await self.save_conversation(generate_summary=True)
            if success:
                self._show_save_confirmation(self.session_id)

            # Cleanup agent if it has cleanup method
            if hasattr(self.agent, "cleanup"):
                try:
                    if asyncio.iscoroutinefunction(self.agent.cleanup):
                        await self.agent.cleanup()
                    else:
                        self.agent.cleanup()
                except Exception as e:
                    logger.warning(f"Error during agent cleanup: {e}")

            # Display session summary
            self.display_manager.display_session_summary(
                self.session_start_time, self.query_count, self.token_tracker
            )

            print(Colors.success(f"\n{self.agent_name} session complete!"))

    def run(self):
        """Run the interactive chat loop."""
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            print(f"\n\nChat interrupted. Thanks for using {self.agent_name}!")
        except Exception as e:
            logger.error(f"Fatal error in chat loop: {e}", exc_info=True)
            print(f"\nFatal error: {e}")


def main():
    """Main entry point for the chat loop."""
    parser = argparse.ArgumentParser(
        description=(
            "Interactive CLI for AI Agents with token tracking and rich features"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with agent path
    chat_loop path/to/agent.py

    # Run with alias
    chat_loop my_agent

    # Auto-install dependencies
    chat_loop my_agent --auto-setup
    chat_loop path/to/agent.py -a

    # Configuration
    chat_loop --wizard              # Create/customize .chatrc
    chat_loop --reset-config        # Reset .chatrc to defaults

    # Alias management
    chat_loop --save-alias my_agent path/to/agent.py
    chat_loop --list-aliases
    chat_loop --remove-alias my_agent
        """,
    )

    # Import version for --version flag
    try:
        from . import __version__

        version_string = f"%(prog)s {__version__}"
    except ImportError:
        version_string = "%(prog)s (version unknown)"

    parser.add_argument(
        "--version",
        action="version",
        version=version_string,
    )

    parser.add_argument("agent", nargs="?", help="Agent path or alias name")

    parser.add_argument(
        "--config", help="Path to configuration file (default: ~/.chatrc or .chatrc)"
    )

    # Alias management commands
    alias_group = parser.add_argument_group("alias management")

    alias_group.add_argument(
        "--save-alias",
        nargs=2,
        metavar=("ALIAS", "PATH"),
        help="Save an agent alias: --save-alias pete path/to/agent.py",
    )

    alias_group.add_argument(
        "--list-aliases", action="store_true", help="List all saved aliases"
    )

    alias_group.add_argument(
        "--remove-alias", metavar="ALIAS", help="Remove an alias: --remove-alias pete"
    )

    alias_group.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing alias when using --save-alias",
    )

    # Dependency management
    parser.add_argument(
        "--auto-setup",
        "-a",
        action="store_true",
        help=(
            "Automatically install agent dependencies "
            "(requirements.txt, pyproject.toml)"
        ),
    )

    # Session management
    session_group = parser.add_argument_group("session management")

    session_group.add_argument(
        "--resume",
        "-r",
        nargs="?",
        const="pick",
        metavar="SESSION",
        help=(
            "Resume a previous session (optionally specify session ID or number, "
            "otherwise shows picker)"
        ),
    )

    session_group.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all saved sessions and exit",
    )

    # Configuration wizard
    parser.add_argument(
        "--wizard",
        "-w",
        action="store_true",
        help="Run interactive configuration wizard to create .chatrc file",
    )

    parser.add_argument(
        "--reset-config",
        action="store_true",
        help="Reset .chatrc file to default values",
    )

    args = parser.parse_args()

    # Handle configuration wizard
    if args.wizard:
        wizard = ConfigWizard()
        config_path = wizard.run()
        if config_path:
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle config reset
    if args.reset_config:
        from .components.config_wizard import reset_config_to_defaults

        config_path = reset_config_to_defaults()
        if config_path:
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle alias management commands
    alias_manager = AliasManager()

    if args.save_alias:
        alias_name, agent_path = args.save_alias
        success, message = alias_manager.add_alias(
            alias_name, agent_path, overwrite=args.overwrite
        )
        if success:
            print(Colors.success(message))
            sys.exit(0)
        else:
            print(Colors.error(message))
            sys.exit(1)

    if args.list_aliases:
        aliases = alias_manager.list_aliases()
        if aliases:
            print(f"\n{Colors.system('Saved Agent Aliases')} ({len(aliases)}):")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            for alias_name, agent_path in sorted(aliases.items()):
                # Check if path still exists
                if Path(agent_path).exists():
                    print(f"  {Colors.success(alias_name):<20} → {agent_path}")
                else:
                    status = f"{Colors.SYSTEM}(missing){Colors.RESET}"
                    print(f"  {Colors.error(alias_name):<20} → {agent_path} {status}")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(f"\nUsage: {Colors.system('chat_loop <alias>')}")
        else:
            print(f"\n{Colors.system('No aliases saved yet')}")
            print("\nCreate an alias with:")
            print(f"  {Colors.system('chat_loop --save-alias <name> <path>')}")
        sys.exit(0)

    if args.remove_alias:
        success, message = alias_manager.remove_alias(args.remove_alias)
        if success:
            print(Colors.success(message))
            sys.exit(0)
        else:
            print(Colors.error(message))
            sys.exit(1)

    # Handle session management commands
    if args.list_sessions:
        # List sessions and exit (from ./.chat-sessions in current directory)
        session_manager = SessionManager()
        sessions = session_manager.list_sessions(limit=50)

        if sessions:
            print(f"\n{Colors.system('Saved Sessions')} ({len(sessions)}):")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            for i, session in enumerate(sessions, 1):
                created_str = session.created.strftime("%b %d, %Y %H:%M")
                session_line = f"  {i:2}. {session.agent_name:<20} {created_str}"
                session_line += f"  {session.query_count:3} queries"
                print(session_line)
                preview_text = f'      "{session.preview}"'
                print(f"{Colors.DIM}{preview_text}{Colors.RESET}")

            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(f"\nResume: {Colors.system('chat_loop <agent> --resume <number>')}")
            print(f"        {Colors.system('chat_loop <agent> --resume <session_id>')}")
        else:
            print(f"\n{Colors.system('No saved sessions found')}")
            print("Sessions will be saved to: ./.chat-sessions")

        sys.exit(0)

    # Require agent argument if not doing alias management
    if not args.agent:
        print(Colors.error("Error: Agent path or alias required"))
        print()
        print("Usage:")
        print(f"  {Colors.system('chat_loop <agent_path>')}")
        print(f"  {Colors.system('chat_loop <alias>')}")
        print()
        print("Alias Management:")
        print(f"  {Colors.system('chat_loop --save-alias <name> <path>')}")
        print(f"  {Colors.system('chat_loop --list-aliases')}")
        print(f"  {Colors.system('chat_loop --remove-alias <name>')}")
        sys.exit(1)

    # Resolve agent path (try as path first, then as alias)
    agent_path = alias_manager.resolve_agent_path(args.agent)

    if not agent_path:
        print(Colors.error(f"Error: Agent not found: {args.agent}"))
        print()
        print("Not found as:")
        print(f"  • File path: {args.agent}")
        print(f"  • Alias name: {args.agent}")
        print()
        print("Available aliases:")
        aliases = alias_manager.list_aliases()
        if aliases:
            for alias_name in sorted(aliases.keys()):
                print(f"  • {alias_name}")
        else:
            print("  (none)")
        sys.exit(1)

    # Handle dependency installation if requested
    dep_manager = DependencyManager(agent_path)

    if args.auto_setup:
        # User explicitly requested dependency installation
        dep_info = dep_manager.detect_dependency_file()
        if dep_info:
            file_type, file_path = dep_info
            print(
                Colors.system(f"📦 Found {file_path.name}, installing dependencies...")
            )
            success, message = dep_manager.install_dependencies(file_type, file_path)
            if success:
                print(Colors.success(message))
            else:
                print(Colors.error(message))
                print(Colors.system("\nContinuing without dependency installation..."))
        else:
            msg = (
                "💡 No dependency files found "
                "(requirements.txt, pyproject.toml, setup.py)"
            )
            print(Colors.system(msg))
    else:
        # Check if dependencies exist and suggest using --auto-setup
        suggestion = dep_manager.suggest_auto_setup()
        if suggestion:
            print(Colors.system(suggestion))
            print()  # Extra spacing

    try:
        # Load configuration FIRST (before any print statements)
        config = None
        config_path = Path(args.config) if args.config else None
        config = get_config(config_path)

        # Apply color configuration immediately
        if config:
            color_config = config.get_section("colors")
            Colors.configure(color_config)

        # Show config info
        if config:
            if args.config:
                print(Colors.system(f"Loaded configuration from: {args.config}"))
            else:
                # Check which config file was loaded
                global_config = Path.home() / ".chatrc"
                project_config = Path.cwd() / ".chatrc"
                if project_config.exists():
                    print(Colors.system(f"Loaded configuration from: {project_config}"))
                elif global_config.exists():
                    print(Colors.system(f"Loaded configuration from: {global_config}"))

        # Load the agent
        # Show what we're loading (path or alias)
        if agent_path != args.agent:
            print(Colors.system(f"Resolved alias '{args.agent}' → {agent_path}"))
        print(Colors.system(f"Loading agent from: {agent_path}"))
        agent, agent_name, agent_description = load_agent_module(agent_path)

        # Setup logging with agent name
        setup_logging(agent_name)

        print(Colors.success(f"Agent loaded successfully: {agent_name}"))
        logger.info(f"Agent loaded successfully: {agent_name} - {agent_description}")

        # Create agent factory for session reset
        def create_fresh_agent():
            """Factory function to create a fresh agent instance."""
            new_agent, _, _ = load_agent_module(agent_path)
            return new_agent

        # Start chat loop with config
        chat_loop = ChatLoop(
            agent,
            agent_name,
            agent_description,
            agent_factory=create_fresh_agent,
            agent_path=str(agent_path),
            config=config,
        )

        # Handle --resume flag if provided
        if args.resume:
            # Store resume session for processing in _async_run
            chat_loop.resume_session_ref = args.resume
        else:
            chat_loop.resume_session_ref = None

        chat_loop.run()

        # Explicitly exit with success code
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
