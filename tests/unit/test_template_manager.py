"""Tests for TemplateManager component."""

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
    manager = TemplateManager(prompts_dir)
    # Override template_dirs to only use test directory
    manager.template_dirs = [prompts_dir]
    return manager


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
        "# Complex Template\n\nContent: {input}\nAdditional: {extra}"
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
        manager.template_dirs = [prompts_dir]
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
        manager.template_dirs = [prompts_dir]
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
        manager.template_dirs = [prompts_dir]
        templates = manager.list_templates()

        assert len(templates) == 1
        assert "template" in templates


class TestListTemplatesWithDescriptions:
    """Test listing templates with their descriptions."""

    def test_list_with_descriptions_no_heading(self, prompts_dir):
        """Test listing templates without markdown heading."""
        (prompts_dir / "simple.md").write_text("No heading here")

        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        templates = manager.list_templates_with_descriptions()

        assert len(templates) == 1
        assert templates[0] == ("simple", "simple")  # Uses name as description

    def test_list_with_descriptions_with_heading(
        self, prompts_dir, populated_prompts_dir
    ):
        """Test listing templates with markdown headings."""
        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        templates = manager.list_templates_with_descriptions()

        # Find the complex template
        complex_template = next((t for t in templates if t[0] == "complex"), None)
        assert complex_template is not None
        assert complex_template[1] == "Complex Template"

    def test_list_with_descriptions_mixed(self, prompts_dir, populated_prompts_dir):
        """Test listing mix of templates with and without headings."""
        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
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
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("simple")

        assert content == "This is a simple template."

    def test_load_template_with_variable_substitution(
        self, prompts_dir, populated_prompts_dir
    ):
        """Test loading template and substituting variables."""
        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("review", "my_code.py")

        assert "# Code Review" in content
        assert "my_code.py" in content
        assert "{input}" not in content

    def test_load_template_without_input(self, prompts_dir, populated_prompts_dir):
        """Test loading template with {input} placeholder but no input provided."""
        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("review")

        # {input} should be replaced with empty string
        assert "{input}" not in content or content.endswith("\n\n")

    def test_load_template_with_heading(self, prompts_dir, populated_prompts_dir):
        """Test loading template with markdown heading."""
        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("complex", "test input")

        assert "# Complex Template" in content
        assert "test input" in content

    def test_load_template_multiple_variables(self, prompts_dir):
        """Test loading template with multiple variable types."""
        (prompts_dir / "multi.md").write_text(
            "Input: {input}\nExtra: {extra}\nAnother: {something}"
        )

        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
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
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("empty")

        assert content == ""

    def test_template_without_input_placeholder(self, prompts_dir):
        """Test loading template without {input} placeholder."""
        (prompts_dir / "no_placeholder.md").write_text(
            "# Title\n\nContent without placeholder"
        )

        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("no_placeholder", "extra text")

        # Input should be appended
        assert "Content without placeholder" in content
        assert "extra text" in content

    def test_unicode_in_template(self, prompts_dir):
        """Test template with unicode characters."""
        (prompts_dir / "unicode.md").write_text(
            "Template with émojis 🎉 and spëcial çharacters: {input}", encoding="utf-8"
        )

        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("unicode", "test 测试")

        assert "émojis 🎉" in content
        assert "test 测试" in content

    def test_very_long_input(self, prompts_dir, populated_prompts_dir):
        """Test template with very long input."""
        long_input = "x" * 10000

        manager = TemplateManager(prompts_dir)
        manager.template_dirs = [prompts_dir]
        content = manager.load_template("review", long_input)

        assert long_input in content
        assert len(content) > 10000


