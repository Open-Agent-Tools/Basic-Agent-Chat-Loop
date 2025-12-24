# OpenAI Harmony Integration

This document describes the integration of OpenAI Harmony format support into the Basic Agent Chat Loop.

## Summary

The chat loop includes built-in support for the [OpenAI Harmony](https://pypi.org/project/openai-harmony/) response format, which is designed for gpt-oss open-weight models. **Harmony support is a core dependency** and is automatically available in all installations.

## What Was Added

### 1. New Component: `HarmonyProcessor`
- **Location**: `src/basic_agent_chat_loop/components/harmony_processor.py`
- **Purpose**: Detect and process Harmony-formatted responses
- **Features**:
  - Automatic detection of Harmony agents
  - Response parsing for multiple output channels (analysis, commentary, final)
  - Enhanced display formatting for reasoning and tool calls
  - Always available (core dependency)

### 2. Detection Strategies

The system detects Harmony agents using multiple strategies:

1. **Explicit marker**: Agent has `uses_harmony = True` attribute
2. **Model name**: Model ID contains "gpt-oss" or "harmony"
3. **Harmony methods**: Agent has `render_conversation` or `parse_messages` methods
4. **Class name**: Agent class name contains "harmony"
5. **Harmony encoding**: Agent has `harmony_encoding` attribute

### 3. Enhanced Response Processing

When a Harmony agent is detected:
- Responses are parsed for structured channels
- Internal reasoning/analysis is separated from final output
- Tool calls are properly detected and formatted
- Multiple output channels are displayed appropriately

### 4. Installation

Harmony support is included by default in all installations:

```bash
# Standard installation includes Harmony
pip install basic-agent-chat-loop
```

## Code Changes

### Files Modified

1. **`pyproject.toml`**
   - Added `openai-harmony>=0.0.8` to core dependencies
   - Harmony is now always installed with the package

2. **`src/basic_agent_chat_loop/components/agent_loader.py`**
   - Updated `extract_agent_metadata()` to detect Harmony agents
   - Adds `uses_harmony` flag to agent metadata
   - Direct import (no try/except needed)

3. **`src/basic_agent_chat_loop/chat_loop.py`**
   - Added import for `HarmonyProcessor`
   - Initialize Harmony processor in `ChatLoop.__init__()` when detected
   - Process responses through Harmony processor in `_stream_agent_response()`
   - Always available (no installation warnings)

4. **`src/basic_agent_chat_loop/components/__init__.py`**
   - Export `HarmonyProcessor` for public use

5. **`README.md`**
   - Added Harmony to features list
   - Added installation instructions
   - Added comprehensive Harmony Format Support section
   - Updated optional dependencies list

### Files Created

1. **`src/basic_agent_chat_loop/components/harmony_processor.py`** (295 lines)
   - Complete implementation of Harmony detection and processing
   - Handles graceful degradation without openai-harmony installed
   - Channel extraction and display formatting

## Usage Examples

### Basic Usage

```python
# Agent explicitly marks Harmony usage
class MyHarmonyAgent:
    uses_harmony = True

    def __call__(self, query):
        # Returns Harmony-formatted response
        return harmony_response

# Chat loop automatically detects and handles Harmony
chat_loop my_harmony_agent
```

### Response Processing

When Harmony is detected, responses are processed to extract:

```python
{
    "text": "main response text",
    "has_reasoning": True,  # If reasoning detected
    "has_tools": False,     # If tool calls detected
    "channels": {
        "analysis": "internal reasoning...",
        "final": "user-facing response..."
    }
}
```

### Display Output

```
Agent: Here's the solution...

────────────────────────────────────────────────────────────
💭 Internal Reasoning:
First, I analyzed the problem by breaking it down...

────────────────────────────────────────────────────────────
📝 Commentary:
This approach was chosen because...
```

## Testing

All existing tests pass (318/318):
```bash
pytest tests/
# ====== 318 passed in 1.04s ======
```

No regressions were introduced. The integration:
- Always available (core dependency)
- Does not affect non-Harmony agents
- Automatic detection with zero configuration

## Backward Compatibility

✅ **Fully backward compatible**
- Existing agents continue to work unchanged
- No breaking changes to API
- Core dependency increases package size slightly (~100KB)
- Automatic detection (no configuration required)

## Future Enhancements

Potential improvements:
1. More sophisticated channel parsing using Harmony encoding API
2. Configuration options for which channels to display
3. Syntax highlighting for tool calls
4. Token counting for Harmony-specific features
5. Session replay support for Harmony conversations

## References

- [openai-harmony on PyPI](https://pypi.org/project/openai-harmony/)
- OpenAI Harmony documentation
- gpt-oss model series

## Version Info

- **Implemented**: 2024-12-24
- **Package Version**: 1.2.1+
- **OpenAI Harmony Version**: >=0.0.8
- **Python Requirement**: 3.8+
