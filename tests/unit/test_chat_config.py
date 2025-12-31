"""Tests for ChatConfig component."""

import sys
from pathlib import Path

import pytest

from basic_agent_chat_loop.chat_config import ChatConfig, get_config


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / ".chatrc"
    config_file.write_text(
        """
features:
  show_tokens: false
  rich_enabled: false

behavior:
  max_retries: 5
  timeout: 60.0

ui:
  show_banner: false
"""
    )
    return config_file


@pytest.fixture
def agent_override_config(tmp_path):
    """Create config with agent-specific overrides."""
    config_file = tmp_path / ".chatrc"
    config_file.write_text(
        """
features:
  show_tokens: false

agents:
  'Test Agent':
    features:
      show_tokens: true
  'Another Agent':
    behavior:
      max_retries: 10
"""
    )
    return config_file


class TestChatConfigInitialization:
    """Test ChatConfig initialization."""

    def test_defaults_loaded(self):
        """Test that default configuration is loaded."""
        config = ChatConfig()

        assert config.get("features.show_tokens") is True
        assert config.get("features.rich_enabled") is True
        assert config.get("behavior.max_retries") == 3
        assert config.get("ui.show_banner") is True
        assert config.get("ui.show_status_bar") is True
        assert config.get("harmony.show_detailed_thinking") is True

    def test_load_explicit_config(self, temp_config_file, tmp_path, monkeypatch):
        """Test loading explicit config file."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config = ChatConfig(temp_config_file)

        assert config.get("features.show_tokens") is False
        assert config.get("features.rich_enabled") is False
        assert config.get("behavior.max_retries") == 5
        assert config.get("behavior.timeout") == 60.0

    def test_nonexistent_config_uses_defaults(self):
        """Test that nonexistent config file falls back to defaults."""
        config = ChatConfig(Path("/nonexistent/.chatrc"))

        assert config.get("features.show_tokens") is True
        assert config.get("behavior.max_retries") == 3


class TestConfigGet:
    """Test config value retrieval."""

    def test_get_nested_value(self, temp_config_file, tmp_path, monkeypatch):
        """Test getting nested configuration values."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config = ChatConfig(temp_config_file)

        assert config.get("features.show_tokens") is False
        assert config.get("behavior.max_retries") == 5

    def test_get_with_default(self):
        """Test getting value with default fallback."""
        config = ChatConfig()

        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("features.nonexistent", False) is False

    def test_get_agent_override(self, agent_override_config):
        """Test agent-specific configuration override."""
        config = ChatConfig(agent_override_config)

        # Global config
        assert config.get("features.show_tokens") is False

        # Agent-specific override
        assert config.get("features.show_tokens", agent_name="Test Agent") is True

        # Different agent
        assert config.get("behavior.max_retries", agent_name="Another Agent") == 10

    def test_get_agent_fallback_to_global(self, agent_override_config):
        """Test that agent config falls back to global if not overridden."""
        config = ChatConfig(agent_override_config)

        # Not overridden for this agent, should use global
        assert config.get("features.show_tokens", agent_name="Unknown Agent") is False


class TestConfigGetSection:
    """Test getting entire configuration sections."""

    def test_get_section(self, temp_config_file, tmp_path, monkeypatch):
        """Test getting an entire configuration section."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config = ChatConfig(temp_config_file)

        features = config.get_section("features")
        assert features["show_tokens"] is False
        assert features["rich_enabled"] is False

        behavior = config.get_section("behavior")
        assert behavior["max_retries"] == 5
        assert behavior["timeout"] == 60.0

    def test_get_section_with_agent_override(self, agent_override_config):
        """Test getting section with agent-specific overrides applied."""
        config = ChatConfig(agent_override_config)

        # Global section
        features = config.get_section("features")
        assert features["show_tokens"] is False

        # Agent-specific section
        agent_features = config.get_section("features", agent_name="Test Agent")
        assert agent_features["show_tokens"] is True

    def test_get_colors_section_decodes_escapes(self, tmp_path, monkeypatch):
        """Test that colors section contains valid color values."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config = ChatConfig()

        colors = config.get_section("colors")

        # Should have color names or ANSI escape codes
        assert colors["user"] in ["bright_white", "\033[97m"]
        assert colors["agent"] in ["bright_blue", "\033[94m"]
        assert colors["error"] in ["bright_red", "\033[91m"]
        # Default colors should be color names now
        assert colors["user"] == "bright_white"
        assert colors["agent"] == "bright_blue"


