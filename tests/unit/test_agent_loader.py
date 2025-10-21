"""Tests for agent_loader module."""


import pytest

from basic_agent_chat_loop.components.agent_loader import (
    extract_agent_metadata,
    load_agent_module,
)


@pytest.fixture
def mock_agent_file(tmp_path):
    """Create a mock agent file."""
    agent_file = tmp_path / "test_agent.py"
    agent_file.write_text(
        """
class MockModel:
    def __init__(self):
        self.model_id = "test-model-id"
        self.max_tokens = 1000
        self.temperature = 0.7

class MockTool:
    def __init__(self, name):
        self.name = name

class MockAgent:
    def __init__(self):
        self.name = "Test Agent"
        self.description = "A test agent for unit tests"
        self.model = MockModel()
        self.tools = [MockTool("tool1"), MockTool("tool2"), MockTool("tool3")]

    def __call__(self, query):
        return {"response": f"Processed: {query}"}

root_agent = MockAgent()
"""
    )
    return agent_file


@pytest.fixture
def agent_without_metadata(tmp_path):
    """Create an agent file without metadata."""
    agent_file = tmp_path / "simple_agent.py"
    agent_file.write_text(
        """
class SimpleAgent:
    pass

root_agent = SimpleAgent()
"""
    )
    return agent_file


class TestLoadAgentModule:
    """Test agent module loading."""

    def test_load_agent_with_metadata(self, mock_agent_file):
        """Test loading agent with full metadata."""
        agent, name, description = load_agent_module(str(mock_agent_file))

        assert agent is not None
        assert name == "Test Agent"
        assert description == "A test agent for unit tests"
        assert hasattr(agent, "model")
        assert hasattr(agent, "tools")

    def test_load_agent_without_metadata(self, agent_without_metadata):
        """Test loading agent without metadata attributes."""
        agent, name, description = load_agent_module(str(agent_without_metadata))

        assert agent is not None
        # Should use directory name as fallback
        assert isinstance(name, str)
        assert description == "AI Agent"  # Default description

    def test_load_nonexistent_file(self):
        """Test loading nonexistent agent file."""
        with pytest.raises(FileNotFoundError):
            load_agent_module("/nonexistent/agent.py")

    def test_load_agent_without_root_agent(self, tmp_path):
        """Test loading module without root_agent attribute."""
        agent_file = tmp_path / "no_root.py"
        agent_file.write_text("# No root_agent here")

        with pytest.raises(
            AttributeError, match="must expose a 'root_agent' attribute"
        ):
            load_agent_module(str(agent_file))

    def test_agent_directory_added_to_sys_path(self, mock_agent_file):
        """Test that agent directory is added to sys.path."""
        import sys

        agent_dir = str(mock_agent_file.parent)
        sys.path.copy()

        agent, _, _ = load_agent_module(str(mock_agent_file))

        # Agent directory should be in sys.path
        assert agent_dir in sys.path

        # Cleanup
        if agent_dir in sys.path:
            sys.path.remove(agent_dir)

    def test_agent_name_from_directory(self, tmp_path):
        """Test that agent name defaults to parent directory name."""
        agent_dir = tmp_path / "MyCustomAgent"
        agent_dir.mkdir()
        agent_file = agent_dir / "agent.py"
        agent_file.write_text(
            """
class Agent:
    pass

root_agent = Agent()
"""
        )

        _, name, _ = load_agent_module(str(agent_file))
        assert name == "MyCustomAgent"


