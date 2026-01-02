"""Tests for CommandRouter component."""

import pytest
from basic_agent_chat_loop.components.command_router import (
    CommandResult,
    CommandRouter,
    CommandType,
)


class TestExitCommands:
    """Test exit command detection."""

    def test_exit_command(self):
        """Test 'exit' is recognized."""
        router = CommandRouter()
        result = router.parse_input("exit")
        assert result.command_type == CommandType.EXIT
        assert result.is_command is True

    def test_quit_command(self):
        """Test 'quit' is recognized."""
        router = CommandRouter()
        result = router.parse_input("quit")
        assert result.command_type == CommandType.EXIT
        assert result.is_command is True

    def test_bye_command(self):
        """Test 'bye' is recognized."""
        router = CommandRouter()
        result = router.parse_input("bye")
        assert result.command_type == CommandType.EXIT
        assert result.is_command is True

    def test_exit_with_hash_prefix(self):
        """Test '#exit' is recognized."""
        router = CommandRouter()
        result = router.parse_input("#exit")
        assert result.command_type == CommandType.EXIT
        assert result.is_command is True

    def test_exit_with_slash_prefix(self):
        """Test '/exit' is recognized."""
        router = CommandRouter()
        result = router.parse_input("/exit")
        assert result.command_type == CommandType.EXIT
        assert result.is_command is True

    def test_exit_case_insensitive(self):
        """Test exit commands are case insensitive."""
        router = CommandRouter()
        for cmd in ["EXIT", "Exit", "QUIT", "Quit", "BYE", "Bye"]:
            result = router.parse_input(cmd)
            assert result.command_type == CommandType.EXIT

    def test_exit_with_whitespace(self):
        """Test exit command with surrounding whitespace."""
        router = CommandRouter()
        result = router.parse_input("  exit  ")
        assert result.command_type == CommandType.EXIT

    def test_is_exit_command_helper(self):
        """Test is_exit_command helper method."""
        router = CommandRouter()
        assert router.is_exit_command("exit") is True
        assert router.is_exit_command("#quit") is True
        assert router.is_exit_command("help") is False


class TestBuiltinCommands:
    """Test built-in # commands."""

    def test_help_command(self):
        """Test #help command."""
        router = CommandRouter()
        result = router.parse_input("#help")
        assert result.command_type == CommandType.HELP
        assert result.is_command is True
        assert result.args is None

    def test_info_command(self):
        """Test #info command."""
        router = CommandRouter()
        result = router.parse_input("#info")
        assert result.command_type == CommandType.INFO
        assert result.is_command is True

    def test_templates_command(self):
        """Test #templates command."""
        router = CommandRouter()
        result = router.parse_input("#templates")
        assert result.command_type == CommandType.TEMPLATES
        assert result.is_command is True

    def test_sessions_command(self):
        """Test #sessions command."""
        router = CommandRouter()
        result = router.parse_input("#sessions")
        assert result.command_type == CommandType.SESSIONS
        assert result.is_command is True

    def test_compact_command(self):
        """Test #compact command."""
        router = CommandRouter()
        result = router.parse_input("#compact")
        assert result.command_type == CommandType.COMPACT
        assert result.is_command is True

    def test_context_command(self):
        """Test #context command."""
        router = CommandRouter()
        result = router.parse_input("#context")
        assert result.command_type == CommandType.CONTEXT
        assert result.is_command is True

    def test_clear_command(self):
        """Test #clear command."""
        router = CommandRouter()
        result = router.parse_input("#clear")
        assert result.command_type == CommandType.CLEAR
        assert result.is_command is True

    def test_commands_case_insensitive(self):
        """Test commands are case insensitive."""
        router = CommandRouter()
        result = router.parse_input("#HELP")
        assert result.command_type == CommandType.HELP

        result = router.parse_input("#Info")
        assert result.command_type == CommandType.INFO

    def test_command_with_leading_whitespace(self):
        """Test command with whitespace after #."""
        router = CommandRouter()
        result = router.parse_input("#  help")
        assert result.command_type == CommandType.HELP


