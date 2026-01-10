# Windows Testing Checklist
**For Commit:** 481617e - Windows VT Support
**Created:** 2026-01-10

---

## Pre-Testing Setup

### Environment Requirements
- [ ] Windows 10 build 1511 or later (for VT support)
- [ ] Python 3.10 or later installed
- [ ] Git installed
- [ ] Access to cmd.exe, PowerShell, and Windows Terminal

### Installation Steps
```bash
# Clone repository
git clone <repository_url>
cd Basic-Agent-Chat-Loop

# Ensure on correct commit
git checkout 481617e

# Install dependencies
python -m pip install -e .[dev]

# Verify installation
python -c "import basic_agent_chat_loop; print('✓ Package installed')"
```

---

## Test Suite 1: Automated Testing

### 1.1 Windows Compatibility Tests
```bash
python test_windows_compatibility.py
```

**Expected Result:**
```
Test Summary
Tests Run: 16
Successes: 16
Failures: 0
Errors: 0
Success Rate: 100.0%
```

**Pass Criteria:** All 16 tests must pass
- [ ] All tests passed
- [ ] No errors or warnings displayed

### 1.2 Visual VT Mode Test
```bash
python test_windows_vt.py
```

**Expected Output:**
- [ ] Platform detected as "win32"
- [ ] `enable_windows_vt_mode()` returns `True`
- [ ] Colored text displays correctly (not raw escape codes)
- [ ] Rich library integration shows colored output

**Visual Verification:**
- [ ] Red text appears red
- [ ] Green text appears green
- [ ] Yellow text appears yellow
- [ ] Blue text appears blue
- [ ] Cyan text appears cyan
- [ ] No `[31m` or similar escape codes visible

### 1.3 Full Test Suite
```bash
python -m pytest tests/ -v
```

**Expected Result:**
- [ ] All 510 tests pass
- [ ] No new failures compared to baseline
- [ ] No Windows-specific test failures

**Note:** This may take several minutes

---

## Test Suite 2: Manual Terminal Testing

### 2.1 Command Prompt (cmd.exe)

**Setup:**
1. [ ] Open cmd.exe (Windows + R, type `cmd`)
2. [ ] Navigate to project directory
3. [ ] Activate virtual environment (if used)

**Test Steps:**
```cmd
REM Test basic functionality
python -c "from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode; print('VT Mode:', enable_windows_vt_mode())"
```

**Expected:** Output shows `VT Mode: True`
- [ ] Test passed

**Visual Test:**
```cmd
python test_windows_vt.py
```

**Expected:** Colored text displays correctly
- [ ] Colors render properly
- [ ] No escape codes visible as text
- [ ] No errors or warnings

### 2.2 PowerShell 5.1

**Setup:**
1. [ ] Open PowerShell (Windows + X, then I)
2. [ ] Navigate to project directory
3. [ ] Set execution policy if needed: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

**Test Steps:**
```powershell
# Test VT mode
python -c "from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode; print('VT Mode:', enable_windows_vt_mode())"
```

**Expected:** Output shows `VT Mode: True`
- [ ] Test passed

**Visual Test:**
```powershell
python test_windows_vt.py
```

**Expected:** Colors render correctly
- [ ] All colors display properly
- [ ] Rich library output looks good
- [ ] No warnings

### 2.3 Windows Terminal (Recommended)

**Setup:**
1. [ ] Open Windows Terminal
2. [ ] Create new PowerShell or cmd.exe tab
3. [ ] Navigate to project directory

**Test Steps:**
```bash
python test_windows_vt.py
```

**Expected:** Best color rendering
- [ ] All colors vibrant and correct
- [ ] Rich library formatting perfect
- [ ] No issues

### 2.4 PowerShell Core (7+)

**Setup:**
1. [ ] Open PowerShell 7+ (if installed)
2. [ ] Navigate to project directory

**Test Steps:**
```powershell
python test_windows_vt.py
```

**Expected:** Same as PowerShell 5.1
- [ ] VT mode enabled
- [ ] Colors display correctly

---

## Test Suite 3: Integration Testing

### 3.1 Application Startup

**Test:** Verify VT mode is called at startup
```bash
# Run with a test agent (if available)
python -m basic_agent_chat_loop.cli --help
```

**Expected:**
- [ ] No errors during startup
- [ ] Help text displays with colored formatting
- [ ] VT mode enabled silently

### 3.2 pyreadline3 Integration

**Test:** Verify readline history works on Windows
```bash
python -c "from basic_agent_chat_loop.components import input_handler; print('Readline:', input_handler.READLINE_AVAILABLE)"
```

**Expected:** Output shows `Readline: True`
- [ ] pyreadline3 is available
- [ ] No import errors

### 3.3 Error Handling

**Test:** Simulate VT mode failure
1. [ ] Run on Windows 7 or 8.1 (if available)
2. [ ] Or mock GetConsoleMode failure

