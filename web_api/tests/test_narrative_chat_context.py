"""Tests for get_narrative_chat_context function."""

from dataclasses import dataclass

# IMPORTANT: Use markdown_parser types for narrative modules, not core.modules.types
from core.modules.markdown_parser import (
    ArticleSection,
    TextSegment,
    ChatSegment,
)


class TestGetNarrativeChatContext:
    """Tests for get_narrative_chat_context accumulation logic."""

    def test_text_segment_included_in_context(self):
        """TextSegment content should be included in LLM context."""
        from web_api.routes.modules import get_narrative_chat_context

        # Create a mock module with text -> chat structure
        @dataclass
        class MockModule:
            sections: list

        section = ArticleSection(
            type="article",
            source="articles/test.md",
            segments=[
                TextSegment(type="text", content="This is important context."),
                ChatSegment(
                    type="chat",
                    instructions="Discuss the text.",
                    show_user_previous_content=True,
                    show_tutor_previous_content=True,
                ),
            ],
        )
        module = MockModule(sections=[section])

        instructions, previous_content = get_narrative_chat_context(
            module, section_index=0, segment_index=1
        )

        assert instructions == "Discuss the text."
        assert previous_content is not None
        assert "This is important context." in previous_content

    def test_multiple_segments_accumulated_in_order(self):
        """Multiple segments should be accumulated earliest-to-latest."""
        from web_api.routes.modules import get_narrative_chat_context

        @dataclass
        class MockModule:
            sections: list

        section = ArticleSection(
            type="article",
            source="articles/test.md",
            segments=[
                TextSegment(type="text", content="First segment."),
                TextSegment(type="text", content="Second segment."),
                TextSegment(type="text", content="Third segment."),
                ChatSegment(
                    type="chat",
                    instructions="Discuss all.",
                    show_user_previous_content=True,
                    show_tutor_previous_content=True,
                ),
            ],
        )
        module = MockModule(sections=[section])

        instructions, previous_content = get_narrative_chat_context(
            module, section_index=0, segment_index=3
        )

        assert previous_content is not None
        # Check order: first should appear before second, second before third
        first_pos = previous_content.find("First segment.")
        second_pos = previous_content.find("Second segment.")
        third_pos = previous_content.find("Third segment.")
        assert first_pos < second_pos < third_pos

    def test_last_segment_marked_specially(self):
        """The last segment should be marked as 'read last'."""
        from web_api.routes.modules import get_narrative_chat_context

        @dataclass
        class MockModule:
            sections: list

        section = ArticleSection(
            type="article",
            source="articles/test.md",
            segments=[
                TextSegment(type="text", content="Earlier content."),
                TextSegment(type="text", content="Most recent content."),
                ChatSegment(
                    type="chat",
                    instructions="Discuss.",
                    show_user_previous_content=True,
                    show_tutor_previous_content=True,
                ),
            ],
        )
        module = MockModule(sections=[section])

        instructions, previous_content = get_narrative_chat_context(
            module, section_index=0, segment_index=2
        )

        assert previous_content is not None
        # Last segment should have special marker
        assert (
            "read last" in previous_content.lower()
            or "most recent" in previous_content.lower()
        )
