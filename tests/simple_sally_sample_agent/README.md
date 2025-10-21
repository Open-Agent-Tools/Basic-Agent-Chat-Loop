# Simple Sally - Test Agent

A minimal test agent for the Basic-Agent-Chat-Loop tool, demonstrating core Strands Agent functionality.

## Purpose

Simple Sally serves as a test agent for validating the chat loop tool's functionality. It provides a minimal implementation with basic conversational capabilities, making it ideal for:

- Testing the chat loop interface
- Validating agent-to-tool communication
- Demonstrating basic Strands agent patterns
- Serving as a reference implementation for new agents

## Architecture

This agent uses:
- **Model**: Anthropic Claude Sonnet 4 (via direct Anthropic API)
- **Framework**: Strands Agents
- **Tools**: None (minimal test configuration)
- **Prompt**: Friendly conversational personality

## Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Add your Anthropic API key to `.env`:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

3. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

### As a Test Agent

Use with the Basic-Agent-Chat-Loop tool to test chat functionality:

```bash
# From the chat loop tool directory
python -m your_chat_loop_command --agent simple_sally_sample_agent
```

### Standalone Testing

Run directly to verify the agent works:

```python
from simple_sally_sample_agent import root_agent

response = root_agent("Hello!")
print(response)
```

## Configuration

### Model Parameters
- **Model ID**: `claude-sonnet-4-20250514`
- **Max Tokens**: 4096
- **Temperature**: 0.7

### Environment Variables
- `ANTHROPIC_API_KEY` (required): Your Anthropic API key

## Files

- `agent.py` - Main agent implementation
- `prompts.py` - System prompt configuration
- `__init__.py` - Module exports
- `.env.example` - Template environment file
- `pyproject.toml` - Project dependencies
- `requirements.txt` - Pip requirements

## Testing Notes

This is a test agent with minimal functionality by design. For more complex examples with tools and MCP integration, see other agents in the repository.
