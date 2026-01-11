"""Message template loading and rendering."""

from pathlib import Path

import yaml


_templates: dict | None = None


def load_templates() -> dict:
    """
    Load message templates from YAML file.

    Caches templates after first load.
    """
    global _templates
    if _templates is not None:
        return _templates

    yaml_path = Path(__file__).parent / "messages.yaml"
    with open(yaml_path) as f:
        _templates = yaml.safe_load(f)

    return _templates


def render_message(template: str, context: dict) -> str:
    """
    Render a message template with context variables.

    Args:
        template: String with {variable} placeholders
        context: Dict of variable names to values

    Returns:
        Rendered string

    Raises:
        KeyError: If a required variable is missing from context
    """
    return template.format(**context)


def get_message(message_type: str, channel: str, context: dict) -> str:
    """
    Get and render a message for a specific type and channel.

    Args:
        message_type: e.g., "welcome", "group_assigned"
        channel: e.g., "email_subject", "email_body", "discord"
        context: Variables to substitute

    Returns:
        Rendered message string
    """
    templates = load_templates()
    template = templates[message_type][channel]
    return render_message(template, context)
