"""Smart stdout filter for selectively suppressing output.

Allows interactive prompts to pass through while suppressing
accumulated agent output during streaming.
"""

import io
import re


class SmartStdoutFilter(io.StringIO):
    """Stdout wrapper that detects and passes through interactive prompts.

    Suppresses accumulated agent output during streaming but allows
    tool confirmation prompts to display normally.
    """

    def __init__(self, real_stdout):
        """Initialize the filter.

        Args:
            real_stdout: The real sys.stdout to pass prompts through to
        """
        super().__init__()
        self.real_stdout = real_stdout
        self.buffer = ""

        # Patterns that indicate an interactive prompt
        self.prompt_patterns = [
            r'\? *$',              # Ends with ? (e.g., "Delete file?")
            r'[Yy]/[Nn] *:? *$',   # Contains Y/n (e.g., "Continue? Y/n:")
            r': *$',               # Ends with : (e.g., "Enter name:")
            r'\[.*\] *:? *$',      # Ends with [option]: (e.g., "Choose [Y/n]:")
            r'> *$',               # Ends with > (shell-like prompt)
        ]

    def write(self, text: str) -> int:
        """Write text, passing through if it looks like a prompt.

        Args:
            text: Text to write

        Returns:
            Number of characters written
        """
        if not text:
            return 0

        # Accumulate text for pattern detection
        self.buffer += text

        # Check if this looks like an interactive prompt
        if self._looks_like_prompt():
            # Pass through to real stdout
            self.real_stdout.write(text)
            self.real_stdout.flush()
            return len(text)

        # Otherwise suppress it (accumulate in buffer)
        return super().write(text)

    def _looks_like_prompt(self) -> bool:
        """Check if buffered text looks like an interactive prompt.

        Returns:
            True if text appears to be a prompt
        """
        # Get the last line (prompts are typically on their own line)
        lines = self.buffer.split('\n')
        last_line = lines[-1] if lines else ""

        # Also check the previous line in case of multi-line prompts
        prev_line = lines[-2] if len(lines) > 1 else ""

        # Check both lines against patterns
        for pattern in self.prompt_patterns:
            if re.search(pattern, last_line):
                return True
            if re.search(pattern, prev_line):
                return True

        return False

    def flush(self):
        """Flush both buffers."""
        super().flush()
        self.real_stdout.flush()

    def get_suppressed_output(self) -> str:
        """Get the output that was suppressed.

        Useful for debugging what was filtered out.

        Returns:
            The suppressed output text
        """
        return self.getvalue()
