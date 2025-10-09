#!/usr/bin/env python3
"""
Configuration management for Basic Agent Chat Loop.

Supports hierarchical configuration with the following precedence (highest to lowest):
1. Project-level .chatrc in current directory
2. Global ~/.chatrc
3. Built-in defaults

Configuration file format: YAML
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ChatConfig:
    """Configuration manager for chat loop."""

    # Default configuration
    DEFAULTS = {
        "colors": {
            "user": "\033[97m",  # Bright white
            "agent": "\033[94m",  # Bright blue
            "system": "\033[33m",  # Yellow
            "error": "\033[91m",  # Bright red
            "success": "\033[92m",  # Bright green
            "dim": "\033[2m",  # Dim
            "reset": "\033[0m",  # Reset
        },
        "features": {
            "auto_save": False,
            "rich_enabled": True,
            "show_tokens": False,
            "show_metadata": True,
            "readline_enabled": True,
        },
        "paths": {
            "save_location": "~/agent-conversations",
            "log_location": ".logs",
        },
        "behavior": {
            "max_retries": 3,
            "retry_delay": 2.0,
            "timeout": 120.0,
            "spinner_style": "dots",
        },
        "ui": {
            "show_banner": True,
            "show_thinking_indicator": True,
            "show_duration": True,
            "show_status_bar": False,
        },
        # Per-agent overrides (example structure)
        "agents": {
            # 'Complex Coding Clara': {
            #     'features': {'auto_save': True}
            # }
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional explicit config file path
        """
        self.config = self._load_config(config_path)

    def _load_config(self, explicit_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration with hierarchical precedence.

        Args:
            explicit_path: Explicit config file path (highest priority)

        Returns:
            Merged configuration dictionary
        """
        # Start with defaults
        config = self._deep_copy(self.DEFAULTS)

        if not YAML_AVAILABLE:
            return config

        config_files = []

        # Check for explicit path
        if explicit_path and explicit_path.exists():
            config_files.append(explicit_path)

        # Global config
        global_config = Path.home() / ".chatrc"
        if global_config.exists():
            config_files.append(global_config)

        # Project config (current directory and up to 3 parents)
        for i in range(4):
            if i == 0:
                project_config = Path.cwd() / ".chatrc"
            else:
                try:
                    project_config = Path.cwd().parents[i - 1] / ".chatrc"
                except IndexError:
                    break

            if project_config.exists():
                config_files.append(project_config)
                break  # Use first found, don't search higher

        # Load and merge configs (global first, then project overrides)
        for config_file in config_files:
            try:
                with open(config_file) as f:
                    user_config = yaml.safe_load(f) or {}
                    config = self._merge_config(config, user_config)
            except Exception:
                # Silently skip invalid configs, use defaults
                pass

        return config

    def _deep_copy(self, d: Dict) -> Dict:
        """Deep copy a dictionary."""
        import copy

        return copy.deepcopy(d)

    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = self._deep_copy(base)

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursive merge for nested dicts
                result[key] = self._merge_config(result[key], value)
            else:
                # Direct override
                result[key] = value

        return result

    def get(
        self, key: str, default: Any = None, agent_name: Optional[str] = None
    ) -> Any:
        """
        Get configuration value with optional agent-specific override.

        Args:
            key: Dot-notation config key (e.g., 'features.auto_save')
            default: Default value if key not found
            agent_name: Optional agent name for per-agent overrides

        Returns:
            Configuration value
        """
        # Check agent-specific override first
        if agent_name and agent_name in self.config.get("agents", {}):
            agent_config = self.config["agents"][agent_name]
            agent_value = self._get_nested(agent_config, key)
            if agent_value is not None:
                return agent_value

        # Fall back to global config
        value = self._get_nested(self.config, key)
        return value if value is not None else default

    def _get_nested(self, d: Dict, key: str) -> Any:
        """
        Get nested dictionary value using dot notation.

        Args:
            d: Dictionary to search
            key: Dot-notation key (e.g., 'features.auto_save')

        Returns:
            Value or None if not found
        """
        keys = key.split(".")
        current = d

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def get_section(
        self, section: str, agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get entire configuration section with agent overrides applied.

        Args:
            section: Section name (e.g., 'colors', 'features')
            agent_name: Optional agent name for overrides

        Returns:
            Configuration section dictionary
        """
        base_section = self.config.get(section, {})

        # Apply agent overrides if specified
        if agent_name and agent_name in self.config.get("agents", {}):
            agent_config = self.config["agents"][agent_name]
            if section in agent_config:
                base_section = self._merge_config(base_section, agent_config[section])

        # Special handling for colors section - decode escape sequences
        if section == "colors":
            decoded_colors = {}
            for key, value in base_section.items():
                if isinstance(value, str) and "\\" in value:
                    # Decode YAML-escaped strings (\\033 -> \033)
                    try:
                        decoded_colors[key] = value.encode().decode("unicode_escape")
                    except Exception:
                        decoded_colors[key] = value
                else:
                    decoded_colors[key] = value
            return decoded_colors

        return base_section

    def set(self, key: str, value: Any, agent_name: Optional[str] = None):
        """
        Set configuration value (runtime only, not persisted).

        Args:
            key: Dot-notation config key
            value: Value to set
            agent_name: Optional agent name for per-agent setting
        """
        keys = key.split(".")

        # Determine target dict
        if agent_name:
            if "agents" not in self.config:
                self.config["agents"] = {}
            if agent_name not in self.config["agents"]:
                self.config["agents"][agent_name] = {}
            target = self.config["agents"][agent_name]
        else:
            target = self.config

        # Navigate to parent and set value
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def expand_path(self, path: str) -> Path:
        """
        Expand path with ~ and environment variables.

        Args:
            path: Path string potentially with ~ or $VAR

        Returns:
            Expanded Path object
        """
        return Path(os.path.expanduser(os.path.expandvars(path)))


# Global config instance (lazy loaded)
_global_config: Optional[ChatConfig] = None


def get_config(config_path: Optional[Path] = None, reload: bool = False) -> ChatConfig:
    """
    Get global configuration instance.

    Args:
        config_path: Optional explicit config file path
        reload: Force reload configuration

    Returns:
        ChatConfig instance
    """
    global _global_config

    if _global_config is None or reload:
        _global_config = ChatConfig(config_path)

    return _global_config
