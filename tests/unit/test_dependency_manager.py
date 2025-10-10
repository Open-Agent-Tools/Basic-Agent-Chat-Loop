"""Tests for DependencyManager component."""

from unittest.mock import MagicMock, patch

import pytest

from basic_agent_chat_loop.components.dependency_manager import DependencyManager


@pytest.fixture
def agent_dir(tmp_path):
    """Create a temporary agent directory with agent.py."""
    agent_path = tmp_path / "agent.py"
    agent_path.write_text("# test agent")
    return tmp_path


@pytest.fixture
def dep_manager(agent_dir):
    """Create DependencyManager for test agent."""
    agent_path = agent_dir / "agent.py"
    return DependencyManager(str(agent_path))


class TestDependencyManagerInitialization:
    """Test DependencyManager initialization."""

    def test_initialization_with_absolute_path(self, agent_dir):
        """Test initialization with absolute path."""
        agent_path = agent_dir / "agent.py"
        manager = DependencyManager(str(agent_path))
        assert manager.agent_path == agent_path
        assert manager.agent_dir == agent_dir

    def test_initialization_with_relative_path(self, agent_dir, monkeypatch):
        """Test initialization with relative path."""
        monkeypatch.chdir(agent_dir.parent)
        agent_path = agent_dir.name + "/agent.py"
        manager = DependencyManager(agent_path)
        assert manager.agent_path.is_absolute()
        assert manager.agent_dir.is_absolute()


class TestDetectDependencyFile:
    """Test dependency file detection."""

    def test_detect_requirements_txt(self, agent_dir, dep_manager):
        """Test detection of requirements.txt."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("pyyaml>=6.0.1\nrich>=13.7.0\n")

        result = dep_manager.detect_dependency_file()
        assert result is not None
        file_type, file_path = result
        assert file_type == "requirements"
        assert file_path == req_file

    def test_detect_pyproject_toml_with_dependencies(self, agent_dir, dep_manager):
        """Test detection of pyproject.toml with dependencies."""
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-agent"
dependencies = [
    "pyyaml>=6.0.1",
    "rich>=13.7.0",
]
        """
        )

        result = dep_manager.detect_dependency_file()
        assert result is not None
        file_type, file_path = result
        assert file_type == "pyproject"
        assert file_path == pyproject

    def test_detect_pyproject_toml_alternative_format(self, agent_dir, dep_manager):
        """Test detection of pyproject.toml with alternative format."""
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project.dependencies]
pyyaml = ">=6.0.1"
rich = ">=13.7.0"
        """
        )

        result = dep_manager.detect_dependency_file()
        assert result is not None
        file_type, file_path = result
        assert file_type == "pyproject"
        assert file_path == pyproject

    def test_detect_setup_py(self, agent_dir, dep_manager):
        """Test detection of setup.py."""
        setup = agent_dir / "setup.py"
        setup.write_text(
            """
from setuptools import setup

setup(
    name="test-agent",
    install_requires=["pyyaml>=6.0.1"],
)
        """
        )

        result = dep_manager.detect_dependency_file()
        assert result is not None
        file_type, file_path = result
        assert file_type == "setup"
        assert file_path == setup

    def test_detect_no_dependency_files(self, dep_manager):
        """Test detection when no dependency files exist."""
        result = dep_manager.detect_dependency_file()
        assert result is None

    def test_detect_priority_requirements_over_pyproject(self, agent_dir, dep_manager):
        """Test that requirements.txt has priority over pyproject.toml."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("pyyaml>=6.0.1\n")

        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project]
dependencies = ["rich>=13.7.0"]
        """
        )

        result = dep_manager.detect_dependency_file()
        assert result is not None
        file_type, file_path = result
        assert file_type == "requirements"
        assert file_path == req_file

    def test_detect_pyproject_without_dependencies(self, agent_dir, dep_manager):
        """Test that pyproject.toml without dependencies is skipped."""
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-agent"
version = "1.0.0"
        """
        )

        setup = agent_dir / "setup.py"
        setup.write_text("# setup")

        result = dep_manager.detect_dependency_file()
        # Should skip pyproject and find setup.py
        assert result is not None
        file_type, file_path = result
        assert file_type == "setup"


