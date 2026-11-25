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
from pathlib import Path
from typing import Any, Optional

import pyperclip  # type: ignore[import-untyped]

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False


from .chat_config import ChatConfig, get_config
from .components import (
    AliasManager,
    AudioNotifier,
    Colors,
    CommandRouter,
    CommandType,
    ConfigWizard,
    DependencyManager,
    DisplayManager,
    ErrorMessages,
    ResponseRenderer,
    ResponseStreamer,
    SessionManager,
    SessionPersister,
    SessionRestorer,
    SessionState,
    StatusBar,
    StreamingEventParser,
    TemplateManager,
    TokenTracker,
    UsageExtractor,
    extract_agent_metadata,
    get_multiline_input,
    load_agent_module,
)

try:
    from rich.console import Console
    from rich.markdown import Markdown

    RICH_AVAILABLE = True
    ConsoleType = Console
    MarkdownType = Markdown
except ImportError:
    RICH_AVAILABLE = False
    ConsoleType = None  # type: ignore
    MarkdownType = None  # type: ignore

log_dir = Path.home() / ".chat_loop_logs"

READLINE_HISTORY_LENGTH = 1000

TOKEN_TO_WORD_RATIO = 1.3

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
        log_dir.mkdir(exist_ok=True, mode=0o700)

        safe_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        log_file = log_dir / f"{safe_name}_chat.log"

        logger.setLevel(logging.INFO)

        logger.handlers = []

        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

        if log_file.exists():
            os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)

        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)

        logger.info(f"Logging initialized for agent: {agent_name}")
        logger.info(f"Log file: {log_file}")
        return True

    except Exception as e:
        print(f"Warning: Could not setup logging: {e}", file=sys.stderr)
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
        print(f"\033]0;{title}\033\\", end="", flush=True)
    except Exception:
        pass


def enable_windows_vt_mode() -> bool:
    """
    Enable Virtual Terminal Processing on Windows.

    This allows ANSI escape codes to work in standard cmd.exe and PowerShell
    without needing an external library like colorama for every print.
    """
    if sys.platform != "win32":
        return True

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32

        handle = kernel32.GetStdHandle(-11)

        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False

        enable_virtual_terminal_processing = 0x0004
        if not (mode.value & enable_virtual_terminal_processing):
            if kernel32.SetConsoleMode(
                handle, mode.value | enable_virtual_terminal_processing
            ):
                return True
            return False

        return True
    except Exception:
        return False


