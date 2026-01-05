"""Session restoration component for resuming previous conversations.

Handles loading session summaries and restoring agent context from saved sessions.
Extracted from chat_loop.py to improve modularity and reduce file size.
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .session_manager import SessionManager
    from .session_state import SessionState
    from .token_tracker import TokenTracker
    from .ui_components import Colors, StatusBar

# Rough token-to-word ratio for restoration token estimation
TOKEN_TO_WORD_RATIO = 1.3

logger = logging.getLogger(__name__)

try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore
    Markdown = None  # type: ignore
    Spinner = None  # type: ignore
    Live = None  # type: ignore


class SessionRestorer:
    """Handles session restoration and context loading.

    Coordinates loading previous sessions, extracting summaries,
    sending restoration prompts to the agent, and initializing
    the new session with restored context.
    """

    def __init__(
        self,
        agent: Any,
        agent_name: str,
        agent_path: str,
        session_manager: "SessionManager",
        session_state: "SessionState",
        token_tracker: "TokenTracker",
        colors_module: type["Colors"],
        use_rich: bool = False,
        console: Optional["Console"] = None,
        status_bar: Optional["StatusBar"] = None,
    ):
        """Initialize the session restorer.

        Args:
            agent: The agent instance to send restoration prompts to
            agent_name: Name of the agent
            agent_path: Path to the agent file
            session_manager: Session manager for loading session files
            session_state: Session state for tracking current session
            token_tracker: Token tracker for formatting token counts
            colors_module: Colors class for terminal colorization
            use_rich: Whether to use rich rendering
            console: Optional Rich console for rendering
            status_bar: Optional status bar for updates
        """
        self.agent = agent
        self.agent_name = agent_name
        self.agent_path = agent_path
        self.session_manager = session_manager
        self.session_state = session_state
        self.token_tracker = token_tracker
        self.colors: type[Colors] = colors_module
        self.use_rich = use_rich
        self.console = console
        self.status_bar = status_bar

        # Track parent session ID for resumed sessions
        self._resumed_from: Optional[str] = None
        # Store previous summary for progressive summarization
        self._previous_summary: Optional[str] = None

        logger.debug("SessionRestorer initialized")
        logger.debug(f"  agent_name: {agent_name}")
        logger.debug(f"  use_rich: {use_rich}")

    def _build_restoration_prompt(
        self,
        session_id: str,
        query_count: int,
        total_tokens: int,
        summary: str,
        session_file: Optional[Path] = None,
        resumed_from: Optional[str] = None,
    ) -> str:
        """Build restoration prompt for session resumption or compaction.

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

    def _extract_text_from_event(self, event: Any) -> str:
        """Extract text content from a streaming event.

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
        """Stream response from agent and accumulate text.

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
        """Resolve session ID from numeric index or direct ID.

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
                print(self.colors.error(f"Invalid session number: {session_num}"))
                print(f"Valid range: 1-{len(sessions)}")
                return None

            # Get actual session_id from the list (1-indexed)
            session_info = sessions[session_num - 1]
            return session_info.session_id

        return session_id

    def _load_and_validate_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """Load session data and validate it's restorable.

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
            print(self.colors.error(f"⚠️  Session file not found: {session_id}"))
            return None

        # Extract metadata from markdown
        metadata = self._extract_metadata_from_markdown(session_file)
        if not metadata:
            print(self.colors.error("Failed to parse session metadata"))
            return None

        # Extract summary
        summary = self._extract_summary_from_markdown(session_file)
        if not summary:
            print(
                self.colors.error(
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
            self.colors.success(
                f"✓ Found: {metadata.get('agent_name', 'Unknown')} - {session_id}"
            )
        )
        print(
            self.colors.system(
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
        """Check if session agent matches current agent, prompt user if different.

        Args:
            metadata: Session metadata dict

        Returns:
            True if user confirms continuation, False otherwise
        """
        # Check if agent path matches (graceful warning)
        if "agent_path" in metadata and metadata["agent_path"] != self.agent_path:
            print(
                self.colors.system(
                    f"\n⚠️  Different agent detected:\n"
                    f"  Session created with: {metadata['agent_path']}\n"
                    f"  Current agent:        {self.agent_path}"
                )
            )
            confirm = input(self.colors.system("Continue? (y/n): "))
            if confirm.lower() != "y":
                print(self.colors.system("Resume cancelled"))
                return False

        return True

    async def _send_restoration_prompt(
        self, restoration_prompt: str
    ) -> tuple[str, float]:
        """Send restoration prompt to agent and get response.

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
        """Display agent's restoration acknowledgment.

        Args:
            restoration_response: Agent's response to display
        """
        print(self.colors.agent(f"{self.agent_name}:"), end=" ")
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
        response_streamer: Any,  # Avoid circular import
    ) -> None:
        """Initialize new session with restored context.

        Args:
            old_session_id: Previous session ID
            new_session_id: New session ID for resumed session
            restoration_response: Agent's restoration response
            restoration_duration: Time taken for restoration
            restoration_input_tokens: Approximate input tokens
            restoration_output_tokens: Approximate output tokens
            session_data: Dict with query_count, total_tokens, summary, session_file
            response_streamer: ResponseStreamer instance for resetting token counts
        """
        # Initialize new session
        self.session_state.session_id = new_session_id
        self._resumed_from = old_session_id  # Track parent session
        self._previous_summary = session_data["summary"]  # Store for next compaction

        # Reset conversation but add restoration exchange
        self.session_state.conversation_markdown = [
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
        self.session_state.query_count = 0
        response_streamer.total_input_tokens = 0
        response_streamer.total_output_tokens = 0
        self.session_state.session_start_time = time.time()

        # Update status bar if enabled
        if self.status_bar:
            self.status_bar.query_count = 0
            self.status_bar.start_time = self.session_state.session_start_time

        print(self.colors.success("✓ Session restored! Ready to continue."))
        print()

        logger.info(f"Successfully restored session: {old_session_id}")

    async def restore_session(self, session_id: str, response_streamer: Any) -> bool:
        """Restore a previous session by loading its summary and creating a new session.

        Args:
            session_id: Session ID or number from sessions list
            response_streamer: ResponseStreamer instance for token tracking

        Returns:
            True if successful, False otherwise
        """
        try:
            print(self.colors.system("\n📋 Loading session..."))

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
            print(self.colors.system("🔄 Restoring context..."))
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
                response_streamer=response_streamer,
            )

            return True

        except Exception as e:
            logger.error(f"Failed to restore session: {e}", exc_info=True)
            print(self.colors.error(f"\n⚠️  Failed to restore session: {e}"))
            return False

    def _extract_summary_from_markdown(self, file_path: Path) -> Optional[str]:
        """Extract summary block from a markdown file.

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
        """Extract session metadata from markdown file headers.

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

    @property
    def resumed_from(self) -> Optional[str]:
        """Get the ID of the parent session if this is a resumed session."""
        return self._resumed_from

    @property
    def previous_summary(self) -> Optional[str]:
        """Get the summary from the previous session for progressive summarization."""
        return self._previous_summary
