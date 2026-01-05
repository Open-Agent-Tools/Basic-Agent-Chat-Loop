"""Response renderer for displaying agent responses in the terminal.

Handles formatting and display of agent responses with support for:
- Rich markdown rendering
- Plain text with colorization
- Visual separators for final responses
- Agent name headers
"""

from typing import TYPE_CHECKING, Optional

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


class ResponseRenderer:
    """Renderer for formatting and displaying agent responses.

    Supports multiple display modes:
    - Rich markdown rendering (when enabled)
    - Plain text with ANSI colorization
    - Visual separators for final responses
    - Streaming text display
    """

    def __init__(
        self,
        agent_name: str,
        use_rich: bool = True,
        console: Optional["Console"] = None,
        harmony_processor: Optional[object] = None,
        colors_module: Optional[type["Colors"]] = None,
    ):
        """Initialize the response renderer.

        Args:
            agent_name: Name of the agent for header display
            use_rich: Whether to use rich markdown rendering
            console: Rich Console instance (required if use_rich=True)
            harmony_processor: Optional HarmonyProcessor for format detection
            colors_module: Colors class for text colorization (required)
        """
        if not colors_module:
            raise ValueError("colors_module is required for ResponseRenderer")

        self.agent_name = agent_name
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = console if self.use_rich else None
        self.harmony_processor = harmony_processor
        self.colors: type[Colors] = colors_module  # Guaranteed to be non-None here

        # Debug logging for Windows troubleshooting
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("ResponseRenderer initialized:")
        logger.debug(f"  use_rich (param): {use_rich}")
        logger.debug(f"  RICH_AVAILABLE: {RICH_AVAILABLE}")
        logger.debug(f"  self.use_rich: {self.use_rich}")
        logger.debug(f"  console provided: {console is not None}")
        logger.debug(f"  self.console: {self.console is not None}")

    def render_agent_header(self) -> None:
        """Print the agent name header at the start of a response.

        Displays: "\n<AgentName>: " in blue color
        """
        print(f"\n{self.colors.agent(self.agent_name)}: ", end="", flush=True)

    def render_streaming_text(self, text: str) -> None:
        """Display text during streaming (real-time display).

        Only displays if NOT using rich mode and NOT using harmony processor,
        as those require post-processing before display.

        Args:
            text: Text chunk to display
        """
        if not self.use_rich and not self.harmony_processor:
            # Apply colorization for tool messages during streaming
            formatted_text = self.colors.format_agent_response(text)
            print(formatted_text, end="", flush=True)

    def should_skip_streaming_display(self) -> bool:
        """Check if streaming display should be skipped.

        Returns:
            True if using rich mode or harmony processor (requires post-processing)
        """
        return self.use_rich or self.harmony_processor is not None

    def render_final_response(
        self, display_text: str, first_token_received: bool
    ) -> None:
        """Render the final response after streaming completes.

        Handles:
        - Visual separator (if streaming occurred)
        - Rich markdown rendering (if enabled)
        - Plain text with colorization (if rich disabled)

        Args:
            display_text: The final response text to display
            first_token_received: Whether any tokens were received during streaming
        """
        if not display_text.strip():
            return

        # Add visual separator when streaming occurred
        if first_token_received:
            print("\n")
            print(self.colors.success("─── Final Response ───"))

        # Render using rich markdown or plain text
        if self.use_rich and self.console:
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
        assert self.console is not None  # Only called when use_rich is True
        self.console.print(md)

    def _render_plain_text(self, text: str) -> None:
        """Render text as plain text with colorization.

        Args:
            text: Text to render
        """
        formatted_response = self.colors.format_agent_response(text)
        print(formatted_response)
