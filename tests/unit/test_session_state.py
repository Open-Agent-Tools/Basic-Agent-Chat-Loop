"""Tests for SessionState component."""

import time

from basic_agent_chat_loop.components.session_state import SessionState


class TestSessionStateInitialization:
    """Test SessionState initialization."""

    def test_initialization_basic(self):
        """Test basic initialization."""
        state = SessionState("TestAgent")
        assert state.session_id.startswith("testagent_")
        assert state.query_count == 0
        assert state.conversation_markdown == []
        assert state.last_query == ""
        assert state.last_response == ""
        assert state.last_accumulated_input == 0
        assert state.last_accumulated_output == 0

    def test_session_id_generation(self):
        """Test session ID is generated correctly."""
        state = SessionState("MyAgent")
        assert state.session_id.startswith("myagent_")
        # Should contain timestamp in format YYYYMMDD_HHMMSS
        parts = state.session_id.split("_")
        assert len(parts) == 3  # agent_YYYYMMDD_HHMMSS
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS

    def test_session_id_with_spaces(self):
        """Test session ID generation with spaces in agent name."""
        state = SessionState("My Agent")
        assert state.session_id.startswith("my_agent_")
        assert " " not in state.session_id

    def test_session_id_with_slashes(self):
        """Test session ID generation with slashes in agent name."""
        state = SessionState("provider/model")
        assert state.session_id.startswith("provider_model_")
        assert "/" not in state.session_id

    def test_session_start_time_set(self):
        """Test session start time is set."""
        before = time.time()
        state = SessionState("TestAgent")
        after = time.time()
        assert before <= state.session_start_time <= after

    def test_unique_session_ids(self):
        """Test multiple instances get unique session IDs."""
        state1 = SessionState("TestAgent")
        time.sleep(1.1)  # Ensure different timestamp
        state2 = SessionState("TestAgent")
        assert state1.session_id != state2.session_id


class TestQueryCountManagement:
    """Test query count tracking."""

    def test_increment_query_count(self):
        """Test incrementing query count."""
        state = SessionState("TestAgent")
        assert state.query_count == 0

        count = state.increment_query_count()
        assert count == 1
        assert state.query_count == 1

    def test_multiple_increments(self):
        """Test multiple query count increments."""
        state = SessionState("TestAgent")

        for i in range(1, 6):
            count = state.increment_query_count()
            assert count == i
            assert state.query_count == i

    def test_increment_returns_new_count(self):
        """Test increment returns the new count value."""
        state = SessionState("TestAgent")
        result = state.increment_query_count()
        assert result == state.query_count


class TestLastQueryResponse:
    """Test last query/response tracking."""

    def test_update_last_query(self):
        """Test updating last query."""
        state = SessionState("TestAgent")
        state.update_last_query("What is Python?")
        assert state.last_query == "What is Python?"

    def test_update_last_query_multiple(self):
        """Test updating last query multiple times."""
        state = SessionState("TestAgent")
        state.update_last_query("First query")
        assert state.last_query == "First query"

        state.update_last_query("Second query")
        assert state.last_query == "Second query"

    def test_update_last_response(self):
        """Test updating last response."""
        state = SessionState("TestAgent")
        state.update_last_response("Python is a programming language.")
        assert state.last_response == "Python is a programming language."

    def test_update_last_response_multiple(self):
        """Test updating last response multiple times."""
        state = SessionState("TestAgent")
        state.update_last_response("First response")
        assert state.last_response == "First response"

        state.update_last_response("Second response")
        assert state.last_response == "Second response"

    def test_has_last_query_initially_false(self):
        """Test has_last_query is false initially."""
        state = SessionState("TestAgent")
        assert state.has_last_query() is False

    def test_has_last_query_after_update(self):
        """Test has_last_query is true after update."""
        state = SessionState("TestAgent")
        state.update_last_query("Test query")
        assert state.has_last_query() is True

    def test_has_last_query_empty_string(self):
        """Test has_last_query with empty string."""
        state = SessionState("TestAgent")
        state.update_last_query("")
        assert state.has_last_query() is False

    def test_has_last_response_initially_false(self):
        """Test has_last_response is false initially."""
        state = SessionState("TestAgent")
        assert state.has_last_response() is False

    def test_has_last_response_after_update(self):
        """Test has_last_response is true after update."""
        state = SessionState("TestAgent")
        state.update_last_response("Test response")
        assert state.has_last_response() is True

    def test_has_last_response_empty_string(self):
        """Test has_last_response with empty string."""
        state = SessionState("TestAgent")
        state.update_last_response("")
        assert state.has_last_response() is False


