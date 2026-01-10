#!/usr/bin/env python3
"""
Test script for Windows VT mode compatibility.
This tests the enable_windows_vt_mode() function across platforms.
"""
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode


def test_windows_vt_mode():
    """Test the Windows VT mode enablement function."""
    print(f"Platform: {sys.platform}")
    print(f"Python version: {sys.version}")
    print("-" * 60)

    # Test the function
    result = enable_windows_vt_mode()
    print(f"\nenable_windows_vt_mode() returned: {result}")

    # On non-Windows platforms, it should return True immediately
    if sys.platform != "win32":
        expected = True
        if result == expected:
            print(f"✓ PASS: Non-Windows platform returns {expected} as expected")
        else:
            print(f"✗ FAIL: Expected {expected}, got {result}")
    else:
        # On Windows, it should attempt to enable VT mode
        print(f"Windows platform detected - VT mode enablement attempted")
        if result:
            print("✓ PASS: VT mode enabled successfully")
        else:
            print("✗ FAIL: VT mode could not be enabled")

    print("\n" + "=" * 60)
    print("Testing ANSI color codes:")
    print("=" * 60)

    # Test ANSI color codes
    colors = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "bright_white": "\033[97m",
        "reset": "\033[0m",
    }

    for name, code in colors.items():
        if name != "reset":
            print(f"{code}This text should be {name}{colors['reset']}")

    print("\n" + "=" * 60)
    print("Testing Rich library integration:")
    print("=" * 60)

    try:
        from rich.console import Console
        console = Console()
        console.print("[bold green]Rich library works correctly![/bold green]")
        console.print("[yellow]Yellow text[/yellow]")
        console.print("[cyan]Cyan text[/cyan]")
        print("✓ Rich library integration successful")
    except Exception as e:
        print(f"✗ Rich library test failed: {e}")


if __name__ == "__main__":
    test_windows_vt_mode()