class TestExtractAgentMetadata:
    """Test agent metadata extraction."""

    def test_extract_metadata_from_complete_agent(self, mock_agent_file):
        """Test extracting metadata from agent with all attributes."""
        agent, _, _ = load_agent_module(str(mock_agent_file))
        metadata = extract_agent_metadata(agent)

        assert metadata["model_id"] == "test-model-id"
        assert metadata["max_tokens"] == 1000
        assert metadata["temperature"] == 0.7
        assert metadata["tool_count"] == 3
        assert len(metadata["tools"]) == 3
        assert "tool1" in metadata["tools"]
        assert "tool2" in metadata["tools"]
        assert "tool3" in metadata["tools"]

    def test_extract_metadata_minimal_agent(self, agent_without_metadata):
        """Test extracting metadata from agent with minimal attributes."""
        agent, _, _ = load_agent_module(str(agent_without_metadata))
        metadata = extract_agent_metadata(agent)

        assert metadata.get("tool_count") == 0
        assert metadata.get("tools") == []

    def test_extract_metadata_claude_model_cleanup(self, tmp_path):
        """Test that AWS Claude model IDs are cleaned up."""
        agent_file = tmp_path / "claude_agent.py"
        agent_file.write_text(
            """
class Model:
    def __init__(self):
        self.model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

class Agent:
    def __init__(self):
        self.model = Model()

root_agent = Agent()
"""
        )

        agent, _, _ = load_agent_module(str(agent_file))
        metadata = extract_agent_metadata(agent)

        # Should be cleaned up to readable format
        assert metadata["model_id"] == "Claude Sonnet 4.5"

    def test_extract_metadata_various_claude_versions(self, tmp_path):
        """Test metadata extraction for different Claude versions."""
        test_cases = [
            ("us.anthropic.claude-sonnet-3-5-v1:0", "Claude Sonnet 3.5"),
            ("claude-opus-v1", "Claude Opus"),
            ("claude-haiku-model", "Claude Haiku"),
            ("anthropic.claude-sonnet-v1", "Claude Sonnet"),
        ]

        for model_id, expected in test_cases:
            agent_file = tmp_path / f"agent_{expected.replace(' ', '_')}.py"
            agent_file.write_text(
                f"""
class Model:
    def __init__(self):
        self.model_id = "{model_id}"

class Agent:
    def __init__(self):
        self.model = Model()

root_agent = Agent()
"""
            )

            agent, _, _ = load_agent_module(str(agent_file))
            metadata = extract_agent_metadata(agent)
            assert metadata["model_id"] == expected

    def test_extract_tools_with_different_formats(self, tmp_path):
        """Test extracting tools in different formats."""
        agent_file = tmp_path / "tools_agent.py"
        agent_file.write_text(
            """
def tool_function():
    pass

class Tool:
    def __init__(self, name):
        self.name = name

class FunctionTool:
    def __init__(self, func):
        self.func = func

class Agent:
    def __init__(self):
        self.tools = [
            Tool("named_tool"),
            FunctionTool(tool_function),
            "string_tool"
        ]

root_agent = Agent()
"""
        )

        agent, _, _ = load_agent_module(str(agent_file))
        metadata = extract_agent_metadata(agent)

        assert metadata["tool_count"] == 3
        assert "named_tool" in metadata["tools"]
        assert "tool_function" in metadata["tools"]

    def test_extract_metadata_truncates_many_tools(self, tmp_path):
        """Test that tool list is truncated to first 10."""
        agent_file = tmp_path / "many_tools_agent.py"
        tools_list = ", ".join([f'Tool("tool{i}")' for i in range(15)])
        agent_file.write_text(
            f"""
class Tool:
    def __init__(self, name):
        self.name = name

class Agent:
    def __init__(self):
        self.tools = [{tools_list}]

root_agent = Agent()
"""
        )

        agent, _, _ = load_agent_module(str(agent_file))
        metadata = extract_agent_metadata(agent)

        assert metadata["tool_count"] == 15
        assert len(metadata["tools"]) == 10  # Should only return first 10

    def test_extract_metadata_tools_alternate_attributes(self, tmp_path):
        """Test extracting tools from alternate attribute names."""
        agent_file = tmp_path / "alt_tools_agent.py"
        agent_file.write_text(
            """
class Tool:
    def __init__(self, name):
        self.name = name

class Agent:
    def __init__(self):
        self._tools = [Tool("tool1"), Tool("tool2")]

root_agent = Agent()
"""
        )

        agent, _, _ = load_agent_module(str(agent_file))
        metadata = extract_agent_metadata(agent)

        assert metadata["tool_count"] == 2
        assert "tool1" in metadata["tools"]

    def test_extract_metadata_no_model(self, agent_without_metadata):
        """Test extracting metadata from agent without model."""
        agent, _, _ = load_agent_module(str(agent_without_metadata))
        metadata = extract_agent_metadata(agent)

        # Should return empty metadata
        assert "model_id" not in metadata or metadata["model_id"] == "Unknown Model"