class TestConfigSet:
    """Test setting configuration values at runtime."""

    def test_set_global_value(self):
        """Test setting a global configuration value."""
        config = ChatConfig()

        config.set("features.show_tokens", True)
        assert config.get("features.show_tokens") is True

    def test_set_creates_nested_keys(self):
        """Test that set creates nested keys if they don't exist."""
        config = ChatConfig()

        config.set("new.nested.key", "value")
        assert config.get("new.nested.key") == "value"

    def test_set_agent_specific_value(self):
        """Test setting agent-specific configuration."""
        config = ChatConfig()

        config.set("features.show_tokens", False, agent_name="My Agent")

        # Global should remain unchanged (default is True now)
        assert config.get("features.show_tokens") is True

        # Agent-specific should be set
        assert config.get("features.show_tokens", agent_name="My Agent") is False


class TestConfigMerging:
    """Test configuration merging behavior."""

    def test_merge_preserves_defaults(self, temp_config_file, tmp_path, monkeypatch):
        """Test that user config merges with defaults."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config = ChatConfig(temp_config_file)

        # User-defined values
        assert config.get("features.show_tokens") is False

        # Default values not in user config
        assert config.get("features.readline_enabled") is True
        assert config.get("ui.show_duration") is True

    def test_hierarchical_config_loading(self, tmp_path, monkeypatch):
        """Test that configs are loaded in correct hierarchy."""
        # Create global config
        global_config = tmp_path / ".chatrc"
        global_config.write_text(
            """
features:
  show_tokens: true
behavior:
  max_retries: 5
"""
        )

        # Create project config
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config = project_dir / ".chatrc"
        project_config.write_text(
            """
behavior:
  max_retries: 10
ui:
  show_banner: false
"""
        )

        # Simulate being in project directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setattr(Path, "cwd", lambda: project_dir)

        config = ChatConfig()

        # Project config should override global
        assert config.get("behavior.max_retries") == 10

        # Project config adds new values
        assert config.get("ui.show_banner") is False

        # Global config values not overridden
        assert config.get("features.show_tokens") is True


class TestExpandPath:
    """Test path expansion utilities."""

    def test_expand_path_with_tilde(self):
        """Test expanding paths with ~ for home directory."""
        config = ChatConfig()

        expanded = config.expand_path("~/test/path")
        assert "~" not in str(expanded)
        assert expanded.is_absolute()

    def test_expand_path_with_environment_variable(self, monkeypatch):
        """Test expanding paths with environment variables."""
        monkeypatch.setenv("TEST_VAR", "/test/value")

        config = ChatConfig()
        # Use platform-appropriate syntax
        if sys.platform == "win32":
            expanded = config.expand_path("%TEST_VAR%/path")
        else:
            expanded = config.expand_path("$TEST_VAR/path")

        assert "/test/value/path" in str(expanded) or "\\test\\value\\path" in str(
            expanded
        )


class TestInvalidConfig:
    """Test handling of invalid configuration files."""

    def test_invalid_yaml_falls_back_to_defaults(self, tmp_path):
        """Test that invalid YAML falls back to defaults."""
        config_file = tmp_path / ".chatrc"
        config_file.write_text("invalid: yaml: [unclosed")

        config = ChatConfig(config_file)

        # Should use defaults
        assert config.get("features.show_tokens") is True
        assert config.get("behavior.max_retries") == 3

    def test_empty_config_file(self, tmp_path):
        """Test that empty config file uses defaults."""
        config_file = tmp_path / ".chatrc"
        config_file.write_text("")

        config = ChatConfig(config_file)

        # Should use defaults
        assert config.get("features.show_tokens") is True


class TestGetConfigFunction:
    """Test the global get_config function."""

    def test_get_config_singleton(self):
        """Test that get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_get_config_reload(self, temp_config_file, tmp_path, monkeypatch):
        """Test that get_config can reload configuration."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config1 = get_config()
        config2 = get_config(temp_config_file, reload=True)

        # Should be different configuration
        assert config1.get("features.show_tokens") != config2.get(
            "features.show_tokens"
        )


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_deeply_nested_config(self):
        """Test deeply nested configuration structure."""
        config = ChatConfig()

        config.set("level1.level2.level3.value", "deep")
        assert config.get("level1.level2.level3.value") == "deep"

    def test_numeric_values(self, tmp_path, monkeypatch):
        """Test numeric configuration values."""
        # Isolate by redirecting home and cwd to temp directories with no configs
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        config_file = tmp_path / ".chatrc"
        config_file.write_text(
            """
behavior:
  max_retries: 100
  timeout: 3.14159
  retry_delay: 0
"""
        )

        config = ChatConfig(config_file)

        assert config.get("behavior.max_retries") == 100
        assert config.get("behavior.timeout") == 3.14159
        assert config.get("behavior.retry_delay") == 0

    def test_boolean_values(self, tmp_path):
        """Test boolean configuration values."""
        config_file = tmp_path / ".chatrc"
        config_file.write_text(
            """
features:
  option_true: true
  option_false: false
  option_yes: yes
  option_no: no
"""
        )

        config = ChatConfig(config_file)

        assert config.get("features.option_true") is True
        assert config.get("features.option_false") is False
        assert config.get("features.option_yes") is True
        assert config.get("features.option_no") is False
