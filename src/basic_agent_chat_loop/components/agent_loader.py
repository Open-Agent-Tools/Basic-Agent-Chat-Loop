"""
Agent loading and metadata extraction.

Handles dynamic loading of agent modules and extraction of agent metadata.
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment_variables() -> Optional[Path]:
    """
    Load environment variables from .env file up to 3 levels up.

    Returns:
        Path to .env file if found, None otherwise
    """
    try:
        # Look for .env file up to 3 levels up from current file
        for i in range(3):
            env_path = Path(__file__).parents[i] / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=False)  # Don't override existing vars
                return env_path
    except ImportError:
        pass
    return None


def load_agent_module(agent_path: str) -> Tuple[Any, str, str]:
    """
    Dynamically load agent module and extract root_agent.

    Args:
        agent_path: Path to agent module file

    Returns:
        Tuple of (agent, agent_name, agent_description)

    Raises:
        FileNotFoundError: If agent file not found
        ImportError: If module cannot be loaded
        AttributeError: If module doesn't have root_agent
    """
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"Agent file not found: {agent_path}")

    # Add the agent directory to sys.path to fix import issues
    agent_dir = os.path.dirname(agent_path)
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)

    # Convert path to module name
    spec = importlib.util.spec_from_file_location("agent_module", agent_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {agent_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["agent_module"] = module
    spec.loader.exec_module(module)

    # Extract root_agent
    if not hasattr(module, "root_agent"):
        raise AttributeError(
            f"Agent module {agent_path} must expose a 'root_agent' attribute"
        )

    agent = module.root_agent

    # Extract agent metadata if available
    agent_name = getattr(agent, "name", os.path.basename(os.path.dirname(agent_path)))
    agent_description = getattr(agent, "description", "AI Agent")

    return agent, agent_name, agent_description


def extract_agent_metadata(agent: Any) -> Dict[str, Any]:
    """
    Extract metadata from agent for display.

    Args:
        agent: Agent instance

    Returns:
        Dictionary with agent metadata including model_id, max_tokens,
        temperature, tool_count, and tools list
    """
    metadata = {}

    # Try to extract model information
    if hasattr(agent, "model"):
        model = agent.model

        # Try multiple attribute names for model ID
        model_id = None
        for attr in ["model_id", "model", "model_name", "_model_id", "name"]:
            if hasattr(model, attr):
                model_id = getattr(model, attr)
                if model_id and model_id != "Unknown":
                    break

        # Clean up model_id if it's a long AWS model string
        if model_id and isinstance(model_id, str):
            # Extract meaningful part from AWS model IDs
            # e.g., "us.anthropic.claude-sonnet-4-5-20250929-v1:0" -> "Claude Sonnet 4.5"
            if "claude-sonnet" in model_id.lower():
                if "4-5" in model_id or "4.5" in model_id:
                    model_id = "Claude Sonnet 4.5"
                elif "3-5" in model_id or "3.5" in model_id:
                    model_id = "Claude Sonnet 3.5"
                else:
                    model_id = "Claude Sonnet"
            elif "claude-opus" in model_id.lower():
                model_id = "Claude Opus"
            elif "claude-haiku" in model_id.lower():
                model_id = "Claude Haiku"

        metadata["model_id"] = model_id or "Unknown Model"
        metadata["max_tokens"] = getattr(model, "max_tokens", "Unknown")
        metadata["temperature"] = getattr(model, "temperature", "Unknown")

    # Try to extract tools - check multiple attributes
    tools = None
    for attr in ["tools", "_tools", "tool_list"]:
        if hasattr(agent, attr):
            tools = getattr(agent, attr)
            if tools:
                break

    if tools and isinstance(tools, (list, tuple)):
        metadata["tool_count"] = len(tools)
        # Extract tool names safely
        tool_names = []
        for t in tools[:10]:  # First 10
            if hasattr(t, "name"):
                tool_names.append(t.name)
            elif hasattr(t, "__name__"):
                tool_names.append(t.__name__)
            elif hasattr(t, "func") and hasattr(t.func, "__name__"):
                tool_names.append(t.func.__name__)
            else:
                tool_names.append(str(t)[:30])
        metadata["tools"] = tool_names
    else:
        metadata["tool_count"] = 0
        metadata["tools"] = []

    return metadata
