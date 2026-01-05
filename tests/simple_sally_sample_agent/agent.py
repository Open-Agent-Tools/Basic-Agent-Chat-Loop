"""
Simple Sally - Test Agent for Basic-Agent-Chat-Loop

A minimal test agent demonstrating core Strands functionality.
Used for testing and validating the chat loop tool.
"""

import os
from pathlib import Path

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands_tools import editor, file_read, file_write

# Load .env file
try:
    from dotenv import load_dotenv

    # Start with current file directory
    current_path = Path(__file__).parent
    env_path = current_path / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Search up to 3 parent directories
        for i in range(min(3, len(Path(__file__).parents))):
            env_path = Path(__file__).parents[i] / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                break
except ImportError:
    pass

try:
    from .prompts import SYSTEM_PROMPT
except ImportError:
    from prompts import SYSTEM_PROMPT

# Create the Anthropic model
model = AnthropicModel(
    client_args={
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
    },
    model_id="claude-sonnet-4-20250514",
    max_tokens=4096,
    params={
        "temperature": 0.7,
    },
)


def create_agent() -> Agent:
    """Create Simple Sally agent."""
    return Agent(
        name="Simple Sally",
        description="A friendly minimal agent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[file_read, file_write, editor],
    )


# Module-level agent
root_agent = create_agent()

if __name__ == "__main__":
    agent = create_agent()
    print(f"✓ Agent: {agent.name}")
    print(f"✓ Model: {agent.model}")
    print("✓ Agent ready for use")
