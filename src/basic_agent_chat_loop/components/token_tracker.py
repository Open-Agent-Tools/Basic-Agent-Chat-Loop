"""
Token tracking.

Tracks token usage per query and session.
"""


class TokenTracker:
    """Track token usage."""

    def __init__(self, model_name: str = "Unknown"):
        """
        Initialize token tracker.

        Args:
            model_name: Name of the model for pricing
        """
        self.model_name = model_name
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.query_history: list[tuple[int, int]] = []  # List of (input, output) tuples

    def add_usage(self, input_tokens: int, output_tokens: int):
        """
        Add token usage for a query.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.query_history.append((input_tokens, output_tokens))

    def get_total_tokens(self) -> int:
        """Get total tokens (input + output)."""
        return self.total_input_tokens + self.total_output_tokens

    def format_tokens(self, tokens: int) -> str:
        """Format token count with K/M suffix."""
        if tokens >= 1_000_000:
            return f"{tokens / 1_000_000:.1f}M"
        elif tokens >= 1_000:
            return f"{tokens / 1_000:.1f}K"
        else:
            return str(tokens)