class TestConversationHistory:
    """Test conversation history management."""

    def test_add_conversation_entry(self):
        """Test adding conversation entry."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("User: Hello")
        assert len(state.conversation_markdown) == 1
        assert state.conversation_markdown[0] == "User: Hello"

    def test_add_multiple_entries(self):
        """Test adding multiple conversation entries."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("User: Hello")
        state.add_conversation_entry("Agent: Hi there!")
        state.add_conversation_entry("User: How are you?")

        assert len(state.conversation_markdown) == 3
        assert state.conversation_markdown[0] == "User: Hello"
        assert state.conversation_markdown[1] == "Agent: Hi there!"
        assert state.conversation_markdown[2] == "User: How are you?"

    def test_get_conversation_history(self):
        """Test getting conversation history."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("Entry 1")
        state.add_conversation_entry("Entry 2")

        history = state.get_conversation_history()
        assert history == ["Entry 1", "Entry 2"]

    def test_get_conversation_history_returns_copy(self):
        """Test get_conversation_history returns a copy."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("Entry 1")

        history = state.get_conversation_history()
        history.append("Entry 2")

        # Original should not be modified
        assert len(state.conversation_markdown) == 1

    def test_clear_conversation_history(self):
        """Test clearing conversation history."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("Entry 1")
        state.add_conversation_entry("Entry 2")

        state.clear_conversation_history()
        assert len(state.conversation_markdown) == 0

    def test_has_conversation_history_initially_false(self):
        """Test has_conversation_history is false initially."""
        state = SessionState("TestAgent")
        assert state.has_conversation_history() is False

    def test_has_conversation_history_after_add(self):
        """Test has_conversation_history is true after adding entry."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("Entry 1")
        assert state.has_conversation_history() is True

    def test_has_conversation_history_after_clear(self):
        """Test has_conversation_history is false after clear."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("Entry 1")
        state.clear_conversation_history()
        assert state.has_conversation_history() is False


class TestSessionDuration:
    """Test session duration tracking."""

    def test_get_session_duration_initial(self):
        """Test session duration initially is near zero."""
        state = SessionState("TestAgent")
        duration = state.get_session_duration()
        assert 0 <= duration < 0.1  # Should be very small

    def test_get_session_duration_after_delay(self):
        """Test session duration after a delay."""
        state = SessionState("TestAgent")
        time.sleep(0.5)
        duration = state.get_session_duration()
        assert 0.4 <= duration <= 0.7  # Account for timing variance

    def test_get_session_duration_increases(self):
        """Test session duration increases over time."""
        state = SessionState("TestAgent")
        duration1 = state.get_session_duration()
        time.sleep(0.2)
        duration2 = state.get_session_duration()
        assert duration2 > duration1


class TestAccumulatedUsage:
    """Test accumulated usage delta calculation."""

    def test_update_accumulated_usage_initial(self):
        """Test initial accumulated usage update."""
        state = SessionState("TestAgent")
        delta_in, delta_out = state.update_accumulated_usage(100, 50)

        assert delta_in == 100
        assert delta_out == 50
        assert state.last_accumulated_input == 100
        assert state.last_accumulated_output == 50

    def test_update_accumulated_usage_delta(self):
        """Test accumulated usage delta calculation."""
        state = SessionState("TestAgent")
        # First update
        state.update_accumulated_usage(100, 50)

        # Second update with cumulative values
        delta_in, delta_out = state.update_accumulated_usage(250, 125)

        assert delta_in == 150  # 250 - 100
        assert delta_out == 75  # 125 - 50
        assert state.last_accumulated_input == 250
        assert state.last_accumulated_output == 125

    def test_update_accumulated_usage_multiple(self):
        """Test multiple accumulated usage updates."""
        state = SessionState("TestAgent")

        # Update 1
        delta1 = state.update_accumulated_usage(100, 50)
        assert delta1 == (100, 50)

        # Update 2
        delta2 = state.update_accumulated_usage(200, 100)
        assert delta2 == (100, 50)

        # Update 3
        delta3 = state.update_accumulated_usage(350, 175)
        assert delta3 == (150, 75)

    def test_update_accumulated_usage_zero_delta(self):
        """Test accumulated usage with zero delta."""
        state = SessionState("TestAgent")
        state.update_accumulated_usage(100, 50)

        # Same values again
        delta_in, delta_out = state.update_accumulated_usage(100, 50)
        assert delta_in == 0
        assert delta_out == 0


class TestReset:
    """Test session state reset."""

    def test_reset_clears_query_count(self):
        """Test reset clears query count."""
        state = SessionState("TestAgent")
        state.increment_query_count()
        state.increment_query_count()

        state.reset("TestAgent")
        assert state.query_count == 0

    def test_reset_clears_conversation(self):
        """Test reset clears conversation history."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("Entry 1")
        state.add_conversation_entry("Entry 2")

        state.reset("TestAgent")
        assert len(state.conversation_markdown) == 0

    def test_reset_clears_last_query_response(self):
        """Test reset clears last query and response."""
        state = SessionState("TestAgent")
        state.update_last_query("Test query")
        state.update_last_response("Test response")

        state.reset("TestAgent")
        assert state.last_query == ""
        assert state.last_response == ""

    def test_reset_clears_accumulated_usage(self):
        """Test reset clears accumulated usage."""
        state = SessionState("TestAgent")
        state.update_accumulated_usage(100, 50)

        state.reset("TestAgent")
        assert state.last_accumulated_input == 0
        assert state.last_accumulated_output == 0

    def test_reset_generates_new_session_id(self):
        """Test reset generates new session ID."""
        state = SessionState("TestAgent")
        old_session_id = state.session_id

        time.sleep(1.1)  # Ensure different timestamp
        state.reset("TestAgent")

        assert state.session_id != old_session_id
        assert state.session_id.startswith("testagent_")

    def test_reset_resets_start_time(self):
        """Test reset resets session start time."""
        state = SessionState("TestAgent")
        old_start = state.session_start_time

        time.sleep(0.5)
        state.reset("TestAgent")

        assert state.session_start_time > old_start

    def test_reset_with_different_agent(self):
        """Test reset with different agent name."""
        state = SessionState("TestAgent")
        state.reset("NewAgent")

        assert state.session_id.startswith("newagent_")


