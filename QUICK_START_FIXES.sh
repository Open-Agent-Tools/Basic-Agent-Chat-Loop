#!/bin/bash
# Basic Agent Chat Loop - Quick Start Fixes
# Run this script to address immediate QA findings

set -e

echo "=========================================="
echo "Basic Agent Chat Loop - Quick Fixes"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# 1. Remove unrelated main.py
echo "1. Removing main.py (PyCharm sample code)..."
if [ -f "main.py" ]; then
    rm main.py
    echo "   ✓ Removed main.py"
else
    echo "   - main.py already removed"
fi

# 2. Find AWS Strands references
echo ""
echo "2. Finding AWS Strands references to update..."
echo "   Files to update:"
grep -rl "Strands" src/ README.md docs/ 2>/dev/null | sed 's/^/   - /'

# 3. Check for missing dependencies
echo ""
echo "3. Checking for import mismatches..."
python3 << 'PYEOF'
import ast
from pathlib import Path

imports = set()
for file in Path('src').rglob('*.py'):
    try:
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except:
        pass

stdlib = {'os', 'sys', 'time', 'pathlib', 'typing', 'logging', 'argparse',
          'asyncio', 'importlib', 'json', 'copy', 'platform', 'subprocess'}
external = sorted(imports - stdlib)
print('   External imports found:', ', '.join(external))
print('   ⚠ Verify these are in pyproject.toml dependencies')
PYEOF

# 4. List files needing updates
echo ""
echo "4. Files requiring manual updates:"
echo "   - pyproject.toml (lines 13, 29, 46-48)"
echo "     • Update author/email"
echo "     • Update repository URLs"
echo "     • Add python-dotenv dependency"
echo "     • Verify anthropic-bedrock availability"
echo ""
echo "   - src/basic_agent_chat_loop/chat_loop.py"
echo "     • Lines 3, 5, 22-24, 147, 787: Remove Strands refs"
echo "     • Line 81: Fix logging config"
echo "     • Line 100: Extract magic number (1000)"
echo "     • Lines 572-573: Fix duplicate cost display"
echo ""
echo "   - src/basic_agent_chat_loop/components/agent_loader.py"
echo "     • Line 28: Extract magic number (3)"
echo "     • Line 78: Remove Strands reference"
echo ""
echo "   - src/basic_agent_chat_loop/components/alias_manager.py"
echo "     • Line 92: Fix type hint (tuple -> Tuple[bool, str])"
echo ""
echo "   - src/basic_agent_chat_loop/chat_config.py"
echo "     • Lines 126-127: Improve error handling"

# 5. Create test structure
echo ""
echo "5. Creating test directory structure..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures

cat > tests/conftest.py << 'CONFTEST'
"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path
from typing import Dict, Any

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
            self.model = type('obj', (object,), {'model_id': 'test-model'})()

        def __call__(self, query):
            return {"message": "Test response"}

    return MockAgent()
CONFTEST

cat > tests/unit/test_token_tracker.py << 'TOKENTEST'
"""Tests for TokenTracker component."""
import pytest
from basic_agent_chat_loop.components.token_tracker import TokenTracker


def test_token_tracker_initialization():
    """Test TokenTracker initializes correctly."""
    tracker = TokenTracker("Claude Sonnet 4.5")
    assert tracker.model_name == "Claude Sonnet 4.5"
    assert tracker.total_input_tokens == 0
    assert tracker.total_output_tokens == 0


def test_add_usage():
    """Test adding token usage."""
    tracker = TokenTracker("Claude Sonnet 4.5")
    tracker.add_usage(100, 50)
    assert tracker.total_input_tokens == 100
    assert tracker.total_output_tokens == 50
    assert tracker.get_total_tokens() == 150


def test_cost_calculation():
    """Test cost calculation for known model."""
    tracker = TokenTracker("Claude Sonnet 4.5")
    tracker.add_usage(1_000_000, 1_000_000)  # 1M tokens each
    cost = tracker.get_cost()
    assert cost == 18.0  # $3 input + $15 output


def test_format_tokens():
    """Test token formatting with K/M suffixes."""
    tracker = TokenTracker()
    assert tracker.format_tokens(500) == "500"
    assert tracker.format_tokens(1_500) == "1.5K"
    assert tracker.format_tokens(2_500_000) == "2.5M"
TOKENTEST

echo "   ✓ Created test structure"
echo "   ✓ Created tests/conftest.py"
echo "   ✓ Created tests/unit/test_token_tracker.py"

# 6. Create .gitattributes for Windows compatibility
echo ""
echo "6. Creating .gitattributes for cross-platform compatibility..."
cat > .gitattributes << 'GITATTR'
# Force Windows line endings for batch files
*.bat text eol=crlf

# Force Unix line endings for shell scripts
*.sh text eol=lf

# Python files use LF
*.py text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.toml text eol=lf
GITATTR
echo "   ✓ Created .gitattributes"

# 7. Summary
echo ""
echo "=========================================="
echo "Quick Fixes Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Review and update files listed above"
echo "2. Add python-dotenv to pyproject.toml"
echo "3. Run: pip install -e '.[dev]'"
echo "4. Run: pytest -v"
echo "5. Run: mypy src/"
echo "6. Run: ruff check src/ --fix"
echo "7. Run: black src/ tests/"
echo ""
echo "See QA_REPORT.md for complete details"
echo ""
