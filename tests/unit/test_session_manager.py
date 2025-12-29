"""Tests for SessionManager component."""

import json
import sys
import time
from datetime import datetime

import pytest

from basic_agent_chat_loop.components.session_manager import SessionInfo, SessionManager


@pytest.fixture
def session_manager(tmp_path):
    """Create SessionManager with temporary sessions directory."""
    sessions_dir = tmp_path / "sessions"
    return SessionManager(sessions_dir=sessions_dir)


@pytest.fixture
def sample_conversation():
    """Create sample conversation data for testing."""
    return [
        {
            "timestamp": time.time(),
            "query": "What is Python?",
            "response": "Python is a programming language...",
            "duration": 2.3,
            "usage": {"input_tokens": 234, "output_tokens": 456},
        },
        {
            "timestamp": time.time() + 10,
            "query": "Tell me more",
            "response": "Python is widely used for...",
            "duration": 1.8,
            "usage": {"input_tokens": 123, "output_tokens": 567},
        },
    ]


class TestSessionManagerInitialization:
    """Test SessionManager initialization."""

    def test_initialization_does_not_create_directory(self, tmp_path):
        """Test that initialization does not create sessions directory."""
        sessions_dir = tmp_path / "sessions"
        SessionManager(sessions_dir=sessions_dir)
        # Directory is not created until save_session is called
        assert not sessions_dir.exists()

    def test_initialization_with_existing_directory(self, tmp_path):
        """Test initialization with existing sessions directory."""
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        manager = SessionManager(sessions_dir=sessions_dir)
        assert manager.sessions_dir == sessions_dir


