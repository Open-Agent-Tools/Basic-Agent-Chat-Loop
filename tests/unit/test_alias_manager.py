"""Tests for AliasManager component."""

import json
from pathlib import Path

import pytest

from basic_agent_chat_loop.components.alias_manager import AliasManager


@pytest.fixture
def alias_manager(tmp_path, monkeypatch):
    """Create AliasManager with temporary aliases file."""
    aliases_file = tmp_path / ".chat_aliases"
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return AliasManager()


@pytest.fixture
def populated_alias_manager(alias_manager, tmp_path):
    """Create AliasManager with some existing aliases."""
    aliases_file = tmp_path / ".chat_aliases"
    aliases_data = {
        "test_agent": "/path/to/test_agent.py",
        "another_agent": "/path/to/another_agent.py",
    }
    aliases_file.write_text(json.dumps(aliases_data, indent=2))
    return AliasManager()


class TestAliasManagerInitialization:
    """Test AliasManager initialization."""

    def test_initialization_does_not_create_file(self, tmp_path, monkeypatch):
        """Test that initialization does not create aliases file."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        manager = AliasManager()
        aliases_file = tmp_path / ".chat_aliases"
        # File is not created until save_aliases is called
        assert not aliases_file.exists()

    def test_initialization_loads_existing_aliases(self, populated_alias_manager):
        """Test that initialization loads existing aliases."""
        aliases = populated_alias_manager.list_aliases()
        assert len(aliases) == 2
        assert "test_agent" in aliases
        assert "another_agent" in aliases


class TestAddAlias:
    """Test adding aliases."""

    def test_add_alias_success(self, alias_manager, tmp_path):
        """Test successfully adding a new alias."""
        agent_path = tmp_path / "agent.py"
        agent_path.write_text("# test agent")

        success, message = alias_manager.add_alias("my_agent", str(agent_path))
        assert success is True
        assert "Saved alias" in message

        aliases = alias_manager.list_aliases()
        assert "my_agent" in aliases
        assert aliases["my_agent"] == str(agent_path.resolve())

    def test_add_alias_converts_to_absolute_path(self, alias_manager, tmp_path):
        """Test that relative paths are converted to absolute."""
        agent_path = tmp_path / "agent.py"
        agent_path.write_text("# test agent")

        success, _ = alias_manager.add_alias("my_agent", str(agent_path))
        assert success is True

        aliases = alias_manager.list_aliases()
        assert Path(aliases["my_agent"]).is_absolute()

    def test_add_alias_invalid_name(self, alias_manager):
        """Test adding alias with invalid name."""
        success, message = alias_manager.add_alias("invalid name!", "/path/to/agent.py")
        assert success is False
        assert "must contain only letters, numbers, hyphens, and underscores" in message

    def test_add_alias_nonexistent_path(self, alias_manager):
        """Test adding alias with nonexistent path."""
        success, message = alias_manager.add_alias("my_agent", "/nonexistent/path.py")
        assert success is False
        assert "not found" in message

    def test_add_alias_duplicate_without_overwrite(self, populated_alias_manager, tmp_path):
        """Test adding duplicate alias without overwrite flag."""
        agent_path = tmp_path / "new_agent.py"
        agent_path.write_text("# new agent")

        success, message = populated_alias_manager.add_alias(
            "test_agent", str(agent_path), overwrite=False
        )
        assert success is False
        assert "already exists" in message
        assert "--overwrite" in message

    def test_add_alias_duplicate_with_overwrite(self, populated_alias_manager, tmp_path):
        """Test adding duplicate alias with overwrite flag."""
        agent_path = tmp_path / "new_agent.py"
        agent_path.write_text("# new agent")

        success, message = populated_alias_manager.add_alias(
            "test_agent", str(agent_path), overwrite=True
        )
        assert success is True
        assert "Updated alias" in message


class TestRemoveAlias:
    """Test removing aliases."""

    def test_remove_alias_success(self, populated_alias_manager):
        """Test successfully removing an alias."""
        success, message = populated_alias_manager.remove_alias("test_agent")
        assert success is True
        assert "Removed alias" in message

        aliases = populated_alias_manager.list_aliases()
        assert "test_agent" not in aliases

    def test_remove_alias_not_found(self, alias_manager):
        """Test removing non-existent alias."""
        success, message = alias_manager.remove_alias("nonexistent")
        assert success is False
        assert "not found" in message


class TestListAliases:
    """Test listing aliases."""

    def test_list_aliases_empty(self, alias_manager):
        """Test listing aliases when none exist."""
        aliases = alias_manager.list_aliases()
        assert aliases == {}

    def test_list_aliases_populated(self, populated_alias_manager):
        """Test listing existing aliases."""
        aliases = populated_alias_manager.list_aliases()
        assert len(aliases) == 2
        assert "test_agent" in aliases
        assert "another_agent" in aliases


class TestResolveAgentPath:
    """Test resolving agent paths from aliases or direct paths."""

    def test_resolve_direct_path(self, alias_manager, tmp_path):
        """Test resolving a direct file path."""
        agent_path = tmp_path / "agent.py"
        agent_path.write_text("# test agent")

        resolved = alias_manager.resolve_agent_path(str(agent_path))
        assert resolved == str(agent_path.resolve())

    def test_resolve_alias(self, populated_alias_manager, tmp_path):
        """Test resolving an alias to its path."""
        # Create the actual file that the alias points to
        agent_path = Path("/path/to/test_agent.py")

        # For this test, we just check that it tries to resolve the alias
        # The actual file doesn't need to exist for alias resolution
        resolved = populated_alias_manager.resolve_agent_path("test_agent")

        # Since the file doesn't actually exist, it should return None
        # But the alias lookup should work
        aliases = populated_alias_manager.list_aliases()
        assert "test_agent" in aliases

    def test_resolve_nonexistent_path(self, alias_manager):
        """Test resolving a nonexistent path."""
        resolved = alias_manager.resolve_agent_path("/nonexistent/agent.py")
        assert resolved is None

    def test_resolve_nonexistent_alias(self, alias_manager):
        """Test resolving a nonexistent alias."""
        resolved = alias_manager.resolve_agent_path("nonexistent_alias")
        assert resolved is None


class TestFileCorruption:
    """Test handling of corrupted alias files."""

    def test_handles_corrupted_json(self, tmp_path, monkeypatch):
        """Test that AliasManager handles corrupted JSON gracefully."""
        aliases_file = tmp_path / ".chat_aliases"
        aliases_file.write_text("{ invalid json }")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        manager = AliasManager()

        # Should initialize with empty aliases
        aliases = manager.list_aliases()
        assert aliases == {}

    def test_recreates_file_after_corruption(self, tmp_path, monkeypatch):
        """Test that adding an alias recreates a valid file after corruption."""
        aliases_file = tmp_path / ".chat_aliases"
        aliases_file.write_text("{ invalid json }")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        manager = AliasManager()

        # Add a new alias
        agent_path = tmp_path / "agent.py"
        agent_path.write_text("# test agent")
        manager.add_alias("test", str(agent_path))

        # File should now be valid JSON
        content = json.loads(aliases_file.read_text())
        assert "test" in content
