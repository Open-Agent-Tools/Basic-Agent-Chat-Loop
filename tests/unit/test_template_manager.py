"""Tests for TemplateManager component."""

from pathlib import Path

import pytest

from basic_agent_chat_loop.components.template_manager import TemplateManager


@pytest.fixture
def prompts_dir(tmp_path):
    """Create a temporary prompts directory."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    return prompts


@pytest.fixture
def template_manager(prompts_dir):
    """Create TemplateManager with temporary prompts directory."""
    return TemplateManager(prompts_dir)


@pytest.fixture
def populated_prompts_dir(prompts_dir):
    """Create prompts directory with sample templates."""
    # Simple template
    (prompts_dir / "simple.md").write_text("This is a simple template.")

    # Template with heading (description)
    (prompts_dir / "review.md").write_text(
        "# Code Review\n\nPlease review the following:\n\n{input}"
    )

    # Template with different heading
    (prompts_dir / "complex.md").write_text(
        "# Complex Template\n"
        "\n"
        "Content: {input}\n"
        "Additional: {extra}"
    )

    return prompts_dir


class TestTemplateManagerInitialization:
    """Test TemplateManager initialization."""

    def test_initialization(self, template_manager, prompts_dir):
        """Test that TemplateManager initializes with correct directory."""
        assert template_manager.prompts_dir == prompts_dir

    def test_initialization_does_not_create_directory(self, tmp_path):
        """Test that initialization does not create prompts directory."""
        prompts_dir = tmp_path / "new_prompts"
        assert not prompts_dir.exists()

        manager = TemplateManager(prompts_dir)
        assert manager.prompts_dir == prompts_dir
        # Directory is not created until templates are loaded


class TestListTemplates:
    """Test listing available templates."""

    def test_list_templates_empty(self, template_manager):
        """Test listing templates when directory is empty."""
        templates = template_manager.list_templates()
        assert templates == []

    def test_list_templates_populated(self, prompts_dir, populated_prompts_dir):
        """Test listing templates with existing files."""
        manager = TemplateManager(prompts_dir)
        templates = manager.list_templates()

        assert len(templates) == 3
        assert "simple" in templates
        assert "review" in templates
        assert "complex" in templates

    def test_list_templates_ignores_non_md_files(self, prompts_dir):
        """Test that non-.md files are ignored."""
        (prompts_dir / "template.md").write_text("Valid template")
        (prompts_dir / "readme.txt").write_text("Not a template")
        (prompts_dir / "notes.doc").write_text("Also not a template")

        manager = TemplateManager(prompts_dir)
        templates = manager.list_templates()

        assert len(templates) == 1
        assert "template" in templates


class TestListTemplatesWithDescriptions:
    """Test listing templates with their descriptions."""

    def test_list_with_descriptions_no_heading(self, prompts_dir):
        """Test listing templates without markdown heading."""
        (prompts_dir / "simple.md").write_text("No heading here")

        manager = TemplateManager(prompts_dir)
        templates = manager.list_templates_with_descriptions()

        assert len(templates) == 1
        assert templates[0] == ("simple", "simple")  # Uses name as description

    def test_list_with_descriptions_with_heading(self, prompts_dir, populated_prompts_dir):
        """Test listing templates with markdown headings."""
        manager = TemplateManager(prompts_dir)
        templates = manager.list_templates_with_descriptions()

        # Find the complex template
        complex_template = next((t for t in templates if t[0] == "complex"), None)
        assert complex_template is not None
        assert complex_template[1] == "Complex Template"

    def test_list_with_descriptions_mixed(self, prompts_dir, populated_prompts_dir):
        """Test listing mix of templates with and without headings."""
        manager = TemplateManager(prompts_dir)
        templates = manager.list_templates_with_descriptions()

        assert len(templates) == 3

        # Convert to dict for easier checking
        templates_dict = dict(templates)
        assert templates_dict["simple"] == "simple"  # No heading
        assert templates_dict["review"] == "Code Review"  # Has heading
        assert templates_dict["complex"] == "Complex Template"  # Has heading


class TestLoadTemplate:
    """Test loading individual templates."""

    def test_load_nonexistent_template(self, template_manager):
        """Test loading a template that doesn't exist."""
        result = template_manager.load_template("nonexistent")
        assert result is None

    def test_load_simple_template(self, prompts_dir, populated_prompts_dir):
        """Test loading a simple template without variables."""
        manager = TemplateManager(prompts_dir)
        content = manager.load_template("simple")

        assert content == "This is a simple template."

    def test_load_template_with_variable_substitution(self, prompts_dir, populated_prompts_dir):
        """Test loading template and substituting variables."""
        manager = TemplateManager(prompts_dir)
        content = manager.load_template("review", "my_code.py")

        assert "# Code Review" in content
        assert "my_code.py" in content
        assert "{input}" not in content

    def test_load_template_without_input(self, prompts_dir, populated_prompts_dir):
        """Test loading template with {input} placeholder but no input provided."""
        manager = TemplateManager(prompts_dir)
        content = manager.load_template("review")

        # {input} should be replaced with empty string
        assert "{input}" not in content or content.endswith("\n\n")

    def test_load_template_with_heading(self, prompts_dir, populated_prompts_dir):
        """Test loading template with markdown heading."""
        manager = TemplateManager(prompts_dir)
        content = manager.load_template("complex", "test input")

        assert "# Complex Template" in content
        assert "test input" in content

    def test_load_template_multiple_variables(self, prompts_dir):
        """Test loading template with multiple variable types."""
        (prompts_dir / "multi.md").write_text(
            "Input: {input}\nExtra: {extra}\nAnother: {something}"
        )

        manager = TemplateManager(prompts_dir)
        content = manager.load_template("multi", "user input here")

        assert "user input here" in content
        assert "{input}" not in content
        # Other variables should remain if not provided
        assert "{extra}" in content
        assert "{something}" in content


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_template_file(self, prompts_dir):
        """Test loading an empty template file."""
        (prompts_dir / "empty.md").write_text("")

        manager = TemplateManager(prompts_dir)
        content = manager.load_template("empty")

        assert content == ""

    def test_template_without_input_placeholder(self, prompts_dir):
        """Test loading template without {input} placeholder."""
        (prompts_dir / "no_placeholder.md").write_text("# Title\n\nContent without placeholder")

        manager = TemplateManager(prompts_dir)
        content = manager.load_template("no_placeholder", "extra text")

        # Input should be appended
        assert "Content without placeholder" in content
        assert "extra text" in content

    def test_unicode_in_template(self, prompts_dir):
        """Test template with unicode characters."""
        (prompts_dir / "unicode.md").write_text(
            "Template with émojis 🎉 and spëcial çharacters: {input}"
        )

        manager = TemplateManager(prompts_dir)
        content = manager.load_template("unicode", "test 测试")

        assert "émojis 🎉" in content
        assert "test 测试" in content

    def test_very_long_input(self, prompts_dir, populated_prompts_dir):
        """Test template with very long input."""
        long_input = "x" * 10000

        manager = TemplateManager(prompts_dir)
        content = manager.load_template("review", long_input)

        assert long_input in content
        assert len(content) > 10000
