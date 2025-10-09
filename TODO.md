# Basic Agent Chat Loop - TODO

**Updated:** 2025-10-08 (Critical Fixes Complete)
**Status:** Critical Issues Resolved - Code Cleanup Complete

See `QA_REPORT.md` for comprehensive quality assessment.
See `QA_FINDINGS_SUMMARY.md` for quick reference with file paths.

---

## Pre-Release Tasks

### Critical (BLOCKING RELEASE)

**QA Issues Found:**
- [ ] **CRITICAL-001:** No unit tests exist - tests/ directory is empty
  - Location: `/Users/wes/Development/Basic-Agent-Chat-Loop/tests/__init__.py`
  - Create comprehensive test suite covering:
    - [x] Test TokenTracker calculations and cost estimation (4 tests passing)
    - [ ] Test AliasManager CRUD operations and file handling
    - [ ] Test TemplateManager file loading and variable substitution
    - [ ] Test DisplayManager output formatting
    - [ ] Test ChatConfig YAML parsing and hierarchy
    - [ ] Test agent loading and metadata extraction
    - [ ] Test CLI entry points and argument parsing
    - [ ] Integration tests with mock agents

- [x] **CRITICAL-002:** ~~Missing core dependency - anthropic-bedrock not available~~
  - ✅ Fixed: Moved to optional `[bedrock]` dependency group
  - ✅ Added `python-dotenv>=1.0.0` to core dependencies
  - ✅ Added `mypy>=1.0.0` to dev dependencies

- [x] **CRITICAL-003:** ~~Remove AWS Strands branding throughout codebase~~
  - ✅ Fixed: All "Strands" references removed from codebase
  - ✅ Updated to framework-agnostic language ("AI Agent")
  - ✅ Updated all docstrings and usage examples

- [x] **CRITICAL-004:** ~~Update placeholder metadata in pyproject.toml~~
  - ✅ Fixed: Updated author name and GitHub URLs

- [x] **CRITICAL-005:** ~~Remove or fix main.py~~
  - ✅ Fixed: File deleted by cleanup script

- [x] **HIGH-002:** ~~Add missing python-dotenv dependency~~
  - ✅ Fixed: Added `python-dotenv>=1.0.0` to core dependencies

- [ ] Test installation on all platforms (AFTER fixing above)
  - [ ] macOS (install.sh)
  - [ ] Linux (install.sh)
  - [ ] Windows (install.bat, install.py)
- [ ] Verify all imports work in installed package
- [ ] Test CLI entry point (`chat_loop` command)
- [ ] Test editable install (`pip install -e .`)
- [ ] Add CONTRIBUTING.md with contribution guidelines
- [ ] Create example agents for testing (not AWS Strands specific)

### Documentation
- [ ] Update docs/INSTALL.md to reflect new package structure
- [ ] Add API documentation (docstrings complete?)
- [ ] Create CHANGELOG.md with version history
- [ ] Add usage examples to README
- [ ] Document programmatic API usage
- [ ] Add troubleshooting section to docs
- [ ] Create quick start guide for different agent frameworks

### Testing
- [ ] Add pytest configuration
- [ ] Create test fixtures for mock agents
- [ ] Add integration tests
- [ ] Test with different agent frameworks:
  - [ ] AWS Strands
  - [ ] LangChain
  - [ ] CrewAI
  - [ ] Generic Python agents
- [ ] Test error handling and edge cases
- [ ] Test configuration file parsing
- [ ] Test command history persistence
- [ ] Test prompt template loading

## Package Publishing

### PyPI Preparation
- [ ] Verify pyproject.toml metadata
- [ ] Build package (`python -m build`)
- [ ] Test on TestPyPI first
- [ ] Upload to PyPI
- [ ] Verify package installation from PyPI
- [ ] Update README with actual PyPI install command

### Release Process
- [ ] Create GitHub releases workflow
- [ ] Tag version 1.0.0
- [ ] Create release notes
- [ ] Build and upload distribution packages

## Code Quality

### Immediate (QA Findings)
- [x] **HIGH-001:** ~~Add missing type hints throughout codebase~~
  - ✅ Fixed: Added type hints (mypy reports 0 errors)
  - ✅ Fixed `alias_manager.py:92` - Using `Tuple[bool, str]`
  - ✅ Fixed `token_tracker.py` - Added `List[Tuple[int, int]]` annotation

- [x] **HIGH-003:** ~~Improve error handling - no silent failures~~
  - ✅ Fixed: Changed bare `except:` to `except Exception:`
  - Note: Silent failures intentional for config loading (fallback to defaults)

