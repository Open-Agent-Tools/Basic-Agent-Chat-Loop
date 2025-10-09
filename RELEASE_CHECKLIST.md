# Basic Agent Chat Loop - v0.1.0 Release Checklist

**Status:** Ready for Testing
**Version:** 0.1.0
**Date:** 2025-10-09

---

## ✅ Pre-Release QA Completed

- [x] **Code Quality Fixes**
  - [x] Fixed logging configuration (no longer clears root handlers)
  - [x] Fixed cost display duplication bug
  - [x] Sanitized error messages (removed path exposure)
  - [x] Extracted magic numbers to constants
  - [x] All linting issues resolved (ruff, black, mypy)

- [x] **Testing**
  - [x] 158 unit tests passing
  - [x] 61% code coverage achieved
  - [x] All critical and high-priority bugs fixed

- [x] **Documentation**
  - [x] README.md complete with usage examples
  - [x] CHANGELOG.md created with full v0.1.0 history
  - [x] CONTRIBUTING.md with development guidelines
  - [x] All documentation files reviewed

- [x] **Package Metadata**
  - [x] Updated author email: unseriousai@gmail.com
  - [x] Updated GitHub URLs: Open-Agent-Tools/Basic-Agent-Chat-Loop
  - [x] Development status: Beta
  - [x] All required classifiers present

- [ ] **Build**
  - [ ] Source distribution built: `basic_agent_chat_loop-0.1.0.tar.gz`
  - [ ] Wheel built: `basic_agent_chat_loop-0.1.0-py3-none-any.whl`
  - [ ] Both packages validated with `twine check`

---

## 📋 Release Steps

### Step 1: Test on TestPyPI (RECOMMENDED)

Before publishing to the real PyPI, test on TestPyPI first:

```bash
# 1. Upload to TestPyPI (requires TestPyPI account)
python -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your TestPyPI API token>

# 2. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ basic-agent-chat-loop

# 3. Test the command works
chat_loop --help

# 4. Test basic functionality
#    (You'll need a test agent to fully verify)

# 5. Uninstall test version
pip uninstall basic-agent-chat-loop
```

