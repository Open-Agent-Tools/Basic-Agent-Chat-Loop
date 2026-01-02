# Chat Loop Refactoring Plan

## Overview
Break down `chat_loop.py` (3,188 lines) into smaller, focused components. Each refactoring will be done incrementally with full test coverage.

## Guiding Principles
- **One component at a time** - Extract, test, iterate
- **Test coverage requirement** - 50% minimum, 80% target for each new component
- **All tests must pass** - Before moving to next component
- **Backwards compatible** - No breaking changes to public API
- **Small, safe changes** - Low risk refactorings first

---

## Component Extraction Plan

### Phase 1: Extract Event Parsing (Low Risk) ✓ START HERE
**File**: `components/streaming_event_parser.py`
**Lines to extract**: ~100 lines from `_stream_agent_response()` (lines 1937-2005)
**Complexity**: Low
**Dependencies**: None

**What it does**:
- Parses streaming events from different agent types (AWS Strands, Anthropic, etc.)
- Extracts text from various event formats
- Handles nested event structures

**Public API**:
```python
class StreamingEventParser:
    def parse_event(self, event: Any) -> Optional[str]:
        """Extract text from a streaming event."""
```

**Why first**:
- Self-contained logic with deep nesting (6+ levels)
- No dependencies on ChatLoop state
- Easy to test in isolation
- Mentioned in QA report as needing simplification

**Test coverage target**: 80%
- Test AWS Strands dict format events
- Test data attribute events
- Test text attribute events
- Test string events
- Test nested contentBlockDelta events
- Test edge cases (None, empty, malformed)

---

### Phase 2: Extract Response Rendering (Low Risk)
**File**: `components/response_renderer.py`
**Lines to extract**: ~50 lines from `_stream_agent_response()` (lines 2105-2125, 1898-1900)
**Complexity**: Low
**Dependencies**: `Colors`, `HarmonyProcessor`, `Console` from rich

**What it does**:
- Formats and displays final responses
- Handles rich markdown vs plain text rendering
- Shows visual separator when appropriate
- Prints agent name header

**Public API**:
```python
class ResponseRenderer:
    def __init__(self, use_rich: bool, console: Optional[Console],
                 harmony_processor: Optional[HarmonyProcessor]):
        ...

    def render_agent_header(self, agent_name: str) -> None:
        """Print agent name header."""

    def render_final_response(self, display_text: str,
                             first_token_received: bool,
                             already_printed_streaming: bool) -> None:
        """Render the final response with appropriate formatting."""
```

**Why second**:
- Clear, focused responsibility
- Minimal state dependencies
- Recent changes we just made are here (visual separator)

**Test coverage target**: 80%
- Test rich markdown rendering
- Test plain text rendering
- Test visual separator display
- Test header rendering
- Test empty response handling

---

### Phase 3: Extract Token/Metadata Extraction (Medium Risk)
**File**: `components/usage_extractor.py`
**Lines to extract**: ~100 lines (multiple methods: `_extract_token_usage`, `_extract_tokens_from_usage`, `_try_bedrock_token_extraction`, `_try_standard_usage_extraction`)
**Complexity**: Medium
**Dependencies**: None (pure extraction logic)

**What it does**:
- Extracts token usage from various response formats
- Handles Bedrock, Anthropic, OpenAI formats
- Calculates deltas for accumulated usage (AWS Strands)
- Extracts cycle counts and tool metrics

**Public API**:
```python
class UsageExtractor:
    def extract_token_usage(self, response_obj: Any) -> Optional[tuple[dict[str, int], bool]]:
        """Extract token usage, returns (usage_dict, is_accumulated)."""

    def extract_cycle_count(self, response_obj: Any) -> Optional[int]:
        """Extract cycle count from framework-specific responses."""

    def extract_tool_count(self, response_obj: Any) -> Optional[int]:
        """Extract tool call count from responses."""
```

**Why third**:
- Well-contained extraction logic
- Multiple small methods that can be consolidated
- Currently scattered across ChatLoop class

**Test coverage target**: 80%
- Test Bedrock format extraction
- Test Anthropic format extraction
- Test OpenAI format extraction
- Test accumulated vs per-query usage
- Test cycle/tool count extraction
- Test None/missing/malformed responses

