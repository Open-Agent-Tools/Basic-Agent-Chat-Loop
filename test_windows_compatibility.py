#!/usr/bin/env python3
"""
Comprehensive Windows Compatibility Test Suite

Tests the Windows-specific features added in commit 481617e:
1. Windows VT mode enablement for ANSI color support
2. Python version requirement bump to 3.10+
3. Cross-platform compatibility
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode


class TestWindowsVTMode(unittest.TestCase):
    """Test Windows Virtual Terminal Processing enablement."""

    def test_non_windows_returns_true(self):
        """On non-Windows platforms, should return True immediately."""
        with patch("sys.platform", "darwin"):
            result = enable_windows_vt_mode()
            self.assertTrue(result)

        with patch("sys.platform", "linux"):
            result = enable_windows_vt_mode()
            self.assertTrue(result)

    def test_windows_ctypes_import_failure(self):
        """When ctypes import fails on Windows, should return False."""
        with patch("sys.platform", "win32"):
            with patch("builtins.__import__", side_effect=ImportError("ctypes not available")):
                result = enable_windows_vt_mode()
                self.assertFalse(result)

    @patch("sys.platform", "win32")
    def test_windows_vt_mode_already_enabled(self):
        """When VT mode is already enabled, should return True."""
        # Mock ctypes module
        mock_ctypes = MagicMock()
        mock_kernel32 = MagicMock()
        mock_ctypes.windll.kernel32 = mock_kernel32

        # Mock GetStdHandle
        mock_handle = 123
        mock_kernel32.GetStdHandle.return_value = mock_handle

        # Mock GetConsoleMode - VT mode already enabled (bit 0x0004 set)
        mock_mode = MagicMock()
        mock_mode.value = 0x0007  # Has VT bit set (0x0004)
        mock_ctypes.c_ulong.return_value = mock_mode
        mock_kernel32.GetConsoleMode.return_value = True

        with patch.dict("sys.modules", {"ctypes": mock_ctypes}):
            result = enable_windows_vt_mode()
            self.assertTrue(result)

    @patch("sys.platform", "win32")
    def test_windows_vt_mode_enable_success(self):
        """When VT mode needs enabling and succeeds, should return True."""
        mock_ctypes = MagicMock()
        mock_kernel32 = MagicMock()
        mock_ctypes.windll.kernel32 = mock_kernel32

        mock_handle = 123
        mock_kernel32.GetStdHandle.return_value = mock_handle

        # VT mode not enabled initially
        mock_mode = MagicMock()
        mock_mode.value = 0x0003  # VT bit not set
        mock_ctypes.c_ulong.return_value = mock_mode
        mock_kernel32.GetConsoleMode.return_value = True

        # SetConsoleMode succeeds
        mock_kernel32.SetConsoleMode.return_value = True

        with patch.dict("sys.modules", {"ctypes": mock_ctypes}):
            result = enable_windows_vt_mode()
            self.assertTrue(result)
            mock_kernel32.SetConsoleMode.assert_called_once()

    @patch("sys.platform", "win32")
    def test_windows_vt_mode_enable_failure(self):
        """When VT mode enable fails, should return False."""
        mock_ctypes = MagicMock()
        mock_kernel32 = MagicMock()
        mock_ctypes.windll.kernel32 = mock_kernel32

        mock_handle = 123
        mock_kernel32.GetStdHandle.return_value = mock_handle

        mock_mode = MagicMock()
        mock_mode.value = 0x0003
        mock_ctypes.c_ulong.return_value = mock_mode
        mock_kernel32.GetConsoleMode.return_value = True

        # SetConsoleMode fails
        mock_kernel32.SetConsoleMode.return_value = False

        with patch.dict("sys.modules", {"ctypes": mock_ctypes}):
            result = enable_windows_vt_mode()
            self.assertFalse(result)

    @patch("sys.platform", "win32")
    def test_windows_get_console_mode_failure(self):
        """When GetConsoleMode fails, should return False."""
        mock_ctypes = MagicMock()
        mock_kernel32 = MagicMock()
        mock_ctypes.windll.kernel32 = mock_kernel32

        mock_handle = 123
        mock_kernel32.GetStdHandle.return_value = mock_handle

        # GetConsoleMode fails
        mock_kernel32.GetConsoleMode.return_value = False

        with patch.dict("sys.modules", {"ctypes": mock_ctypes}):
            result = enable_windows_vt_mode()
            self.assertFalse(result)

    @patch("sys.platform", "win32")
    def test_windows_exception_handling(self):
        """When any exception occurs, should return False gracefully."""
        mock_ctypes = MagicMock()
        mock_kernel32 = MagicMock()
        mock_ctypes.windll.kernel32 = mock_kernel32

        # Simulate exception during API call
        mock_kernel32.GetStdHandle.side_effect = Exception("Windows API error")

        with patch.dict("sys.modules", {"ctypes": mock_ctypes}):
            result = enable_windows_vt_mode()
            self.assertFalse(result)


class TestPythonVersionRequirement(unittest.TestCase):
    """Test Python 3.10+ requirement."""

    def test_current_python_version(self):
        """Current Python version should be 3.10 or higher."""
        self.assertGreaterEqual(
            sys.version_info[:2],
            (3, 10),
            f"Python version {sys.version_info.major}.{sys.version_info.minor} "
            f"does not meet the minimum requirement of 3.10"
        )

    def test_version_info_accessible(self):
        """sys.version_info should be accessible and valid."""
        self.assertIsNotNone(sys.version_info)
        self.assertGreaterEqual(len(sys.version_info), 2)
        self.assertIsInstance(sys.version_info.major, int)
        self.assertIsInstance(sys.version_info.minor, int)


class TestANSIColorSupport(unittest.TestCase):
    """Test ANSI color code support."""

    def test_ansi_codes_defined(self):
        """ANSI color codes should be properly defined in ui_components."""
        from basic_agent_chat_loop.components.ui_components import Colors

        # Test basic color access via class attributes
        self.assertIsNotNone(Colors.USER)
        self.assertIsNotNone(Colors.AGENT)
        self.assertIsNotNone(Colors.ERROR)
        self.assertIsNotNone(Colors.SUCCESS)

    def test_ansi_codes_format(self):
        """ANSI codes should follow proper escape sequence format."""
        from basic_agent_chat_loop.components.ui_components import Colors

        # Test that default color codes use ANSI format
        color_code = Colors.SUCCESS
        # ANSI codes start with \033[ or \x1b[
        self.assertTrue(
            color_code.startswith("\033[") or color_code.startswith("\x1b["),
            f"Color code '{color_code}' doesn't start with ANSI escape sequence"
        )


class TestPlatformDetection(unittest.TestCase):
    """Test platform detection and cross-platform compatibility."""

    def test_platform_detection(self):
        """Platform should be correctly detected."""
        self.assertIn(sys.platform, ["darwin", "linux", "win32", "cygwin"])

    def test_platform_specific_imports(self):
        """Platform-specific imports should not break on other platforms."""
        # This should work on all platforms
        from basic_agent_chat_loop import chat_loop
        self.assertTrue(hasattr(chat_loop, "enable_windows_vt_mode"))

    def test_readline_availability(self):
        """Readline should be available (readline or pyreadline3)."""
        from basic_agent_chat_loop.components import input_handler
        # READLINE_AVAILABLE can be True or False, both are valid
        self.assertIsInstance(input_handler.READLINE_AVAILABLE, bool)


class TestWindowsSpecificDependencies(unittest.TestCase):
    """Test Windows-specific dependency handling."""

    def test_pyreadline3_conditional_import(self):
        """pyreadline3 should only be required on Windows."""
        # On non-Windows, this test just verifies the condition exists
        if sys.platform == "win32":
            try:
                import pyreadline3
                self.assertIsNotNone(pyreadline3)
            except ImportError:
                self.fail("pyreadline3 should be available on Windows")
        else:
            # On non-Windows, pyreadline3 is not required
            self.assertNotEqual(sys.platform, "win32")


class TestMainEntryPoint(unittest.TestCase):
    """Test that main() calls enable_windows_vt_mode."""

    @patch("basic_agent_chat_loop.chat_loop.ChatLoop")
    @patch("basic_agent_chat_loop.chat_loop.enable_windows_vt_mode")
    def test_main_calls_enable_vt_mode(self, mock_enable_vt, mock_chat_loop):
        """main() should call enable_windows_vt_mode() early."""
        from basic_agent_chat_loop.chat_loop import main

        # Mock sys.argv to prevent argument parsing issues
        with patch("sys.argv", ["chat_loop"]):
            try:
                # Call main - it will fail due to missing config, but that's OK
                main()
            except SystemExit:
                pass  # Expected when no agent is provided
            except Exception:
                pass  # Other exceptions are fine for this test

        # Verify enable_windows_vt_mode was called
        mock_enable_vt.assert_called_once()


def run_tests():
    """Run all tests and generate a report."""
    print("=" * 70)
    print("Windows Compatibility Test Suite")
    print("Commit: 481617e - Windows VT Support")
    print("=" * 70)
    print(f"\nPlatform: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestWindowsVTMode))
    suite.addTests(loader.loadTestsFromTestCase(TestPythonVersionRequirement))
    suite.addTests(loader.loadTestsFromTestCase(TestANSIColorSupport))
    suite.addTests(loader.loadTestsFromTestCase(TestPlatformDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestWindowsSpecificDependencies))
    suite.addTests(loader.loadTestsFromTestCase(TestMainEntryPoint))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