class TestMultiDirectorySupport:
    """Test multi-directory template loading with priority."""

    @pytest.fixture
    def multi_dir_setup(self, tmp_path):
        """Create multiple template directories with overlapping templates."""
        # Create three directories
        base_dir = tmp_path / "prompts"
        project_dir = tmp_path / "project_claude" / "commands"
        user_dir = tmp_path / "user_claude" / "commands"

        base_dir.mkdir(parents=True)
        project_dir.mkdir(parents=True)
        user_dir.mkdir(parents=True)

        # Base directory templates (highest priority)
        (base_dir / "base_only.md").write_text("# Base Only\nTemplate from base")
        (base_dir / "shared.md").write_text("# Shared Base\nFrom base directory")

        # Project directory templates (medium priority)
        (project_dir / "project_only.md").write_text(
            "# Project Only\nTemplate from project"
        )
        (project_dir / "shared.md").write_text(
            "# Shared Project\nFrom project directory (overridden by base)"
        )

        # User directory templates (lowest priority)
        (user_dir / "user_only.md").write_text("# User Only\nTemplate from user")
        (user_dir / "shared.md").write_text(
            "# Shared User\nFrom user directory (overridden by base and project)"
        )

        return {
            "base": base_dir,
            "project": project_dir,
            "user": user_dir,
        }

    def test_list_templates_grouped(self, multi_dir_setup):
        """Test listing templates grouped by source directory."""
        manager = TemplateManager(multi_dir_setup["base"])
        # Manually set template_dirs to use test directories
        manager.template_dirs = [
            multi_dir_setup["base"],
            multi_dir_setup["project"],
            multi_dir_setup["user"],
        ]

        grouped = manager.list_templates_grouped()

        # Should have 3 groups
        assert len(grouped) == 3

        # Check base directory templates
        base_group = next((g for g in grouped if g[0] == multi_dir_setup["base"]), None)
        assert base_group is not None
        base_templates = dict(base_group[1])
        assert "base_only" in base_templates
        assert "shared" in base_templates

        # Check project directory templates
        project_group = next(
            (g for g in grouped if g[0] == multi_dir_setup["project"]), None
        )
        assert project_group is not None
        project_templates = dict(project_group[1])
        assert "project_only" in project_templates
        assert "shared" in project_templates

        # Check user directory templates
        user_group = next((g for g in grouped if g[0] == multi_dir_setup["user"]), None)
        assert user_group is not None
        user_templates = dict(user_group[1])
        assert "user_only" in user_templates
        assert "shared" in user_templates

    def test_list_templates_deduplicates(self, multi_dir_setup):
        """Test that list_templates returns deduplicated list of all templates."""
        manager = TemplateManager(multi_dir_setup["base"])
        manager.template_dirs = [
            multi_dir_setup["base"],
            multi_dir_setup["project"],
            multi_dir_setup["user"],
        ]

        templates = manager.list_templates()

        # Should have 4 unique templates (base_only, project_only, user_only, shared)
        assert len(templates) == 4
        assert "base_only" in templates
        assert "project_only" in templates
        assert "user_only" in templates
        assert "shared" in templates

    def test_load_template_priority_order(self, multi_dir_setup):
        """Test that templates are loaded from highest priority directory."""
        manager = TemplateManager(multi_dir_setup["base"])
        manager.template_dirs = [
            multi_dir_setup["base"],
            multi_dir_setup["project"],
            multi_dir_setup["user"],
        ]

        # Load shared template - should come from base dir (highest priority)
        content = manager.load_template("shared")
        assert "From base directory" in content
        assert "From project directory" not in content
        assert "From user directory" not in content

    def test_load_template_fallback_to_lower_priority(self, multi_dir_setup):
        """Test that templates fall back to lower priority if not found in higher."""
        manager = TemplateManager(multi_dir_setup["base"])
        manager.template_dirs = [
            multi_dir_setup["base"],
            multi_dir_setup["project"],
            multi_dir_setup["user"],
        ]

        # Load project_only - should come from project dir
        content = manager.load_template("project_only")
        assert "Template from project" in content

        # Load base_only - should come from base dir
        content = manager.load_template("base_only")
        assert "Template from base" in content

    def test_empty_directories_handled(self, tmp_path):
        """Test that empty directories don't break template loading."""
        base_dir = tmp_path / "prompts"
        empty_dir1 = tmp_path / "empty1"
        empty_dir2 = tmp_path / "empty2"

        base_dir.mkdir()
        (base_dir / "test.md").write_text("# Test\nContent")

        manager = TemplateManager(base_dir)
        manager.template_dirs = [base_dir, empty_dir1, empty_dir2]

        # Should work even with non-existent directories
        templates = manager.list_templates()
        assert "test" in templates

        grouped = manager.list_templates_grouped()
        assert len(grouped) == 1  # Only base_dir exists

    def test_get_template_info_from_specific_directory(self, multi_dir_setup):
        """Test getting template info from a specific directory."""
        manager = TemplateManager(multi_dir_setup["base"])
        manager.template_dirs = [
            multi_dir_setup["base"],
            multi_dir_setup["project"],
            multi_dir_setup["user"],
        ]

        # Get info from specific directory
        info = manager.get_template_info("shared", multi_dir_setup["project"])
        assert info is not None
        assert info[0] == "shared"
        assert "Shared Project" in info[1]
