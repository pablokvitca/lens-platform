# core/modules/tests/test_content.py
"""Tests for content extraction."""

from pathlib import Path
from core.modules.content import extract_article_section, parse_frontmatter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_frontmatter_strips_metadata():
    """Should strip YAML frontmatter and return only body content."""
    fixture_path = FIXTURES_DIR / "test-article.md"
    raw_text = fixture_path.read_text()

    metadata, content = parse_frontmatter(raw_text)

    # Frontmatter should be parsed into metadata
    assert metadata.title == "Test Article"
    assert metadata.author == "Test Author"

    # Content should not contain frontmatter delimiters
    assert "---" not in content
    assert "title:" not in content
    assert "author:" not in content

    # Content should have the body text
    assert "This is the body content" in content
    assert len(content) > 50


def test_extract_section_with_anchors():
    """Should extract text between from/to anchors."""
    full_text = """
    Some intro text here.

    The first claim is that general intelligence exists.
    This is a very important point to understand.
    It relates to instrumental convergence.

    More text after.
    """

    section = extract_article_section(
        full_text, from_text="The first claim is", to_text="instrumental convergence."
    )

    assert "The first claim is" in section
    assert "instrumental convergence." in section
    assert "Some intro text" not in section
    assert "More text after" not in section


def test_extract_section_no_anchors():
    """Should return full text when no anchors specified."""
    full_text = "Complete article content here."
    section = extract_article_section(full_text, None, None)
    assert section == full_text


def test_bundle_narrative_module_includes_optional_field():
    """Should include optional field when bundling article and video sections."""
    from unittest.mock import patch

    from core.modules.content import bundle_narrative_module
    from core.modules.markdown_parser import (
        ArticleSection,
        VideoSection,
        TextSegment,
        ParsedModule,
    )

    class MockMetadata:
        title = "Mock Title"
        author = "Mock Author"
        source_url = "https://example.com"
        channel = "Mock Channel"
        video_id = "abc123"

    class MockResult:
        metadata = MockMetadata()
        content = "Mock content"

    # Create a module with optional and non-optional sections
    module = ParsedModule(
        slug="test-module",
        title="Test Module",
        sections=[
            ArticleSection(
                source="test-article.md",
                segments=[TextSegment(content="Test content")],
                optional=True,
            ),
            VideoSection(
                source="test-video.md",
                segments=[TextSegment(content="Test content")],
                optional=False,
            ),
        ],
    )

    with (
        patch(
            "core.modules.content.load_article_with_metadata", return_value=MockResult()
        ),
        patch(
            "core.modules.content.load_video_transcript_with_metadata",
            return_value=MockResult(),
        ),
    ):
        result = bundle_narrative_module(module)

    # Verify optional field is present and correct
    assert result["sections"][0]["optional"] is True
    assert result["sections"][1]["optional"] is False
