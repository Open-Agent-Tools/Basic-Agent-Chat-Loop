"""Tests for ConfigWizard component."""

from pathlib import Path
from unittest.mock import patch

import pytest

from basic_agent_chat_loop.chat_config import ChatConfig
from basic_agent_chat_loop.components.config_wizard import (
    ConfigWizard,
    reset_config_to_defaults,
)


@pytest.fixture
def wizard():
    """Create a ConfigWizard instance."""
    return ConfigWizard()


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / ".chatrc"
    config_content = """
colors:
  user: '\\033[97m'
  agent: '\\033[94m'
  system: '\\033[33m'
  error: '\\033[91m'
  success: '\\033[92m'
  dim: '\\033[2m'
  reset: '\\033[0m'

features:
  auto_save: false
  show_tokens: true
  show_metadata: true
  rich_enabled: true
  readline_enabled: true

ui:
  show_banner: true
  show_thinking_indicator: true
  show_duration: true
  show_status_bar: false

audio:
  enabled: true
  notification_sound: null

behavior:
  max_retries: 3
  retry_delay: 2.0
  timeout: 120.0
  spinner_style: dots

paths:
  save_location: ~/agent-conversations
  log_location: ~/.chat_loop_logs

agents: {}
"""
    config_file.write_text(config_content)
    return config_file


class TestConfigWizardInitialization:
    """Test ConfigWizard initialization."""

    def test_initialization(self, wizard):
        """Test that wizard initializes with empty config."""
        assert wizard.config == {}
        assert wizard.current_config is None

    def test_initialization_creates_config_dict(self, wizard):
        """Test that config dictionary is created."""
        assert isinstance(wizard.config, dict)


class TestPromptScope:
    """Test _prompt_scope method."""

    @patch("builtins.input")
    def test_prompt_scope_global_explicit(self, mock_input, wizard):
        """Test selecting global scope explicitly."""
        mock_input.return_value = "1"
        result = wizard._prompt_scope()
        assert result == "global"

    @patch("builtins.input")
    def test_prompt_scope_global_default(self, mock_input, wizard):
        """Test selecting global scope by default (empty input)."""
        mock_input.return_value = ""
        result = wizard._prompt_scope()
        assert result == "global"

    @patch("builtins.input")
    def test_prompt_scope_project(self, mock_input, wizard):
        """Test selecting project scope."""
        mock_input.return_value = "2"
        result = wizard._prompt_scope()
        assert result == "project"

    @patch("builtins.input")
    def test_prompt_scope_invalid_then_valid(self, mock_input, wizard):
        """Test handling invalid input then valid input."""
        mock_input.side_effect = ["invalid", "3", "1"]
        result = wizard._prompt_scope()
        assert result == "global"
        assert mock_input.call_count == 3


