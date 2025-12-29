"""Google ADK Test Agent.

A minimal test agent demonstrating Google ADK compatibility with
the Basic Agent Chat Loop.
"""

import os
from pathlib import Path

from google.adk.agents import Agent


# Load .env file if available
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
    from .prompts import agent_instruction
except ImportError:
    from prompts import agent_instruction


def create_agent() -> Agent:
    """
    Create and return a configured Google ADK test agent.

    Returns:
        Agent: Configured test agent instance.
    """
    return Agent(
        model=os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash"),
        name="GoogleADK_Test_Agent",
        instruction=agent_instruction,
        description="A minimal test agent for validating Google ADK compatibility with chat loop",
        tools=[],  # No tools needed for basic testing
    )


# Module-level agent
root_agent = create_agent()

if __name__ == "__main__":
    agent = create_agent()
    print(f"✓ Agent: {agent.name}")
    print(f"✓ Model: {agent.model}")
    print("✓ Google ADK: Available")
    print("✓ Agent ready for use")
