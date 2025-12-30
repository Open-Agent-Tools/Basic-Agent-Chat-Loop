# Session Compaction and Resume - Implementation Plan

## Overview

Replace the old query-replay resume system with a transcript-based approach using auto-generated summaries.

## Core Design Principles

1. **Auto-summarize on exit** - Generate structured summary when saving conversations
2. **n-1 chain model** - Each session references only its immediate parent
3. **Simple restoration** - Agent reads summary and acknowledges context
4. **Progressive summarization** - Summaries compress older context, detail recent content
5. **No configuration needed** - If auto_save is enabled, summaries are generated

## Data Structures

### Markdown File Format (Enhanced)

```markdown
# Simple Sally Conversation

**Session ID:** session_3
**Date:** 2025-12-30T14:30:22.123456
**Agent:** Simple Sally
**Agent Path:** /Users/wes/Development/agents/simple_sally/agent.py
**Total Queries:** 3

---

## Session Restored (14:30:22)
**Context:** Resumed from session_2 (5 queries, 2.3K tokens)
**Previous Session:** /Users/wes/agent-conversations/session_2.md

**Simple Sally:** I've reviewed our previous conversation about auth refactoring.
We discussed JWT tokens and Redis session storage. Ready to continue!

*Time: 2.1s | Tokens: 156 (in: 89, out: 67)*

---

## Query 1 (14:30:45)
**You:** Let's implement the rate limiter

**Simple Sally:** [response]

*Time: 3.2s | Tokens: 345 (in: 123, out: 222)*

---

<!-- SESSION_SUMMARY_START -->
**Background Context:** We discussed auth refactoring with JWT tokens and Redis session storage in the previous session.

**Current Session Summary:**
**Topics Discussed:**
- Rate limiter implementation strategies
- Token bucket vs sliding window algorithms

**Decisions Made:**
- Use token bucket with Redis backing
- 100 requests per minute per user

**Pending:**
- Integration testing with auth system
<!-- SESSION_SUMMARY_END -->
```

### Key Metadata Fields

- **Session ID** - Unique identifier for this session
- **Resumed From** - Parent session_id (if resumed)
- **Previous Session** - Full file path to parent markdown file
- **Agent Path** - Path to agent file used

### Summary Block Structure

```markdown
<!-- SESSION_SUMMARY_START -->
**Background Context:** [1-2 sentences condensing previous summary, or "Initial session."]

**Current Session Summary:**
**Topics Discussed:**
- [bullet points]

**Decisions Made:**
- [bullet points]

**Pending:**
- [bullet points]
<!-- SESSION_SUMMARY_END -->
```

## Implementation Phases

### Phase 1: Summary Generation on Exit

**Goal:** Auto-generate structured summaries when saving conversations

**Changes Needed:**

1. **ChatLoop.save_conversation()** - Add summary generation step
   - Before saving markdown, ask agent to generate summary
   - Use hybrid instruction prompt
   - Extract summary and append to markdown
   - If summary fails: save without summary, warn user

2. **Summary Generation Prompt:**
   ```
   Generate a progressive session summary:

   [If previous summary exists:]
   **Background Context:** Condense this previous summary to 1-2 sentences:
   [previous summary]

   **Current Session:**
   [current conversation markdown]

   Create a structured summary:

   **Background Context:** [condensed previous context or "Initial session."]

   **Current Session Summary:**
   **Topics Discussed:**
   - [bullet points about THIS session]

   **Decisions Made:**
   - [bullet points about THIS session]

   **Pending:**
   - [what's still open]

   Aim for less than 500 words, be complete but terse, no fluff.
   Use the exact format with HTML comment markers:

   <!-- SESSION_SUMMARY_START -->
   [your summary here]
   <!-- SESSION_SUMMARY_END -->
   ```

3. **Exit Flow Changes:**
   ```
   You: exit
   📝 Generating session summary... ✓
   Goodbye!
   ✓ Conversation saved successfully!
     Session ID: simple_sally_20251230_112153
     Queries: 5
     Tokens: 2,345
   ```

4. **Error Handling:**
   - If summary generation times out: Save without summary, warn user
   - If summary generation fails: Save without summary, warn user
   - One automatic retry attempt
   - User never loses their conversation data

**Files to Modify:**
- `src/basic_agent_chat_loop/chat_loop.py` - save_conversation()
- `src/basic_agent_chat_loop/components/session_manager.py` - save_markdown_with_summary()

**Testing:**
- Test summary generation with various conversation lengths
- Test summary failure handling
- Test progressive summarization (resume + exit)
- Verify HTML markers are correctly formatted

---

### Phase 2: Compact Command

**Goal:** User-triggered compaction that saves current session and starts new one

**Changes Needed:**

1. **Add `compact` command handler** in main loop
   - Trigger summary generation
   - Save current session
   - Extract generated summary
   - Start new session with summary as restoration prompt
   - Agent acknowledges context
   - Continue in new session

