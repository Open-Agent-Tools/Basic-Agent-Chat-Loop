"""Tests for UI components."""

import time

from basic_agent_chat_loop.components.ui_components import (
    COLOR_PALETTE,
    Colors,
    StatusBar,
)


class TestColors:
    """Test Colors class."""

    def test_default_colors_defined(self):
        """Test that default color codes are defined."""
        assert Colors.RESET
        assert Colors.BOLD
        assert Colors.DIM
        assert Colors.USER
        assert Colors.AGENT
        assert Colors.SYSTEM
        assert Colors.ERROR
        assert Colors.SUCCESS

    def test_user_formatting(self):
        """Test user text formatting."""
        result = Colors.user("Hello")
        assert "Hello" in result
        assert Colors.USER in result
        assert Colors.RESET in result

    def test_agent_formatting(self):
        """Test agent text formatting."""
        result = Colors.agent("Response")
        assert "Response" in result
        assert Colors.AGENT in result
        assert Colors.RESET in result

    def test_system_formatting(self):
        """Test system text formatting."""
        result = Colors.system("System message")
        assert "System message" in result
        assert Colors.SYSTEM in result
        assert Colors.RESET in result

    def test_error_formatting(self):
        """Test error text formatting."""
        result = Colors.error("Error occurred")
        assert "Error occurred" in result
        assert Colors.ERROR in result
        assert Colors.RESET in result

    def test_success_formatting(self):
        """Test success text formatting."""
        result = Colors.success("Success!")
        assert "Success!" in result
        assert Colors.SUCCESS in result
        assert Colors.RESET in result

    def test_configure_colors(self):
        """Test configuring custom colors."""
        original_user = Colors.USER
        original_agent = Colors.AGENT

        try:
            # Configure with custom colors
            custom_config = {
                "user": "\033[95m",  # Magenta
                "agent": "\033[96m",  # Cyan
                "error": "\033[93m",  # Yellow
            }

            Colors.configure(custom_config)

            assert Colors.USER == "\033[95m"
            assert Colors.AGENT == "\033[96m"
            assert Colors.ERROR == "\033[93m"

        finally:
            # Restore original colors
            Colors.USER = original_user
            Colors.AGENT = original_agent

    def test_configure_partial_colors(self):
        """Test that configure only updates provided colors."""
        original_system = Colors.SYSTEM

        try:
            # Configure only user color
            Colors.configure({"user": "\033[90m"})

            # User color should be updated
            assert Colors.USER == "\033[90m"

            # System color should remain unchanged
            assert Colors.SYSTEM == original_system

        finally:
            # Restore
            Colors.USER = "\033[97m"

    def test_configure_with_empty_dict(self):
        """Test configure with empty dictionary."""
        original_user = Colors.USER

        Colors.configure({})

        # Should remain unchanged
        assert Colors.USER == original_user

    def test_resolve_color_with_color_name(self):
        """Test resolving color names to ANSI codes."""
        assert Colors._resolve_color("bright_green") == COLOR_PALETTE["bright_green"]
        assert Colors._resolve_color("red") == COLOR_PALETTE["red"]
        assert Colors._resolve_color("blue") == COLOR_PALETTE["blue"]

    def test_resolve_color_with_ansi_code(self):
        """Test that ANSI codes are passed through unchanged."""
        ansi_code = "\033[95m"
        assert Colors._resolve_color(ansi_code) == ansi_code

    def test_configure_with_color_names(self):
        """Test configuring colors using named palette."""
        original_user = Colors.USER
        original_agent = Colors.AGENT

        try:
            config = {
                "user": "bright_white",
                "agent": "bright_green",
            }
            Colors.configure(config)

            assert Colors.USER == COLOR_PALETTE["bright_white"]
            assert Colors.AGENT == COLOR_PALETTE["bright_green"]

        finally:
            Colors.USER = original_user
            Colors.AGENT = original_agent

    def test_format_agent_response_with_tool_messages(self):
        """Test formatting agent response with tool messages."""
        text = (
            "Regular line\n[Thinking about the problem]\n"
            "Tool #1: Read file\nAnother regular line"
        )

        formatted = Colors.format_agent_response(text)

        # Should contain bright_green for tool/thinking lines
        assert COLOR_PALETTE["bright_green"] in formatted
        # Should contain agent color for regular lines
        assert Colors.AGENT in formatted
        # Should contain all original text
        assert "Regular line" in formatted
        assert "[Thinking about the problem]" in formatted
        assert "Tool #1: Read file" in formatted
        assert "Another regular line" in formatted

    def test_format_agent_response_no_tool_messages(self):
        """Test formatting response with no tool messages."""
        text = (
            "Just a regular response\nWith multiple lines\nNo special formatting needed"
        )

        formatted = Colors.format_agent_response(text)

        # Should use agent color throughout
        assert Colors.AGENT in formatted
        # Should not use bright_green since no tool messages
        # (Can't assert absence easily since AGENT might be bright_green)
        assert "Just a regular response" in formatted

    def test_format_agent_response_only_tool_messages(self):
        """Test formatting response with only tool messages."""
        text = "[Analyzing the code]\nTool #1: Grep search\nTool #2: Read file"

        formatted = Colors.format_agent_response(text)

        # All lines should use bright_green
        assert COLOR_PALETTE["bright_green"] in formatted
        assert "[Analyzing the code]" in formatted
        assert "Tool #1: Grep search" in formatted
        assert "Tool #2: Read file" in formatted

    def test_format_agent_response_empty_string(self):
        """Test formatting empty response."""
        formatted = Colors.format_agent_response("")

        # Should return empty string (with colors)
        assert isinstance(formatted, str)

    def test_format_agent_response_single_line_with_bracket(self):
        """Test formatting single line starting with bracket."""
        text = "[Thinking...]"

        formatted = Colors.format_agent_response(text)

        assert COLOR_PALETTE["bright_green"] in formatted
        assert "[Thinking...]" in formatted


