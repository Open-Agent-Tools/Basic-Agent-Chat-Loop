"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / ".chatrc"
    config_file.write_text("""
features:
  show_tokens: true
  rich_enabled: true

behavior:
  max_retries: 3
  timeout: 120.0
""")
    return config_file


@pytest.fixture
def temp_aliases_file(tmp_path):
    """Create a temporary aliases file."""
    aliases_file = tmp_path / ".chat_aliases"
    return aliases_file


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""

    class MockAgent:
        def __init__(self):
            self.name = "Test Agent"
            self.description = "A test agent"
            self.model = type("obj", (object,), {"model_id": "test-model"})()

        def __call__(self, query):
            return {"message": "Test response"}

    return MockAgent()