2. **User Flow:**
   ```
   You: compact
   📝 Generating session summary...
   💾 Saved session: session_1 (5 queries, 2.3K tokens)
   🔄 Starting new session with summary...

   Simple Sally: I've reviewed our conversation about auth refactoring.
   We discussed JWT tokens and Redis session storage. Ready to continue!

   You: [continue in new session_2]
   ```

3. **New Session Setup:**
   - Create new session_id
   - Store "Resumed from: session_1" metadata
   - Store "Previous Session: /path/to/session_1.md"
   - Extract summary from saved session_1.md
   - Send restoration prompt to agent
   - Save agent acknowledgment as first entry in conversation_markdown
   - Track restoration tokens (not counted as a query)

4. **ChatLoop._handle_compact()** method:
   ```python
   async def _handle_compact(self) -> None:
       """Compact current session and continue in new session."""
       # 1. Generate summary and save current session
       # 2. Extract summary from saved file
       # 3. Create new session_id
       # 4. Send restoration prompt
       # 5. Display agent acknowledgment
       # 6. Reset for new session but keep context
   ```

**Files to Modify:**
- `src/basic_agent_chat_loop/chat_loop.py` - Add _handle_compact(), wire into command handler
- `src/basic_agent_chat_loop/components/display_manager.py` - Add compact to help text

**Testing:**
- Test compact after various query counts (1, 5, 20 queries)
- Test compact with different agents
- Test that new session continues naturally
- Test token tracking across compaction
- Verify file chain is correct (session_2 -> session_1)

---

### Phase 3: Resume Command

**Goal:** Load and resume old sessions using their summaries

**Changes Needed:**

1. **Summary Extraction Utility:**
   ```python
   def _extract_summary_from_markdown(self, file_path: Path) -> Optional[str]:
       """Extract summary block from markdown file."""
       content = file_path.read_text()
       start_marker = '<!-- SESSION_SUMMARY_START -->'
       end_marker = '<!-- SESSION_SUMMARY_END -->'

       if start_marker not in content or end_marker not in content:
           return None

       start_idx = content.index(start_marker) + len(start_marker)
       end_idx = content.index(end_marker)
       return content[start_idx:end_idx].strip()
   ```

2. **Metadata Extraction:**
   - Parse markdown to get session_id, agent_path, query count, total tokens
   - Extract "Resumed from" if present (for chain info)

3. **Restoration Prompt:**
   ```
   CONTEXT RESTORATION: You are continuing a previous conversation from [date].

   Previous session summary (Session ID: session_2, 5 queries, 2.3K tokens):

   This session was resumed from: session_1
   Previous session file: /Users/wes/agent-conversations/session_2.md

   <!-- SESSION_SUMMARY_START -->
   [extracted summary]
   <!-- SESSION_SUMMARY_END -->

   Task: Review the above and provide a brief acknowledgment (2-6 sentences or bullets) that includes:
   1. Main topics discussed
   2. Key decisions made
   3. Confirmation you're ready to continue

   Keep your response concise.
   ```

4. **Resume Flow:**
   ```
   You: resume 1
   📋 Loading session...
   ✓ Found: Simple Sally - Dec 30, 11:22 (5 queries, 2.3K tokens)
   🔄 Restoring context...

   Simple Sally: I've reviewed our previous conversation about auth refactoring...

   You: [continue in new session]
   ```

5. **Error Handling (Graceful Degradation):**
   - Missing parent session file: "⚠️ Parent session not found, starting fresh"
   - Agent path mismatch: "⚠️ Different agent detected. Continue? (y/n)"
   - No summary markers: "⚠️ Session can't be resumed (no summary), starting fresh"
   - Summary extraction fails: Fallback to fresh start with warning
   - Agent acknowledgment fails/times out: Trust response, show it, continue

6. **ChatLoop.restore_session()** - Complete rewrite:
   - Remove old replay logic (lines 899-1045)
   - Implement new summary-based approach
   - Load by session number or ID
   - Extract summary from parent markdown
   - Send restoration prompt
   - Create new session with proper metadata
   - Track restoration as overhead (tokens yes, query no)

**Files to Modify:**
- `src/basic_agent_chat_loop/chat_loop.py` - restore_session() complete rewrite
- `src/basic_agent_chat_loop/components/session_manager.py` - Add summary extraction utility
- `src/basic_agent_chat_loop/components/display_manager.py` - Update help text (remove "temporarily disabled")

**Testing:**
- Test resume with session number (resume 1)
- Test resume with session_id (resume simple_sally_20251230_112153)
- Test resume with missing parent file
- Test resume with corrupted summary
- Test resume with different agent
- Test resume chain (session_3 -> session_2 -> session_1)
- Test that only n-1 summary is loaded (not full chain)

---

## Token and Query Tracking

### Restoration Exchange:
- **Counted:** Input tokens (summary prompt) + Output tokens (acknowledgment)
- **Not counted:** As a user query
- **Display:** Shown in markdown as "Session Restored" with token info

### Example:
```
Total Queries: 3 (user queries only)
Restoration: 156 tokens (in: 89, out: 67)
Session Tokens: 1,234 tokens
Combined Total: 1,390 tokens
```