class TestColorPalette:
    """Test COLOR_PALETTE constant."""

    def test_palette_has_all_colors(self):
        """Test that palette contains all expected colors."""
        expected_colors = [
            "black",
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "white",
            "bright_red",
            "bright_green",
            "bright_blue",
            "bright_white",
        ]

        for color in expected_colors:
            assert color in COLOR_PALETTE

    def test_palette_has_correct_count(self):
        """Test that palette has exactly 12 colors."""
        assert len(COLOR_PALETTE) == 12

    def test_palette_values_are_ansi_codes(self):
        """Test that all palette values are ANSI escape codes."""
        for color, code in COLOR_PALETTE.items():
            assert code.startswith("\033[")
            assert code.endswith("m")


class TestStatusBar:
    """Test StatusBar class."""

    def test_initialization(self):
        """Test StatusBar initialization."""
        status = StatusBar("Test Agent", "Claude Sonnet 4.5", show_tokens=True)

        assert status.agent_name == "Test Agent"
        assert status.model_info == "Claude Sonnet 4.5"
        assert status.show_tokens is True
        assert status.query_count == 0
        assert status.total_tokens == 0
        assert status.start_time > 0

    def test_initialization_without_tokens(self):
        """Test initialization with show_tokens=False."""
        status = StatusBar("Agent", "Model")

        assert status.show_tokens is False

    def test_get_session_time_seconds(self):
        """Test session time formatting for seconds only."""
        status = StatusBar("Test", "Model")
        status.start_time = time.time() - 30  # 30 seconds ago

        session_time = status.get_session_time()
        assert "s" in session_time
        assert "m" not in session_time

    def test_get_session_time_minutes(self):
        """Test session time formatting with minutes."""
        status = StatusBar("Test", "Model")
        status.start_time = time.time() - 125  # 2 minutes 5 seconds ago

        session_time = status.get_session_time()
        assert "m" in session_time
        assert "s" in session_time

    def test_increment_query(self):
        """Test incrementing query counter."""
        status = StatusBar("Test", "Model")

        assert status.query_count == 0

        status.increment_query()
        assert status.query_count == 1

        status.increment_query()
        assert status.query_count == 2

    def test_update_tokens(self):
        """Test updating token count."""
        status = StatusBar("Test", "Model", show_tokens=True)

        assert status.total_tokens == 0

        status.update_tokens(1500)
        assert status.total_tokens == 1500

        status.update_tokens(3000)
        assert status.total_tokens == 3000

    def test_render_basic(self):
        """Test basic status bar rendering."""
        status = StatusBar("Test Agent", "Claude Sonnet 4.5")
        status.start_time = time.time()

        rendered = status.render()

        # Check structure
        assert "┌" in rendered
        assert "└" in rendered
        assert "│" in rendered

        # Check content
        assert "Test Agent" in rendered
        assert "Claude Sonnet 4.5" in rendered
        assert "0 queries" in rendered

    def test_render_with_queries_singular(self):
        """Test rendering with exactly 1 query (singular)."""
        status = StatusBar("Test", "Model")
        status.query_count = 1

        rendered = status.render()
        assert "1 query" in rendered
        assert "queries" not in rendered

    def test_render_with_queries_plural(self):
        """Test rendering with multiple queries (plural)."""
        status = StatusBar("Test", "Model")
        status.query_count = 5

        rendered = status.render()
        assert "5 queries" in rendered

    def test_render_with_tokens_disabled(self):
        """Test rendering without token display."""
        status = StatusBar("Test", "Model", show_tokens=False)
        status.total_tokens = 10000

        rendered = status.render()

        # Tokens should not appear
        assert "tokens" not in rendered

    def test_render_with_tokens_enabled_zero(self):
        """Test rendering with tokens enabled but zero count."""
        status = StatusBar("Test", "Model", show_tokens=True)
        status.total_tokens = 0

        rendered = status.render()

        # Should not show tokens when count is 0
        assert "tokens" not in rendered

    def test_render_with_tokens_small(self):
        """Test rendering with small token count (< 1000)."""
        status = StatusBar("Test", "Model", show_tokens=True)
        status.total_tokens = 500

        rendered = status.render()
        assert "500 tokens" in rendered

    def test_render_with_tokens_thousands(self):
        """Test rendering with thousands of tokens."""
        status = StatusBar("Test", "Model", show_tokens=True)
        status.total_tokens = 5500

        rendered = status.render()
        assert "5.5K tokens" in rendered or "5.6K tokens" in rendered

    def test_render_with_tokens_millions(self):
        """Test rendering with millions of tokens."""
        status = StatusBar("Test", "Model", show_tokens=True)
        status.total_tokens = 2_500_000

        rendered = status.render()
        assert "2.5M tokens" in rendered

    def test_render_border_alignment(self):
        """Test that borders are properly aligned."""
        status = StatusBar("Test", "Model")

        rendered = status.render()
        lines = rendered.split("\n")

        # Should have 3 lines
        assert len(lines) == 3

        # All lines should have same length
        assert len(lines[0]) == len(lines[1]) == len(lines[2])

    def test_session_time_in_render(self):
        """Test that session time appears in rendered output."""
        status = StatusBar("Test", "Model")
        status.start_time = time.time() - 45

        rendered = status.render()

        # Should show seconds
        assert "s" in rendered

    def test_render_with_all_features(self):
        """Test rendering with all features enabled."""
        status = StatusBar("Complex Agent", "Claude Sonnet 4.5", show_tokens=True)
        status.query_count = 12
        status.total_tokens = 15_000
        status.start_time = time.time() - 300  # 5 minutes

        rendered = status.render()

        # Check all components present
        assert "Complex Agent" in rendered
        assert "Claude Sonnet 4.5" in rendered
        assert "12 queries" in rendered
        assert "15.0K tokens" in rendered or "15K tokens" in rendered
        assert "5m" in rendered

    def test_render_unicode_borders(self):
        """Test that unicode box-drawing characters are used."""
        status = StatusBar("Test", "Model")

        rendered = status.render()

        # Check for box-drawing characters
        assert "┌" in rendered  # Top-left corner
        assert "┐" in rendered  # Top-right corner
        assert "└" in rendered  # Bottom-left corner
        assert "┘" in rendered  # Bottom-right corner
        assert "─" in rendered  # Horizontal line
        assert "│" in rendered  # Vertical line