class TestSaveSession:
    """Test saving sessions."""

    def test_save_session_creates_files(
        self, session_manager, sample_conversation, tmp_path
    ):
        """Test that save_session creates both JSON and markdown files."""
        success, message = session_manager.save_session(
            session_id="test_20250126_120000",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="A test agent",
            conversation=sample_conversation,
            metadata={"duration": 120},
        )

        assert success is True
        assert "Session saved" in message

        # Check files were created
        sessions_dir = session_manager.sessions_dir
        assert (sessions_dir / "test_20250126_120000.json").exists()
        assert (sessions_dir / "test_20250126_120000.md").exists()

    def test_save_session_creates_json_with_correct_structure(
        self, session_manager, sample_conversation
    ):
        """Test that saved JSON has the correct structure."""
        session_manager.save_session(
            session_id="test_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test description",
            conversation=sample_conversation,
            metadata={"duration": 120},
        )

        json_path = session_manager.sessions_dir / "test_session.json"
        with open(json_path) as f:
            data = json.load(f)

        assert data["session_id"] == "test_session"
        assert data["agent_name"] == "TestAgent"
        assert data["agent_path"] == "/path/to/agent.py"
        assert data["agent_description"] == "Test description"
        assert len(data["conversation"]) == 2
        assert data["metadata"]["total_queries"] == 2

    def test_save_session_updates_index(self, session_manager, sample_conversation):
        """Test that save_session updates the session index."""
        session_manager.save_session(
            session_id="test_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        index_path = session_manager.index_file
        assert index_path.exists()

        with open(index_path) as f:
            index = json.load(f)

        assert len(index["sessions"]) == 1
        assert index["sessions"][0]["session_id"] == "test_session"

    def test_save_empty_conversation_fails(self, session_manager):
        """Test that saving empty conversation fails."""
        success, message = session_manager.save_session(
            session_id="empty_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=[],
        )

        assert success is False
        assert "No conversation to save" in message

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="File permissions work differently on Windows"
    )
    def test_save_session_sets_secure_permissions(
        self, session_manager, sample_conversation
    ):
        """Test that saved files have secure permissions (0600)."""
        session_manager.save_session(
            session_id="secure_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        json_path = session_manager.sessions_dir / "secure_session.json"
        md_path = session_manager.sessions_dir / "secure_session.md"

        # Check permissions (owner read/write only)
        assert oct(json_path.stat().st_mode)[-3:] == "600"
        assert oct(md_path.stat().st_mode)[-3:] == "600"


class TestLoadSession:
    """Test loading sessions."""

    def test_load_existing_session(self, session_manager, sample_conversation):
        """Test loading an existing session."""
        # Save a session first
        session_manager.save_session(
            session_id="load_test",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        # Load it back
        data = session_manager.load_session("load_test")

        assert data is not None
        assert data["session_id"] == "load_test"
        assert len(data["conversation"]) == 2

    def test_load_nonexistent_session(self, session_manager):
        """Test loading a non-existent session returns None."""
        data = session_manager.load_session("nonexistent")
        assert data is None


class TestListSessions:
    """Test listing sessions."""

    def test_list_sessions_empty(self, session_manager):
        """Test listing sessions when none exist."""
        sessions = session_manager.list_sessions()
        assert len(sessions) == 0

    def test_list_sessions_returns_all(self, session_manager, sample_conversation):
        """Test that list_sessions returns all saved sessions."""
        # Save multiple sessions
        for i in range(3):
            session_manager.save_session(
                session_id=f"session_{i}",
                agent_name=f"Agent{i}",
                agent_path="/path/to/agent.py",
                agent_description="Test",
                conversation=sample_conversation,
            )

        sessions = session_manager.list_sessions()
        assert len(sessions) == 3

    def test_list_sessions_filter_by_agent(self, session_manager, sample_conversation):
        """Test filtering sessions by agent name."""
        session_manager.save_session(
            session_id="session_1",
            agent_name="AgentA",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )
        session_manager.save_session(
            session_id="session_2",
            agent_name="AgentB",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        sessions = session_manager.list_sessions(agent_name="AgentA")
        assert len(sessions) == 1
        assert sessions[0].agent_name == "AgentA"

    def test_list_sessions_respects_limit(self, session_manager, sample_conversation):
        """Test that list_sessions respects the limit parameter."""
        # Save multiple sessions
        for i in range(5):
            session_manager.save_session(
                session_id=f"session_{i}",
                agent_name="TestAgent",
                agent_path="/path/to/agent.py",
                agent_description="Test",
                conversation=sample_conversation,
            )

        sessions = session_manager.list_sessions(limit=3)
        assert len(sessions) == 3

    def test_list_sessions_most_recent_first(
        self, session_manager, sample_conversation
    ):
        """Test that sessions are returned in reverse chronological order."""
        # Save sessions with delays to ensure different timestamps
        for i in range(3):
            session_manager.save_session(
                session_id=f"session_{i}",
                agent_name="TestAgent",
                agent_path="/path/to/agent.py",
                agent_description="Test",
                conversation=sample_conversation,
            )
            time.sleep(0.01)

        sessions = session_manager.list_sessions()
        # Most recent (session_2) should be first
        assert sessions[0].session_id == "session_2"
        assert sessions[1].session_id == "session_1"
        assert sessions[2].session_id == "session_0"


class TestDeleteSession:
    """Test deleting sessions."""

    def test_delete_existing_session(self, session_manager, sample_conversation):
        """Test deleting an existing session."""
        session_manager.save_session(
            session_id="delete_me",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        success, message = session_manager.delete_session("delete_me")
        assert success is True
        assert "Deleted session" in message

        # Verify files are deleted
        assert not (session_manager.sessions_dir / "delete_me.json").exists()
        assert not (session_manager.sessions_dir / "delete_me.md").exists()

    def test_delete_nonexistent_session(self, session_manager):
        """Test deleting a non-existent session."""
        success, message = session_manager.delete_session("nonexistent")
        assert success is False
        assert "not found" in message

    def test_delete_session_removes_from_index(
        self, session_manager, sample_conversation
    ):
        """Test that delete_session removes entry from index."""
        session_manager.save_session(
            session_id="indexed_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        session_manager.delete_session("indexed_session")

        with open(session_manager.index_file) as f:
            index = json.load(f)

        assert len(index["sessions"]) == 0


class TestSearchSessions:
    """Test searching sessions."""

    def test_search_sessions_by_preview(self, session_manager, sample_conversation):
        """Test searching sessions by query text in preview."""
        session_manager.save_session(
            session_id="python_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,  # First query is "What is Python?"
        )

        results = session_manager.search_sessions("Python")
        assert len(results) == 1
        assert results[0].session_id == "python_session"

    def test_search_sessions_by_agent_name(self, session_manager, sample_conversation):
        """Test searching sessions by agent name."""
        session_manager.save_session(
            session_id="test_session",
            agent_name="CodeHelper",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        results = session_manager.search_sessions("CodeHelper")
        assert len(results) == 1

    def test_search_sessions_case_insensitive(
        self, session_manager, sample_conversation
    ):
        """Test that search is case insensitive."""
        session_manager.save_session(
            session_id="test_session",
            agent_name="TestAgent",
            agent_path="/path/to/agent.py",
            agent_description="Test",
            conversation=sample_conversation,
        )

        results = session_manager.search_sessions("PYTHON")
        assert len(results) == 1


class TestSessionInfo:
    """Test SessionInfo dataclass."""

    def test_session_info_to_dict(self):
        """Test SessionInfo conversion to dictionary."""
        info = SessionInfo(
            session_id="test",
            agent_name="TestAgent",
            agent_path="/path",
            created=datetime(2025, 1, 26, 14, 30),
            last_updated=datetime(2025, 1, 26, 15, 45),
            query_count=10,
            total_tokens=5000,
            preview="Test query...",
        )

        data = info.to_dict()
        assert data["session_id"] == "test"
        assert data["agent_name"] == "TestAgent"
        assert data["query_count"] == 10

    def test_session_info_from_dict(self):
        """Test SessionInfo creation from dictionary."""
        data = {
            "session_id": "test",
            "agent_name": "TestAgent",
            "agent_path": "/path",
            "created": "2025-01-26T14:30:00",
            "last_updated": "2025-01-26T15:45:00",
            "query_count": 10,
            "total_tokens": 5000,
            "preview": "Test query...",
        }

        info = SessionInfo.from_dict(data)
        assert info.session_id == "test"
        assert info.agent_name == "TestAgent"
        assert info.query_count == 10


class TestCleanupOldSessions:
    """Test cleanup of old sessions."""

    def test_cleanup_old_sessions(self, session_manager, sample_conversation):
        """Test deleting sessions older than specified days."""
        # This test would require mocking time to create "old" sessions
        # For now, verify the method exists and runs without error
        count, message = session_manager.cleanup_old_sessions(max_age_days=30)
        assert count == 0
        assert "Deleted 0 sessions" in message
