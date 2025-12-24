"""
Simple Sally - Test Agent for Basic-Agent-Chat-Loop

A minimal test agent demonstrating core Strands functionality.
Used for testing and validating the chat loop tool.
"""

from .agent import create_agent, root_agent
from .prompts import SYSTEM_PROMPT

__all__ = [
    "create_agent",
    "SYSTEM_PROMPT",
    "root_agent",
]

__version__ = "1.0.0"