class TestStateSummary:
    """Test state summary functionality."""

    def test_get_state_summary_initial(self):
        """Test state summary for initial state."""
        state = SessionState("TestAgent")
        summary = state.get_state_summary()

        assert "session_id" in summary
        assert summary["query_count"] == 0
        assert summary["conversation_entries"] == 0
        assert summary["has_last_query"] is False
        assert summary["has_last_response"] is False
        assert summary["accumulated_input"] == 0
        assert summary["accumulated_output"] == 0

    def test_get_state_summary_with_data(self):
        """Test state summary with populated data."""
        state = SessionState("TestAgent")
        state.increment_query_count()
        state.increment_query_count()
        state.add_conversation_entry("Entry 1")
        state.update_last_query("Query")
        state.update_last_response("Response")
        state.update_accumulated_usage(100, 50)

        summary = state.get_state_summary()

        assert summary["query_count"] == 2
        assert summary["conversation_entries"] == 1
        assert summary["has_last_query"] is True
        assert summary["has_last_response"] is True
        assert summary["accumulated_input"] == 100
        assert summary["accumulated_output"] == 50

    def test_get_state_summary_includes_duration(self):
        """Test state summary includes session duration."""
        state = SessionState("TestAgent")
        time.sleep(0.3)

        summary = state.get_state_summary()
        assert "session_duration" in summary
        assert summary["session_duration"] >= 0.3


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_very_long_agent_name(self):
        """Test with very long agent name."""
        long_name = "A" * 200
        state = SessionState(long_name)
        assert state.session_id.startswith(long_name.lower() + "_")

    def test_unicode_agent_name(self):
        """Test with Unicode agent name."""
        state = SessionState("Agent_世界")
        assert state.session_id.startswith("agent_世界_")

    def test_empty_conversation_entry(self):
        """Test adding empty conversation entry."""
        state = SessionState("TestAgent")
        state.add_conversation_entry("")
        assert len(state.conversation_markdown) == 1
        assert state.conversation_markdown[0] == ""

    def test_very_long_conversation_entry(self):
        """Test adding very long conversation entry."""
        state = SessionState("TestAgent")
        long_entry = "A" * 10000
        state.add_conversation_entry(long_entry)
        assert state.conversation_markdown[0] == long_entry

    def test_multiline_conversation_entry(self):
        """Test adding multiline conversation entry."""
        state = SessionState("TestAgent")
        entry = "Line 1\nLine 2\nLine 3"
        state.add_conversation_entry(entry)
        assert state.conversation_markdown[0] == entry

    def test_negative_accumulated_usage(self):
        """Test accumulated usage can handle decreasing values."""
        state = SessionState("TestAgent")
        state.update_accumulated_usage(100, 50)

        # Decreasing values (shouldn't happen but test resilience)
        delta_in, delta_out = state.update_accumulated_usage(50, 25)
        assert delta_in == -50
        assert delta_out == -25