class TestCopyCommand:
    """Test #copy command with variants."""

    def test_copy_default(self):
        """Test basic #copy command."""
        router = CommandRouter()
        result = router.parse_input("#copy")
        assert result.command_type == CommandType.COPY
        assert result.args is None  # No mode specified

    def test_copy_query(self):
        """Test #copy query variant."""
        router = CommandRouter()
        result = router.parse_input("#copy query")
        assert result.command_type == CommandType.COPY
        assert result.args == "query"

    def test_copy_all(self):
        """Test #copy all variant."""
        router = CommandRouter()
        result = router.parse_input("#copy all")
        assert result.command_type == CommandType.COPY
        assert result.args == "all"

    def test_copy_code(self):
        """Test #copy code variant."""
        router = CommandRouter()
        result = router.parse_input("#copy code")
        assert result.command_type == CommandType.COPY
        assert result.args == "code"

    def test_copy_case_insensitive(self):
        """Test copy mode is case insensitive."""
        router = CommandRouter()
        result = router.parse_input("#COPY QUERY")
        assert result.command_type == CommandType.COPY
        assert result.args == "query"


class TestResumeCommand:
    """Test #resume command."""

    def test_resume_without_args(self):
        """Test #resume without session reference."""
        router = CommandRouter()
        result = router.parse_input("#resume")
        assert result.command_type == CommandType.RESUME
        assert result.args is None

    def test_resume_with_session_id(self):
        """Test #resume with session ID."""
        router = CommandRouter()
        result = router.parse_input("#resume test_session_123")
        assert result.command_type == CommandType.RESUME
        assert result.args == "test_session_123"

    def test_resume_with_number(self):
        """Test #resume with session number."""
        router = CommandRouter()
        result = router.parse_input("#resume 5")
        assert result.command_type == CommandType.RESUME
        assert result.args == "5"

    def test_resume_with_extra_whitespace(self):
        """Test #resume with extra whitespace."""
        router = CommandRouter()
        result = router.parse_input("#resume   session_id  ")
        assert result.command_type == CommandType.RESUME
        assert result.args == "session_id"


class TestTemplateCommands:
    """Test template commands (/template_name)."""

    def test_template_without_input(self):
        """Test /template without input text."""
        router = CommandRouter()
        result = router.parse_input("/summarize")
        assert result.command_type == CommandType.TEMPLATE
        assert result.is_command is True

        name, input_text = router.extract_template_info(result)
        assert name == "summarize"
        assert input_text == ""

    def test_template_with_input(self):
        """Test /template with input text."""
        router = CommandRouter()
        result = router.parse_input("/summarize This is my text")
        assert result.command_type == CommandType.TEMPLATE

        name, input_text = router.extract_template_info(result)
        assert name == "summarize"
        assert input_text == "This is my text"

    def test_template_with_multiword_input(self):
        """Test template with multi-word input."""
        router = CommandRouter()
        result = router.parse_input("/analyze This is a longer input text")

        name, input_text = router.extract_template_info(result)
        assert name == "analyze"
        assert input_text == "This is a longer input text"

    def test_template_just_slash(self):
        """Test just / is not treated as template."""
        router = CommandRouter()
        result = router.parse_input("/")
        # Single / should be treated as query, not template
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False

    def test_extract_template_info_on_non_template(self):
        """Test extract_template_info raises error for non-template."""
        router = CommandRouter()
        result = router.parse_input("#help")

        with pytest.raises(ValueError, match="not a template command"):
            router.extract_template_info(result)


class TestMultilineCommand:
    """Test multi-line input trigger."""

    def test_multiline_trigger(self):
        """Test \\\\ triggers multi-line mode."""
        router = CommandRouter()
        result = router.parse_input("\\\\")
        assert result.command_type == CommandType.MULTILINE
        assert result.is_command is True

    def test_multiline_with_whitespace(self):
        """Test \\\\ with surrounding whitespace."""
        router = CommandRouter()
        result = router.parse_input("  \\\\  ")
        assert result.command_type == CommandType.MULTILINE