## Configuration

**No new configuration needed!**

Summary generation is automatically enabled when:
```yaml
features:
  auto_save: true  # Summaries generated automatically
```

Future (if needed):
```yaml
resume:
  # No config for now, but could add:
  # max_summary_tokens: 1000
  # summarization_model: "claude-sonnet-4"  # if we support model override
```

## Edge Cases and Error Handling

### 1. Summary Generation Fails
- **Action:** Save conversation without summary
- **Warning:** "⚠️ Summary generation failed - session saved but cannot be resumed"
- **Impact:** File exists, can be read manually, but resume won't work

### 2. Parent Session Deleted
- **Action:** Warn user, start fresh session
- **Warning:** "⚠️ Parent session session_2 not found, starting fresh"
- **Impact:** User can continue but without restored context

### 3. Corrupted Summary Markers
- **Action:** Treat as missing summary
- **Warning:** "⚠️ Session can't be resumed (invalid summary format)"
- **Impact:** Same as missing summary

### 4. Agent Path Mismatch
- **Action:** Warn and prompt for confirmation
- **Warning:** "⚠️ Session created with /path/to/old_agent.py, using /path/to/new_agent.py. Continue? (y/n)"
- **Impact:** User decides if agent can handle old context

### 5. Agent Acknowledgment Weird/Failed
- **Action:** Trust whatever happened, show user
- **Warning:** None - display acknowledgment as-is
- **Impact:** User sees what agent said, can decide to continue or restart

### 6. Very Long Summaries
- **Action:** Accept them (we said <500 words, but don't enforce)
- **Warning:** None
- **Impact:** Larger token cost on resume, but complete context

## Benefits of This Design

1. **✅ Fast resume** - No query replay, just summary injection
2. **✅ Token efficient** - Summaries are compact compared to full transcripts
3. **✅ Traceable** - File paths create clear session lineage
4. **✅ Simple** - n-1 model, no complex compression algorithms
5. **✅ Testable** - `compact` command tests the whole flow
6. **✅ Transparent** - Users see restoration exchange in saved files
7. **✅ Progressive** - Old context compresses naturally over time
8. **✅ Graceful** - Errors don't block saving or resuming

## Migration from Old System

### Old Resume (Disabled):
- Loaded JSON file with conversation history
- Replayed all queries through agent
- Slow, expensive, broken with markdown-only saving

### New Resume:
- Reads markdown file summary block
- Injects summary as invisible first query
- Fast, cheap, works with markdown-only

### Transition:
- Old sessions without summaries: Can't be resumed (graceful warning)
- New sessions: Auto-generate summaries on exit
- No migration script needed (old sessions still readable as markdown)

## Testing Strategy

### Unit Tests:
- Summary extraction from markdown
- Markdown generation with summary blocks
- Metadata parsing from markdown headers
- Error handling for missing/corrupted summaries

### Integration Tests:
- Full compact flow (exit → save → restore → continue)
- Full resume flow (load → restore → continue)
- Chain following (session_3 → session_2, not deeper)
- Token tracking across compaction/resume

### Manual Testing:
- Test with Simple Sally sample agent
- Test with complex multi-tool agents
- Test very long conversations (20+ queries)
- Test compact → compact → compact (multiple chains)
- Test resume → compact → resume (mixed operations)

## Success Criteria

- [ ] Phase 1: Auto-summarization working on exit
- [ ] Phase 1: Summaries have correct structure and markers
- [ ] Phase 1: Failed summaries handled gracefully
- [ ] Phase 2: `compact` command works end-to-end
- [ ] Phase 2: New session properly references parent
- [ ] Phase 2: Agent acknowledgment displays correctly
- [ ] Phase 3: `resume` command loads old sessions
- [ ] Phase 3: Only n-1 summary loaded (not full chain)
- [ ] Phase 3: All edge cases handled gracefully
- [ ] All tests passing
- [ ] User test confirms natural conversation flow

## Future Enhancements (Not in Scope)

- Context limit monitoring (Issue #48)
- Auto-suggest compact when approaching limits
- Multi-session resume (load n-2, n-3, etc. on demand)
- Summary quality validation
- Custom summarization prompts per agent
- Export conversation chains as single document

---

## Implementation Order

1. **Start:** Phase 1 (Summary generation)
2. **Then:** Phase 2 (Compact command) - tests Phase 1
3. **Finally:** Phase 3 (Resume command) - uses Phase 1 & 2 logic

**Estimated Effort:** ~4-6 hours total
- Phase 1: 2 hours
- Phase 2: 1 hour
- Phase 3: 1-2 hours
- Testing: 1 hour

---

## Notes

- HTML comment markers chosen for clarity in markdown and easy parsing
- Agent path stored for debugging and validation
- Restoration tokens counted but not as queries (overhead tracking)
- Progressive summarization happens naturally through n-1 chain
- No limit on chain depth (user can resume indefinitely)
- Compact command provides immediate value and tests resume flow