class TestInstallDependencies:
    """Test dependency installation."""

    @patch("subprocess.run")
    def test_install_from_requirements_success(self, mock_run, agent_dir, dep_manager):
        """Test successful installation from requirements.txt."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("pyyaml>=6.0.1\n")

        # Mock successful pip install
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        success, message = dep_manager.install_dependencies("requirements", req_file)
        assert success is True
        assert "Successfully installed" in message
        assert "requirements.txt" in message

    @patch("subprocess.run")
    def test_install_from_requirements_failure(self, mock_run, agent_dir, dep_manager):
        """Test failed installation from requirements.txt."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("nonexistent-package>=99.99.99\n")

        # Mock failed pip install
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "ERROR: Could not find a version"
        mock_run.return_value = mock_result

        success, message = dep_manager.install_dependencies("requirements", req_file)
        assert success is False
        assert "Failed to install" in message

    @patch("subprocess.run")
    def test_install_from_pyproject_success(self, mock_run, agent_dir, dep_manager):
        """Test successful installation from pyproject.toml."""
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-agent"
dependencies = ["pyyaml>=6.0.1"]
        """
        )

        # Mock successful pip install
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        success, message = dep_manager.install_dependencies("pyproject", pyproject)
        assert success is True
        assert "Successfully installed project" in message

    @patch("subprocess.run")
    def test_install_from_setup_success(self, mock_run, agent_dir, dep_manager):
        """Test successful installation from setup.py."""
        setup = agent_dir / "setup.py"
        setup.write_text("# setup")

        # Mock successful pip install
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        success, message = dep_manager.install_dependencies("setup", setup)
        assert success is True
        assert "Successfully installed project" in message

    def test_install_unknown_file_type(self, agent_dir, dep_manager):
        """Test installation with unknown file type."""
        fake_file = agent_dir / "unknown.txt"
        fake_file.write_text("test")

        success, message = dep_manager.install_dependencies("unknown", fake_file)
        assert success is False
        assert "Unknown dependency file type" in message

    @patch("subprocess.run")
    def test_install_timeout(self, mock_run, agent_dir, dep_manager):
        """Test installation timeout."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("pyyaml>=6.0.1\n")

        # Mock timeout
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("pip", 300)

        success, message = dep_manager.install_dependencies("requirements", req_file)
        assert success is False
        assert "timed out" in message.lower()


class TestSuggestAutoSetup:
    """Test auto-setup suggestion."""

    def test_suggest_when_requirements_exists(self, agent_dir, dep_manager):
        """Test suggestion when requirements.txt exists."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("pyyaml>=6.0.1\n")

        suggestion = dep_manager.suggest_auto_setup()
        assert suggestion is not None
        assert "requirements.txt" in suggestion
        assert "--auto-setup" in suggestion or "-a" in suggestion

    def test_suggest_when_pyproject_exists(self, agent_dir, dep_manager):
        """Test suggestion when pyproject.toml exists."""
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project]
dependencies = ["pyyaml>=6.0.1"]
        """
        )

        suggestion = dep_manager.suggest_auto_setup()
        assert suggestion is not None
        assert "pyproject.toml" in suggestion

    def test_no_suggestion_when_no_deps(self, dep_manager):
        """Test no suggestion when no dependency files exist."""
        suggestion = dep_manager.suggest_auto_setup()
        assert suggestion is None


class TestInstallCommandConstruction:
    """Test that correct pip commands are constructed."""

    @patch("subprocess.run")
    def test_requirements_uses_pip_install_r(self, mock_run, agent_dir, dep_manager):
        """Test that requirements.txt uses 'pip install -r'."""
        req_file = agent_dir / "requirements.txt"
        req_file.write_text("pyyaml>=6.0.1\n")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        dep_manager.install_dependencies("requirements", req_file)

        # Check that subprocess.run was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]  # First positional argument
        assert "-m" in call_args
        assert "pip" in call_args
        assert "install" in call_args
        assert "-r" in call_args
        assert str(req_file) in call_args

    @patch("subprocess.run")
    def test_pyproject_uses_pip_install_e(self, mock_run, agent_dir, dep_manager):
        """Test that pyproject.toml uses 'pip install -e'."""
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            """
[project]
dependencies = ["pyyaml>=6.0.1"]
        """
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        dep_manager.install_dependencies("pyproject", pyproject)

        # Check that subprocess.run was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "pip" in call_args
        assert "install" in call_args
        assert "-e" in call_args
        assert str(agent_dir) in call_args  # Should install from directory