---

### Phase 4: Extract Command Router (Medium-High Risk)
**File**: `components/command_router.py`
**Lines to extract**: ~200 lines from `_async_run()` command handling
**Complexity**: Medium-High
**Dependencies**: Most ChatLoop methods (copy, save, compact, context, help, etc.)

**What it does**:
- Routes # commands to appropriate handlers
- Validates command syntax
- Provides command autocomplete/suggestions
- Handles command errors

**Public API**:
```python
class CommandRouter:
    def __init__(self, chat_loop: 'ChatLoop'):
        self.chat_loop = chat_loop

    async def route_command(self, command: str) -> bool:
        """Route a command, returns True if handled."""

    def get_available_commands(self) -> list[str]:
        """Get list of available commands."""
```

**Why fourth**:
- More complex - interacts with many ChatLoop methods
- Good place to add command pattern
- Will make adding new commands easier

**Test coverage target**: 70% (harder to test due to interactions)
- Test each command routing
- Test command validation
- Test invalid commands
- Test command suggestions

---

### Phase 5: Extract Session State Manager (High Risk)
**File**: `components/session_state.py`
**Lines to extract**: ~150 lines (session save/restore, history tracking)
**Complexity**: High
**Dependencies**: SessionManager, conversation_history, TokenTracker

**What it does**:
- Manages conversation history state
- Tracks incremental saves
- Handles session metadata
- Coordinates with SessionManager

**Public API**:
```python
class SessionState:
    def __init__(self, session_manager: SessionManager):
        self.conversation_history: list[dict[str, str]] = []
        self.last_saved_message_count = 0
        ...

    def add_exchange(self, user_query: str, agent_response: str) -> None:
        """Add a user-agent exchange to history."""

    async def save_incremental(self, agent_name: str, metadata: dict) -> Optional[str]:
        """Save conversation incrementally, returns session_id."""

    def needs_save(self) -> bool:
        """Check if conversation has unsaved changes."""
```

**Why fifth**:
- More complex state management
- Critical for data integrity
- Requires careful testing

**Test coverage target**: 75%
- Test history tracking
- Test incremental saves
- Test session restoration
- Test metadata handling

---

## Implementation Strategy

### For Each Component:

1. **Create component file with tests**
   ```bash
   touch src/basic_agent_chat_loop/components/<name>.py
   touch tests/unit/test_<name>.py
   ```

2. **Extract code + Write tests**
   - Move code to new component
   - Import in chat_loop.py
   - Update ChatLoop to use component
   - Write comprehensive tests (50-80% coverage)

3. **Run full test suite**
   ```bash
   uv run pytest tests/ -v
   ```

4. **Fix any failures**
   - Debug and resolve all test failures
   - Ensure 100% of existing tests still pass
   - Verify new tests pass

5. **Verify coverage**
   ```bash
   uv run pytest tests/unit/test_<name>.py --cov=src/basic_agent_chat_loop/components/<name>.py --cov-report=term-missing
   ```

6. **Commit and continue**
   ```bash
   git add -A
   git commit -m "refactor: extract <component_name> from ChatLoop"
   ```

---

## Success Metrics

- ✓ All 318+ existing tests pass after each refactoring
- ✓ Each new component has 50-80% test coverage
- ✓ chat_loop.py reduced from 3,188 to ~2,000 lines
- ✓ No breaking changes to public API
- ✓ ChatLoop class has <30 methods (currently 40)
- ✓ Longest method <200 lines (currently 478)

---

## Order of Execution

1. **Phase 1**: StreamingEventParser (START HERE - safest, most isolated)
2. **Phase 2**: ResponseRenderer (recent changes, well-defined)
3. **Phase 3**: UsageExtractor (consolidate scattered logic)
4. **Phase 4**: CommandRouter (enable easier command additions)
5. **Phase 5**: SessionState (highest risk, most payoff)

---

## Next Steps

Ready to start **Phase 1: StreamingEventParser**?

This will:
- Extract the deeply nested event parsing logic (lines 1937-2005)
- Create `components/streaming_event_parser.py`
- Create `tests/unit/test_streaming_event_parser.py` with 80% coverage
- Reduce complexity in `_stream_agent_response()`
