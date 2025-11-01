# Multi-Line Editor Enhancements

## Overview

The multi-line editor has been significantly enhanced with intuitive keyboard controls:
1. **ESC key cancellation** - instantly cancel with ESC
2. **Up arrow editing** - press ↑ at start of line to edit previous line
3. **History integration** - recall entire multi-line blocks with up arrow at main prompt
4. **Multiple cancel options** - ESC, .cancel, Ctrl+C, or Ctrl+D

## Features Implemented

### 1. Cancel Options

Users can now cancel multi-line input in four ways:

- **ESC key**: Press ESC at the start of any line for instant cancellation (cross-platform)
- **`.cancel` command**: Type `.cancel` at any prompt to cancel
- **Ctrl+C**: Keyboard interrupt to cancel
- **Ctrl+D**: EOF signal to cancel

All cancel methods return empty string and show a clear cancellation message. The ESC key detection works on Unix/Linux/Mac (via termios) and Windows (via msvcrt).

### 2. Previous Line Editing with Up Arrow

Press **↑** (up arrow) at the start of any line to edit the previous line:

```
1│ first line
2│ second line
3│ [press ↑]
↑ Editing line 2...
2│ second line edited
3│ [empty line to submit]
```

**How it works**:
- Press **↑** at the very start of a line (before typing anything)
- The previous line is popped and added to readline history
- Press ↑ again to recall it in the input buffer and edit
- Press Enter when done to add the edited line
- Can press ↑ multiple times to traverse back through lines
- Shows warning if no previous line exists

**Alternative**: Type `.back` for same functionality (useful if up arrow detection unavailable)

### 3. History Integration

The entire multi-line input block is saved to readline history as a single entry:

```
1│ line one
2│ line two
3│ line three
4│ [empty line submits]
✓ 3 lines captured
```

Later in the same session or future sessions:
- Press **up arrow** to recall the entire multi-line block
- Newlines are preserved in the history entry
- Can be edited and resubmitted as a whole

### 4. Visual Improvements

**Line Numbers**: Each line shows its number for context
```
 1│ first line
 2│ second line
 3│ third line
```

**Clear Instructions**: User-friendly prompts
```
Multi-line mode:
  • Empty line to submit
  • .cancel to cancel
  • .back to edit previous line
```

**Status Feedback**:
- `✓ 3 lines captured` on successful submission
- `✗ Multi-line input cancelled` on cancellation
- `↑ Editing line 2...` when editing previous line
- `⚠ No previous line to edit` when .back used incorrectly

### 4. Keyboard Control Implementation

The multi-line editor detects special keys at the start of each line:

**ESC Key** - Instant cancellation:
```
1│ [press ESC]
✗ Multi-line input cancelled (ESC)
```

**Up Arrow** - Edit previous line:
```
1│ line one
2│ [press ↑]
↑ Editing line 1...
```

**Implementation Details**:
- Uses platform-specific terminal control:
  - Unix/Linux/Mac: `termios` and `tty` for raw input, `select` for sequence detection
  - Windows: `msvcrt` for character-level input
- Detects special keys on the first character of each line
- ESC key: ASCII 27 (`\x1b`)
- Up arrow: Escape sequence `\x1b[A` on Unix, `\xe0H` on Windows
- Falls back gracefully to `.cancel` and `.back` commands if detection unavailable
- Zero dependencies - uses Python standard library only

**How it works**:
1. Before reading a line, attempts to read a single character in raw mode
2. If ESC detected, checks within 100ms for following characters:
   - If `[A` follows → Up arrow detected
   - If no characters follow → ESC key detected
3. If other character detected, includes it and continues with normal `input()`
4. Maintains full readline editing capabilities for mid-line input

## Implementation Details

### Code Location

- **Main implementation**: `src/basic_agent_chat_loop/chat_loop.py:739-810`
- **ESC key detection**: `src/basic_agent_chat_loop/chat_loop.py:307-380`
- **Help text**: `src/basic_agent_chat_loop/components/display_manager.py:110-161`
- **Tests**: `tests/unit/test_multiline_input.py` (11 tests)

### Key Design Decisions

1. **Up Arrow Editing**: The most intuitive way to edit previous lines - just press ↑ at the start of a line. Detects arrow key sequences in raw terminal mode before `input()` takes over.

2. **ESC for Cancel**: ESC key provides instant cancellation, matching user expectations from other terminal applications and editors.

3. **First-Character Detection Only**: Special keys (ESC, ↑) are only detected at the start of a line. Once typing begins, readline takes over with full editing capabilities (including mid-line arrow navigation).

4. **Graceful Fallback**: If terminal control is unavailable, `.back` and `.cancel` commands always work as alternatives.

5. **Readline Integration**: Uses standard `readline` module for history and line editing, maintaining compatibility with existing infrastructure.

6. **Sequence Timing**: 100ms timeout distinguishes ESC alone from ESC as part of arrow sequence on Unix systems.

7. **Exception Handling**: Gracefully handles EOFError (Ctrl+D) and KeyboardInterrupt (Ctrl+C) for consistent cancel behavior.

8. **Empty Line Validation**: First line cannot be empty - prompts user to enter content or cancel.

9. **Zero Dependencies**: Uses only Python standard library modules (`termios`, `tty`, `select` for Unix; `msvcrt` for Windows).

## Usage Examples

### Basic Multi-Line Input
```
You: \\
Multi-line mode:
  • Empty line to submit
  • .cancel to cancel
  • .back to edit previous line
 1│ Here is a multi-line
 2│ code example:
 3│ def hello():
 4│     print("world")
 5│
✓ 4 lines captured
```

### Editing Previous Line (Up Arrow)
```
You: \\
 1│ This is line one
 2│ This is line too  # oops, typo!
 3│ [press ↑]
↑ Editing line 2...
 2│ [press ↑ to recall "This is line too"]
 2│ This is line two  # fixed!
 3│
✓ 2 lines captured
```

### Editing Previous Line (.back command)
```
You: \\
 1│ This is line one
 2│ This is line too  # oops, typo!
 3│ .back
↑ Editing line 2...
 2│ [press ↑ to recall "This is line too"]
 2│ This is line two  # fixed!
 3│
✓ 2 lines captured
```

### Cancelling Input (ESC Key)
```
You: \\
 1│ Started typing but
 2│ changed my mind
 3│ [press ESC]
✗ Multi-line input cancelled (ESC)
```

### Cancelling Input (.cancel Command)
```
You: \\
 1│ Started typing but
 2│ changed my mind
 3│ .cancel
✗ Multi-line input cancelled
```

### Recalling from History
```
You: [press up arrow]
You: Here is a multi-line
code example:
def hello():
    print("world")
```

## Testing

Comprehensive test suite with 13 test cases covering:
- ✅ Basic submission
- ✅ Cancel via `.cancel` command
- ✅ Cancel via ESC key
- ✅ Cancel via Ctrl+D (EOFError)
- ✅ Cancel via Ctrl+C (KeyboardInterrupt)
- ✅ `.back` command functionality
- ✅ `.back` on empty lines
- ✅ Up arrow key functionality
- ✅ Up arrow on empty lines
- ✅ Empty first line validation
- ✅ History integration
- ✅ Line number display
- ✅ Multiple `.back` commands

All tests pass: `pytest tests/unit/test_multiline_input.py -v` (286 total tests pass)

## Documentation Updates

Updated documentation in:
- Module docstring (`chat_loop.py`)
- Banner display
- Help command
- User guide sections

## Backward Compatibility

Fully backward compatible:
- Existing behavior (empty line to submit) preserved
- New features are opt-in commands
- No breaking changes to API or user workflow