**TestPyPI Setup:**
- Create account at: https://test.pypi.org/account/register/
- Generate API token at: https://test.pypi.org/manage/account/token/
- Save token securely (you'll only see it once)

### Step 2: Commit and Tag Release

```bash
# 1. Stage all changes
git add .

# 2. Commit release
git commit -m "chore: release v0.1.0

- Fixed logging configuration (MEDIUM-002)
- Fixed cost display duplication (MEDIUM-004)
- Fixed error message path leakage (MEDIUM-006)
- Added CHANGELOG.md and CONTRIBUTING.md
- Updated package metadata
- Built and validated distribution packages

All 158 tests passing with 61% coverage"

# 3. Create and push tag
git tag -a v0.1.0 -m "Release v0.1.0 - Initial public release"
git push origin main
git push origin v0.1.0
```

### Step 3: Create GitHub Release

1. Go to: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/new
2. Select tag: `v0.1.0`
3. Release title: `v0.1.0 - Initial Release`
4. Description: Copy from CHANGELOG.md (v0.1.0 section)
5. Upload artifacts:
   - `dist/basic_agent_chat_loop-0.1.0.tar.gz`
   - `dist/basic_agent_chat_loop-0.1.0-py3-none-any.whl`
6. Click "Publish release"

### Step 4: Publish to PyPI

**⚠️ CAUTION: This cannot be undone. Once published, you cannot delete or replace v0.1.0**

```bash
# 1. Upload to PyPI (requires PyPI account)
python -m twine upload dist/*

# You'll be prompted for:
# Username: __token__
# Password: <your PyPI API token>

# 2. Verify upload at: https://pypi.org/project/basic-agent-chat-loop/

# 3. Test installation from PyPI
pip install basic-agent-chat-loop

# 4. Verify command works
chat_loop --help
chat_loop --list-aliases
```

**PyPI Setup:**
- Create account at: https://pypi.org/account/register/
- Generate API token at: https://pypi.org/manage/account/token/
- Optionally add project-scoped token after first upload
- Configure in `~/.pypirc` (optional):

```ini
[pypi]
username = __token__
password = pypi-<your-token-here>

[testpypi]
username = __token__
password = pypi-<your-testpypi-token-here>
```

### Step 5: Post-Release Tasks

```bash
# 1. Update README badge (if not already):
#    [![PyPI version](https://badge.fury.io/py/basic-agent-chat-loop.svg)](https://pypi.org/project/basic-agent-chat-loop/)

# 2. Tweet/announce release (if applicable)

# 3. Update TODO.md to mark release tasks complete

# 4. Start development on v0.1.1 or v0.2.0
#    - Create new branch: git checkout -b develop
```

---

## 🧪 Testing Checklist

### Local Testing

- [ ] Install from local build: `pip install dist/basic_agent_chat_loop-0.1.0-py3-none-any.whl`
- [ ] Verify `chat_loop` command available
- [ ] Test `chat_loop --help`
- [ ] Test `chat_loop --list-aliases`
- [ ] Test with a sample agent
- [ ] Test configuration loading
- [ ] Test prompt templates
- [ ] Test token tracking display
- [ ] Uninstall: `pip uninstall basic-agent-chat-loop`

### TestPyPI Testing

- [ ] Upload to TestPyPI
- [ ] Install from TestPyPI
- [ ] Run all local tests again
- [ ] Verify dependencies install correctly
- [ ] Uninstall test version

### PyPI Testing (After Publishing)

- [ ] Install from PyPI
- [ ] Verify package on PyPI web interface
- [ ] Check that README renders correctly
- [ ] Verify all classifiers display properly
- [ ] Test installation on fresh virtual environment
- [ ] Test on different Python versions (3.8, 3.9, 3.10, 3.11, 3.12)

---

## 📊 Package Information

**Package Name:** basic-agent-chat-loop
**Version:** 0.1.0
**License:** MIT
**Python Requirement:** >=3.8
**Development Status:** Beta

**Distribution Files:**
- Source: `basic_agent_chat_loop-0.1.0.tar.gz`
- Wheel: `basic_agent_chat_loop-0.1.0-py3-none-any.whl`

**Dependencies:**
- `pyyaml>=6.0.1`
- `rich>=13.7.0`
- `python-dotenv>=1.0.0`

**Optional Dependencies:**
- `[dev]`: pytest, pytest-cov, black, ruff, mypy
- `[windows]`: pyreadline3
- `[bedrock]`: anthropic-bedrock

---

## 🔍 Verification Commands

```bash
# Check package contents
tar -tzf dist/basic_agent_chat_loop-0.1.0.tar.gz | head -20
unzip -l dist/basic_agent_chat_loop-0.1.0-py3-none-any.whl | head -20

# Verify metadata
python -m twine check dist/*

# Check package info
pip show basic-agent-chat-loop

# Run tests
pytest tests/ -v

# Check coverage
pytest --cov=src/basic_agent_chat_loop tests/
```

---

## 🚨 Troubleshooting

### Issue: "Username/Password authentication is no longer supported"
**Solution:** Use API tokens instead. Generate at PyPI account settings.

### Issue: "File already exists"
**Solution:** Cannot re-upload same version. Increment version number.

### Issue: "Invalid classifier"
**Solution:** Check PyPI classifier list: https://pypi.org/classifiers/

### Issue: "README not rendering"
**Solution:** Validate README: `python -m readme_renderer README.md`

### Issue: "Package not found after upload"
**Solution:** Wait 1-2 minutes for CDN to propagate, then refresh.

---

## 📝 Notes

- **Version numbers**: Follow semantic versioning (MAJOR.MINOR.PATCH)
- **Cannot delete**: Once on PyPI, versions cannot be deleted (only yanked)
- **Test first**: Always test on TestPyPI before real PyPI
- **Backup tokens**: Store API tokens securely (password manager)
- **Rate limits**: PyPI has rate limits; don't spam uploads

---

## ✅ Release Sign-Off

- [ ] All tests passing
- [ ] Documentation complete
- [ ] Package built and validated
- [ ] Tested on TestPyPI
- [ ] GitHub release created
- [ ] Published to PyPI
- [ ] Installation verified
- [ ] Post-release tasks completed

**Released by:** _______________
**Date:** _______________
**Version:** v0.1.0

---

## 🎉 Success!

Once published, users can install with:

```bash
pip install basic-agent-chat-loop
```

**PyPI Page:** https://pypi.org/project/basic-agent-chat-loop/
**GitHub:** https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop
**Issues:** https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues

---

*For questions or issues with the release process, refer to:*
- *[PyPI Publishing Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)*
- *[Twine Documentation](https://twine.readthedocs.io/)*
- *CONTRIBUTING.md for release process details*
