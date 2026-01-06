"""
Components for Basic Agent Chat Loop.

This package contains modular components extracted from the main chat loop
for better maintainability and testability.
"""

from .agent_loader import (
    extract_agent_metadata,
    load_agent_module,
)
from .alias_manager import AliasManager
from .audio_notifier import AudioNotifier
from .command_router import CommandResult, CommandRouter, CommandType
from .config_wizard import ConfigWizard
from .dependency_manager import DependencyManager
from .display_manager import DisplayManager
from .error_messages import ErrorMessages
from .harmony_processor import HarmonyProcessor
from .input_handler import get_multiline_input, input_with_esc
from .response_renderer import ResponseRenderer
from .response_streamer import ResponseStreamer
from .session_manager import SessionInfo, SessionManager
from .session_persister import SessionPersister
from .session_restorer import SessionRestorer
from .session_state import SessionState
from .streaming_event_parser import StreamingEventParser
from .template_manager import TemplateManager
from .token_tracker import TokenTracker
from .ui_components import Colors, StatusBar
from .usage_extractor import UsageExtractor

__all__ = [
    "AudioNotifier",
    "Colors",
    "CommandResult",
    "CommandRouter",
    "CommandType",
    "ConfigWizard",
    "DependencyManager",
    "DisplayManager",
    "ErrorMessages",
    "AliasManager",
    "HarmonyProcessor",
    "ResponseRenderer",
    "ResponseStreamer",
    "SessionInfo",
    "SessionManager",
    "SessionPersister",
    "SessionRestorer",
    "SessionState",
    "StatusBar",
    "StreamingEventParser",
    "TemplateManager",
    "TokenTracker",
    "UsageExtractor",
    "extract_agent_metadata",
    "get_multiline_input",
    "input_with_esc",
    "load_agent_module",
]
