"""Response renderer for displaying agent header in terminal.

Simplified for v1.8.0 - only handles agent name header display.
Agent library handles all response rendering naturally.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ui_components import Colors

logger = logging.getLogger(__name__)


class ResponseRenderer:
    """Renderer for displaying agent header.

    Simplified in v1.8.0 to only handle agent name display.
    Agent library handles all response output naturally.
    """

    def __init__(
        self,
        agent_name: str,
        colors_module: type["Colors"],
    ):
        """Initialize the response renderer.

        Args:
            agent_name: Name of the agent for header display
            colors_module: Colors class for text colorization
        """
        self.agent_name = agent_name
        self.colors = colors_module

        logger.debug(f"ResponseRenderer initialized for agent: {agent_name}")

    def render_agent_header(self) -> None:
        """Print the agent name header at the start of a response.

        Displays: "\n<AgentName>: " in blue color
        """
        print(f"\n{self.colors.agent(self.agent_name)}: ", end="", flush=True)
