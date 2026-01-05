"""Input handling utilities for chat loop.

Provides multi-line input capabilities with features like:
- ESC key detection for cancellation
- Arrow key support for editing previous lines
- Cross-platform compatibility (Windows, Unix, Mac)
- Readline integration for history

Extracted from chat_loop.py to reduce file size and improve modularity.
"""

import logging
import sys
from typing import Optional

from .ui_components import Colors

logger = logging.getLogger(__name__)

# Check for readline availability (Unix/Mac/Linux)
try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

# Platform-specific imports for ESC key detection
# Note: imports are done inside functions to avoid unused import warnings
try:
    if sys.platform != "win32":
        TERMIOS_AVAILABLE = True
    else:
        TERMIOS_AVAILABLE = False
    ESC_KEY_SUPPORT = True
except Exception:
    ESC_KEY_SUPPORT = False
    TERMIOS_AVAILABLE = False


def get_char_with_esc_detection() -> Optional[str]:
    """Get a single character from stdin with ESC and arrow key detection.

    Returns:
        The character typed, None if ESC was pressed,
        "UP_ARROW" if up arrow was pressed, or "" if detection failed
    """
    if not ESC_KEY_SUPPORT:
        return ""  # Fall back to regular input

    try:
        if sys.platform == "win32":
            # Windows implementation
            import msvcrt

            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\xe0":  # Extended key prefix on Windows
                    if msvcrt.kbhit():
                        extended = msvcrt.getch()
                        if extended == b"H":  # Up arrow
                            return "UP_ARROW"
                    return ""
                elif char == b"\x1b":  # ESC key
                    return None
                return char.decode("utf-8", errors="ignore")
            return ""
        else:
            # Unix/Linux/Mac implementation
            import select
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
                if char == "\x1b":  # ESC or arrow key sequence
                    # Check if more characters follow (within 100ms)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq = sys.stdin.read(2)
                        if seq == "[A":  # Up arrow
                            return "UP_ARROW"
                        # Other arrow keys would be [B, [C, [D
                    # Just ESC pressed
                    return None
                return char
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        logger.debug(f"Key detection failed: {e}")
        return ""  # Fall back to regular input


def input_with_esc(prompt: str) -> Optional[str]:
    """Enhanced input() that detects ESC and arrow key presses.

    Args:
        prompt: The prompt to display

    Returns:
        The user's input string, None if ESC was pressed,
        or "UP_ARROW" if up arrow was pressed
    """
    if not ESC_KEY_SUPPORT:
        # Fall back to regular input
        return input(prompt)

    # Print the prompt
    print(prompt, end="", flush=True)

    # Try to detect ESC/arrows on first character
    first_char = get_char_with_esc_detection()

    if first_char is None:
        # ESC was pressed
        print()  # New line after ESC
        return None
    elif first_char == "UP_ARROW":
        # Up arrow was pressed
        print()  # New line
        return "UP_ARROW"
    elif first_char == "":
        # Detection not available or failed, use regular input
        # But we already printed the prompt, so use empty prompt
        return input("")
    else:
        # Got a character, print it and continue with regular input
        print(first_char, end="", flush=True)
        rest_of_line = input("")
        return first_char + rest_of_line


async def get_multiline_input() -> str:
    """Get multi-line input from user.

    Features:
    - Empty line submits
    - Ctrl+D or .cancel to cancel input
    - Up arrow or .back to edit previous line
    - Saves to history as single entry
    """
    lines: list[str] = []
    print(Colors.system("Multi-line mode:"))
    print(Colors.system("  • Empty line to submit"))
    print(Colors.system("  • Ctrl+D or .cancel to cancel"))
    if ESC_KEY_SUPPORT:
        print(Colors.system("  • ↑ or .back to edit previous line"))
    else:
        print(Colors.system("  • .back to edit previous line"))

    # Variable to hold text for pre-input hook
    prefill_text = None

    def startup_hook():
        """Readline startup hook to pre-fill input buffer."""
        nonlocal prefill_text
        if prefill_text is not None:
            readline.insert_text(prefill_text)
            readline.redisplay()

    # Set the startup hook if readline is available
    if READLINE_AVAILABLE:
        readline.set_startup_hook(startup_hook)

    try:
        while True:
            try:
                # Show line number for context
                line_num = len(lines) + 1
                prompt = Colors.user(f"{line_num:2d}│ ")

                # Use input_with_esc for ESC/arrow key detection
                line = input_with_esc(prompt)

                # Check if ESC was pressed (returns None)
                if line is None:
                    print(Colors.system("✗ Multi-line input cancelled (ESC)"))
                    return ""

                # Check if up arrow was pressed - edit previous line
                if line == "UP_ARROW":
                    if lines:
                        # Pop the last line and let user edit it
                        prev_line = lines.pop()
                        print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                        # Set prefill text for next input
                        prefill_text = prev_line
                    else:
                        print(Colors.system("⚠ No previous line to edit"))
                    continue

                # Clear prefill text after each input
                prefill_text = None

                # Check for cancel command
                if line.strip() == ".cancel":
                    print(Colors.system("✗ Multi-line input cancelled"))
                    return ""

                # Check for back command - edit previous line
                if line.strip() == ".back":
                    if lines:
                        # Pop the last line and let user edit it
                        prev_line = lines.pop()
                        print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                        # Set prefill text for next input
                        prefill_text = prev_line
                    else:
                        print(Colors.system("⚠ No previous line to edit"))
                    continue

                # Empty line submits (only if we have content)
                if not line.strip():
                    if lines:
                        break
                    else:
                        # First line can't be empty
                        print(Colors.system("⚠ Enter some text or use .cancel"))
                        continue

                # Add the line
                lines.append(line)

            except EOFError:
                # Ctrl+D cancels
                print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+D)"))
                return ""
            except KeyboardInterrupt:
                # Ctrl+C cancels
                print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+C)"))
                return ""

        result = "\n".join(lines)

        # Save to readline history as single entry for later recall
        if result and READLINE_AVAILABLE:
            readline.add_history(result)

        print(Colors.success(f"✓ {len(lines)} lines captured"))
        return result

    finally:
        # Clean up the startup hook
        if READLINE_AVAILABLE:
            readline.set_startup_hook(None)
