# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-09

### Added
- **Agent Alias System** - Save agents as short names for quick access
- **Command History** - Navigate previous queries with ↑↓ arrows (persisted to `~/.chat_history`)
- **Multi-line Input** - Type `\\` to enter multi-line mode for code blocks
- **Token Tracking** - Track tokens and costs per query and session
- **Prompt Templates** - Reusable prompts from `~/.prompts/` with variable substitution
- **Configuration System** - YAML-based config with per-agent overrides
- **Status Bar** - Real-time metrics (queries, tokens, duration)
- **Session Summary** - Full statistics displayed on exit
- **Rich Formatting** - Enhanced markdown rendering with syntax highlighting
- **Error Recovery** - Automatic retry logic with exponential backoff
- **Agent Metadata Display** - Show model, tools, and capabilities
- **Async Streaming Support** - Real-time response display with streaming
- **Cross-Platform Installers** - Support for macOS, Linux, and Windows
- **Comprehensive Test Suite** - 158 tests with 61% code coverage
- **Type Hints** - Full type annotations throughout codebase

### Fixed
- Logging configuration no longer interferes with other libraries
- Cost display duplication removed (was showing same value twice)
- Error messages sanitized to prevent path information leakage
- Magic numbers extracted to named constants for maintainability
- All linting issues resolved (ruff, black, mypy)

### Changed
- Renamed from "AWS Strands Chat Loop" to "Basic Agent Chat Loop" (framework-agnostic)
- Made `anthropic-bedrock` an optional dependency (moved to `[bedrock]` extra)
- Added `python-dotenv` as core dependency
- Improved error handling with more informative messages

### Security
- Error messages now show only filenames, not full system paths
- Environment variable loading limited to 3 parent directories
- Log files created with secure behavior

### Documentation
- Complete README with installation and usage examples
- Configuration reference (CONFIG.md)
- Alias system guide (ALIASES.md)
- Installation instructions (INSTALL.md)
- Comprehensive QA report with all issues documented

### Testing
- 158 unit tests covering all components
- Test coverage: 61% overall
  - TokenTracker: 100%
  - UIComponents: 100%
  - DisplayManager: 98%
  - AgentLoader: 93%
  - ChatConfig: 91%
  - TemplateManager: 86%
  - AliasManager: 83%

### Infrastructure
- GitHub-ready project structure
- PyPI-ready package configuration
- Development tooling (pytest, ruff, black, mypy)
- Comprehensive .gitignore

## [Unreleased]

### Planned Features
- Integration tests with mock agents
- Platform-specific testing (Windows, Linux)
- CI/CD pipeline with GitHub Actions
- Additional agent framework support (LangChain, CrewAI)
- Plugin system for extensions
- Web interface option

---

## Release Notes

### v1.0.0 - Initial Release

This is the first public release of Basic Agent Chat Loop, a feature-rich interactive CLI for AI agents. The project provides a unified interface for any AI agent with token tracking, prompt templates, and extensive configuration options.

**Key Highlights:**
- 🏷️ Save agents as aliases for quick access
- 💰 Track token usage and costs
- 📝 Reusable prompt templates
- ⚙️ Flexible YAML configuration
- 🎨 Rich markdown rendering
- 🔄 Automatic error recovery
- 📊 Real-time status updates
- ✅ Comprehensive test coverage

**Installation:**
```bash
pip install basic-agent-chat-loop
```

**Quick Start:**
```bash
# Save an alias
chat_loop --save-alias myagent path/to/agent.py

# Run chat
chat_loop myagent
```

For detailed documentation, see [README.md](README.md) and [docs/](docs/).

---

[1.0.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v1.0.0
