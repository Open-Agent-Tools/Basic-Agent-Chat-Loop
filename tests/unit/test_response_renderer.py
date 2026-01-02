"""Tests for ResponseRenderer component."""

import io
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest
from basic_agent_chat_loop.components.response_renderer import ResponseRenderer


class MockColors:
    """Mock Colors module for testing."""

    @staticmethod
    def agent(text):
        return f"[BLUE]{text}[/BLUE]"

    @staticmethod
    def success(text):
        return f"[GREEN]{text}[/GREEN]"

    @staticmethod
    def format_agent_response(text):
        # Simulate colorization for tool messages
        if text.startswith("["):
            return f"[YELLOW]{text}[/YELLOW]"
        return text


class TestResponseRendererInitialization:
    """Test ResponseRenderer initialization."""

    def test_initialization_minimal(self):
        """Test basic initialization with required parameters."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        assert renderer.agent_name == "TestAgent"
        assert renderer.use_rich is False
        assert renderer.console is None
        assert renderer.colors == MockColors

    def test_initialization_with_rich(self):
        """Test initialization with rich mode enabled."""
        mock_console = Mock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=True,
            console=mock_console,
            colors_module=MockColors,
        )
        assert renderer.use_rich is True
        assert renderer.console == mock_console

    def test_initialization_with_harmony_processor(self):
        """Test initialization with harmony processor."""
        mock_harmony = Mock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=False,
            harmony_processor=mock_harmony,
            colors_module=MockColors,
        )
        assert renderer.harmony_processor == mock_harmony

    def test_initialization_without_colors_raises_error(self):
        """Test that missing colors module raises ValueError."""
        with pytest.raises(ValueError, match="colors_module is required"):
            ResponseRenderer(agent_name="TestAgent", use_rich=False)


class TestRenderAgentHeader:
    """Test agent header rendering."""

    def test_render_agent_header(self, capsys):
        """Test rendering agent name header."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_agent_header()

        captured = capsys.readouterr()
        assert "\n[BLUE]TestAgent[/BLUE]: " in captured.out

    def test_render_agent_header_with_special_characters(self, capsys):
        """Test rendering agent name with special characters."""
        renderer = ResponseRenderer(
            agent_name="Test-Agent_123", use_rich=False, colors_module=MockColors
        )
        renderer.render_agent_header()

        captured = capsys.readouterr()
        assert "[BLUE]Test-Agent_123[/BLUE]" in captured.out


class TestRenderStreamingText:
    """Test streaming text display."""

    def test_render_streaming_text_plain_mode(self, capsys):
        """Test streaming text in plain mode (no rich, no harmony)."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_streaming_text("Hello, world!")

        captured = capsys.readouterr()
        assert "Hello, world!" in captured.out

    def test_render_streaming_text_with_tool_message(self, capsys):
        """Test streaming text with tool message colorization."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_streaming_text("[Tool #1] Calling function")

        captured = capsys.readouterr()
        assert "[YELLOW][Tool #1] Calling function[/YELLOW]" in captured.out

    def test_render_streaming_text_rich_mode_skips_display(self, capsys):
        """Test that streaming text is not displayed in rich mode."""
        mock_console = Mock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=True,
            console=mock_console,
            colors_module=MockColors,
        )
        renderer.render_streaming_text("Should not display")

        captured = capsys.readouterr()
        assert "Should not display" not in captured.out

    def test_render_streaming_text_harmony_mode_skips_display(self, capsys):
        """Test that streaming text is not displayed with harmony processor."""
        mock_harmony = Mock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=False,
            harmony_processor=mock_harmony,
            colors_module=MockColors,
        )
        renderer.render_streaming_text("Should not display")

        captured = capsys.readouterr()
        assert "Should not display" not in captured.out