class TestRelativeImports:
    """Test relative imports in agent packages."""

    def test_agent_with_relative_imports(self, tmp_path):
        """Test loading agent that uses relative imports."""
        # Create a package structure:
        # my_agent/
        #   __init__.py
        #   agent.py (has: from .utils import helper)
        #   utils.py (has: helper function)

        agent_dir = tmp_path / "my_agent"
        agent_dir.mkdir()

        # Create __init__.py to make it a package
        (agent_dir / "__init__.py").write_text("")

        # Create utils module with a helper function
        (agent_dir / "utils.py").write_text(
            """
def helper():
    return "Helper function result"
"""
        )

        # Create agent that uses relative import
        agent_file = agent_dir / "agent.py"
        agent_file.write_text(
            """
from .utils import helper

class Agent:
    def __init__(self):
        self.name = "Test Agent"
        self.helper_result = helper()

root_agent = Agent()
"""
        )

        # Load the agent - should work with relative imports
        agent, name, description = load_agent_module(str(agent_file))

        assert agent is not None
        assert name == "Test Agent"
        assert hasattr(agent, "helper_result")
        assert agent.helper_result == "Helper function result"

    def test_agent_with_parent_relative_imports(self, tmp_path):
        """Test loading agent with parent-level relative imports."""
        # Create a deeper package structure:
        # my_package/
        #   __init__.py
        #   shared/
        #     __init__.py
        #     helpers.py
        #   agents/
        #     __init__.py
        #     agent.py (has: from ..shared.helpers import func)

        root = tmp_path / "my_package"
        root.mkdir()
        (root / "__init__.py").write_text("")

        shared = root / "shared"
        shared.mkdir()
        (shared / "__init__.py").write_text("")
        (shared / "helpers.py").write_text(
            """
def shared_function():
    return "Shared function"
"""
        )

        agents = root / "agents"
        agents.mkdir()
        (agents / "__init__.py").write_text("")

        agent_file = agents / "agent.py"
        agent_file.write_text(
            """
from ..shared.helpers import shared_function

class Agent:
    def __init__(self):
        self.result = shared_function()

root_agent = Agent()
"""
        )

        # Load the agent - should work with parent relative imports
        agent, _, _ = load_agent_module(str(agent_file))

        assert agent is not None
        assert hasattr(agent, "result")
        assert agent.result == "Shared function"

    def test_agent_with_multiple_sibling_imports(self, tmp_path):
        """Test loading agent that imports from multiple sibling modules."""
        # Create package structure:
        # multi_import/
        #   __init__.py
        #   agent.py (imports from .utils, .helpers, .config)
        #   utils.py
        #   helpers.py
        #   config.py

        agent_dir = tmp_path / "multi_import"
        agent_dir.mkdir()
        (agent_dir / "__init__.py").write_text("")

        # Create multiple utility modules
        (agent_dir / "utils.py").write_text('VALUE = "utils"')
        (agent_dir / "helpers.py").write_text('HELPER = "helper"')
        (agent_dir / "config.py").write_text('CONFIG = "config"')

        # Create agent that imports from all of them
        agent_file = agent_dir / "agent.py"
        agent_file.write_text(
            """
from .utils import VALUE
from .helpers import HELPER
from .config import CONFIG

class Agent:
    def __init__(self):
        self.name = "Multi Import Agent"
        self.combined = f"{VALUE}_{HELPER}_{CONFIG}"

root_agent = Agent()
"""
        )

        # Should work with multiple sibling imports
        agent, name, description = load_agent_module(str(agent_file))

        assert agent is not None
        assert name == "Multi Import Agent"
        assert hasattr(agent, "combined")
        assert agent.combined == "utils_helper_config"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_invalid_python_syntax(self, tmp_path):
        """Test loading agent file with invalid Python syntax."""
        agent_file = tmp_path / "invalid.py"
        agent_file.write_text("this is not valid python ][{")

        with pytest.raises((SyntaxError, ImportError)):
            load_agent_module(str(agent_file))

    def test_agent_with_import_errors(self, tmp_path):
        """Test loading agent that has import errors."""
        agent_file = tmp_path / "import_error.py"
        agent_file.write_text(
            """
import nonexistent_module

class Agent:
    pass

root_agent = Agent()
"""
        )

        with pytest.raises(ImportError, match="Failed to execute module"):
            load_agent_module(str(agent_file))

    def test_metadata_with_unknown_model_id(self, tmp_path):
        """Test metadata extraction with unknown model."""
        agent_file = tmp_path / "unknown_model.py"
        agent_file.write_text(
            """
class Model:
    model_id = "unknown-custom-model"

class Agent:
    model = Model()

root_agent = Agent()
"""
        )

        agent, _, _ = load_agent_module(str(agent_file))
        metadata = extract_agent_metadata(agent)

        # Should preserve unknown model name
        assert metadata["model_id"] == "unknown-custom-model"
