"""Tests for ResponseRenderer component.

Simplified for v1.8.0 - ResponseRenderer now only handles agent header display.
Agent library handles all response rendering naturally.
"""

import pytest

from basic_agent_chat_loop.components.response_renderer import ResponseRenderer


class MockColors:
    """Mock Colors module for testing."""

    @staticmethod
    def agent(text):
        return f"[BLUE]{text}[/BLUE]"


class TestResponseRendererInitialization:
    """Test ResponseRenderer initialization."""

    def test_initialization(self):
        """Test basic initialization with required parameters."""
        renderer = ResponseRenderer(agent_name="TestAgent", colors_module=MockColors)
        assert renderer.agent_name == "TestAgent"
        assert renderer.colors == MockColors

    def test_initialization_with_different_agent_name(self):
        """Test initialization with different agent names."""
        renderer = ResponseRenderer(agent_name="MyCustomAgent", colors_module=MockColors)
        assert renderer.agent_name == "MyCustomAgent"

    def test_initialization_with_special_characters_in_name(self):
        """Test initialization with special characters in agent name."""
        renderer = ResponseRenderer(
            agent_name="Test-Agent_123", colors_module=MockColors
        )
        assert renderer.agent_name == "Test-Agent_123"


class TestRenderAgentHeader:
    """Test agent header rendering."""

    def test_render_agent_header(self, capsys):
        """Test rendering agent name header."""
        renderer = ResponseRenderer(agent_name="TestAgent", colors_module=MockColors)
        renderer.render_agent_header()

        captured = capsys.readouterr()
        assert "\n[BLUE]TestAgent[/BLUE]: " in captured.out

    def test_render_agent_header_with_special_characters(self, capsys):
        """Test rendering agent name with special characters."""
        renderer = ResponseRenderer(
            agent_name="Test-Agent_123", colors_module=MockColors
        )
        renderer.render_agent_header()

        captured = capsys.readouterr()
        assert "[BLUE]Test-Agent_123[/BLUE]" in captured.out

    def test_render_agent_header_multiple_calls(self, capsys):
        """Test rendering agent header multiple times."""
        renderer = ResponseRenderer(agent_name="TestAgent", colors_module=MockColors)

        renderer.render_agent_header()
        renderer.render_agent_header()

        captured = capsys.readouterr()
        # Should appear twice
        assert captured.out.count("[BLUE]TestAgent[/BLUE]: ") == 2

    def test_render_agent_header_unicode(self, capsys):
        """Test rendering agent name with unicode characters."""
        renderer = ResponseRenderer(agent_name="Test🤖Agent", colors_module=MockColors)
        renderer.render_agent_header()

        captured = capsys.readouterr()
        assert "[BLUE]Test🤖Agent[/BLUE]" in captured.out