**Expected:**
- [ ] Application starts normally
- [ ] No crashes or exceptions
- [ ] Function returns `False` gracefully
- [ ] Colors may not render (acceptable)

---

## Test Suite 4: Edge Cases

### 4.1 Older Windows Versions

**Platform:** Windows 7, 8, 8.1 (if available)

**Test Steps:**
```bash
python test_windows_vt.py
```

**Expected:**
- [ ] `enable_windows_vt_mode()` returns `False`
- [ ] No crashes or errors
- [ ] Application continues to work
- [ ] Colors may show as escape codes (acceptable degradation)

### 4.2 Restricted Permissions

**Test:** Run as limited user (non-admin)

**Test Steps:**
1. [ ] Create limited user account
2. [ ] Login as limited user
3. [ ] Run tests

**Expected:**
- [ ] VT mode enablement succeeds or fails gracefully
- [ ] No permission errors
- [ ] Application works normally

### 4.3 Multiple Console Windows

**Test:** Verify VT mode works across multiple instances

**Test Steps:**
1. [ ] Open 3 separate cmd.exe windows
2. [ ] Run test in each window simultaneously

**Expected:**
- [ ] All instances show colors correctly
- [ ] No conflicts or race conditions
- [ ] Each window independent

---

## Test Suite 5: Performance Testing

### 5.1 Startup Time Measurement

**Test:** Measure startup overhead

```python
import time
start = time.perf_counter()
from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode
result = enable_windows_vt_mode()
elapsed = time.perf_counter() - start
print(f"VT Mode: {result}, Time: {elapsed*1000:.2f}ms")
```

**Expected:**
- [ ] Execution time < 1ms
- [ ] No noticeable delay
- [ ] VT mode returns `True`

### 5.2 Memory Impact

**Test:** Check memory usage

```bash
# Before enabling VT
python -c "import psutil, os; print(f'Memory: {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB')"

# After enabling VT
python -c "from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode; import psutil, os; enable_windows_vt_mode(); print(f'Memory: {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB')"
```

**Expected:**
- [ ] Memory increase < 1 MB
- [ ] No memory leaks

---

## Test Suite 6: Regression Testing

### 6.1 Existing Functionality

**Test:** Verify no features broken

**Critical Features to Test:**
- [ ] Agent loading works
- [ ] Configuration management works
- [ ] Command history works (pyreadline3)
- [ ] Alias management works
- [ ] Session management works
- [ ] All existing commands work

### 6.2 Cross-Platform Compatibility

**Test:** Verify changes don't affect other platforms

**If you have access to macOS/Linux:**
```bash
# Run same tests on macOS/Linux
python test_windows_compatibility.py
python test_windows_vt.py
python -m pytest tests/ -v
```

**Expected:**
- [ ] All tests pass on non-Windows platforms
- [ ] No platform-specific failures
- [ ] Performance unchanged

---

## Bug Reporting Template

If you encounter any issues, please report using this template:

```markdown
### Issue Description
[Brief description of the problem]

### Environment
- Windows Version: [e.g., Windows 10 build 19045]
- Python Version: [e.g., 3.10.5]
- Terminal: [cmd.exe / PowerShell / Windows Terminal]
- Commit: 481617e

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [...]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### Screenshots/Logs
[Attach screenshots or error logs]

### VT Mode Status
[Run: python -c "from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode; print(enable_windows_vt_mode())"]
Result: [True/False]

### Additional Context
[Any other relevant information]
```

---

## Sign-Off Checklist

### Testing Complete
- [ ] All automated tests passed (Suite 1)
- [ ] Manual terminal tests passed (Suite 2)
- [ ] Integration tests passed (Suite 3)
- [ ] Edge cases handled correctly (Suite 4)
- [ ] Performance acceptable (Suite 5)
- [ ] No regressions found (Suite 6)

### Issues Found
- [ ] No critical issues
- [ ] No blocking issues
- [ ] Minor issues documented (if any)

### Documentation
- [ ] Test results documented
- [ ] Screenshots captured (if needed)
- [ ] Issues reported (if any)

### Approval
- [ ] Ready for production deployment
- [ ] Recommends merge to main branch

**Tester Name:** ___________________
**Date Completed:** ___________________
**Signature:** ___________________

---

## Quick Reference Commands

```bash
# Run all automated tests
python test_windows_compatibility.py && python test_windows_vt.py && python -m pytest tests/ -v

# Test VT mode quickly
python -c "from basic_agent_chat_loop.chat_loop import enable_windows_vt_mode; print('VT:', enable_windows_vt_mode())"

# Check Python version
python --version

# Check Windows version
ver
```

---

**For Questions:** Refer to WINDOWS_COMPATIBILITY_REPORT.md for detailed analysis
**For Summary:** See WINDOWS_COMPATIBILITY_SUMMARY.md for quick overview