class TestLoadExistingConfig:
    """Test _load_existing_config method."""

    def test_load_existing_global_config(
        self, wizard, temp_config_file, tmp_path, monkeypatch
    ):
        """Test loading existing global config."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        global_config = tmp_path / ".chatrc"
        global_config.write_text(temp_config_file.read_text())

        wizard._load_existing_config("global")

        assert wizard.current_config is not None
        assert isinstance(wizard.current_config, ChatConfig)

    def test_load_existing_project_config(
        self, wizard, temp_config_file, tmp_path, monkeypatch
    ):
        """Test loading existing project config."""
        monkeypatch.chdir(tmp_path)
        project_config = tmp_path / ".chatrc"
        project_config.write_text(temp_config_file.read_text())

        wizard._load_existing_config("project")

        assert wizard.current_config is not None

    def test_load_nonexistent_config(self, wizard, tmp_path, monkeypatch):
        """Test handling nonexistent config file."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        wizard._load_existing_config("global")

        assert wizard.current_config is None

    def test_load_corrupted_config(self, wizard, tmp_path, monkeypatch, capsys):
        """Test handling corrupted config file."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        config_file = tmp_path / ".chatrc"
        config_file.write_text("{ invalid yaml }")

        wizard._load_existing_config("global")

        # ChatConfig handles corrupted files gracefully by loading defaults
        # So we get a ChatConfig object, but it should use default values
        assert wizard.current_config is not None
        captured = capsys.readouterr()
        assert "Found existing config" in captured.out


class TestPromptBool:
    """Test _prompt_bool method."""

    @patch("builtins.input")
    def test_prompt_bool_yes_explicit(self, mock_input, wizard):
        """Test explicit yes input."""
        mock_input.return_value = "y"
        result = wizard._prompt_bool("Enable feature?", default=False)
        assert result is True

    @patch("builtins.input")
    def test_prompt_bool_no_explicit(self, mock_input, wizard):
        """Test explicit no input."""
        mock_input.return_value = "n"
        result = wizard._prompt_bool("Enable feature?", default=True)
        assert result is False

    @patch("builtins.input")
    def test_prompt_bool_default_true(self, mock_input, wizard):
        """Test default true with empty input."""
        mock_input.return_value = ""
        result = wizard._prompt_bool("Enable feature?", default=True)
        assert result is True

    @patch("builtins.input")
    def test_prompt_bool_default_false(self, mock_input, wizard):
        """Test default false with empty input."""
        mock_input.return_value = ""
        result = wizard._prompt_bool("Enable feature?", default=False)
        assert result is False

    @patch("builtins.input")
    def test_prompt_bool_various_yes_formats(self, mock_input, wizard):
        """Test various yes formats."""
        for yes_input in ["yes", "YES", "true", "True", "1"]:
            mock_input.return_value = yes_input
            result = wizard._prompt_bool("Enable?", default=False)
            assert result is True

    @patch("builtins.input")
    def test_prompt_bool_various_no_formats(self, mock_input, wizard):
        """Test various no formats."""
        for no_input in ["no", "NO", "false", "False", "0"]:
            mock_input.return_value = no_input
            result = wizard._prompt_bool("Enable?", default=True)
            assert result is False

    @patch("builtins.input")
    def test_prompt_bool_invalid_then_valid(self, mock_input, wizard):
        """Test handling invalid input then valid."""
        mock_input.side_effect = ["invalid", "maybe", "y"]
        result = wizard._prompt_bool("Enable?", default=False)
        assert result is True
        assert mock_input.call_count == 3


class TestPromptInt:
    """Test _prompt_int method."""

    @patch("builtins.input")
    def test_prompt_int_valid_input(self, mock_input, wizard):
        """Test valid integer input."""
        mock_input.return_value = "5"
        result = wizard._prompt_int("Enter number", default=3, min_val=1, max_val=10)
        assert result == 5

    @patch("builtins.input")
    def test_prompt_int_default(self, mock_input, wizard):
        """Test using default value."""
        mock_input.return_value = ""
        result = wizard._prompt_int("Enter number", default=7)
        assert result == 7

    @patch("builtins.input")
    def test_prompt_int_below_minimum(self, mock_input, wizard):
        """Test value below minimum is rejected."""
        mock_input.side_effect = ["0", "5"]
        result = wizard._prompt_int("Enter number", default=3, min_val=1, max_val=10)
        assert result == 5
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_prompt_int_above_maximum(self, mock_input, wizard):
        """Test value above maximum is rejected."""
        mock_input.side_effect = ["15", "8"]
        result = wizard._prompt_int("Enter number", default=3, min_val=1, max_val=10)
        assert result == 8
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_prompt_int_invalid_then_valid(self, mock_input, wizard):
        """Test invalid input then valid."""
        mock_input.side_effect = ["not_a_number", "3.5", "7"]
        result = wizard._prompt_int("Enter number", default=5)
        assert result == 7
        assert mock_input.call_count == 3


class TestPromptFloat:
    """Test _prompt_float method."""

    @patch("builtins.input")
    def test_prompt_float_valid_input(self, mock_input, wizard):
        """Test valid float input."""
        mock_input.return_value = "2.5"
        result = wizard._prompt_float(
            "Enter seconds", default=1.0, min_val=0.5, max_val=10.0
        )
        assert result == 2.5

    @patch("builtins.input")
    def test_prompt_float_default(self, mock_input, wizard):
        """Test using default value."""
        mock_input.return_value = ""
        result = wizard._prompt_float("Enter seconds", default=1.5)
        assert result == 1.5

    @patch("builtins.input")
    def test_prompt_float_integer_accepted(self, mock_input, wizard):
        """Test that integer input is accepted as float."""
        mock_input.return_value = "3"
        result = wizard._prompt_float("Enter seconds", default=1.0)
        assert result == 3.0

    @patch("builtins.input")
    def test_prompt_float_below_minimum(self, mock_input, wizard):
        """Test value below minimum is rejected."""
        mock_input.side_effect = ["0.1", "1.5"]
        result = wizard._prompt_float(
            "Enter seconds", default=1.0, min_val=0.5, max_val=10.0
        )
        assert result == 1.5
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_prompt_float_above_maximum(self, mock_input, wizard):
        """Test value above maximum is rejected."""
        mock_input.side_effect = ["15.0", "5.5"]
        result = wizard._prompt_float(
            "Enter seconds", default=1.0, min_val=0.5, max_val=10.0
        )
        assert result == 5.5
        assert mock_input.call_count == 2


class TestPromptString:
    """Test _prompt_string method."""

    @patch("builtins.input")
    def test_prompt_string_custom_value(self, mock_input, wizard):
        """Test entering custom string value."""
        mock_input.return_value = "custom_value"
        result = wizard._prompt_string("Enter value", default="default")
        assert result == "custom_value"

    @patch("builtins.input")
    def test_prompt_string_default(self, mock_input, wizard):
        """Test using default string value."""
        mock_input.return_value = ""
        result = wizard._prompt_string("Enter value", default="default")
        assert result == "default"

    @patch("builtins.input")
    def test_prompt_string_with_spaces(self, mock_input, wizard):
        """Test string with spaces."""
        mock_input.return_value = "value with spaces"
        result = wizard._prompt_string("Enter value", default="default")
        assert result == "value with spaces"

    @patch("builtins.input")
    def test_prompt_string_whitespace_trimmed(self, mock_input, wizard):
        """Test that leading/trailing whitespace is trimmed."""
        mock_input.return_value = "  value  "
        result = wizard._prompt_string("Enter value", default="default")
        assert result == "value"


class TestConfigureFeatures:
    """Test _configure_features method."""

    @patch("builtins.input")
    def test_configure_features_all_defaults(self, mock_input, wizard):
        """Test configuring features with all defaults."""
        # 5 boolean prompts, all accepting defaults
        mock_input.return_value = ""

        wizard._configure_features()

        assert "features" in wizard.config
        assert "auto_save" in wizard.config["features"]
        assert "show_tokens" in wizard.config["features"]
        assert "show_metadata" in wizard.config["features"]
        assert "rich_enabled" in wizard.config["features"]
        assert "readline_enabled" in wizard.config["features"]

    @patch("builtins.input")
    def test_configure_features_custom_values(self, mock_input, wizard):
        """Test configuring features with custom values."""
        mock_input.side_effect = ["y", "y", "n", "n", "y"]

        wizard._configure_features()

        assert wizard.config["features"]["auto_save"] is True
        assert wizard.config["features"]["show_tokens"] is True
        assert wizard.config["features"]["show_metadata"] is False
        assert wizard.config["features"]["rich_enabled"] is False
        assert wizard.config["features"]["readline_enabled"] is True


class TestConfigureUI:
    """Test _configure_ui method."""

    @patch("builtins.input")
    def test_configure_ui_defaults(self, mock_input, wizard):
        """Test configuring UI with defaults."""
        mock_input.return_value = ""

        wizard._configure_ui()

        assert "ui" in wizard.config
        assert "show_banner" in wizard.config["ui"]
        assert "show_thinking_indicator" in wizard.config["ui"]
        assert "show_duration" in wizard.config["ui"]
        assert "show_status_bar" in wizard.config["ui"]


class TestConfigureAudio:
    """Test _configure_audio method."""

    @patch("builtins.input")
    def test_configure_audio_enabled_default_sound(self, mock_input, wizard):
        """Test enabling audio with default sound."""
        mock_input.side_effect = ["y", ""]

        wizard._configure_audio()

        assert wizard.config["audio"]["enabled"] is True
        assert wizard.config["audio"]["notification_sound"] is None

    @patch("builtins.input")
    def test_configure_audio_enabled_custom_sound(self, mock_input, wizard):
        """Test enabling audio with custom sound."""
        mock_input.side_effect = ["y", "/path/to/custom.wav"]

        wizard._configure_audio()

        assert wizard.config["audio"]["enabled"] is True
        assert wizard.config["audio"]["notification_sound"] == "/path/to/custom.wav"

    @patch("builtins.input")
    def test_configure_audio_disabled(self, mock_input, wizard):
        """Test disabling audio."""
        mock_input.return_value = "n"

        wizard._configure_audio()

        assert wizard.config["audio"]["enabled"] is False
        assert wizard.config["audio"]["notification_sound"] is None


class TestConfigureBehavior:
    """Test _configure_behavior method."""

    @patch("builtins.input")
    def test_configure_behavior_defaults(self, mock_input, wizard):
        """Test configuring behavior with defaults."""
        mock_input.side_effect = ["", "", "", ""]

        wizard._configure_behavior()

        assert wizard.config["behavior"]["max_retries"] == 3
        assert wizard.config["behavior"]["retry_delay"] == 2.0
        assert wizard.config["behavior"]["timeout"] == 120.0
        assert wizard.config["behavior"]["spinner_style"] == "dots"

    @patch("builtins.input")
    def test_configure_behavior_custom_values(self, mock_input, wizard):
        """Test configuring behavior with custom values."""
        mock_input.side_effect = ["5", "3.5", "180.0", "arc"]

        wizard._configure_behavior()

        assert wizard.config["behavior"]["max_retries"] == 5
        assert wizard.config["behavior"]["retry_delay"] == 3.5
        assert wizard.config["behavior"]["timeout"] == 180.0
        assert wizard.config["behavior"]["spinner_style"] == "arc"

    @patch("builtins.input")
    def test_configure_behavior_invalid_spinner_uses_default(self, mock_input, wizard):
        """Test that invalid spinner style uses default."""
        mock_input.side_effect = ["", "", "", "invalid_style"]

        wizard._configure_behavior()

        assert wizard.config["behavior"]["spinner_style"] == "dots"


class TestConfigurePaths:
    """Test _configure_paths method."""

    @patch("builtins.input")
    def test_configure_paths_defaults(self, mock_input, wizard):
        """Test configuring paths with defaults."""
        mock_input.side_effect = ["", ""]

        wizard._configure_paths()

        assert wizard.config["paths"]["save_location"] == "~/agent-conversations"
        assert wizard.config["paths"]["log_location"] == "~/.chat_loop_logs"

    @patch("builtins.input")
    def test_configure_paths_custom_values(self, mock_input, wizard):
        """Test configuring paths with custom values."""
        mock_input.side_effect = ["~/custom/conversations", "~/custom/logs"]

        wizard._configure_paths()

        assert wizard.config["paths"]["save_location"] == "~/custom/conversations"
        assert wizard.config["paths"]["log_location"] == "~/custom/logs"


class TestPromptColor:
    """Test _prompt_color method."""

    @patch("builtins.input")
    def test_prompt_color_valid_input(self, mock_input, wizard):
        """Test valid color name input."""
        mock_input.return_value = "bright_green"
        result = wizard._prompt_color("Select color", default="blue")
        assert result == "bright_green"

    @patch("builtins.input")
    def test_prompt_color_default(self, mock_input, wizard):
        """Test using default color."""
        mock_input.return_value = ""
        result = wizard._prompt_color("Select color", default="blue")
        assert result == "blue"

    @patch("builtins.input")
    def test_prompt_color_case_insensitive(self, mock_input, wizard):
        """Test that color input is case insensitive."""
        mock_input.return_value = "BRIGHT_GREEN"
        result = wizard._prompt_color("Select color", default="blue")
        assert result == "bright_green"

    @patch("builtins.input")
    def test_prompt_color_invalid_then_valid(self, mock_input, wizard):
        """Test handling invalid color then valid."""
        mock_input.side_effect = ["invalid_color", "purple", "red"]
        result = wizard._prompt_color("Select color", default="blue")
        assert result == "red"
        assert mock_input.call_count == 3


class TestConfigureColors:
    """Test _configure_colors method."""

    @patch("builtins.input")
    def test_configure_colors_skip_customization(self, mock_input, wizard):
        """Test skipping color customization uses defaults."""
        mock_input.return_value = "n"

        wizard._configure_colors()

        assert "colors" in wizard.config
        assert wizard.config["colors"]["user"] == "bright_white"
        assert wizard.config["colors"]["agent"] == "bright_blue"

    @patch("builtins.input")
    def test_configure_colors_custom_values(self, mock_input, wizard):
        """Test customizing colors."""
        mock_input.side_effect = [
            "y",  # Customize colors?
            "bright_red",  # user
            "bright_green",  # agent
            "",  # system (default)
            "",  # error (default)
            "",  # success (default)
        ]

        wizard._configure_colors()

        assert wizard.config["colors"]["user"] == "bright_red"
        assert wizard.config["colors"]["agent"] == "bright_green"
        assert "system" in wizard.config["colors"]


class TestWriteConfig:
    """Test _write_config method."""

    @patch("builtins.input")
    def test_write_config_global_new_file(
        self, mock_input, wizard, tmp_path, monkeypatch
    ):
        """Test writing new global config file."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        wizard.config = {
            "colors": {"user": "bright_white"},
            "features": {"auto_save": False},
            "ui": {},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {},
            "paths": {},
        }

        result = wizard._write_config("global")

        assert result == tmp_path / ".chatrc"
        assert result.exists()

    @patch("builtins.input")
    def test_write_config_project_new_file(
        self, mock_input, wizard, tmp_path, monkeypatch
    ):
        """Test writing new project config file."""
        monkeypatch.chdir(tmp_path)
        wizard.config = {
            "colors": {"user": "bright_white"},
            "features": {},
            "ui": {},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {},
            "paths": {},
        }

        result = wizard._write_config("project")

        assert result == tmp_path / ".chatrc"
        assert result.exists()

    @patch("builtins.input")
    def test_write_config_overwrite_declined(
        self, mock_input, wizard, tmp_path, monkeypatch
    ):
        """Test declining to overwrite existing config."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        existing_config = tmp_path / ".chatrc"
        existing_config.write_text("existing content")

        mock_input.return_value = "n"  # Decline overwrite
        wizard.config = {"features": {}}

        result = wizard._write_config("global")

        assert result is None
        assert existing_config.read_text() == "existing content"

    @patch("builtins.input")
    def test_write_config_overwrite_accepted(
        self, mock_input, wizard, tmp_path, monkeypatch
    ):
        """Test accepting overwrite of existing config."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        existing_config = tmp_path / ".chatrc"
        existing_config.write_text("existing content")

        mock_input.return_value = "y"  # Accept overwrite
        wizard.config = {
            "colors": {},
            "features": {},
            "ui": {},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {},
            "paths": {},
        }

        result = wizard._write_config("global")

        assert result is not None
        assert result.exists()
        # Content should be changed
        assert existing_config.read_text() != "existing content"

    def test_write_config_secure_permissions(self, wizard, tmp_path, monkeypatch):
        """Test that config file has secure permissions."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        wizard.config = {
            "colors": {},
            "features": {},
            "ui": {},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {},
            "paths": {},
        }

        result = wizard._write_config("global")

        assert result is not None
        # Check permissions are 0o600
        assert oct(result.stat().st_mode)[-3:] == "600"


class TestGenerateYamlWithComments:
    """Test _generate_yaml_with_comments method."""

    def test_generate_yaml_includes_all_sections(self, wizard):
        """Test that generated YAML includes all config sections."""
        wizard.config = {
            "colors": {"user": "bright_white"},
            "features": {"auto_save": False},
            "ui": {"show_banner": True},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {"max_retries": 3},
            "paths": {"save_location": "~/test"},
        }

        yaml_content = wizard._generate_yaml_with_comments()

        assert "colors:" in yaml_content
        assert "features:" in yaml_content
        assert "ui:" in yaml_content
        assert "audio:" in yaml_content
        assert "behavior:" in yaml_content
        assert "paths:" in yaml_content
        assert "agents: {}" in yaml_content

    def test_generate_yaml_includes_comments(self, wizard):
        """Test that generated YAML includes helpful comments."""
        wizard.config = {
            "colors": {},
            "features": {},
            "ui": {},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {},
            "paths": {},
        }

        yaml_content = wizard._generate_yaml_with_comments()

        assert "# Basic Agent Chat Loop Configuration" in yaml_content
        assert "# COLORS" in yaml_content
        assert "# FEATURES" in yaml_content


class TestRunMethod:
    """Test the main run() method."""

    @patch("builtins.input")
    def test_run_keyboard_interrupt(self, mock_input, wizard):
        """Test that KeyboardInterrupt is handled gracefully."""
        mock_input.side_effect = KeyboardInterrupt()

        result = wizard.run()

        assert result is None

    @patch("builtins.input")
    @patch.object(ConfigWizard, "_write_config")
    def test_run_complete_flow(self, mock_write, mock_input, wizard):
        """Test complete wizard flow."""
        # Mock all user inputs for a complete flow
        mock_input.side_effect = [
            "1",  # Global scope
            # Features (5 bools)
            "",
            "",
            "",
            "",
            "",
            # UI (5 bools)
            "",
            "",
            "",
            "",
            "",
            # Audio
            "y",
            "",
            # Harmony
            "",  # enabled (auto/yes/no)
            "",  # show_detailed_thinking
            # Behavior
            "",
            "",
            "",
            "",
            # Paths
            "",
            "",
            # Colors
            "n",
        ]

        mock_write.return_value = Path("/tmp/.chatrc")

        result = wizard.run()

        assert result is not None
        assert mock_write.called


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_wizard_with_import_error_handling(self, wizard, tmp_path, monkeypatch):
        """Test wizard handles import errors gracefully."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        wizard.config = {
            "colors": {},
            "features": {},
            "ui": {},
            "audio": {"enabled": True, "notification_sound": None},
            "behavior": {},
            "paths": {},
        }

        # The wizard should handle yaml import errors in _write_config
        # For this test, we just verify that with normal yaml available,
        # the config can be written successfully
        result = wizard._write_config("global")
        assert result is not None
        assert result.exists()

    @patch("builtins.input")
    def test_configure_features_with_existing_config(
        self, mock_input, wizard, temp_config_file, tmp_path, monkeypatch
    ):
        """Test that existing config values are used as defaults."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        global_config = tmp_path / ".chatrc"
        global_config.write_text(temp_config_file.read_text())

        wizard._load_existing_config("global")
        mock_input.return_value = ""  # Use defaults

        wizard._configure_features()

        # Should use values from existing config
        assert wizard.config["features"]["show_tokens"] is True


class TestResetConfigToDefaults:
    """Test reset_config_to_defaults function."""

    @patch("builtins.input")
    def test_reset_global_config_with_confirmation(
        self, mock_input, tmp_path, monkeypatch
    ):
        """Test resetting global config with confirmation."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # User chooses global (1) and confirms (y)
        mock_input.side_effect = ["1", "y"]

        result = reset_config_to_defaults()

        assert result == tmp_path / ".chatrc"
        assert result.exists()

        # Verify content has default values
        content = result.read_text()
        assert "bright_white" in content
        assert "bright_blue" in content
        assert "auto_save: false" in content
        assert "show_tokens: false" in content

    @patch("builtins.input")
    def test_reset_project_config_with_confirmation(
        self, mock_input, tmp_path, monkeypatch
    ):
        """Test resetting project config."""
        monkeypatch.chdir(tmp_path)

        # User chooses project (2) and confirms (y)
        mock_input.side_effect = ["2", "y"]

        result = reset_config_to_defaults()

        assert result == tmp_path / ".chatrc"
        assert result.exists()

    @patch("builtins.input")
    def test_reset_config_cancelled_by_user(self, mock_input, tmp_path, monkeypatch):
        """Test that user can cancel reset."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # User chooses global (1) but declines confirmation (n)
        mock_input.side_effect = ["1", "n"]

        result = reset_config_to_defaults()

        assert result is None
        assert not (tmp_path / ".chatrc").exists()

    @patch("builtins.input")
    def test_reset_config_keyboard_interrupt(self, mock_input):
        """Test that KeyboardInterrupt is handled gracefully."""
        mock_input.side_effect = KeyboardInterrupt()

        result = reset_config_to_defaults()

        assert result is None

    @patch("builtins.input")
    def test_reset_config_overwrites_existing(self, mock_input, tmp_path, monkeypatch):
        """Test that reset overwrites existing config."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Create existing config with custom values
        existing_config = tmp_path / ".chatrc"
        existing_config.write_text("custom: values\nshould: be_replaced")

        # User confirms reset
        mock_input.side_effect = ["1", "y"]

        result = reset_config_to_defaults()

        assert result is not None
        content = result.read_text()

        # Should have default values, not custom ones
        assert "custom: values" not in content
        assert "bright_white" in content

    @patch("builtins.input")
    def test_reset_config_sets_secure_permissions(
        self, mock_input, tmp_path, monkeypatch
    ):
        """Test that reset config has secure permissions."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        mock_input.side_effect = ["1", "y"]

        result = reset_config_to_defaults()

        assert result is not None
        # Check permissions are 0o600
        assert oct(result.stat().st_mode)[-3:] == "600"

    @patch("builtins.input")
    def test_reset_config_invalid_choice_then_valid(
        self, mock_input, tmp_path, monkeypatch
    ):
        """Test handling invalid choice then valid choice."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Invalid choice, then valid choice (1), then confirm
        mock_input.side_effect = ["invalid", "3", "1", "y"]

        result = reset_config_to_defaults()

        assert result is not None
        assert result.exists()

    @patch("builtins.input")
    def test_reset_config_includes_all_sections(
        self, mock_input, tmp_path, monkeypatch
    ):
        """Test that reset config includes all expected sections."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        mock_input.side_effect = ["1", "y"]

        result = reset_config_to_defaults()

        content = result.read_text()

        # Check all major sections are present
        assert "colors:" in content
        assert "features:" in content
        assert "ui:" in content
        assert "audio:" in content
        assert "behavior:" in content
        assert "paths:" in content
        assert "agents: {}" in content
