"""Tests for message template loading and rendering."""

import pytest
from core.notifications.templates import load_templates, render_message


class TestLoadTemplates:
    def test_loads_yaml_file(self):
        templates = load_templates()
        assert isinstance(templates, dict)
        assert "welcome" in templates

    def test_welcome_has_required_fields(self):
        templates = load_templates()
        welcome = templates["welcome"]
        assert "email_subject" in welcome
        assert "email_body" in welcome
        assert "discord" in welcome


class TestRenderMessage:
    def test_renders_simple_variable(self):
        result = render_message("Hello {name}!", {"name": "Alice"})
        assert result == "Hello Alice!"

    def test_renders_multiple_variables(self):
        result = render_message(
            "Hi {name}, your group is {group_name}",
            {"name": "Alice", "group_name": "Curious Capybaras"},
        )
        assert result == "Hi Alice, your group is Curious Capybaras"

    def test_missing_variable_raises(self):
        with pytest.raises(KeyError):
            render_message("Hello {name}!", {})
