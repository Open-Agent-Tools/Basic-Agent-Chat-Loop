"""Response renderer for displaying agent responses in the terminal.

Handles formatting and display of agent responses with support for:
- Rich markdown rendering
- Plain text with colorization
- Visual separators for final responses
- Agent name headers

Uses OutputState enum to determine rendering strategy (streaming vs buffering).
"""

import logging
from typing import TYPE_CHECKING, Optional

from .output_mode import OutputState, determine_output_state

if TYPE_CHECKING:
    from .ui_components import Colors

try:
    from rich.console import Console
    from rich.markdown import Markdown

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None  # type: ignore
    Markdown = None  # type: ignore

logger = logging.getLogger(__name__)


class ResponseRenderer:
    """Renderer for formatting and displaying agent responses.

    Uses OutputState pattern to determine rendering strategy:
    - STREAMING: Print text immediately (plain text mode)
    - BUFFERING: Accumulate and render with Rich/Harmony

    This eliminates complex boolean logic and provides a single source
    of truth for output behavior.
    """

    def __init__(
        self,
        agent_name: str,
        console: Optional["Console"] = None,
        harmony_processor: Optional[object] = None,
        colors_module: Optional[type["Colors"]] = None,
    ):
        """Initialize the response renderer.

        Args:
            agent_name: Name of the agent for header display
            console: Rich Console instance (None if Rich not available)
            harmony_processor: Optional HarmonyProcessor for format detection
            colors_module: Colors class for text colorization (required)
        """
        if not colors_module:
            raise ValueError("colors_module is required for ResponseRenderer")

        self.agent_name = agent_name
        self.console = console
        self.harmony_processor = harmony_processor
        self.colors: type[Colors] = colors_module

        # Determine output state once at initialization
        # This is the single source of truth for rendering behavior
        self.output_state = determine_output_state(console, harmony_processor)

        logger.debug(f"ResponseRenderer initialized:")
        logger.debug(f"  agent_name: {agent_name}")
        logger.debug(f"  console: {console is not None}")
        logger.debug(f"  harmony: {harmony_processor is not None}")
        logger.debug(f"  output_state: {self.output_state.value}")

    def render_agent_header(self) -> None:
        """Print the agent name header at the start of a response.

        Displays: "\n<AgentName>: " in blue color
        """
        print(f"\n{self.colors.agent(self.agent_name)}: ", end="", flush=True)

    def render_streaming_text(self, text: str) -> None:
        """Display text during streaming (real-time display).

        Only displays if output_state is STREAMING (plain text mode).
        Skips display if BUFFERING (Rich/Harmony will render later).

        Args:
            text: Text chunk to display
        """
        if self.output_state.should_buffer():
            # Buffering mode - text will be rendered later
            logger.debug(
                f"SKIP streaming (buffering): state={self.output_state.value}, "
                f"text_len={len(text)}"
            )
            return

        # Streaming mode - print immediately
        logger.debug(
            f"PRINT streaming: state={self.output_state.value}, text_len={len(text)}"
        )
        formatted_text = self.colors.format_agent_response(text)
        print(formatted_text, end="", flush=True)

    def should_skip_streaming_display(self) -> bool:
        """Check if streaming display should be skipped.

        Returns:
            True if in BUFFERING mode (Rich/Harmony)
            False if in STREAMING mode (plain text)
        """
        return self.output_state.should_buffer()

    def render_final_response(
        self, display_text: str, first_token_received: bool
    ) -> None:
        """Render the final response after streaming completes.

        Handles:
        - Visual separator (if streaming occurred)
        - Rich markdown rendering (if console available)
        - Plain text with colorization (if no console)

        Args:
            display_text: The final response text to display
            first_token_received: Whether any tokens were received during streaming
        """
        if not display_text.strip():
            return

        # Add visual separator when streaming occurred in buffering mode
        # (In streaming mode, text was already printed, no separator needed)
        if first_token_received and self.output_state.should_buffer():
            print("\n")
            print(self.colors.success("─── Final Response ───"))

        # Render using rich markdown or plain text
        if self.console is not None:
            self._render_rich_markdown(display_text)
        else:
            self._render_plain_text(display_text)

    def _render_rich_markdown(self, text: str) -> None:
        """Render text as rich markdown.

        Args:
            text: Markdown text to render
        """
        print()  # New line after separator
        md = Markdown(text)
        assert self.console is not None  # Only called when console exists
        self.console.print(md)

    def _render_plain_text(self, text: str) -> None:
        """Render text as plain text with colorization.

        Args:
            text: Text to render
        """
        formatted_response = self.colors.format_agent_response(text)
        print(formatted_response)
