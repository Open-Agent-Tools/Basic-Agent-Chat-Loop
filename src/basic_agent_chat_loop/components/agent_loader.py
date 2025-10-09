"""
Agent loading and metadata extraction.

Handles dynamic loading of agent modules and extraction of agent metadata.
"""

import contextlib
import importlib.util
import io
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Environment file search depth (number of parent directories to check)
ENV_SEARCH_DEPTH = 3


def load_environment_variables() -> Optional[Path]:
    """
    Load environment variables from .env file searching parent directories.

    Returns:
        Path to .env file if found, None otherwise
    """
    try:
        # Look for .env file in parent directories
        for i in range(ENV_SEARCH_DEPTH):
            env_path = Path(__file__).parents[i] / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=False)  # Don't override existing vars
                return env_path
    except ImportError:
        pass
    return None


def _find_package_root(agent_path: Path) -> Tuple[Path, str]:
    """
    Find the package root by walking up directories looking for __init__.py files.

    Args:
        agent_path: Path to the agent file

    Returns:
        Tuple of (package_root_path, module_name)
    """
    agent_path = Path(agent_path).resolve()
    agent_dir = agent_path.parent

    # Build the module name by walking up the directory tree
    module_parts = [agent_path.stem]
    current_dir = agent_dir

    # Walk up while we find __init__.py files
    while (current_dir / "__init__.py").exists():
        module_parts.insert(0, current_dir.name)
        current_dir = current_dir.parent

    # The package root is one level above the highest __init__.py
    package_root = current_dir
    module_name = ".".join(module_parts)

    return package_root, module_name


def _ensure_package_loaded(package_root: Path, package_name: str) -> None:
    """
    Ensure all parent packages are loaded and registered in sys.modules.

    This is critical for relative imports to work correctly - Python needs
    all parent packages to be in sys.modules to resolve imports like
    'from .sibling import foo'.

    Args:
        package_root: Root directory containing the package
        package_name: Full package name (e.g., 'my_package.subpackage')
    """
    # Build list of all parent packages (e.g., ['my_package', 'my_package.subpackage'])
    parts = package_name.split(".")
    packages_to_load = []
    for i in range(len(parts)):
        pkg = ".".join(parts[: i + 1])
        packages_to_load.append(pkg)

    # Load each package if not already loaded
    for pkg in packages_to_load:
        if pkg in sys.modules:
            continue

        # Build path to __init__.py
        pkg_path = package_root / pkg.replace(".", os.sep) / "__init__.py"

        if not pkg_path.exists():
            # Package doesn't have __init__.py, skip
            continue

        # Load the package __init__.py
        spec = importlib.util.spec_from_file_location(pkg, pkg_path)
        if spec is None or spec.loader is None:
            continue

        pkg_module = importlib.util.module_from_spec(spec)

        # Set package attributes - critical for import machinery
        pkg_module.__package__ = pkg
        pkg_module.__path__ = [str(pkg_path.parent)]

        # Also set __file__ for completeness
        pkg_module.__file__ = str(pkg_path)

        # Register in sys.modules BEFORE executing
        sys.modules[pkg] = pkg_module

        # Suppress stderr during package init - parent packages in agent paths
        # often have import errors that are non-critical (agent still works)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                spec.loader.exec_module(pkg_module)
        except Exception as e:
            # If package init fails, still keep it registered (might just have
            # imports that will work later). This commonly happens with
            # intermediate directories in agent paths (e.g., /path/agents/my_agent.py)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Package {pkg} __init__.py initialization failed: {type(e).__name__}")
            pass


def load_agent_module(agent_path: str) -> Tuple[Any, str, str]:
    """
    Dynamically load agent module and extract root_agent.

    Supports agents with relative imports by properly establishing package context.

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
        # Only show filename, not full path (to avoid exposing system info)
        filename = os.path.basename(agent_path)
        raise FileNotFoundError(f"Agent file not found: {filename}")

    agent_path_obj = Path(agent_path).resolve()

    # Find package root and construct proper module name
    package_root, module_name = _find_package_root(agent_path_obj)

    # Add the package root to sys.path (not just the immediate directory)
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    # Ensure parent packages are loaded and registered in sys.modules
    # This is critical for relative imports to work correctly
    if "." in module_name:
        package_name = ".".join(module_name.split(".")[:-1])
        _ensure_package_loaded(package_root, package_name)

    # Load the module with proper package context
    spec = importlib.util.spec_from_file_location(module_name, agent_path_obj)
    if spec is None or spec.loader is None:
        # Only show filename, not full path
        filename = os.path.basename(agent_path)
        raise ImportError(f"Could not load module from {filename}")

    module = importlib.util.module_from_spec(spec)

    # Set the package attribute for relative imports
    if "." in module_name:
        module.__package__ = ".".join(module_name.split(".")[:-1])

    # Register in sys.modules before executing to support circular imports
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        # Clean up sys.modules on failure
        sys.modules.pop(module_name, None)
        raise ImportError(
            f"Failed to execute module {os.path.basename(agent_path)}: {e}"
        )

    # Extract root_agent
    if not hasattr(module, "root_agent"):
        # Only show filename, not full path
        filename = os.path.basename(agent_path)
        raise AttributeError(
            f"Agent module {filename} must expose a 'root_agent' attribute"
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