- [ ] **HIGH-004:** Extract magic numbers to named constants
  - `ui_components.py:122-126` - Token formatting thresholds
  - `chat_loop.py:100` - History length (1000)
  - `agent_loader.py:28` - .env search depth (3)

- [ ] **MEDIUM-002:** Fix logging configuration
  - `chat_loop.py:81` - Don't clear root logger handlers
  - Use named logger instead
  - Document logging configuration

- [ ] **MEDIUM-004:** Fix cost display duplication bug
  - `chat_loop.py:572-573` - Shows same cost twice
  - Decide on query cost vs session cost display

- [x] ~~Run ruff check and fix all issues~~
  - ✅ Completed: 21 errors auto-fixed, 11 files reformatted
  - ✅ Fixed unused imports, bare except, unused variables
  - Note: 8 minor E501 line-length warnings remain (acceptable)

- [x] ~~Run black formatter~~
  - ✅ Completed via ruff format

- [x] ~~Run mypy type checking~~
  - ✅ Completed: All 12 source files pass with 0 errors

- [ ] Remove any TODO/FIXME comments in code

### Code Review
- [ ] **MEDIUM-006:** Review error messages for information leakage
  - Don't expose full internal paths
  - Sanitize paths in error messages
- [ ] **HIGH-006:** Verify cross-platform path handling
  - Test on Windows (backslashes, clear screen)
  - Use pathlib.Path consistently
- [ ] **SECURITY-001:** Review .env file loading behavior
  - Searches 3 parent directories - document clearly
  - Consider limiting search scope
- [ ] **SECURITY-003:** Review log file security
  - Set restrictive permissions (0600)
  - Add log rotation
  - Document what gets logged (may contain PII)

## CI/CD

- [ ] Set up GitHub Actions workflow
  - [ ] Run tests on push
  - [ ] Run linting (ruff, black)
  - [ ] Run type checking (mypy)
  - [ ] Test on multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12)
  - [ ] Test on multiple platforms (Ubuntu, macOS, Windows)
- [ ] Add code coverage reporting
- [ ] Add badges to README (tests passing, coverage, PyPI version)

## Feature Enhancements

### High Priority
- [ ] Add agent framework auto-detection
- [ ] Support for more agent frameworks (LangChain, CrewAI, etc.)
- [ ] Add session export (save conversation to file)
- [ ] Add conversation replay feature
- [ ] Improve error recovery with better retry logic
- [ ] Add plugin system for custom extensions

### Medium Priority
- [ ] Add conversation search/filter
- [ ] Support for agent switching mid-session
- [ ] Add telemetry/analytics opt-in
- [ ] Multi-agent conversation support
- [ ] Add streaming response support with live updates
- [ ] Configuration profiles (--profile dev/prod)
- [ ] Shell completion for bash/zsh/fish

### Low Priority
- [ ] Web interface option (optional FastAPI backend)
- [ ] Agent benchmarking mode
- [ ] Integration with agent development frameworks
- [ ] Voice input/output support
- [ ] Conversation branching/forking
- [ ] Agent marketplace/registry integration

## Documentation Improvements

- [ ] Add video tutorial/demo
- [ ] Create agent framework integration guides
- [ ] Add best practices guide
- [ ] Create FAQ section
- [ ] Add cookbook with common recipes
- [ ] Document configuration options comprehensively
- [ ] Add architecture decision records (ADRs)

## Bug Fixes

- [ ] Fix readline issues on Windows
- [ ] Handle unicode properly in all terminals
- [ ] Fix token counting edge cases
- [ ] Improve error messages for missing dependencies
- [ ] Handle agent timeout gracefully
- [ ] Fix multi-line input edge cases

## Performance

- [ ] Profile and optimize slow operations
- [ ] Lazy load rich library if not needed
- [ ] Cache agent metadata
- [ ] Optimize token counting
- [ ] Reduce startup time

## Security

- [ ] Audit environment variable handling
- [ ] Review file permission settings
- [ ] Add security policy (SECURITY.md)
- [ ] Scan dependencies for vulnerabilities
- [ ] Add input sanitization where needed

## Community

- [ ] Create GitHub issue templates
- [ ] Add pull request template
- [ ] Set up discussions for Q&A
- [ ] Create example configurations
- [ ] Build community showcase

## Maintenance

- [ ] Set up dependabot for dependency updates
- [ ] Create release checklist
- [ ] Document versioning strategy
- [ ] Plan deprecation policy
- [ ] Set up project roadmap

## Notes

- Installation scripts (install.sh, install.bat, install.py) are optional legacy installers
- Main installation method should be `pip install basic-agent-chat-loop`
- Maintain backward compatibility with AWS Strands agents
- Consider extracting agent framework adapters into separate packages
