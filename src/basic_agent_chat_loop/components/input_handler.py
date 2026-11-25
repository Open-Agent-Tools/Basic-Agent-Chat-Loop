"""Input handling utilities for chat loop.

Provides multi-line input capabilities with features like:
- ESC key detection for cancellation
- Arrow key support for editing previous lines
- Cross-platform compatibility (Windows, Unix, Mac)
- Readline integration for history
"""

import logging
import sys
from typing import Optional

from .ui_components import Colors

logger = logging.getLogger(__name__)

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

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
        return ""

    try:
        if sys.platform == "win32":
            import msvcrt

            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\xe0":
                    if msvcrt.kbhit():
                        extended = msvcrt.getch()
                        if extended == b"H":
                            return "UP_ARROW"
                    return ""
                elif char == b"\x1b":
                    return None
                return char.decode("utf-8", errors="ignore")
            return ""
        else:
            import select
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
                if char == "\x1b":
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq = sys.stdin.read(2)
                        if seq == "[A":
                            return "UP_ARROW"
                    return None
                return char
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        logger.debug(f"Key detection failed: {e}")
        return ""


def input_with_esc(prompt: str) -> Optional[str]:
    """Enhanced input() that detects ESC and arrow key presses.

    Args:
        prompt: The prompt to display

    Returns:
        The user's input string, None if ESC was pressed,
        or "UP_ARROW" if up arrow was pressed
    """
    if not ESC_KEY_SUPPORT:
        return input(prompt)

    print(prompt, end="", flush=True)

    first_char = get_char_with_esc_detection()

    if first_char is None:
        print()
        return None
    elif first_char == "UP_ARROW":
        print()
        return "UP_ARROW"
    elif first_char == "":
        return input("")
    else:
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

    prefill_text = None

    def startup_hook():
        """Readline startup hook to pre-fill input buffer."""
        nonlocal prefill_text
        if prefill_text is not None:
            readline.insert_text(prefill_text)
            readline.redisplay()

    if READLINE_AVAILABLE:
        readline.set_startup_hook(startup_hook)

    try:
        while True:
            try:
                line_num = len(lines) + 1
                prompt = Colors.user(f"{line_num:2d}│ ")

                line = input_with_esc(prompt)

                if line is None:
                    print(Colors.system("✗ Multi-line input cancelled (ESC)"))
                    return ""

                if line == "UP_ARROW":
                    if lines:
                        prev_line = lines.pop()
                        print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                        prefill_text = prev_line
                    else:
                        print(Colors.system("⚠ No previous line to edit"))
                    continue

                prefill_text = None

                if line.strip() == ".cancel":
                    print(Colors.system("✗ Multi-line input cancelled"))
                    return ""

                if line.strip() == ".back":
                    if lines:
                        prev_line = lines.pop()
                        print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                        prefill_text = prev_line
                    else:
                        print(Colors.system("⚠ No previous line to edit"))
                    continue

                if not line.strip():
                    if lines:
                        break
                    else:
                        print(Colors.system("⚠ Enter some text or use .cancel"))
                        continue

                lines.append(line)

            except EOFError:
                print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+D)"))
                return ""
            except KeyboardInterrupt:
                print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+C)"))
                return ""

        result = "\n".join(lines)

        if result and READLINE_AVAILABLE:
            readline.add_history(result)

        print(Colors.success(f"✓ {len(lines)} lines captured"))
        return result

    finally:
        if READLINE_AVAILABLE:
            readline.set_startup_hook(None)
