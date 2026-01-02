"""Tests for copy command functionality."""

from unittest.mock import Mock, patch

import pytest

from basic_agent_chat_loop.chat_loop import ChatLoop


class TestExtractCodeBlocks:
    """Test _extract_code_blocks method."""

    def test_extract_single_code_block(self):
        """Test extracting a single code block."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test", "Desc")

            text = """Here is some code:
```python
def hello():
    print("Hello World")
```
That's it!"""

            blocks = chat_loop._extract_code_blocks(text)

            assert len(blocks) == 1
            assert "def hello():" in blocks[0]
            assert 'print("Hello World")' in blocks[0]

    def test_extract_multiple_code_blocks(self):
        """Test extracting multiple code blocks."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test", "Desc")

            text = """First block:
```python
print("first")
```
Second block:
```javascript
console.log("second");
```
Done."""

            blocks = chat_loop._extract_code_blocks(text)

            assert len(blocks) == 2
            assert 'print("first")' in blocks[0]
            assert 'console.log("second")' in blocks[1]

    def test_extract_code_block_without_language(self):
        """Test extracting code block without language specifier."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test", "Desc")

            text = """Some code:
```
generic code here
```
"""

            blocks = chat_loop._extract_code_blocks(text)

            assert len(blocks) == 1
            assert "generic code here" in blocks[0]

    def test_extract_no_code_blocks(self):
        """Test text with no code blocks."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test", "Desc")

            text = "Just plain text with no code blocks"
            blocks = chat_loop._extract_code_blocks(text)

            assert len(blocks) == 0


class TestFormatConversationAsMarkdown:
    """Test _format_conversation_as_markdown method."""

    def test_format_empty_conversation(self):
        """Test formatting with no conversation history."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test Agent", "Desc")

            markdown = chat_loop._format_conversation_as_markdown()

            assert "# Test Agent - Conversation" in markdown
            assert "Session ID:" in markdown
            assert "Agent: Test Agent" in markdown

    def test_format_conversation_with_history(self):
        """Test formatting with conversation history."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test Agent", "Desc")

            # Add conversation markdown
            chat_loop.session_state.query_count = 1
            chat_loop.session_state.conversation_markdown = [
                "\n## Query 1 (00:00:00)\n",
                "**You:** What is 2+2?\n\n",
                "**Test Agent:** The answer is 4.\n\n",
                "*Time: 1.5s | Tokens: 15 (in: 10, out: 5)*\n\n",
                "---\n",
            ]

            markdown = chat_loop._format_conversation_as_markdown()

            assert "# Test Agent - Conversation" in markdown
            assert "## Query 1" in markdown
            assert "**You:** What is 2+2?" in markdown
            assert "**Test Agent:**" in markdown
            assert "The answer is 4." in markdown
            assert "Time: 1.5s" in markdown
            assert "Tokens: 15" in markdown

    def test_format_conversation_without_usage(self):
        """Test formatting without usage info."""
        agent = Mock()
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(agent, "Test", "Desc")

            chat_loop.session_state.query_count = 1
            chat_loop.session_state.conversation_markdown = [
                "\n## Query 1 (00:00:00)\n",
                "**You:** Hello\n\n",
                "**Test:** Hi there!\n\n",
                "*Time: 0.5s*\n\n",
                "---\n",
            ]

            markdown = chat_loop._format_conversation_as_markdown()

            assert "Hello" in markdown
            assert "Hi there!" in markdown
            assert "Time: 0.5s" in markdown
            # Should not have token info
            assert "Tokens:" not in markdown


class TestCopyCommand:
    """Test copy command handling."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = Mock()
        return agent

    def test_last_query_tracked(self, mock_agent):
        """Test that last_query is initialized and can be set."""
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(mock_agent, "Test", "Desc")

            assert chat_loop.session_state.last_query == ""

            chat_loop.session_state.last_query = "test query"
            assert chat_loop.session_state.last_query == "test query"

    def test_last_response_tracked(self, mock_agent):
        """Test that last_response is initialized and can be set."""
        with patch(
            "basic_agent_chat_loop.chat_loop.extract_agent_metadata"
        ) as mock_extract:
            mock_extract.return_value = {"model_id": "test", "tool_count": 0}
            chat_loop = ChatLoop(mock_agent, "Test", "Desc")

            assert chat_loop.session_state.last_response == ""

            chat_loop.session_state.last_response = "test response"
            assert chat_loop.session_state.last_response == "test response"
