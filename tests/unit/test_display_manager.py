"""Tests for DisplayManager component."""

import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from basic_agent_chat_loop.components.display_manager import DisplayManager
from basic_agent_chat_loop.components.token_tracker import TokenTracker


@pytest.fixture
def basic_display():
    """Create basic DisplayManager instance."""
    return DisplayManager(
        agent_name="Test Agent",
        agent_description="A test agent for unit tests",
        show_banner=True,
    )


@pytest.fixture
def display_with_metadata():
    """Create DisplayManager with metadata."""
    metadata = {
        "model_id": "claude-sonnet-4.5",
        "max_tokens": 4096,
        "temperature": 0.7,
        "tool_count": 3,
        "tools": ["tool1", "tool2", "tool3"],
    }
    return DisplayManager(
        agent_name="Test Agent",
        agent_description="Test description",
        agent_metadata=metadata,
        show_banner=True,
        show_metadata=True,
    )


@pytest.fixture
def display_with_config():
    """Create DisplayManager with config."""
    config = Mock()
    config.get.return_value = "~/test-conversations"

    return DisplayManager(
        agent_name="Test Agent",
        agent_description="Test description",
        auto_save=True,
        config=config,
    )


class TestDisplayManagerInitialization:
    """Test DisplayManager initialization."""

    def test_initialization_defaults(self):
        """Test DisplayManager initialization with defaults."""
        display = DisplayManager(
            agent_name="My Agent", agent_description="Test description"
        )

        assert display.agent_name == "My Agent"
        assert display.agent_description == "Test description"
        assert display.agent_metadata == {}
        assert display.show_banner is True
        assert display.show_metadata is False
        assert display.use_rich is False
        assert display.auto_save is False
        assert display.config is None
        assert display.status_bar is None

    def test_initialization_with_all_params(self):
        """Test initialization with all parameters."""
        metadata = {"model": "test"}
        config = Mock()
        status_bar = Mock()

        display = DisplayManager(
            agent_name="Agent",
            agent_description="Desc",
            agent_metadata=metadata,
            show_banner=False,
            show_metadata=True,
            use_rich=True,
            auto_save=True,
            config=config,
            status_bar=status_bar,
        )

        assert display.show_banner is False
        assert display.show_metadata is True
        assert display.use_rich is True
        assert display.auto_save is True
        assert display.config is config
        assert display.status_bar is status_bar


class TestDisplayBanner:
    """Test display_banner method."""

    def test_display_banner_basic(self, basic_display, capsys):
        """Test basic banner display."""
        basic_display.display_banner()
        captured = capsys.readouterr()

        assert "TEST AGENT" in captured.out
        assert "Interactive Chat" in captured.out
        assert "Welcome to Test Agent" in captured.out
        assert "A test agent for unit tests" in captured.out
        assert "Commands:" in captured.out
        assert "help" in captured.out

    def test_display_banner_disabled(self, capsys):
        """Test banner not shown when disabled."""
        display = DisplayManager(
            agent_name="Test", agent_description="Desc", show_banner=False
        )

        display.display_banner()
        captured = capsys.readouterr()

        assert captured.out == ""

    def test_display_banner_with_status_bar(self, capsys):
        """Test banner with status bar."""
        status_bar = Mock()
        status_bar.render.return_value = "Status Bar Content"

        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            status_bar=status_bar,
        )

        display.display_banner()
        captured = capsys.readouterr()

        status_bar.render.assert_called_once()
        assert "Status Bar Content" in captured.out

    def test_display_banner_with_metadata(self, display_with_metadata, capsys):
        """Test banner showing agent metadata."""
        display_with_metadata.display_banner()
        captured = capsys.readouterr()

        assert "Agent Configuration:" in captured.out
        assert "Max Tokens: 4096" in captured.out
        assert "Tools: 3 available" in captured.out

    def test_display_banner_with_config(self, display_with_config, capsys):
        """Test banner showing config info."""
        display_with_config.display_banner()
        captured = capsys.readouterr()

        assert "Configuration loaded" in captured.out
        assert "Auto-save: enabled" in captured.out


