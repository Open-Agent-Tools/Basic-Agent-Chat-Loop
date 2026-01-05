"""Tests for multi-line input functionality."""

from unittest.mock import Mock, patch

import pytest

from basic_agent_chat_loop.chat_loop import ChatLoop
from basic_agent_chat_loop.components.input_handler import get_multiline_input

# Patch to use regular input() for testing (bypass ESC detection)
# This allows us to test with simple mocked input
INPUT_PATCH_TARGET = "basic_agent_chat_loop.components.input_handler.input_with_esc"


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = Mock()
    agent.stream_async = None  # No streaming support
    return agent


@pytest.fixture
def chat_loop(mock_agent):
    """Create a ChatLoop instance for testing."""
    return ChatLoop(
        agent=mock_agent,
        agent_name="TestAgent",
        agent_description="Test agent description",
        config=None,
    )


@pytest.mark.asyncio
async def test_multiline_input_submit(chat_loop):
    """Test basic multi-line input submission."""
    # Mock input to return lines then empty line to submit
    inputs = ["line 1", "line 2", "line 3", ""]
    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        result = await get_multiline_input()

    assert result == "line 1\nline 2\nline 3"


@pytest.mark.asyncio
async def test_multiline_input_cancel_command(chat_loop):
    """Test cancelling multi-line input with .cancel command."""
    inputs = ["line 1", ".cancel"]
    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        result = await get_multiline_input()

    assert result == ""


@pytest.mark.asyncio
async def test_multiline_input_cancel_esc(chat_loop):
    """Test cancelling multi-line input with ESC key."""
    inputs = ["line 1", None]  # None indicates ESC was pressed
    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        result = await get_multiline_input()

    assert result == ""


@pytest.mark.asyncio
async def test_multiline_input_cancel_ctrl_d(chat_loop):
    """Test cancelling multi-line input with Ctrl+D (EOFError)."""

    def mock_input_with_eof(prompt):
        raise EOFError()

    with patch(INPUT_PATCH_TARGET, side_effect=mock_input_with_eof):
        result = await get_multiline_input()

    assert result == ""


@pytest.mark.asyncio
async def test_multiline_input_cancel_ctrl_c(chat_loop):
    """Test cancelling multi-line input with Ctrl+C (KeyboardInterrupt)."""

    def mock_input_with_interrupt(prompt):
        raise KeyboardInterrupt()

    with patch(INPUT_PATCH_TARGET, side_effect=mock_input_with_interrupt):
        result = await get_multiline_input()

    assert result == ""


@pytest.mark.asyncio
async def test_multiline_input_back_command(chat_loop):
    """Test editing previous line with .back command."""
    # Simulate: enter two lines, use .back, re-enter line, submit
    inputs = [
        "line 1",
        "line 2",
        ".back",  # Go back to edit line 2
        "line 2 edited",  # Re-enter the line
        "",  # Submit
    ]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        with patch("basic_agent_chat_loop.components.input_handler.READLINE_AVAILABLE", True):
            with patch("readline.add_history"):
                result = await get_multiline_input()

    assert result == "line 1\nline 2 edited"


@pytest.mark.asyncio
async def test_multiline_input_up_arrow(chat_loop):
    """Test editing previous line with up arrow key."""
    # Simulate: enter two lines, press up arrow, re-enter line, submit
    inputs = [
        "line 1",
        "line 2",
        "UP_ARROW",  # Up arrow pressed
        "line 2 edited",  # Re-enter the line
        "",  # Submit
    ]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        with patch("basic_agent_chat_loop.components.input_handler.READLINE_AVAILABLE", True):
            with patch("readline.add_history"):
                result = await get_multiline_input()

    assert result == "line 1\nline 2 edited"


@pytest.mark.asyncio
async def test_multiline_input_up_arrow_on_empty(chat_loop):
    """Test up arrow when no previous lines exist."""
    inputs = ["UP_ARROW", "line 1", ""]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        result = await get_multiline_input()

    assert result == "line 1"


@pytest.mark.asyncio
async def test_multiline_input_back_on_empty(chat_loop):
    """Test .back command when no previous lines exist."""
    inputs = [".back", "line 1", ""]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        result = await get_multiline_input()

    assert result == "line 1"


@pytest.mark.asyncio
async def test_multiline_input_empty_first_line(chat_loop):
    """Test that empty first line shows warning and continues."""
    inputs = [
        "",  # Empty first line - should warn and continue
        "line 1",
        "",  # Submit
    ]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        result = await get_multiline_input()

    assert result == "line 1"


@pytest.mark.asyncio
async def test_multiline_input_history_saved(chat_loop):
    """Test that multi-line input is saved to readline history."""
    inputs = ["line 1", "line 2", ""]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        with patch("basic_agent_chat_loop.components.input_handler.READLINE_AVAILABLE", True):
            with patch("readline.add_history") as mock_add_history:
                _ = await get_multiline_input()

    # Verify the full block was added to history
    mock_add_history.assert_called_with("line 1\nline 2")


@pytest.mark.asyncio
async def test_multiline_input_line_numbers(chat_loop):
    """Test that line numbers are displayed in prompts."""
    inputs = ["line 1", "line 2", ""]

    prompts_received = []

    def capture_prompts(prompt):
        prompts_received.append(prompt)
        return inputs.pop(0)

    with patch(INPUT_PATCH_TARGET, side_effect=capture_prompts):
        _ = await get_multiline_input()

    # Check that prompts contain line numbers
    assert any("1" in p for p in prompts_received)
    assert any("2" in p for p in prompts_received)


@pytest.mark.asyncio
async def test_multiline_input_multiple_back_commands(chat_loop):
    """Test using .back multiple times to edit multiple lines."""
    inputs = [
        "line 1",
        "line 2",
        "line 3",
        ".back",  # Back to line 3
        "line 3 edited",
        ".back",  # Back to line 3 edited
        "line 3 final",
        "",  # Submit
    ]

    with patch(INPUT_PATCH_TARGET, side_effect=inputs):
        with patch("basic_agent_chat_loop.components.input_handler.READLINE_AVAILABLE", True):
            with patch("readline.add_history"):
                result = await get_multiline_input()

    assert result == "line 1\nline 2\nline 3 final"
