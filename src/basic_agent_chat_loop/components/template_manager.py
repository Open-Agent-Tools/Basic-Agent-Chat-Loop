"""
Prompt template management.

Handles loading and listing markdown-based prompt templates.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manage prompt templates from ~/.prompts/ directory."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            prompts_dir: Directory containing templates (defaults to ~/.prompts/)
        """
        self.prompts_dir = prompts_dir or Path.home() / ".prompts"

    def load_template(self, template_name: str, input_text: str = "") -> Optional[str]:
        """
        Load a prompt template from ~/.prompts/{template_name}.md

        Args:
            template_name: Name of the template (without .md extension)
            input_text: Text to substitute for {input} placeholder

        Returns:
            Processed template text, or None if template not found
        """
        template_path = self.prompts_dir / f"{template_name}.md"

        if not template_path.exists():
            return None

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
            return None

    def list_templates(self) -> List[str]:
        """
        List available prompt templates from ~/.prompts/

        Returns:
            List of template names (without .md extension)
        """
        if not self.prompts_dir.exists():
            return []

        templates = []
        for file in self.prompts_dir.glob("*.md"):
            templates.append(file.stem)

        return sorted(templates)

    def get_template_info(self, template_name: str) -> Optional[Tuple[str, str]]:
        """
        Get template description from first line.

        Args:
            template_name: Name of the template

        Returns:
            Tuple of (name, description) or None if not found
        """
        template_path = self.prompts_dir / f"{template_name}.md"

        if not template_path.exists():
            return None

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

    def list_templates_with_descriptions(self) -> List[Tuple[str, str]]:
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
