"""Output mode system for managing rendering strategies.

This module defines how agent responses are displayed to the user.
The OutputState enum determines whether text is streamed in real-time
or buffered for post-processing.
"""

from enum import Enum
from typing import Optional


class OutputState(Enum):
    """Output rendering state.

    STREAMING: Print text immediately as chunks arrive (plain text mode)
    BUFFERING: Accumulate text for post-processing (Rich/Harmony modes)
    """

    STREAMING = "streaming"  # Print as we go (plain text)
    BUFFERING = "buffering"  # Collect and render at end (Rich/Harmony)

    def should_buffer(self) -> bool:
        """Check if this mode requires buffering.

        Returns:
            True if text should be accumulated, False if printed immediately
        """
        return self == OutputState.BUFFERING

    def should_stream(self) -> bool:
        """Check if this mode streams text.

        Returns:
            True if text should be printed immediately
        """
        return self == OutputState.STREAMING


def determine_output_state(
    console: Optional[object], harmony_processor: Optional[object]
) -> OutputState:
    """Determine the appropriate output state based on available processors.

    Args:
        console: Rich Console instance (None if Rich not available)
        harmony_processor: HarmonyProcessor instance (None if not using Harmony)

    Returns:
        OutputState.BUFFERING if Rich or Harmony is enabled
        OutputState.STREAMING otherwise (plain text mode)

    Examples:
        >>> determine_output_state(Console(), None)
        OutputState.BUFFERING  # Rich enabled

        >>> determine_output_state(None, HarmonyProcessor())
        OutputState.BUFFERING  # Harmony enabled

        >>> determine_output_state(None, None)
        OutputState.STREAMING  # Plain text mode
    """
    if console is not None or harmony_processor is not None:
        return OutputState.BUFFERING
    return OutputState.STREAMING