class TestRegularQueries:
    """Test regular query detection."""

    def test_simple_query(self):
        """Test simple query text."""
        router = CommandRouter()
        result = router.parse_input("Hello, how are you?")
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False
        assert result.original_input == "Hello, how are you?"

    def test_multiline_text_query(self):
        """Test multiline text as query."""
        router = CommandRouter()
        result = router.parse_input("This is\na multiline\nquery")
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False

    def test_query_with_hash_in_middle(self):
        """Test query containing # but not at start."""
        router = CommandRouter()
        result = router.parse_input("What is C# programming?")
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False

    def test_is_regular_query_helper(self):
        """Test is_regular_query helper method."""
        router = CommandRouter()
        assert router.is_regular_query("Hello") is True
        assert router.is_regular_query("#help") is False
        assert router.is_regular_query("exit") is False


class TestUnknownCommands:
    """Test unknown command handling."""

    def test_unknown_hash_command(self):
        """Test unknown # command."""
        router = CommandRouter()
        result = router.parse_input("#unknown")
        assert result.command_type == CommandType.UNKNOWN_COMMAND
        assert result.is_command is True
        assert result.args == "unknown"

    def test_unknown_command_with_args(self):
        """Test unknown command with arguments."""
        router = CommandRouter()
        result = router.parse_input("#foobar some args")
        assert result.command_type == CommandType.UNKNOWN_COMMAND
        assert result.args == "foobar some args"


class TestOriginalInput:
    """Test that original_input is preserved."""

    def test_original_input_preserved_exit(self):
        """Test original input for exit command."""
        router = CommandRouter()
        result = router.parse_input("  exit  ")
        assert result.original_input == "  exit  "

    def test_original_input_preserved_command(self):
        """Test original input for # command."""
        router = CommandRouter()
        result = router.parse_input("  #help  ")
        assert result.original_input == "  #help  "

    def test_original_input_preserved_query(self):
        """Test original input for query."""
        router = CommandRouter()
        result = router.parse_input("  Hello world  ")
        assert result.original_input == "  Hello world  "

    def test_original_input_preserved_template(self):
        """Test original input for template."""
        router = CommandRouter()
        result = router.parse_input("/template input text")
        assert result.original_input == "/template input text"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_empty_string(self):
        """Test empty string input."""
        router = CommandRouter()
        result = router.parse_input("")
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False

    def test_only_whitespace(self):
        """Test only whitespace input."""
        router = CommandRouter()
        result = router.parse_input("   ")
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False

    def test_hash_only(self):
        """Test just # character."""
        router = CommandRouter()
        result = router.parse_input("#")
        # Just # with no command should be unknown
        assert result.command_type == CommandType.UNKNOWN_COMMAND

    def test_hash_with_whitespace_only(self):
        """Test # followed by whitespace."""
        router = CommandRouter()
        result = router.parse_input("#   ")
        assert result.command_type == CommandType.UNKNOWN_COMMAND

    def test_unicode_query(self):
        """Test Unicode text in query."""
        router = CommandRouter()
        result = router.parse_input("Hello 世界 🌍")
        assert result.command_type == CommandType.QUERY
        assert result.is_command is False

    def test_very_long_input(self):
        """Test very long input string."""
        router = CommandRouter()
        long_input = "A" * 10000
        result = router.parse_input(long_input)
        assert result.command_type == CommandType.QUERY
        assert len(result.original_input) == 10000


class TestCommandResult:
    """Test CommandResult dataclass."""

    def test_command_result_creation(self):
        """Test creating CommandResult directly."""
        result = CommandResult(
            command_type=CommandType.HELP,
            args=None,
            original_input="#help",
            is_command=True,
        )
        assert result.command_type == CommandType.HELP
        assert result.args is None
        assert result.original_input == "#help"
        assert result.is_command is True

    def test_command_result_with_args(self):
        """Test CommandResult with arguments."""
        result = CommandResult(
            command_type=CommandType.COPY,
            args="query",
            original_input="#copy query",
            is_command=True,
        )
        assert result.args == "query"

    def test_command_result_defaults(self):
        """Test CommandResult default values."""
        result = CommandResult(command_type=CommandType.HELP)
        assert result.args is None
        assert result.original_input == ""
        assert result.is_command is True
