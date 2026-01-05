"""Session persistence component for saving and compacting conversations.

Handles saving conversation history to markdown files with summaries
and compacting sessions for context management.
Extracted from chat_loop.py to improve modularity and reduce file size.
"""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .session_manager import SessionManager
    from .session_restorer import SessionRestorer
    from .session_state import SessionState
    from .token_tracker import TokenTracker
    from .ui_components import Colors

# Rough token-to-word ratio for restoration token estimation
TOKEN_TO_WORD_RATIO = 1.3

logger = logging.getLogger(__name__)


class SessionPersister:
    """Handles saving and compacting conversation sessions.

    Coordinates saving conversation history to disk, generating
    AI summaries for resumption, and compacting sessions to
    manage context length.
    """

    def __init__(
        self,
        agent: Any,
        agent_name: str,
        agent_path: str,
        session_manager: "SessionManager",
        session_state: "SessionState",
        session_restorer: "SessionRestorer",
        token_tracker: "TokenTracker",
        colors_module: type["Colors"],
        response_streamer: Any,  # Avoid circular import
    ):
        """Initialize the session persister.

        Args:
            agent: The agent instance for generating summaries
            agent_name: Name of the agent
            agent_path: Path to the agent file
            session_manager: Session manager for file operations
            session_state: Session state for tracking conversation
            session_restorer: Session restorer for compaction operations
            token_tracker: Token tracker for formatting token counts
            colors_module: Colors class for terminal colorization
            response_streamer: Response streamer for token tracking
        """
        self.agent = agent
        self.agent_name = agent_name
        self.agent_path = agent_path
        self.session_manager = session_manager
        self.session_state = session_state
        self.session_restorer = session_restorer
        self.token_tracker = token_tracker
        self.colors: type[Colors] = colors_module
        self.response_streamer = response_streamer

        logger.debug("SessionPersister initialized")
        logger.debug(f"  agent_name: {agent_name}")

    def _extract_text_from_event(self, event: Any) -> str:
        """Extract text content from a streaming event.

        Handles various event formats from different agent implementations.

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

    async def _generate_session_summary(
        self, previous_summary: Optional[str] = None
    ) -> Optional[str]:
        """Generate a structured summary of the current session.

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
            prompt_parts.extend(self.session_state.conversation_markdown)
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
                self.colors.system("📝 Generating session summary... "),
                end="",
                flush=True,
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
        """Save conversation as markdown file with optional auto-generated summary.

        Args:
            session_id: Optional custom session ID.
                Uses self.session_state.session_id if not provided.
            generate_summary: Whether to generate an AI summary of the session.
                Defaults to False to avoid generating summaries after every turn.
                Should be True when explicitly compacting or ending a session.

        Returns:
            True if save was successful, False otherwise
        """
        # Only save if there's conversation content
        if not self.session_state.conversation_markdown:
            logger.debug("No conversation to save")
            return False

        # Use provided session_id or fall back to self.session_state.session_id
        save_session_id = session_id or self.session_state.session_id

        try:
            # Generate summary for the session (only if requested)
            summary = None
            if generate_summary:
                summary = await self._generate_session_summary(
                    previous_summary=self.session_restorer.previous_summary
                )

            # Ensure sessions directory exists
            sessions_dir = self.session_manager.sessions_dir
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Build full markdown with header
            md_path = sessions_dir / f"{save_session_id}.md"
            total_tokens = (
                self.response_streamer.total_input_tokens
                + self.response_streamer.total_output_tokens
            )

            markdown_content = [
                f"# {self.agent_name} Conversation\n\n",
                f"**Session ID:** {save_session_id}\n\n",
                f"**Date:** {datetime.now().isoformat()}\n\n",
                f"**Agent:** {self.agent_name}\n\n",
                f"**Agent Path:** {self.agent_path}\n\n",
                f"**Total Queries:** {self.session_state.query_count}\n\n",
            ]

            # Add "Resumed from" info if this session was resumed
            if self.session_restorer.resumed_from:
                markdown_content.append(
                    f"**Resumed From:** {self.session_restorer.resumed_from}\n\n"
                )

            markdown_content.append("---\n")

            # Add conversation content
            markdown_content.extend(self.session_state.conversation_markdown)

            # Add summary if generated successfully
            if summary:
                markdown_content.append("\n")
                markdown_content.append(summary)
                markdown_content.append("\n")
            elif generate_summary:
                # Only warn if we tried to generate a summary but it failed
                logger.warning("Session saved without summary - resume will not work")
                print(
                    self.colors.system(
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
                self.session_state.conversation_markdown[1]
                .replace("**You:** ", "")
                .strip()
                if len(self.session_state.conversation_markdown) > 1
                else ""
            )
            preview = first_query[:100]
            if len(first_query) > 100:
                preview += "..."

            self.session_manager._update_index_simple(
                session_id=save_session_id,
                agent_name=self.agent_name,
                agent_path=self.agent_path,
                query_count=self.session_state.query_count,
                total_tokens=total_tokens,
                preview=preview,
            )

            logger.info(f"Conversation saved: {save_session_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save conversation: {e}", exc_info=True)
            print(self.colors.error(f"\n⚠️  Could not save conversation: {e}"))
            return False

    def show_save_confirmation(self, session_id: str):
        """Show user-friendly save confirmation with file paths.

        Args:
            session_id: ID of the saved session
        """
        save_dir = self.session_manager.sessions_dir
        md_path = save_dir / f"{session_id}.md"

        print()
        print(self.colors.success("✓ Conversation saved successfully!"))
        print()
        print(self.colors.system(f"  Session ID: {session_id}"))
        print(self.colors.system(f"  File:       {md_path}"))
        print(self.colors.system(f"  Queries:    {self.session_state.query_count}"))

        # Show token count if available
        total_tokens = (
            self.response_streamer.total_input_tokens
            + self.response_streamer.total_output_tokens
        )
        if total_tokens > 0:
            print(
                self.colors.system(
                    f"  Tokens:     {self.token_tracker.format_tokens(total_tokens)}"
                )
            )
        print()

    async def handle_compact_command(self):
        """Compact current session and continue in new session.

        This command:
        1. Saves current session with summary
        2. Extracts the summary
        3. Starts a new session with the summary as context
        4. Agent acknowledges the restored context
        """
        # Check if there's anything to compact
        if not self.session_state.conversation_markdown:
            print(
                self.colors.system(
                    "No conversation to compact yet. Start chatting first!"
                )
            )
            return

        try:
            # Save current session with summary
            print(self.colors.system("\n📋 Compacting current session..."))
            old_session_id = self.session_state.session_id
            old_query_count = self.session_state.query_count
            old_total_tokens = (
                self.response_streamer.total_input_tokens
                + self.response_streamer.total_output_tokens
            )

            # Generate summary for compaction
            success = await self.save_conversation(generate_summary=True)
            if not success:
                print(self.colors.error("Failed to save session for compaction"))
                return

            # Extract summary from saved file
            sessions_dir = self.session_manager.sessions_dir
            saved_file = sessions_dir / f"{old_session_id}.md"
            summary = self.session_restorer._extract_summary_from_markdown(saved_file)

            if not summary:
                print(
                    self.colors.error(
                        "Failed to extract summary - session saved but cannot compact"
                    )
                )
                return

            # Show save confirmation
            print(self.colors.success(f"✓ Saved session: {old_session_id}"))
            print(
                self.colors.system(
                    f"  ({old_query_count} queries, "
                    f"{self.token_tracker.format_tokens(old_total_tokens)})"
                )
            )

            # Build and send restoration prompt using SessionRestorer
            print(self.colors.system("🔄 Starting new session with summary..."))
            print()

            restoration_prompt = self.session_restorer._build_restoration_prompt(
                session_id=old_session_id,
                query_count=old_query_count,
                total_tokens=old_total_tokens,
                summary=summary,
                session_file=saved_file,
            )

            (
                restoration_response,
                restoration_duration,
            ) = await self.session_restorer._send_restoration_prompt(restoration_prompt)

            # Display agent acknowledgment
            self.session_restorer._display_restoration_response(restoration_response)

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

            self.session_restorer._initialize_restored_session(
                old_session_id=old_session_id,
                new_session_id=new_session_id,
                restoration_response=restoration_response,
                restoration_duration=restoration_duration,
                restoration_input_tokens=restoration_input_tokens,
                restoration_output_tokens=restoration_output_tokens,
                session_data=session_data,
                response_streamer=self.response_streamer,
            )

            print(self.colors.success("✓ Session compacted and ready to continue!"))
            print()

        except Exception as e:
            logger.error(f"Failed to compact session: {e}", exc_info=True)
            print(self.colors.error(f"\n⚠️  Compaction failed: {e}"))
            print(self.colors.system("Your previous session was saved successfully."))
            print(self.colors.system("Continuing in current session..."))
