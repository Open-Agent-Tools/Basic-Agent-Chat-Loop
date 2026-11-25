"""
Agent loading and metadata extraction.

Handles dynamic loading of agent modules and extraction of agent metadata.
"""

import importlib.util
import io
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .error_messages import ErrorMessages

logger = logging.getLogger(__name__)


def _find_package_root(agent_path: Path) -> tuple[Path, str]:
    """
    Find the package root by walking up directories looking for __init__.py files.

    Args:
        agent_path: Path to the agent file

    Returns:
        Tuple of (package_root_path, module_name)
    """
    agent_path = Path(agent_path).resolve()
    agent_dir = agent_path.parent

    module_parts = [agent_path.stem]
    current_dir = agent_dir

    while (current_dir / "__init__.py").exists():
        module_parts.insert(0, current_dir.name)
        current_dir = current_dir.parent

    package_root = current_dir
    module_name = ".".join(module_parts)

    return package_root, module_name


def _ensure_package_loaded(package_root: Path, package_name: str) -> None:
    """
    Ensure all parent packages are loaded and registered in sys.modules.

    Registers parent packages as stub modules without executing their
    __init__.py files.

    Args:
        package_root: Root directory containing the package
        package_name: Full package name (e.g., 'my_package.subpackage')
    """
    parts = package_name.split(".")
    packages_to_load = []
    for i in range(len(parts)):
        pkg = ".".join(parts[: i + 1])
        packages_to_load.append(pkg)

    for pkg in packages_to_load:
        if pkg in sys.modules:
            continue

        pkg_dir = package_root / pkg.replace(".", os.sep)
        pkg_init = pkg_dir / "__init__.py"

        if not pkg_init.exists():
            continue

        import types

        pkg_module = types.ModuleType(pkg)

        pkg_module.__package__ = pkg
        pkg_module.__path__ = [str(pkg_dir)]
        pkg_module.__file__ = str(pkg_init)
        pkg_module.__name__ = pkg

        sys.modules[pkg] = pkg_module


def load_agent_module(agent_path: str) -> tuple[Any, str, str]:
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
        raise FileNotFoundError(ErrorMessages.agent_file_not_found(agent_path))

    agent_path_obj = Path(agent_path).resolve()

    package_root, module_name = _find_package_root(agent_path_obj)

    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    if "." in module_name:
        package_name = ".".join(module_name.split(".")[:-1])
        _ensure_package_loaded(package_root, package_name)

    spec = importlib.util.spec_from_file_location(module_name, agent_path_obj)
    if spec is None or spec.loader is None:
        filename = os.path.basename(agent_path)
        raise ImportError(
            ErrorMessages.agent_import_error(
                filename, Exception("Could not create module spec")
            )
        )

    module = importlib.util.module_from_spec(spec)

    if "." in module_name:
        module.__package__ = ".".join(module_name.split(".")[:-1])

    sys.modules[module_name] = module

    original_stderr = sys.stderr
    stderr_capture = io.StringIO()
    try:
        sys.stderr = stderr_capture
        spec.loader.exec_module(module)
    except Exception as e:
        sys.modules.pop(module_name, None)
        raise ImportError(
            ErrorMessages.agent_import_error(os.path.basename(agent_path), e)
        )
    finally:
        sys.stderr = original_stderr
        suppressed_output = stderr_capture.getvalue()
        if suppressed_output.strip():
            logger.debug(
                f"Suppressed stderr during agent load from {agent_path}: "
                f"{suppressed_output[:500]}"
            )

    if not hasattr(module, "root_agent"):
        filename = os.path.basename(agent_path)
        raise AttributeError(ErrorMessages.agent_missing_root_agent(filename))

    agent = module.root_agent

    agent_name = getattr(agent, "name", os.path.basename(os.path.dirname(agent_path)))
    agent_description = getattr(agent, "description", "AI Agent")

    return agent, agent_name, agent_description


def extract_agent_metadata(agent: Any) -> dict[str, Any]:
    """
    Extract metadata from agent for display.

    Args:
        agent: Agent instance

    Returns:
        Dictionary with agent metadata including model_id, max_tokens,
        temperature, tool_count, tools list, and uses_harmony flag
    """
    metadata = {}

    model_id = None

    for attr in ["model", "model_id", "model_name"]:
        if hasattr(agent, attr):
            value = getattr(agent, attr)
            if value and isinstance(value, str):
                model_id = value
                break

    if not model_id and hasattr(agent, "model"):
        model = agent.model

        if hasattr(model, "config") and isinstance(model.config, dict):
            model_id = model.config.get("model_id")

        if not model_id:
            for attr in ["model_id", "model", "model_name", "_model_id", "name", "id"]:
                if hasattr(model, attr):
                    model_id = getattr(model, attr)
                    if model_id and model_id != "Unknown":
                        break

        if model_id and isinstance(model_id, str):
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

        from .harmony_processor import HarmonyProcessor

        metadata["uses_harmony"] = HarmonyProcessor.detect_harmony_agent(
            agent, model_id=model_id
        )

        if hasattr(model, "config") and isinstance(model.config, dict):
            metadata["max_tokens"] = model.config.get("max_tokens", "Unknown")
            params = model.config.get("params", {})
            metadata["temperature"] = params.get("temperature", "Unknown")
        else:
            metadata["max_tokens"] = getattr(model, "max_tokens", "Unknown")
            metadata["temperature"] = getattr(model, "temperature", "Unknown")

    tools = None
    for attr in ["tools", "_tools", "tool_list"]:
        if hasattr(agent, attr):
            tools = getattr(agent, attr)
            if tools:
                break

    if tools and isinstance(tools, (list, tuple)):
        metadata["tool_count"] = len(tools)
        tool_names = []
        for t in tools[:10]:
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
