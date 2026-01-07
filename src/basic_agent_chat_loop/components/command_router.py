"""Command routing and parsing for the chat loop.

Handles detection, classification, and argument extraction for:
- Built-in commands (#help, #copy, #resume, etc.)
- Template commands (/template_name)
- Exit commands (exit, quit, bye)
- Multi-line input trigger (\\)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CommandType(Enum):
    """Types of commands recognized by the chat loop."""

    # Exit commands
    EXIT = "exit"

    # Built-in # commands
    HELP = "help"
    INFO = "info"
    TEMPLATES = "templates"
    SESSIONS = "sessions"
    COMPACT = "compact"
    COPY = "copy"
    RESUME = "resume"
    CONTEXT = "context"
    CLEAR = "clear"

    # Special input modes
    TEMPLATE = "template"
    MULTILINE = "multiline"

    # Not a command
    QUERY = "query"
    UNKNOWN_COMMAND = "unknown_command"


@dataclass
class CommandResult:
    """Result of parsing a user input string.

    Attributes:
        command_type: The type of command detected
        args: Command arguments (e.g., template name, session ID, copy mode)
        original_input: The original user input string
        is_command: True if this is a command (not a regular query)
    """

    command_type: CommandType
    args: Optional[str] = None
    original_input: str = ""
    is_command: bool = True


class CommandRouter:
    """Router for parsing and classifying user input commands.

    Provides stateless command detection and argument extraction without
    requiring access to chat loop state or dependencies.
    """

    # Commands that can be invoked with or without prefix
    EXIT_COMMANDS = {"exit", "quit", "bye"}

    # Built-in # commands
    BUILTIN_COMMANDS = {
        "help",
        "info",
        "templates",
        "sessions",
        "compact",
        "copy",
        "resume",
        "context",
        "clear",
    }

    def parse_input(self, user_input: str) -> CommandResult:
        """Parse user input and determine command type and arguments.

        Args:
            user_input: Raw user input string

        Returns:
            CommandResult with command type and extracted arguments
        """
        stripped = user_input.strip()

        # Check for exit commands (with or without prefix)
        normalized = stripped.lstrip("#/").lower()
        if normalized in self.EXIT_COMMANDS:
            return CommandResult(
                command_type=CommandType.EXIT,
                original_input=user_input,
                is_command=True,
            )

        # Check for multi-line input trigger
        if stripped == "\\\\":
            return CommandResult(
                command_type=CommandType.MULTILINE,
                original_input=user_input,
                is_command=True,
            )

        # Check for # commands
        if stripped.startswith("#"):
            return self._parse_hash_command(stripped, user_input)

        # Check for template commands (/ prefix)
        if stripped.startswith("/") and len(stripped) > 1:
            return self._parse_template_command(stripped, user_input)

        # Regular query (not a command)
        return CommandResult(
            command_type=CommandType.QUERY,
            original_input=user_input,
            is_command=False,
        )

    def _parse_hash_command(self, stripped: str, original_input: str) -> CommandResult:
        """Parse a # command and extract arguments.

        Args:
            stripped: Stripped input starting with #
            original_input: Original user input

        Returns:
            CommandResult for the # command
        """
        # Strip # and get command
        cmd_input = stripped[1:].strip()
        cmd_lower = cmd_input.lower()

        # Check for exit commands
        if cmd_lower in self.EXIT_COMMANDS:
            return CommandResult(
                command_type=CommandType.EXIT,
                original_input=original_input,
                is_command=True,
            )

        # Parse command with potential arguments
        parts = cmd_lower.split(maxsplit=1)
        base_cmd = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else None

        # Map to command types
        if base_cmd == "help":
            return CommandResult(
                command_type=CommandType.HELP,
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "info":
            return CommandResult(
                command_type=CommandType.INFO,
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd in ("templates", "prompts", "commands"):
            return CommandResult(
                command_type=CommandType.TEMPLATES,
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "sessions":
            return CommandResult(
                command_type=CommandType.SESSIONS,
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "compact":
            return CommandResult(
                command_type=CommandType.COMPACT,
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "copy":
            # Copy command with optional mode (query, all, code)
            return CommandResult(
                command_type=CommandType.COPY,
                args=args,  # copy mode (query, all, code, or None)
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "resume":
            # Resume command with optional session reference
            return CommandResult(
                command_type=CommandType.RESUME,
                args=args,  # session ID or number
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "context":
            return CommandResult(
                command_type=CommandType.CONTEXT,
                original_input=original_input,
                is_command=True,
            )
        elif base_cmd == "clear":
            return CommandResult(
                command_type=CommandType.CLEAR,
                original_input=original_input,
                is_command=True,
            )
        else:
            # Unknown # command
            return CommandResult(
                command_type=CommandType.UNKNOWN_COMMAND,
                args=cmd_input,  # Full command string for error message
                original_input=original_input,
                is_command=True,
            )

    def _parse_template_command(
        self, stripped: str, original_input: str
    ) -> CommandResult:
        """Parse a template command (/template_name).

        Args:
            stripped: Stripped input starting with /
            original_input: Original user input

        Returns:
            CommandResult for the template command with template name and input
        """
        # Strip / and parse template name and input
        parts = stripped[1:].split(maxsplit=1)
        template_name = parts[0] if parts else ""
        template_input = parts[1] if len(parts) > 1 else ""

        # Store both template name and input in args as "name|input"
        args = f"{template_name}|{template_input}"

        return CommandResult(
            command_type=CommandType.TEMPLATE,
            args=args,
            original_input=original_input,
            is_command=True,
        )

    def is_exit_command(self, user_input: str) -> bool:
        """Check if input is an exit command.

        Args:
            user_input: User input string

        Returns:
            True if this is an exit command
        """
        result = self.parse_input(user_input)
        return result.command_type == CommandType.EXIT

    def is_regular_query(self, user_input: str) -> bool:
        """Check if input is a regular query (not a command).

        Args:
            user_input: User input string

        Returns:
            True if this is a regular query
        """
        result = self.parse_input(user_input)
        return result.command_type == CommandType.QUERY

    def extract_template_info(self, command_result: CommandResult) -> tuple[str, str]:
        """Extract template name and input from template command result.

        Args:
            command_result: CommandResult from parse_input

        Returns:
            Tuple of (template_name, template_input)

        Raises:
            ValueError: If command_result is not a TEMPLATE command
        """
        if command_result.command_type != CommandType.TEMPLATE:
            raise ValueError("Command result is not a template command")

        if not command_result.args:
            return ("", "")

        parts = command_result.args.split("|", maxsplit=1)
        template_name = parts[0] if len(parts) > 0 else ""
        template_input = parts[1] if len(parts) > 1 else ""

        return (template_name, template_input)
