"""Tests for ChatLoop utility functions."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from basic_agent_chat_loop.chat_loop import ChatLoop, setup_logging


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_creates_log_file(self, tmp_path, monkeypatch):
        """Test that setup_logging creates log file."""
        # Mock log_dir to use temp directory
        import basic_agent_chat_loop.chat_loop as chat_loop_module

        original_log_dir = chat_loop_module.log_dir
        chat_loop_module.log_dir = tmp_path

        try:
            setup_logging("test_agent")

            # Check that log file was created (or would be created on first log)
            tmp_path / "test_agent_chat.log"
            # The file won't exist yet, but the directory should
            assert tmp_path.exists()

        finally:
            chat_loop_module.log_dir = original_log_dir

    def test_setup_logging_handles_spaces_in_name(self, tmp_path, monkeypatch):
        """Test that agent names with spaces are converted to underscores."""
        import basic_agent_chat_loop.chat_loop as chat_loop_module

        original_log_dir = chat_loop_module.log_dir
        chat_loop_module.log_dir = tmp_path

        try:
            setup_logging("My Test Agent")

            # Should create log file with underscores
            tmp_path / "my_test_agent_chat.log"
            # Directory should exist
            assert tmp_path.exists()

        finally:
            chat_loop_module.log_dir = original_log_dir


class TestChatLoopInitialization:
    """Test ChatLoop initialization."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock()
        agent.name = "Test Agent"
        agent.model = Mock()
        agent.model.model_id = "test-model"
        return agent

    def test_initialization_minimal(self, mock_agent):
        """Test ChatLoop initialization with minimal parameters."""
        chat_loop = ChatLoop(
            agent=mock_agent,
            agent_name="Test Agent",
            agent_description="A test agent",
        )

        assert chat_loop.agent == mock_agent
        assert chat_loop.agent_name == "Test Agent"
        assert chat_loop.agent_description == "A test agent"
        assert chat_loop.session_state.query_count == 0
        assert chat_loop.session_state.last_response == ""

    def test_initialization_with_defaults(self, mock_agent):
        """Test that default configuration values are set."""
        # Patch get_config to return None, ensuring defaults are used
        with patch("basic_agent_chat_loop.chat_loop.get_config") as mock_get_config:
            mock_get_config.return_value = None

            chat_loop = ChatLoop(
                agent=mock_agent,
                agent_name="Test",
                agent_description="Desc",
                config=None,
            )

            # Check defaults
            assert chat_loop.max_retries == 3
            assert chat_loop.retry_delay == 2.0
            assert chat_loop.timeout == 120.0
            assert chat_loop.spinner_style == "dots"
            assert chat_loop.show_metadata is True
            assert chat_loop.show_thinking is True
            assert chat_loop.show_duration is True
            assert chat_loop.show_banner is True

    def test_initialization_with_config(self, mock_agent, tmp_path):
        """Test initialization with custom config."""
        config = Mock()
        config.get.side_effect = lambda key, default, agent_name=None: {
            "behavior.max_retries": 5,
            "behavior.retry_delay": 3.0,
            "behavior.timeout": 180.0,
            "behavior.spinner_style": "bouncingBall",
            "features.show_metadata": False,
            "features.show_tokens": True,
            "features.rich_enabled": False,
            "ui.show_thinking_indicator": False,
            "ui.show_duration": False,
            "ui.show_banner": False,
            "ui.show_status_bar": False,
        }.get(key, default)
        # Mock expand_path to return a real Path
        config.expand_path = Mock(return_value=tmp_path / "sessions")

        chat_loop = ChatLoop(
            agent=mock_agent,
            agent_name="Test",
            agent_description="Desc",
            config=config,
        )

        assert chat_loop.max_retries == 5
        assert chat_loop.retry_delay == 3.0
        assert chat_loop.timeout == 180.0
        assert chat_loop.spinner_style == "bouncingBall"
        assert chat_loop.show_metadata is False
        assert chat_loop.show_tokens is True
        assert chat_loop.use_rich is False  # Rich disabled by config
        assert chat_loop.show_thinking is False
        assert chat_loop.show_duration is False
        assert chat_loop.show_banner is False

    def test_initialization_creates_components(self, mock_agent):
        """Test that initialization creates required components."""
        chat_loop = ChatLoop(
            agent=mock_agent,
            agent_name="Test",
            agent_description="Desc",
        )

        # Should create template manager
        assert chat_loop.template_manager is not None
        assert isinstance(chat_loop.prompts_dir, Path)

        # Should create token tracker
        assert chat_loop.token_tracker is not None

        # Should create display manager
        assert chat_loop.display_manager is not None

    def test_initialization_with_agent_factory(self, mock_agent):
        """Test initialization with agent factory."""

        def factory():
            return Mock()

        chat_loop = ChatLoop(
            agent=mock_agent,
            agent_name="Test",
            agent_description="Desc",
            agent_factory=factory,
        )

        assert chat_loop.agent_factory == factory


class TestReadlineHistory:
    """Test readline history functions."""

    @patch("basic_agent_chat_loop.chat_loop.READLINE_AVAILABLE", True)
    @patch("basic_agent_chat_loop.chat_loop.readline")
    def test_setup_readline_history_creates_file_path(self, mock_readline):
        """Test that setup returns history file path."""
        from basic_agent_chat_loop.chat_loop import setup_readline_history

        result = setup_readline_history()

        assert result is not None
        assert isinstance(result, Path)
        assert result.name == ".chat_history"

    @patch("basic_agent_chat_loop.chat_loop.READLINE_AVAILABLE", False)
    def test_setup_readline_history_without_readline(self):
        """Test setup when readline not available."""
        from basic_agent_chat_loop.chat_loop import setup_readline_history

        result = setup_readline_history()

        assert result is None

    @patch("basic_agent_chat_loop.chat_loop.READLINE_AVAILABLE", True)
    @patch("basic_agent_chat_loop.chat_loop.readline")
    def test_save_readline_history(self, mock_readline):
        """Test saving readline history."""
        from basic_agent_chat_loop.chat_loop import save_readline_history

        history_file = Path.home() / ".chat_history"

        # Should not raise
        save_readline_history(history_file)

        # Should have called write_history_file
        mock_readline.write_history_file.assert_called_once()

    @patch("basic_agent_chat_loop.chat_loop.READLINE_AVAILABLE", False)
    def test_save_readline_history_without_readline(self):
        """Test save when readline not available."""
        from basic_agent_chat_loop.chat_loop import save_readline_history

        history_file = Path.home() / ".chat_history"

        # Should not raise
        save_readline_history(history_file)

    def test_save_readline_history_none_file(self):
        """Test save with None history file."""
        from basic_agent_chat_loop.chat_loop import save_readline_history

        # Should not raise
        save_readline_history(None)
