"""
Comprehensive tests for conversation saving functionality.

NOTE: Many of these tests are for the old JSON+dict-based conversation tracking.
They need to be rewritten for the new markdown-only conversation tracking.
Tests marked with @pytest.mark.skip are pending rewrite.

Tests for bugs fixed:
1. Empty responses in saved files due to streaming event parsing
2. Conversation history only tracked when auto_save=True
3. Harmony processor overwriting response text with empty channels
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from basic_agent_chat_loop.chat_loop import ChatLoop
from basic_agent_chat_loop.components.harmony_processor import HarmonyProcessor


@pytest.fixture
def mock_strands_agent():
    """Create a mock AWS Strands agent with streaming support."""
    agent = Mock()
    agent.name = "Simple Sally"
    agent.description = "A friendly minimal agent"

    # Mock streaming events with delta attribute (AWS Strands style)
    async def mock_stream_async(query):
        """Simulate AWS Strands streaming events with delta attribute."""
        response_chunks = ["Hello! ", "I'm Simple Sally. ", "How can I help you today?"]

        for chunk in response_chunks:
            # Use spec to limit attributes
            event = Mock(spec=["delta"])
            delta_mock = Mock(spec=["text"])
            delta_mock.text = chunk
            event.delta = delta_mock
            yield event
            await asyncio.sleep(0.01)

    agent.stream_async = mock_stream_async
    return agent


@pytest.fixture
def mock_data_agent():
    """Create a mock agent with .data attribute (original format)."""
    agent = Mock()
    agent.name = "Data Agent"
    agent.description = "Agent using .data events"

    async def mock_stream_async(query):
        """Simulate streaming events with .data attribute."""
        response_chunks = ["Response ", "from ", "data ", "agent."]

        for chunk in response_chunks:
            event = Mock()
            event.data = chunk
            yield event
            await asyncio.sleep(0.01)

    agent.stream_async = mock_stream_async
    return agent


@pytest.fixture
def mock_text_agent():
    """Create a mock agent with .text attribute."""
    agent = Mock()
    agent.name = "Text Agent"
    agent.description = "Agent using .text events"

    async def mock_stream_async(query):
        """Simulate streaming events with .text attribute."""
        response_chunks = ["Using ", "text ", "attribute."]

        for chunk in response_chunks:
            event = Mock(spec=["text"])
            event.text = chunk
            yield event
            await asyncio.sleep(0.01)

    agent.stream_async = mock_stream_async
    return agent


@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config with sessions directory."""
    # Create sessions directory
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Create a mock config that returns the temp sessions dir
    config = Mock()
    config.config_data = {
        "paths": {"save_location": str(sessions_dir)},
        "features": {"auto_save": False, "show_tokens": False, "rich_enabled": True},
        "ui": {"show_banner": False, "show_status_bar": False},
    }

    def mock_get(key, default=None, agent_name=None):
        """Mock get method that handles nested keys."""
        parts = key.split(".")
        value = config.config_data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        return value

    def mock_expand_path(path):
        """Mock expand_path that just returns a Path object."""
        return Path(path).expanduser()

    config.get = mock_get
    config.expand_path = mock_expand_path

    return config


