# Contributing to Basic Agent Chat Loop

Thank you for your interest in contributing to Basic Agent Chat Loop! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, package version)
- **Error messages or logs** (if applicable)
- **Screenshots** (if applicable)

**Example Bug Report:**
```markdown
**Bug:** Cost display shows $0 even with token usage

**Steps to Reproduce:**
1. Run `chat_loop myagent`
2. Ask a question that generates tokens
3. Observe the cost display

**Expected:** Cost should show calculated amount (e.g., $0.015)
**Actual:** Shows $0.000

**Environment:**
- OS: macOS 14.0
- Python: 3.11.5
- Package: basic-agent-chat-loop==1.0.0

**Logs:**
[Paste relevant log output here]
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - Why is this enhancement useful?
- **Proposed solution** - How should it work?
- **Alternatives considered** - What other approaches did you consider?
- **Additional context** - Screenshots, mockups, examples

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the development setup** instructions below
3. **Make your changes** following our coding standards
4. **Add tests** for any new functionality
5. **Update documentation** if needed
6. **Ensure all tests pass** and code is formatted
7. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Python 3.8 or higher
- git

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/your-username/Basic-Agent-Chat-Loop.git
cd Basic-Agent-Chat-Loop

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all extras
pip install -e ".[dev,windows,bedrock]"

# Install pre-commit hooks (if using)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/basic_agent_chat_loop tests/

# Run specific test file
pytest tests/unit/test_token_tracker.py

# Run with verbose output
pytest -v
```

### Code Quality Checks

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/ --fix

# Type check with mypy
mypy src/basic_agent_chat_loop/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ --fix && mypy src/
```

## Coding Standards

### Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use **Black** for code formatting (line length: 88)
- Use **Ruff** for linting
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions and classes

### Code Organization

```python
"""Module docstring explaining purpose."""

import standard_library
import third_party_packages

from .local_modules import something

# Module constants
CONSTANT_VALUE = 100


class MyClass:
    """Class docstring."""

    def __init__(self, param: str):
        """Initialize with clear docstring."""
        self.param = param

    def public_method(self) -> str:
        """Public method with docstring and type hints."""
        return self._private_method()

    def _private_method(self) -> str:
        """Private methods also have docstrings."""
        return self.param
```

### Documentation Standards

- **Docstrings**: Use Google-style docstrings
- **Comments**: Explain "why", not "what"
- **Type hints**: Use for all parameters and return values
- **README updates**: Update if changing user-facing features

**Example Docstring:**
```python
def calculate_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """
    Calculate the cost of an API call based on token usage.

    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        model: Model identifier (e.g., "Claude Sonnet 4.5")

    Returns:
        Cost in USD as a float

    Raises:
        ValueError: If model is not supported

    Example:
        >>> calculate_cost(1000, 500, "Claude Sonnet 4.5")
        0.045
    """
```

### Testing Standards

- **Write tests** for all new functionality
- **Aim for 70%+ coverage** on new code
- **Use descriptive test names** that explain what is being tested
- **Use fixtures** for common test setups
- **Mock external dependencies** (file system, network calls)

**Example Test:**
```python
class TestTokenTracker:
    """Test suite for TokenTracker class."""

    def test_add_usage_accumulates_tokens(self):
        """Test that add_usage correctly accumulates input and output tokens."""
        tracker = TokenTracker(model="test-model")

        tracker.add_usage(100, 50)
        tracker.add_usage(200, 75)

        assert tracker.get_total_tokens() == 425
        assert tracker.input_tokens == 300
        assert tracker.output_tokens == 125
```

## Project Structure

```
Basic-Agent-Chat-Loop/
├── src/basic_agent_chat_loop/     # Source code
│   ├── __init__.py
│   ├── cli.py                     # CLI entry point
│   ├── chat_loop.py               # Main chat loop
│   ├── chat_config.py             # Configuration management
│   └── components/                # Modular components
│       ├── alias_manager.py
│       ├── token_tracker.py
│       ├── template_manager.py
│       ├── display_manager.py
│       ├── agent_loader.py
│       └── ui_components.py
├── tests/                         # Test suite
│   ├── conftest.py               # Shared fixtures
│   └── unit/                     # Unit tests
├── docs/                          # Documentation
├── pyproject.toml                 # Package configuration
├── README.md                      # Main documentation
├── CHANGELOG.md                   # Version history
└── CONTRIBUTING.md                # This file
```

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: add session export functionality
fix: resolve token counting bug for streaming responses
docs: update configuration examples in README
test: add tests for alias manager edge cases
refactor: extract display logic to separate component
chore: update dependencies to latest versions
```

**Format:**
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `style`: Code style changes (formatting, etc.)

## Branch Naming

Use descriptive branch names:

```
feature/session-export
bugfix/token-counting-streaming
docs/update-config-guide
test/alias-manager-coverage
```

## Pull Request Process

1. **Update Documentation**: Ensure README, docstrings, and relevant docs are updated
2. **Add Tests**: New functionality requires tests
3. **Update CHANGELOG**: Add entry under `[Unreleased]` section
4. **Run Quality Checks**: Ensure all checks pass
5. **Request Review**: Assign reviewers if you know who should review
6. **Address Feedback**: Respond to review comments and make requested changes
7. **Squash Commits**: Consider squashing commits before merge (if requested)

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (move items from Unreleased to new version)
3. Create release commit: `chore: release v1.1.0`
4. Tag release: `git tag v1.1.0`
5. Push tag: `git push origin v1.1.0`
6. Build and publish to PyPI
7. Create GitHub release with notes from CHANGELOG

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an issue with the bug template
- **Security**: Email security issues to [maintainer-email]
- **Chat**: Join our Discord (if available)

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- Git commit history

Thank you for contributing to Basic Agent Chat Loop! 🎉
