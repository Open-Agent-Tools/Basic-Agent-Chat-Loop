"""Session state management for chat loop.

Manages all session-related state including:
- Session ID generation
- Query counting
- Conversation history tracking
- Last query/response tracking (for copy commands)
- Accumulated usage tracking (for AWS Strands delta calculation)
"""

import time
from datetime import datetime


class SessionState:
    """Manages session state for a chat loop session.

    Tracks all mutable session state including query count, conversation history,
    last query/response for copy commands, and token usage for delta calculation.
    """

    def __init__(self, agent_name: str):
        """Initialize session state.

        Args:
            agent_name: Name of the agent for session ID generation
        """
        # Generate session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_agent_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        self.session_id = f"{safe_agent_name}_{timestamp}"

        # Query and conversation tracking
        self.query_count = 0
        self.conversation_markdown: list[str] = []

        # Last query/response for copy commands
        self.last_query = ""
        self.last_response = ""

        # Session timing
        self.session_start_time = time.time()

        # Accumulated usage tracking for AWS Strands delta calculation
        # (AWS Strands reports cumulative usage, we need deltas)
        self.last_accumulated_input = 0
        self.last_accumulated_output = 0

    def increment_query_count(self) -> int:
        """Increment query count and return new count.

        Returns:
            New query count after increment
        """
        self.query_count += 1
        return self.query_count

    def update_last_query(self, query: str) -> None:
        """Update the last user query (for copy command).

        Args:
            query: User query text
        """
        self.last_query = query

    def update_last_response(self, response: str) -> None:
        """Update the last agent response (for copy command).

        Args:
            response: Agent response text
        """
        self.last_response = response

    def add_conversation_entry(self, entry: str) -> None:
        """Add an entry to the conversation markdown history.

        Args:
            entry: Markdown-formatted conversation entry
        """
        self.conversation_markdown.append(entry)

    def clear_conversation_history(self) -> None:
        """Clear the conversation history (useful for reset/clear commands)."""
        self.conversation_markdown.clear()

    def get_session_duration(self) -> float:
        """Get session duration in seconds.

        Returns:
            Session duration in seconds since start
        """
        return time.time() - self.session_start_time

    def update_accumulated_usage(
        self, current_input: int, current_output: int
    ) -> tuple[int, int]:
        """Update accumulated usage and return delta.

        For AWS Strands agents that report cumulative usage, this calculates
        the delta from the last query.

        Args:
            current_input: Current cumulative input tokens
            current_output: Current cumulative output tokens

        Returns:
            Tuple of (delta_input, delta_output) tokens
        """
        delta_input = current_input - self.last_accumulated_input
        delta_output = current_output - self.last_accumulated_output

        # Update tracking
        self.last_accumulated_input = current_input
        self.last_accumulated_output = current_output

        return (delta_input, delta_output)

    def get_conversation_history(self) -> list[str]:
        """Get full conversation history.

        Returns:
            List of conversation entries in markdown format
        """
        return self.conversation_markdown.copy()

    def has_conversation_history(self) -> bool:
        """Check if conversation history exists.

        Returns:
            True if there are conversation entries
        """
        return len(self.conversation_markdown) > 0

    def has_last_query(self) -> bool:
        """Check if there is a last query to copy.

        Returns:
            True if last_query is not empty
        """
        return bool(self.last_query)

    def has_last_response(self) -> bool:
        """Check if there is a last response to copy.

        Returns:
            True if last_response is not empty
        """
        return bool(self.last_response)

    def reset(self, agent_name: str) -> None:
        """Reset session state (for clear command).

        Generates a new session ID and clears all tracked state.

        Args:
            agent_name: Name of the agent for new session ID generation
        """
        # Generate new session ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_agent_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        self.session_id = f"{safe_agent_name}_{timestamp}"

        # Reset counters
        self.query_count = 0
        self.conversation_markdown.clear()
        self.last_query = ""
        self.last_response = ""

        # Reset timing
        self.session_start_time = time.time()

        # Reset accumulated usage
        self.last_accumulated_input = 0
        self.last_accumulated_output = 0

    def get_state_summary(self) -> dict:
        """Get a summary of current session state.

        Returns:
            Dict with session state information
        """
        return {
            "session_id": self.session_id,
            "query_count": self.query_count,
            "conversation_entries": len(self.conversation_markdown),
            "session_duration": self.get_session_duration(),
            "has_last_query": self.has_last_query(),
            "has_last_response": self.has_last_response(),
            "accumulated_input": self.last_accumulated_input,
            "accumulated_output": self.last_accumulated_output,
        }