class TestDisplayHelp:
    """Test display_help method."""

    def test_display_help(self, basic_display, capsys):
        """Test help display."""
        basic_display.display_help()
        captured = capsys.readouterr()

        assert "TEST AGENT - Help" in captured.out
        assert "Commands:" in captured.out
        assert "help" in captured.out
        assert "info" in captured.out
        assert "templates" in captured.out
        assert "quit" in captured.out
        assert "Prompt Templates:" in captured.out
        assert "Multi-line Input:" in captured.out


class TestDisplayInfo:
    """Test display_info method."""

    def test_display_info_basic(self, basic_display, capsys):
        """Test basic info display."""
        basic_display.display_info()
        captured = capsys.readouterr()

        assert "TEST AGENT - Information" in captured.out
        assert "Name: Test Agent" in captured.out
        assert "Description: A test agent for unit tests" in captured.out
        assert "Features:" in captured.out

    def test_display_info_with_metadata(self, display_with_metadata, capsys):
        """Test info display with metadata."""
        display_with_metadata.display_info()
        captured = capsys.readouterr()

        assert "Configuration:" in captured.out
        assert "Model ID: claude-sonnet-4.5" in captured.out
        assert "Max Tokens: 4096" in captured.out
        assert "Temperature: 0.7" in captured.out
        assert "Available Tools (3):" in captured.out
        assert "tool1" in captured.out

    def test_display_info_with_many_tools(self, capsys):
        """Test info display with truncated tool list."""
        metadata = {
            "tool_count": 15,
            "tools": [f"tool{i}" for i in range(10)],
        }
        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            agent_metadata=metadata,
        )

        display.display_info()
        captured = capsys.readouterr()

        assert "Available Tools (15):" in captured.out
        assert "and 5 more" in captured.out

    def test_display_info_tools_count_only(self, capsys):
        """Test info display with only tool count, no list."""
        metadata = {"tool_count": 5, "tools": []}
        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            agent_metadata=metadata,
        )

        display.display_info()
        captured = capsys.readouterr()

        assert "Tools: 5 available" in captured.out

    def test_display_info_no_tools(self, capsys):
        """Test info display with no tools."""
        metadata = {"tool_count": 0}
        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            agent_metadata=metadata,
        )

        display.display_info()
        captured = capsys.readouterr()

        assert "Tools: None" in captured.out

    def test_display_info_with_rich(self, capsys):
        """Test info display with rich enabled."""
        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            use_rich=True,
        )

        display.display_info()
        captured = capsys.readouterr()

        assert "Rich markdown rendering" in captured.out

    def test_display_info_with_config(self, display_with_config, capsys):
        """Test info display with config."""
        display_with_config.display_info()
        captured = capsys.readouterr()

        assert "Configuration file support" in captured.out

    def test_display_info_with_auto_save(self, display_with_config, capsys):
        """Test info display with auto-save enabled."""
        display_with_config.display_info()
        captured = capsys.readouterr()

        assert "Auto-save conversations" in captured.out