def setup_readline_history() -> Optional[Path]:
    """
    Setup readline command history with persistence.

    Returns:
        Path to history file if successful, None otherwise
    """
    if not READLINE_AVAILABLE:
        logger.debug("Readline not available, history will not be saved")
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
        history_file = Path.home() / ".chat_history"

        readline.set_history_length(READLINE_HISTORY_LENGTH)

        try:
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

            try:
                readline.parse_and_bind("tab: complete")

                readline.parse_and_bind("set editing-mode emacs")

                readline.parse_and_bind("set horizontal-scroll-mode off")

                readline.parse_and_bind("set show-all-if-ambiguous on")
                readline.parse_and_bind("set completion-ignore-case on")
            finally:
                sys.stderr.close()
                sys.stderr = old_stderr
        except Exception as e:
            logger.debug(f"Could not configure readline bindings: {e}")

        if history_file.exists():
            try:
                readline.read_history_file(str(history_file))
                count = readline.get_current_history_length()
                logger.debug(f"Loaded {count} history entries")
            except Exception as e:
                logger.warning(f"Could not load history from {history_file}: {e}")

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
        history_file.parent.mkdir(parents=True, exist_ok=True)

        readline.write_history_file(str(history_file))

        history_file.chmod(0o600)

        count = readline.get_current_history_length()
        logger.debug(f"Saved {count} history entries to {history_file}")
        return True

    except Exception as e:
        logger.warning(f"Could not save command history to {history_file}: {e}")
        return False


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
        self.agent_factory = agent_factory
        self.agent_path = agent_path or "unknown"
        self.history_file = None

        self.session_state = SessionState(agent_name)

        self.config = config if config else get_config()

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

            rich_enabled = self.config.get(
                "features.rich_enabled", True, agent_name=agent_name
            )
            self.use_rich = RICH_AVAILABLE and rich_enabled

            self.context_warning_thresholds = self.config.get(
                "context.warning_thresholds", [80, 90, 95], agent_name=agent_name
            )
        else:
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

        self.console: Optional[Console] = (
            Console(
                force_terminal=True,
                legacy_windows=False,
            )
            if self.use_rich
            else None
        )

        if self.console:
            logger.debug("Rich Console initialized:")
            logger.debug(f"  is_terminal: {self.console.is_terminal}")
            logger.debug(f"  color_system: {self.console.color_system}")
            logger.debug(f"  legacy_windows: {self.console.legacy_windows}")

        self.agent_metadata = extract_agent_metadata(self.agent)

        detected_model = self.agent_metadata.get("model_id", "Unknown")
        logger.info(f"Model Detected: {detected_model}")

        self.prompts_dir = Path.home() / ".prompts"

        self.template_manager = TemplateManager(self.prompts_dir)

        self.show_tokens = (
            self.config.get("features.show_tokens", False, agent_name=agent_name)
            if self.config
            else False
        )
        model_for_pricing = self.agent_metadata.get("model_id", "Unknown")

        if self.config:
            model_override = self.config.get(
                "agents." + agent_name + ".model_display_name", None
            )
            if model_override:
                model_for_pricing = model_override

        self.token_tracker = TokenTracker(model_for_pricing)

        self.show_status_bar_enabled = (
            self.config.get("ui.show_status_bar", False, agent_name=agent_name)
            if self.config
            else False
        )
        self.status_bar = None
        if self.show_status_bar_enabled:
            model_info = self.agent_metadata.get("model_id", "Unknown Model")

            if self.config:
                model_override = self.config.get(
                    "agents." + agent_name + ".model_display_name", None
                )
                if model_override:
                    model_info = model_override

            model_info = str(model_info) if model_info else "Unknown Model"
            if len(model_info) > 30:
                model_info = model_info[:27] + "..."

            max_tokens_for_bar = self.agent_metadata.get("max_tokens", None)
            if max_tokens_for_bar == "Unknown":
                max_tokens_for_bar = None

            self.status_bar = StatusBar(
                agent_name,
                model_info,
                show_tokens=self.show_tokens,
                max_tokens=max_tokens_for_bar,
            )

            logger.debug(
                f"Status bar initialized: agent={agent_name}, "
                f"model={model_info}, show_tokens={self.show_tokens}"
            )

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

        self.session_manager = SessionManager()

        self.event_parser = StreamingEventParser()

        self.usage_extractor = UsageExtractor()

        self.response_renderer = ResponseRenderer(
            agent_name=self.agent_name,
            colors_module=Colors,
        )

        self.response_streamer = ResponseStreamer(
            agent=self.agent,
            agent_name=self.agent_name,
            response_renderer=self.response_renderer,
            event_parser=self.event_parser,
            session_state=self.session_state,
            usage_extractor=self.usage_extractor,
            token_tracker=self.token_tracker,
            audio_notifier=self.audio_notifier,
            colors_module=Colors,
            show_thinking=self.show_thinking,
            show_duration=self.show_duration,
            show_tokens=self.show_tokens,
            status_bar=self.status_bar,
        )

        self.session_restorer = SessionRestorer(
            agent=self.agent,
            agent_name=self.agent_name,
            agent_path=self.agent_path,
            session_manager=self.session_manager,
            session_state=self.session_state,
            token_tracker=self.token_tracker,
            colors_module=Colors,
            use_rich=self.use_rich,
            console=self.console,
            status_bar=self.status_bar,
        )

        self.session_persister = SessionPersister(
            agent=self.agent,
            agent_name=self.agent_name,
            agent_path=self.agent_path,
            session_manager=self.session_manager,
            session_state=self.session_state,
            session_restorer=self.session_restorer,
            token_tracker=self.token_tracker,
            colors_module=Colors,
            response_streamer=self.response_streamer,
        )

        self.command_router = CommandRouter()

    def _extract_code_blocks(self, text: str) -> list:
        """
        Extract code blocks from markdown text.

        Args:
            text: Markdown text containing code blocks

        Returns:
            List of code block contents (without fence markers)
        """
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [match.strip() for match in matches]

    def _format_conversation_as_markdown(self) -> str:
        """
        Format entire conversation history as markdown.

        Returns:
            Markdown-formatted conversation
        """
        header = [
            f"# {self.agent_name} - Conversation\n\n",
            f"Session ID: {self.session_state.session_id}\n",
            f"Agent: {self.agent_name}\n",
            f"Queries: {self.session_state.query_count}\n\n",
            "---\n",
        ]
        return "".join(header + self.session_state.conversation_markdown)

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

            if match := re.search(r"\*\*Session ID:\*\* (.+)", content):
                metadata["session_id"] = match.group(1).strip()

            if match := re.search(r"\*\*Agent:\*\* (.+)", content):
                metadata["agent_name"] = match.group(1).strip()

            if match := re.search(r"\*\*Agent Path:\*\* (.+)", content):
                metadata["agent_path"] = match.group(1).strip()

            if match := re.search(r"\*\*Total Queries:\*\* (\d+)", content):
                metadata["query_count"] = int(match.group(1))

            if match := re.search(r"\*\*Resumed From:\*\* (.+)", content):
                metadata["resumed_from"] = match.group(1).strip()

            return metadata if metadata else None

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return None

    async def process_query(self, query: str):
        """Process query through agent with streaming and error recovery."""
        for attempt in range(1, self.max_retries + 1):
            try:
                await self.response_streamer.stream_agent_response(
                    query,
                    save_conversation_callback=self.session_persister.save_conversation,
                )
                return

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
                error_msg = str(e)

                if "rate" in error_msg.lower() or "429" in error_msg:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** (attempt - 1))
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
                    logger.error(f"Non-retryable error: {e}", exc_info=True)
                    raise

    async def _async_run(self):
        """Async implementation of the chat loop."""
        self.history_file = setup_readline_history()

        if self.update_terminal_title:
            set_terminal_title(f"{self.agent_name} - Idle")

        will_resume = hasattr(self, "resume_session_ref") and self.resume_session_ref
        if not will_resume:
            self.display_manager.display_banner()

        if will_resume:
            session_ref = self.resume_session_ref

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
                            success = await self.session_restorer.restore_session(
                                choice, self.response_streamer
                            )
                            if success:
                                self.display_manager.display_banner()
                            else:
                                self.display_manager.display_banner()
                        else:
                            self.display_manager.display_banner()
                    except (KeyboardInterrupt, EOFError):
                        print()
                        print(
                            Colors.system("Skipping resume, starting fresh session...")
                        )
                        print()
                        self.display_manager.display_banner()
            else:
                success = await self.session_restorer.restore_session(
                    session_ref, self.response_streamer
                )
                if success:
                    self.display_manager.display_banner()
                else:
                    print(Colors.system("\nContinuing with fresh session...\n"))
                    self.display_manager.display_banner()

        try:
            while True:
                try:
                    user_input = input(f"\n{Colors.user('You')}: ").strip()

                    command_result = self.command_router.parse_input(user_input)

                    if command_result.command_type == CommandType.EXIT:
                        print(
                            Colors.system(
                                f"\nGoodbye! Thanks for using {self.agent_name}!"
                            )
                        )
                        break

                    elif command_result.command_type == CommandType.HELP:
                        self.display_manager.display_help()
                        continue

                    elif command_result.command_type == CommandType.INFO:
                        self.display_manager.display_info()
                        continue

                    elif command_result.command_type == CommandType.TEMPLATES:
                        claude_commands_enabled = (
                            self.config.get(
                                "features.claude_commands_enabled",
                                True,
                                agent_name=self.agent_name,
                            )
                            if self.config
                            else True
                        )
                        if not claude_commands_enabled:
                            print(
                                Colors.system(
                                    "Claude slash commands are disabled in config"
                                )
                            )
                            continue

                        templates_grouped = (
                            self.template_manager.list_templates_grouped()
                        )
                        self.display_manager.display_templates(templates_grouped)
                        continue

                    elif command_result.command_type == CommandType.SESSIONS:
                        sessions = self.session_manager.list_sessions(
                            agent_name=self.agent_name, limit=20
                        )
                        self.display_manager.display_sessions(
                            sessions, agent_name=self.agent_name
                        )
                        continue

                    elif command_result.command_type == CommandType.COMPACT:
                        await self.session_persister.handle_compact_command()
                        continue

                    elif command_result.command_type == CommandType.COPY:
                        copy_mode = command_result.args or ""

                        try:
                            content = None
                            description = ""

                            if copy_mode == "query":
                                if self.session_state.last_query:
                                    content = self.session_state.last_query
                                    description = "last query"
                                else:
                                    print(Colors.system("No query to copy yet"))
                                    continue
                            elif copy_mode == "all":
                                if self.session_state.conversation_markdown:
                                    content = self._format_conversation_as_markdown()
                                    description = "entire conversation"
                                else:
                                    print(Colors.system("No conversation to copy yet"))
                                    continue
                            elif copy_mode == "code":
                                if self.session_state.last_response:
                                    code_blocks = self._extract_code_blocks(
                                        self.session_state.last_response
                                    )
                                    if code_blocks:
                                        content = "\n\n".join(code_blocks)
                                        description = "code blocks from last response"
                                    else:
                                        msg = "No code blocks found in last response"
                                        print(Colors.system(msg))
                                        continue
                                else:
                                    print(Colors.system("No response to copy yet"))
                                    continue
                            else:
                                if self.session_state.last_response:
                                    content = self.session_state.last_response
                                    description = "last response"
                                else:
                                    print(Colors.system("No response to copy yet"))
                                    continue

                            if content:
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

                    elif command_result.command_type == CommandType.RESUME:
                        session_ref = command_result.args

                        if not session_ref:
                            sessions = self.session_manager.list_sessions(
                                agent_name=self.agent_name, limit=20
                            )
                            self.display_manager.display_sessions(
                                sessions, agent_name=self.agent_name
                            )
                            usage_msg = "Usage: #resume <number or session_id>"
                            print(f"\n{Colors.system(usage_msg)}")
                            continue

                        success = await self.session_restorer.restore_session(
                            session_ref, self.response_streamer
                        )

                        if success:
                            self.display_manager.display_banner()
                        continue

                    elif command_result.command_type == CommandType.CONTEXT:
                        total_tokens = self.token_tracker.get_total_tokens()
                        input_tokens = self.token_tracker.total_input_tokens
                        output_tokens = self.token_tracker.total_output_tokens

                        max_tokens = self.agent_metadata.get("max_tokens", "Unknown")

                        percentage_str = ""
                        if (
                            max_tokens != "Unknown"
                            and isinstance(max_tokens, (int, float))
                            and max_tokens > 0
                        ):
                            percentage = (total_tokens / max_tokens) * 100
                            percentage_str = f" ({percentage:.1f}%)"

                        session_duration = (
                            time.time() - self.session_state.session_start_time
                        )
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

                        print(f"\n{Colors.system('Context Usage')}")
                        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")

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
                        print(f"  Queries:        {self.session_state.query_count}")
                        print(f"  Session Time:   {duration_str}")

                        if (
                            max_tokens != "Unknown"
                            and isinstance(max_tokens, (int, float))
                            and max_tokens > 0
                        ):
                            percentage = (total_tokens / max_tokens) * 100

                            sorted_thresholds = sorted(
                                self.context_warning_thresholds, reverse=True
                            )

                            for threshold in sorted_thresholds:
                                if percentage >= threshold:
                                    if threshold == sorted_thresholds[0]:
                                        msg = f"⚠️  Warning: {threshold}% of context used!"
                                        print(f"\n  {Colors.error(msg)}")
                                        msg2 = (
                                            "Consider using #compact "
                                            "to free up context."
                                        )
                                        print(f"  {Colors.system(msg2)}")
                                    elif (
                                        threshold == sorted_thresholds[1]
                                        if len(sorted_thresholds) > 1
                                        else False
                                    ):
                                        msg = (
                                            f"⚠️  Warning: {threshold}% of context used"
                                        )
                                        print(f"\n  {Colors.error(msg)}")
                                    else:
                                        msg = f"💡 Context usage: {threshold}%"
                                        print(f"\n  {Colors.system(msg)}")
                                    break

                        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
                        continue

                    elif command_result.command_type == CommandType.CLEAR:
                        os.system("clear" if os.name != "nt" else "cls")

                        if self.agent_factory:
                            try:
                                if hasattr(self.agent, "cleanup"):
                                    try:
                                        if asyncio.iscoroutinefunction(
                                            self.agent.cleanup
                                        ):
                                            await self.agent.cleanup()
                                        else:
                                            self.agent.cleanup()
                                    except Exception as e:
                                        logger.debug(f"Error during agent cleanup: {e}")

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

                    elif command_result.command_type == CommandType.UNKNOWN_COMMAND:
                        print(
                            Colors.error(
                                f"Unknown command: #{command_result.args or ''}"
                            )
                        )
                        print("Type '#help' for available commands")
                        continue

                    elif command_result.command_type == CommandType.TEMPLATE:
                        claude_commands_enabled = (
                            self.config.get(
                                "features.claude_commands_enabled",
                                True,
                                agent_name=self.agent_name,
                            )
                            if self.config
                            else True
                        )
                        if not claude_commands_enabled:
                            print(
                                Colors.system(
                                    "Claude slash commands are disabled in config"
                                )
                            )
                            continue

                        template_name, input_text = (
                            self.command_router.extract_template_info(command_result)
                        )

                        template = self.template_manager.load_template(
                            template_name, input_text
                        )
                        if template:
                            print(Colors.system(f"✓ Loaded template: {template_name}"))
                            user_input = template
                        else:
                            print(Colors.error(f"Template not found: {template_name}"))
                            templates = self.template_manager.list_templates()
                            tmpl_list = ", ".join(templates) or "none"
                            print(f"Available templates: {tmpl_list}")
                            print(f"Create at: {self.prompts_dir}/{template_name}.md")
                            continue

                    elif command_result.command_type == CommandType.MULTILINE:
                        user_input = await get_multiline_input()
                        if not user_input.strip():
                            continue

                    if command_result.command_type in (
                        CommandType.QUERY,
                        CommandType.TEMPLATE,
                        CommandType.MULTILINE,
                    ):
                        if not user_input.strip():
                            continue

                        logger.info(f"Processing query: {user_input[:100]}...")

                        self.session_state.update_last_query(user_input)

                        if self.update_terminal_title:
                            set_terminal_title(f"{self.agent_name} - Processing...")

                        if self.status_bar:
                            self.status_bar.increment_query()
                            print("\033[2J\033[H", end="")
                            print(self.status_bar.render())
                            print()

                        await self.process_query(user_input)

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
            if self.update_terminal_title:
                set_terminal_title("Terminal")

            save_readline_history(self.history_file)

            success = await self.session_persister.save_conversation(
                generate_summary=True
            )
            if success:
                self.session_persister.show_save_confirmation(
                    self.session_state.session_id
                )

            if hasattr(self.agent, "cleanup"):
                try:
                    if asyncio.iscoroutinefunction(self.agent.cleanup):
                        await self.agent.cleanup()
                    else:
                        self.agent.cleanup()
                except Exception as e:
                    logger.warning(f"Error during agent cleanup: {e}")

            self.display_manager.display_session_summary(
                self.session_state.session_start_time,
                self.session_state.query_count,
                self.token_tracker,
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
    enable_windows_vt_mode()

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

    parser.add_argument(
        "--auto-setup",
        "-a",
        action="store_true",
        help=(
            "Automatically install agent dependencies "
            "(requirements.txt, pyproject.toml)"
        ),
    )

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

    if args.wizard:
        wizard = ConfigWizard()
        config_path = wizard.run()
        if config_path:
            sys.exit(0)
        else:
            sys.exit(1)

    if args.reset_config:
        from .components.config_wizard import reset_config_to_defaults

        config_path = reset_config_to_defaults()
        if config_path:
            sys.exit(0)
        else:
            sys.exit(1)

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

    if args.list_sessions:
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

    dep_manager = DependencyManager(agent_path)

    if args.auto_setup:
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
        suggestion = dep_manager.suggest_auto_setup()
        if suggestion:
            print(Colors.system(suggestion))
            print()

    try:
        config = None
        config_path = Path(args.config) if args.config else None
        config = get_config(config_path)

        if config:
            color_config = config.get_section("colors")
            Colors.configure(color_config)

        if config:
            if args.config:
                print(Colors.system(f"Loaded configuration from: {args.config}"))
            else:
                global_config = Path.home() / ".chatrc"
                project_config = Path.cwd() / ".chatrc"
                if project_config.exists():
                    print(Colors.system(f"Loaded configuration from: {project_config}"))
                elif global_config.exists():
                    print(Colors.system(f"Loaded configuration from: {global_config}"))

        if agent_path != args.agent:
            print(Colors.system(f"Resolved alias '{args.agent}' → {agent_path}"))
        print(Colors.system(f"Loading agent from: {agent_path}"))
        agent, agent_name, agent_description = load_agent_module(agent_path)

        setup_logging(agent_name)

        print(Colors.success(f"Agent loaded successfully: {agent_name}"))
        logger.info(f"Agent loaded successfully: {agent_name} - {agent_description}")

        def create_fresh_agent():
            """Factory function to create a fresh agent instance."""
            new_agent, _, _ = load_agent_module(agent_path)
            return new_agent

        chat_loop = ChatLoop(
            agent,
            agent_name,
            agent_description,
            agent_factory=create_fresh_agent,
            agent_path=str(agent_path),
            config=config,
        )

        if args.resume:
            chat_loop.resume_session_ref = args.resume
        else:
            chat_loop.resume_session_ref = None

        chat_loop.run()

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
