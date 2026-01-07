"""
Prompt template management.

Handles loading and listing markdown-based prompt templates.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manage prompt templates from multiple directories with priority."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            prompts_dir: Base prompts directory (defaults to ~/.prompts/)
                        This is used for backward compatibility and initialization.
        """
        base_prompts_dir = prompts_dir or Path.home() / ".prompts"

        # Template directories in priority order (first = highest priority)
        # Priority: ~/.prompts > ./.claude/commands > ~/.claude/commands
        self.template_dirs = [
            base_prompts_dir,  # Legacy/base (highest priority)
            Path.cwd() / ".claude" / "commands",  # Project-specific (medium)
            Path.home() / ".claude" / "commands",  # User global (lowest priority)
        ]

        # Keep prompts_dir for backward compatibility (used for initialization)
        self.prompts_dir = base_prompts_dir
        self._initialize_templates()

    def _initialize_templates(self):
        """Create prompts directory and sample templates if they don't exist."""
        if self.prompts_dir.exists():
            return

        try:
            self.prompts_dir.mkdir(parents=True, exist_ok=True)

            # Create sample templates
            self._create_sample_template(
                "explain",
                """# Explain this code

Please explain the following code in detail:

{input}

Focus on:
- What the code does
- How it works
- Any potential issues or improvements
- Best practices being followed or violated
""",
            )

            self._create_sample_template(
                "review",
                """# Code Review

Please review the following code:

{input}

Provide feedback on:
- Code quality and readability
- Potential bugs or issues
- Performance considerations
- Security concerns
- Suggestions for improvement
""",
            )

            self._create_sample_template(
                "debug",
                """# Debug Help

I'm having trouble with this code:

{input}

Please help me:
1. Identify the issue
2. Explain why it's happening
3. Suggest a fix
4. Provide the corrected code
""",
            )

            self._create_sample_template(
                "optimize",
                """# Optimize This Code

Please optimize the following code:

{input}

Focus on:
- Performance improvements
- Memory efficiency
- Code simplicity
- Best practices
""",
            )

            self._create_sample_template(
                "test",
                """# Write Tests

Please write comprehensive tests for the following code:

{input}

Include:
- Unit tests for all functions
- Edge cases and error handling
- Test descriptions explaining what each test validates
""",
            )

            self._create_sample_template(
                "document",
                """# Add Documentation

Please add comprehensive documentation to this code:

{input}

Include:
- Docstrings for all functions/classes
- Inline comments for complex logic
- Usage examples
- Type hints if missing
""",
            )

            self._create_sample_template(
                "load",
                """# Load Markdown Files

Please load all markdown (.md) files from the current directory or
specified directory into context for analysis and reference.

**Important**: Only load files directly in the specified directory,
NOT in any subdirectories.

**Process**:
1. Use glob to find all .md files in the target directory (non-recursive)
2. Read each file found to bring it into context
3. Provide a brief summary of what files were loaded

**Directory Selection**:
- If no directory is specified, use current directory: .
- If directory is specified, use that path: {input}
- Validate directory exists before processing

**Output Format**:
- List each file loaded with its path
- Provide brief description of total files processed
- Note any files that couldn't be read

Begin loading files now.
""",
            )

        except Exception as e:
            logger.debug(f"Could not initialize templates: {e}")

    def _create_sample_template(self, name: str, content: str):
        """Create a sample template file."""
        template_path = self.prompts_dir / f"{name}.md"
        if not template_path.exists():
            try:
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.debug(f"Could not create template {name}: {e}")

    def load_template(self, template_name: str, input_text: str = "") -> Optional[str]:
        """
        Load a prompt template, checking directories in priority order.

        Checks in order: ~/.prompts, ./.claude/commands, ~/.claude/commands
        Returns the first match found (highest priority wins).

        Args:
            template_name: Name of the template (without .md extension)
            input_text: Text to substitute for {input} placeholder

        Returns:
            Processed template text, or None if template not found
        """
        # Check directories in priority order (highest priority first)
        for template_dir in self.template_dirs:
            template_path = template_dir / f"{template_name}.md"

            if not template_path.exists():
                continue

            try:
                with open(template_path, encoding="utf-8") as f:
                    template = f.read()

                # Replace {input} placeholder with provided text
                if "{input}" in template:
                    template = template.replace("{input}", input_text)
                elif input_text:
                    # If no {input} placeholder but input provided, append it
                    template = f"{template}\n\n{input_text}"

                return template

            except Exception as e:
                logger.error(f"Error loading template {template_name}: {e}")
                continue

        return None

    def list_templates(self) -> list[str]:
        """
        List all available templates from all directories (deduplicated).

        Returns:
            Sorted list of unique template names (without .md extension)
        """
        templates = set()

        for template_dir in self.template_dirs:
            if not template_dir.exists():
                continue

            for file in template_dir.glob("*.md"):
                templates.add(file.stem)

        return sorted(templates)

    def get_template_info(
        self, template_name: str, template_dir: Optional[Path] = None
    ) -> Optional[tuple[str, str]]:
        """
        Get template description from first line.

        Args:
            template_name: Name of the template
            template_dir: Specific directory to check (if None, uses priority order)

        Returns:
            Tuple of (name, description) or None if not found
        """
        # If specific directory provided, check only that one
        dirs_to_check = [template_dir] if template_dir else self.template_dirs

        for dir_path in dirs_to_check:
            template_path = dir_path / f"{template_name}.md"

            if not template_path.exists():
                continue

            try:
                with open(template_path, encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    # Extract description from markdown heading
                    if first_line.startswith("# "):
                        description = first_line[2:].strip()
                    else:
                        description = template_name
                    return (template_name, description)
            except Exception:
                return (template_name, template_name)

        return None

    def list_templates_with_descriptions(self) -> list[tuple[str, str]]:
        """
        List templates with their descriptions.

        Returns:
            List of (name, description) tuples
        """
        templates = []
        for template_name in self.list_templates():
            info = self.get_template_info(template_name)
            if info:
                templates.append(info)
        return templates

    def list_templates_grouped(self) -> list[tuple[Path, list[tuple[str, str]]]]:
        """
        List templates grouped by source directory.

        Returns:
            List of (directory_path, templates) tuples where templates is a list
            of (name, description) tuples. Directories are returned in priority order.
        """
        grouped = []

        for template_dir in self.template_dirs:
            if not template_dir.exists():
                continue

            templates_in_dir = []
            for file in template_dir.glob("*.md"):
                template_name = file.stem
                info = self.get_template_info(template_name, template_dir)
                if info:
                    templates_in_dir.append(info)

            if templates_in_dir:
                grouped.append((template_dir, sorted(templates_in_dir)))

        return grouped