class TestShouldSkipStreamingDisplay:
    """Test streaming display skip logic."""

    def test_should_skip_when_using_rich(self):
        """Test skip streaming when using rich mode."""
        mock_console = Mock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=True,
            console=mock_console,
            colors_module=MockColors,
        )
        assert renderer.should_skip_streaming_display() is True

    def test_should_skip_when_using_harmony(self):
        """Test skip streaming when using harmony processor."""
        mock_harmony = Mock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=False,
            harmony_processor=mock_harmony,
            colors_module=MockColors,
        )
        assert renderer.should_skip_streaming_display() is True

    def test_should_not_skip_plain_mode(self):
        """Test do not skip streaming in plain mode."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        assert renderer.should_skip_streaming_display() is False


class TestRenderFinalResponsePlainText:
    """Test final response rendering in plain text mode."""

    def test_render_final_response_plain_text(self, capsys):
        """Test rendering final response in plain text mode."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="This is the final response", first_token_received=False
        )

        captured = capsys.readouterr()
        assert "This is the final response" in captured.out

    def test_render_final_response_with_separator(self, capsys):
        """Test rendering final response with visual separator."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="Final response", first_token_received=True
        )

        captured = capsys.readouterr()
        assert "[GREEN]─── Final Response ───[/GREEN]" in captured.out
        assert "Final response" in captured.out

    def test_render_final_response_without_separator(self, capsys):
        """Test rendering final response without separator (no streaming)."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="Direct response", first_token_received=False
        )

        captured = capsys.readouterr()
        assert "─── Final Response ───" not in captured.out
        assert "Direct response" in captured.out

    def test_render_final_response_empty_text(self, capsys):
        """Test rendering empty final response does nothing."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(display_text="", first_token_received=True)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_render_final_response_whitespace_only(self, capsys):
        """Test rendering whitespace-only final response does nothing."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="   \n  ", first_token_received=True
        )

        captured = capsys.readouterr()
        assert captured.out == ""


class TestRenderFinalResponseRichMode:
    """Test final response rendering in rich mode."""

    def test_render_final_response_rich_markdown(self):
        """Test rendering final response with rich markdown."""
        mock_console = MagicMock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=True,
            console=mock_console,
            colors_module=MockColors,
        )
        renderer.render_final_response(
            display_text="# Markdown Title\n\nParagraph text", first_token_received=True
        )

        # Verify console.print was called with a Markdown object
        assert mock_console.print.called
        call_args = mock_console.print.call_args[0]
        assert len(call_args) > 0
        # The first argument should be a Markdown object
        assert call_args[0].__class__.__name__ == "Markdown"

    def test_render_final_response_rich_with_separator(self, capsys):
        """Test rich mode shows separator before markdown."""
        mock_console = MagicMock()
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=True,
            console=mock_console,
            colors_module=MockColors,
        )
        renderer.render_final_response(
            display_text="Response text", first_token_received=True
        )

        # Separator should be printed to stdout
        captured = capsys.readouterr()
        assert "[GREEN]─── Final Response ───[/GREEN]" in captured.out

        # Markdown should be sent to console
        assert mock_console.print.called

    def test_render_final_response_rich_without_console(self, capsys):
        """Test rich mode without console falls back to plain text."""
        renderer = ResponseRenderer(
            agent_name="TestAgent",
            use_rich=True,
            console=None,
            colors_module=MockColors,
        )
        renderer.render_final_response(
            display_text="Fallback text", first_token_received=False
        )

        captured = capsys.readouterr()
        # Should use plain text rendering
        assert "Fallback text" in captured.out


class TestRenderFinalResponseWithToolMessages:
    """Test final response rendering with tool messages."""

    def test_render_tool_message_colorization(self, capsys):
        """Test that tool messages get colorized in plain mode."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="[Tool #1] Function called\nRegular text",
            first_token_received=False,
        )

        captured = capsys.readouterr()
        # Entire response gets passed through format_agent_response
        # which colorizes lines starting with "["
        assert "[YELLOW][Tool #1] Function called" in captured.out
        assert "Regular text" in captured.out


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_render_multiline_response(self, capsys):
        """Test rendering multiline response."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="Line 1\nLine 2\nLine 3", first_token_received=False
        )

        captured = capsys.readouterr()
        assert "Line 1" in captured.out
        assert "Line 2" in captured.out
        assert "Line 3" in captured.out

    def test_render_unicode_response(self, capsys):
        """Test rendering Unicode text."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        renderer.render_final_response(
            display_text="Hello 世界 🌍", first_token_received=False
        )

        captured = capsys.readouterr()
        assert "Hello 世界 🌍" in captured.out

    def test_render_very_long_response(self, capsys):
        """Test rendering very long response."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )
        long_text = "A" * 10000
        renderer.render_final_response(
            display_text=long_text, first_token_received=False
        )

        captured = capsys.readouterr()
        assert long_text in captured.out

    def test_multiple_headers_same_renderer(self, capsys):
        """Test rendering multiple headers with same renderer instance."""
        renderer = ResponseRenderer(
            agent_name="TestAgent", use_rich=False, colors_module=MockColors
        )

        renderer.render_agent_header()
        renderer.render_agent_header()

        captured = capsys.readouterr()
        # Should see header twice
        assert captured.out.count("[BLUE]TestAgent[/BLUE]") == 2
