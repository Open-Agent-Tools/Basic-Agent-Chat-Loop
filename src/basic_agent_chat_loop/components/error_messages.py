"""
Error message utilities with actionable suggestions.

Provides formatted error messages with clear descriptions,
actionable steps, and helpful links.
"""

from .ui_components import Colors


class ErrorMessages:
    """Centralized error messages with actionable suggestions."""

    @staticmethod
    def agent_file_not_found(filepath: str) -> str:
        """Error message for missing agent file."""
        return f"""{Colors.error("Error: Agent file not found")}

File: {filepath}

To fix:
  1. Check that the file path is correct
  2. Verify the file exists: ls "{filepath}"
  3. Use absolute path or path relative to current directory

Current directory: Run 'pwd' to see your location"""

    @staticmethod
    def agent_import_error(filename: str, error: Exception) -> str:
        """Error message for agent import/execution failures."""
        error_str = str(error)

        suggestions = [
            "Check for syntax errors in the agent file",
            "Verify all imports are available",
            "Run the file directly to see full error: python " + filename,
        ]

        # Add specific suggestions based on error type
        if "ModuleNotFoundError" in str(type(error)):
            suggestions.insert(
                0, "Install missing dependencies (check requirements.txt)"
            )
        elif "SyntaxError" in str(type(error)):
            suggestions.insert(0, "Fix Python syntax errors in the file")

        suggestion_text = "\n  ".join(
            f"{i + 1}. {s}" for i, s in enumerate(suggestions)
        )

        return f"""{Colors.error("Error: Failed to load agent module")}

File: {filename}
Error: {error_str}

To fix:
  {suggestion_text}"""

    @staticmethod
    def agent_missing_root_agent(filename: str) -> str:
        """Error message for missing root_agent attribute."""
        return f"""{Colors.error("Error: Agent module missing root_agent")}

File: {filename}

To fix:
  1. Add a 'root_agent' function to your module
  2. Example:

     def root_agent(query: str) -> str:
         # Your agent logic here
         return response

  3. Or define root_agent as an Agent class instance:

     from basic_agent_chat_loop import Agent
     root_agent = Agent(...)"""

    @staticmethod
    def query_timeout(attempt: int, max_retries: int, timeout_seconds: int) -> str:
        """Error message for query timeouts."""
        retry_info = ""
        if attempt < max_retries:
            retry_info = f"\n\n{Colors.system('Retrying automatically...')}"

        return f"""{Colors.error(f"⚠️  Query timeout (attempt {attempt}/{max_retries})")}

The query took longer than {timeout_seconds} seconds.

Possible causes:
  • Complex query requiring more processing time
  • Network connectivity issues
  • API service delays
{retry_info}

To fix:
  1. Try a simpler query
  2. Check your internet connection
  3. Wait a moment and try again"""

    @staticmethod
    def connection_error(error: Exception, attempt: int, max_retries: int) -> str:
        """Error message for connection failures."""
        error_str = str(error)

        suggestions = [
            "Check your internet connection",
            "Verify API endpoint is accessible",
            "Check if firewall is blocking the connection",
        ]

        if "api key" in error_str.lower() or "401" in error_str or "403" in error_str:
            suggestions.insert(0, "Verify your API key is correct and active")
            suggestions.insert(1, "Check API key hasn't expired or been revoked")

        suggestion_text = "\n  ".join(
            f"{i + 1}. {s}" for i, s in enumerate(suggestions)
        )

        retry_info = ""
        if attempt < max_retries:
            retry_info = f"\n\n{Colors.system('Retrying automatically...')}"

        error_header = Colors.error(
            f"⚠️  Connection error (attempt {attempt}/{max_retries})"
        )
        return f"""{error_header}

Error: {error_str}
{retry_info}

To fix:
  {suggestion_text}"""

    @staticmethod
    def rate_limit_error(wait_time: int, attempt: int) -> str:
        """Error message for rate limiting."""
        return f"""{Colors.error("⚠️  Rate limit exceeded")}

The API has rate limited this request.

{Colors.system(f"Waiting {wait_time}s before retry (attempt {attempt})...")}

To avoid rate limits:
  1. Reduce query frequency
  2. Upgrade API plan for higher limits
  3. Implement request batching if supported"""

    @staticmethod
    def dependency_install_failed(package: str, error: Exception) -> str:
        """Error message for dependency installation failures."""
        error_str = str(error)

        suggestions = [
            "Check your internet connection",
            "Verify package name is correct: pip search " + package,
            "Try installing manually: pip install " + package,
            "Check pip is up to date: pip install --upgrade pip",
        ]

        if "permission" in error_str.lower():
            suggestions.insert(0, "Use --user flag: pip install --user " + package)

        suggestion_text = "\n  ".join(
            f"{i + 1}. {s}" for i, s in enumerate(suggestions)
        )

        return f"""{Colors.error("Error: Failed to install dependency")}

Package: {package}
Error: {error_str}

To fix:
  {suggestion_text}"""

    @staticmethod
    def config_file_error(
        filepath: str, error: Exception, operation: str = "read"
    ) -> str:
        """Error message for configuration file errors."""
        error_str = str(error)

        suggestions = []
        if operation == "write":
            suggestions = [
                f'Check write permissions: ls -la "{filepath}"',
                "Verify directory exists and is writable",
                "Try running with appropriate permissions",
            ]
        else:  # read or parse
            suggestions = [
                f'Check file exists: ls -la "{filepath}"',
                "Verify file has correct format (JSON/YAML)",
                "Check file isn't corrupted",
                "Delete and regenerate config if needed",
            ]

        suggestion_text = "\n  ".join(
            f"{i + 1}. {s}" for i, s in enumerate(suggestions)
        )

        return f"""{Colors.error(f"Error: Failed to {operation} configuration file")}

File: {filepath}
Error: {error_str}

To fix:
  {suggestion_text}"""

    @staticmethod
    def session_load_error(filepath: str, error: Exception) -> str:
        """Error message for session loading failures."""
        return f"""{Colors.error("Error: Failed to load saved session")}

File: {filepath}
Error: {str(error)}

To fix:
  1. Check file isn't corrupted: cat "{filepath}"
  2. Verify JSON format is valid
  3. Delete corrupted session: rm "{filepath}"
  4. Start fresh session without --resume"""

    @staticmethod
    def template_error(template_name: str, error: Exception) -> str:
        """Error message for template loading/parsing failures."""
        return f"""{Colors.error("Error: Failed to load template")}

Template: {template_name}
Error: {str(error)}

To fix:
  1. Check template file exists and is readable
  2. Verify template syntax is valid
  3. List available templates to verify name
  4. Check template hasn't been corrupted"""

    @staticmethod
    def api_key_missing(env_var: str = "ANTHROPIC_API_KEY") -> str:
        """Error message for missing API key."""
        return f"""{Colors.error(f"Error: {env_var} not found")}

To fix:
  1. Get API key from: https://console.anthropic.com/
  2. Set environment variable:

     export {env_var}=your-key-here

  3. Or add to .env file:

     {env_var}=your-key-here

  4. Or pass directly to agent configuration

Docs: https://docs.anthropic.com/"""

    @staticmethod
    def generic_error(error: Exception, context: str = "") -> str:
        """Generic error message with context."""
        error_str = str(error)
        context_line = f"\nContext: {context}" if context else ""

        return f"""{Colors.error("Error: An unexpected error occurred")}
{context_line}
Error: {error_str}

To fix:
  1. Check logs for more details
  2. Try the operation again
  3. Report issue if problem persists: https://github.com/anthropics/basic-agent-chat-loop/issues"""