@pytest.mark.skip(reason="Needs rewrite for markdown-only conversation tracking")
class TestStreamingEventParsing:
    """Test that different streaming event formats are parsed correctly."""

    @pytest.mark.asyncio
    async def test_aws_strands_delta_events(
        self, mock_strands_agent, temp_config, tmp_path
    ):
        """Test that AWS Strands events with .delta attribute are captured."""
        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Process a query
        await chat_loop._stream_agent_response("Hello")

        # Verify conversation history was populated
        assert len(chat_loop.conversation_history) == 1

        # Verify response text was captured
        saved_response = chat_loop.conversation_history[0]["response"]
        assert "Hello!" in saved_response
        assert "Simple Sally" in saved_response
        assert "help you" in saved_response

        # Verify it's not empty
        assert saved_response.strip() != ""

    @pytest.mark.asyncio
    async def test_data_attribute_events(self, mock_data_agent, temp_config):
        """Test that events with .data attribute are captured (original format)."""
        chat_loop = ChatLoop(
            mock_data_agent,
            "Data Agent",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        await chat_loop._stream_agent_response("Test")

        assert len(chat_loop.conversation_history) == 1
        saved_response = chat_loop.conversation_history[0]["response"]

        assert "Response" in saved_response
        assert "from" in saved_response
        assert "data" in saved_response
        assert "agent" in saved_response
        assert saved_response.strip() != ""

    @pytest.mark.asyncio
    async def test_text_attribute_events(self, mock_text_agent, temp_config):
        """Test that events with .text attribute are captured."""
        chat_loop = ChatLoop(
            mock_text_agent,
            "Text Agent",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        await chat_loop._stream_agent_response("Test")

        assert len(chat_loop.conversation_history) == 1
        saved_response = chat_loop.conversation_history[0]["response"]

        assert "Using" in saved_response
        assert "text" in saved_response
        assert "attribute" in saved_response
        assert saved_response.strip() != ""


@pytest.mark.skip(reason="Needs rewrite for markdown-only conversation tracking")
class TestConversationHistoryTracking:
    """Test that conversation history is tracked regardless of auto_save setting."""

    @pytest.mark.asyncio
    async def test_history_tracked_with_auto_save_false(
        self, mock_strands_agent, temp_config
    ):
        """Test conversation history is tracked even when auto_save is False."""
        # Ensure auto_save is False
        temp_config.config_data["features"]["auto_save"] = False

        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Process multiple queries
        await chat_loop._stream_agent_response("First query")
        await chat_loop._stream_agent_response("Second query")

        # Conversation history should be populated
        assert len(chat_loop.conversation_history) == 2

        # Both responses should have content
        assert chat_loop.conversation_history[0]["response"].strip() != ""
        assert chat_loop.conversation_history[1]["response"].strip() != ""

        # Verify queries are tracked
        assert chat_loop.conversation_history[0]["query"] == "First query"
        assert chat_loop.conversation_history[1]["query"] == "Second query"

    @pytest.mark.asyncio
    async def test_history_tracked_with_auto_save_true(
        self, mock_strands_agent, temp_config
    ):
        """Test conversation history is tracked when auto_save is True."""
        # Enable auto_save
        temp_config.config_data["features"]["auto_save"] = True

        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        await chat_loop._stream_agent_response("Test query")

        assert len(chat_loop.conversation_history) == 1
        assert chat_loop.conversation_history[0]["response"].strip() != ""
        assert chat_loop.conversation_history[0]["query"] == "Test query"


@pytest.mark.skip(reason="Needs rewrite for markdown-only conversation tracking")
class TestSavedFileContent:
    """Test that saved files contain both user queries and agent responses."""

    @pytest.mark.asyncio
    async def test_markdown_file_contains_responses(
        self, mock_strands_agent, temp_config, tmp_path
    ):
        """Test that markdown files contain agent responses, not just user queries."""
        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Simulate conversation
        await chat_loop._stream_agent_response("What is Python?")
        await chat_loop._stream_agent_response("Tell me more")

        # Save conversation
        success = chat_loop.save_conversation()
        assert success is True

        # Find the markdown file
        sessions_dir = tmp_path / "sessions"
        md_files = list(sessions_dir.glob("*.md"))
        assert len(md_files) == 1

        # Read and verify markdown content
        md_content = md_files[0].read_text()

        # Should contain user queries
        assert "What is Python?" in md_content
        assert "Tell me more" in md_content

        # Should contain agent responses
        assert "Hello!" in md_content
        assert "Simple Sally" in md_content
        assert "help you" in md_content

        # Should have agent name as speaker
        assert "**Simple Sally:**" in md_content

        # Should NOT be just user queries
        assert md_content.count("**You:**") == 2
        assert md_content.count("**Simple Sally:**") == 2

    @pytest.mark.asyncio
    async def test_json_file_contains_responses(
        self, mock_strands_agent, temp_config, tmp_path
    ):
        """Test that JSON files contain agent responses."""
        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        await chat_loop._stream_agent_response("First question")
        await chat_loop._stream_agent_response("Second question")

        success = chat_loop.save_conversation()
        assert success is True

        # Find and read JSON file (exclude index)
        sessions_dir = tmp_path / "sessions"
        json_files = [f for f in sessions_dir.glob("*.json") if f.name != ".index.json"]
        assert len(json_files) == 1

        with open(json_files[0]) as f:
            data = json.load(f)

        # Verify structure
        assert "conversation" in data
        assert len(data["conversation"]) == 2

        # Verify both entries have query and response
        for entry in data["conversation"]:
            assert "query" in entry
            assert "response" in entry

            # Verify response is not empty
            assert entry["response"].strip() != ""

            # Verify response contains expected content
            assert "Hello!" in entry["response"] or "Simple Sally" in entry["response"]

    @pytest.mark.asyncio
    async def test_saved_files_match_terminal_output(
        self, mock_strands_agent, temp_config, tmp_path
    ):
        """Test that saved files match what was displayed in terminal."""
        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Capture what's stored after streaming
        await chat_loop._stream_agent_response("Hello there")

        # What was stored in conversation history
        stored_response = chat_loop.conversation_history[0]["response"]

        # Save and read back from file
        chat_loop.save_conversation()

        sessions_dir = tmp_path / "sessions"
        json_files = [f for f in sessions_dir.glob("*.json") if f.name != ".index.json"]

        with open(json_files[0]) as f:
            data = json.load(f)

        saved_response = data["conversation"][0]["response"]

        # They should match exactly
        assert stored_response == saved_response
        assert saved_response.strip() != ""


class TestHarmonyProcessorNonInterference:
    """Test that Harmony processor doesn't interfere with non-Harmony agents."""

    def test_harmony_not_enabled_for_claude_agents(self):
        """Test that Harmony is not enabled for Claude Sonnet agents."""
        # Create mock Claude agent with limited spec to avoid Mock
        # returning True for all attributes
        agent = Mock(spec=["name", "model"])
        agent.name = "Claude Agent"
        agent.model = Mock(spec=["model_id"])
        agent.model.model_id = "claude-sonnet-4-20250514"

        # Harmony should not detect this as a Harmony agent
        is_harmony = HarmonyProcessor.detect_harmony_agent(
            agent, model_id="claude-sonnet-4-20250514"
        )

        assert is_harmony is False

    def test_harmony_empty_channel_fallback(self):
        """
        Test Harmony processor falls back to original text when channels empty.
        """
        processor = HarmonyProcessor(show_detailed_thinking=False)

        # Simulate response with empty final channel
        response_text = "This is the actual response text"
        processed = {
            "text": response_text,
            "channels": {
                "final": "",  # Empty channel
                "reasoning": "Some reasoning",
            },
            "has_reasoning": True,
            "has_tools": False,
        }

        # Format for display
        display_text = processor.format_for_display(processed)

        # Should fallback to original text, not empty string
        assert display_text == response_text
        assert display_text != ""


@pytest.mark.skip(reason="Needs rewrite for markdown-only conversation tracking")
class TestManualVsAutoSave:
    """Test both manual save and auto_save scenarios."""

    @pytest.mark.asyncio
    async def test_manual_save_works(self, mock_strands_agent, temp_config, tmp_path):
        """Test manual save command works correctly."""
        temp_config.config_data["features"]["auto_save"] = False

        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Have a conversation
        await chat_loop._stream_agent_response("Test question")

        # Manually save
        success = chat_loop.save_conversation()
        assert success is True

        # Verify file exists and has content
        sessions_dir = tmp_path / "sessions"
        json_files = [f for f in sessions_dir.glob("*.json") if f.name != ".index.json"]
        assert len(json_files) == 1

        with open(json_files[0]) as f:
            data = json.load(f)

        assert len(data["conversation"]) == 1
        assert data["conversation"][0]["response"].strip() != ""

    @pytest.mark.asyncio
    async def test_copy_all_command_works(self, mock_strands_agent, temp_config):
        """Test that 'copy all' command has conversation data to copy."""
        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Have a conversation
        await chat_loop._stream_agent_response("First")
        await chat_loop._stream_agent_response("Second")

        # Format conversation as markdown (what copy all does)
        markdown = chat_loop._format_conversation_as_markdown()

        # Should have content
        assert len(markdown) > 100

        # Should have both queries and responses
        assert "First" in markdown
        assert "Second" in markdown
        assert "Simple Sally" in markdown
        assert "Hello!" in markdown


@pytest.mark.skip(reason="Needs rewrite for markdown-only conversation tracking")
class TestMultipleQueryConversation:
    """Test conversations with multiple back-and-forth exchanges."""

    @pytest.mark.asyncio
    async def test_multiple_exchanges_all_saved(
        self, mock_strands_agent, temp_config, tmp_path
    ):
        """Test that all exchanges in a multi-turn conversation are saved."""
        chat_loop = ChatLoop(
            mock_strands_agent,
            "Simple Sally",
            "Test agent",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        # Simulate 5-turn conversation
        queries = [
            "What is Python?",
            "How do I install it?",
            "Can you give me an example?",
            "What about error handling?",
            "Thank you!",
        ]

        for query in queries:
            await chat_loop._stream_agent_response(query)

        # Save conversation
        chat_loop.save_conversation()

        # Verify all saved in JSON
        sessions_dir = tmp_path / "sessions"
        json_files = [f for f in sessions_dir.glob("*.json") if f.name != ".index.json"]

        with open(json_files[0]) as f:
            data = json.load(f)

        assert len(data["conversation"]) == 5

        # Verify each entry has both query and non-empty response
        for i, entry in enumerate(data["conversation"]):
            assert entry["query"] == queries[i]
            assert entry["response"].strip() != ""
            assert "Hello!" in entry["response"] or "Simple Sally" in entry["response"]

        # Verify in markdown
        md_files = list(sessions_dir.glob("*.md"))
        md_content = md_files[0].read_text()

        # All queries should appear
        for query in queries:
            assert query in md_content

        # Should have 5 "You:" and 5 "Simple Sally:" entries
        assert md_content.count("**You:**") == 5
        assert md_content.count("**Simple Sally:**") == 5


@pytest.mark.skip(reason="Needs rewrite for markdown-only conversation tracking")
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_streaming_response(self, temp_config):
        """Test handling of agent that returns no text chunks."""
        agent = Mock()
        agent.name = "Empty Agent"

        async def empty_stream(query):
            """Yield events but no text."""
            event = Mock()
            event.delta = Mock()
            event.delta.text = ""
            yield event

        agent.stream_async = empty_stream

        chat_loop = ChatLoop(
            agent,
            "Empty Agent",
            "Test",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        await chat_loop._stream_agent_response("Test")

        # Should still track the conversation entry
        assert len(chat_loop.conversation_history) == 1

        # Response may be empty but should exist
        assert "response" in chat_loop.conversation_history[0]

    @pytest.mark.asyncio
    async def test_mixed_event_types(self, temp_config):
        """Test agent that returns different event types in same stream."""
        agent = Mock()
        agent.name = "Mixed Agent"

        async def mixed_stream(query):
            """Yield different event types."""
            # First event with .data
            event1 = Mock(spec=["data"])
            event1.data = "Part 1 "
            yield event1

            # Second event with .delta
            event2 = Mock(spec=["delta"])
            delta_mock = Mock(spec=["text"])
            delta_mock.text = "Part 2 "
            event2.delta = delta_mock
            yield event2

            # Third event with .text
            event3 = Mock(spec=["text"])
            event3.text = "Part 3"
            yield event3

        agent.stream_async = mixed_stream

        chat_loop = ChatLoop(
            agent,
            "Mixed Agent",
            "Test",
            agent_path="/test/agent.py",
            config=temp_config,
        )

        await chat_loop._stream_agent_response("Test")

        response = chat_loop.conversation_history[0]["response"]

        # Should have collected all parts
        assert "Part 1" in response
        assert "Part 2" in response
        assert "Part 3" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