class TestDisplaySessionSummary:
    """Test display_session_summary method."""

    def test_session_summary_basic(self, basic_display, capsys):
        """Test basic session summary."""
        tracker = TokenTracker()
        start_time = time.time() - 30  # 30 seconds ago

        basic_display.display_session_summary(start_time, 5, tracker)
        captured = capsys.readouterr()

        assert "Session Summary" in captured.out
        assert "Duration:" in captured.out
        assert "Queries: 5" in captured.out

    def test_session_summary_duration_seconds(self, basic_display, capsys):
        """Test duration formatting in seconds."""
        tracker = TokenTracker()
        start_time = time.time() - 45

        basic_display.display_session_summary(start_time, 1, tracker)
        captured = capsys.readouterr()

        assert "45s" in captured.out or "Duration: 4" in captured.out

    def test_session_summary_duration_minutes(self, basic_display, capsys):
        """Test duration formatting in minutes."""
        tracker = TokenTracker()
        start_time = time.time() - 125  # 2m 5s

        basic_display.display_session_summary(start_time, 1, tracker)
        captured = capsys.readouterr()

        assert "m" in captured.out

    def test_session_summary_duration_hours(self, basic_display, capsys):
        """Test duration formatting in hours."""
        tracker = TokenTracker()
        start_time = time.time() - 7320  # 2h 2m

        basic_display.display_session_summary(start_time, 1, tracker)
        captured = capsys.readouterr()

        assert "h" in captured.out

    def test_session_summary_with_tokens(self, basic_display, capsys):
        """Test session summary with token information."""
        tracker = TokenTracker()
        tracker.add_usage(1000, 500)
        tracker.add_usage(800, 600)

        start_time = time.time() - 60

        basic_display.display_session_summary(start_time, 2, tracker)
        captured = capsys.readouterr()

        assert "Tokens:" in captured.out
        assert "in:" in captured.out
        assert "out:" in captured.out


class TestDisplayTemplates:
    """Test display_templates method."""

    def test_display_templates_with_descriptions(self, basic_display, capsys):
        """Test displaying templates with descriptions."""
        templates = [
            ("review", "Code Review"),
            ("explain", "Explain Code"),
            ("test", "Write Tests"),
        ]
        prompts_dir = Path.home() / ".prompts"

        basic_display.display_templates(templates, prompts_dir)
        captured = capsys.readouterr()

        assert "Available Prompt Templates" in captured.out
        assert "(3)" in captured.out
        assert "/review" in captured.out
        assert "Code Review" in captured.out
        assert "/explain" in captured.out
        assert "Usage:" in captured.out

    def test_display_templates_without_descriptions(self, basic_display, capsys):
        """Test displaying templates as simple list."""
        templates = ["template1", "template2"]
        prompts_dir = Path("/test/prompts")

        basic_display.display_templates(templates, prompts_dir)
        captured = capsys.readouterr()

        assert "/template1" in captured.out
        assert "/template2" in captured.out

    def test_display_templates_empty(self, basic_display, capsys):
        """Test displaying empty template list."""
        templates = []
        prompts_dir = Path("/test/prompts")

        basic_display.display_templates(templates, prompts_dir)
        captured = capsys.readouterr()

        assert "No prompt templates found" in captured.out
        assert "Create templates in:" in captured.out
        assert str(prompts_dir) in captured.out


class TestEdgeCases:
    """Test edge cases."""

    def test_display_with_none_metadata(self):
        """Test initialization with None metadata."""
        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            agent_metadata=None,
        )

        assert display.agent_metadata == {}

    def test_metadata_with_unknown_max_tokens(self, capsys):
        """Test metadata display with unknown max tokens."""
        metadata = {"max_tokens": "Unknown"}
        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            agent_metadata=metadata,
            show_metadata=True,
        )

        display.display_banner()
        captured = capsys.readouterr()

        # Should not show max tokens if Unknown
        assert "Max Tokens: Unknown" not in captured.out

    def test_status_bar_model_override(self, capsys):
        """Test that status bar model info overrides metadata."""
        metadata = {"model_id": "old-model"}
        status_bar = Mock()
        status_bar.model_info = "new-model"
        status_bar.render.return_value = "Status"

        display = DisplayManager(
            agent_name="Test",
            agent_description="Desc",
            agent_metadata=metadata,
            show_metadata=True,
            status_bar=status_bar,
        )

        display.display_banner()
        captured = capsys.readouterr()

        # Should use status bar model, not metadata model
        assert "new-model" in captured.out
        assert "old-model" not in captured.out
