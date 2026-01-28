# core/modules/flattener.py
"""Flatten parsed modules by resolving Learning Outcome and Lens references."""

from abc import ABC, abstractmethod
from uuid import UUID

from core.modules.markdown_parser import (
    ParsedModule,
    ParsedLearningOutcome,
    ParsedLens,
    PageSection,
    LearningOutcomeRef,
    UncategorizedSection,
    LensVideoSection,
    LensArticleSection,
    TextSegment,
    ChatSegment,
    VideoExcerptSegment,
    ArticleExcerptSegment,
    LensSegment,
)
from core.modules.flattened_types import (
    FlattenedModule,
    FlatSection,
    FlatPageSection,
    FlatLensVideoSection,
    FlatLensArticleSection,
)
from core.modules.path_resolver import resolve_wiki_link


class ContentLookup(ABC):
    """Abstract interface for looking up content by cache key."""

    @abstractmethod
    def get_learning_outcome(self, key: str) -> ParsedLearningOutcome:
        """Get a parsed learning outcome by filename stem."""
        pass

    @abstractmethod
    def get_lens(self, key: str) -> ParsedLens:
        """Get a parsed lens by filename stem."""
        pass

    @abstractmethod
    def get_video_metadata(self, key: str) -> dict:
        """Get video metadata (video_id, channel) by transcript filename stem."""
        pass

    @abstractmethod
    def get_article_metadata(self, key: str) -> dict:
        """Get article metadata (title, author, source_url) by filename stem."""
        pass


def _serialize_segment(
    segment: TextSegment
    | ChatSegment
    | VideoExcerptSegment
    | ArticleExcerptSegment
    | LensSegment,
) -> dict:
    """Serialize a segment to a dictionary for the API response."""
    if hasattr(segment, "content") and segment.type == "text":
        return {"type": "text", "content": segment.content}
    elif segment.type == "chat":
        return {
            "type": "chat",
            "instructions": segment.instructions,
            "hidePreviousContentFromUser": segment.hide_previous_content_from_user,
            "hidePreviousContentFromTutor": segment.hide_previous_content_from_tutor,
        }
    elif segment.type == "video-excerpt":
        return {
            "type": "video-excerpt",
            "from": segment.from_time,
            "to": segment.to_time,
        }
    elif segment.type == "article-excerpt":
        return {
            "type": "article-excerpt",
            "from": segment.from_text,
            "to": segment.to_text,
        }
    return {}


def _flatten_lens(
    lens: ParsedLens,
    learning_outcome_id: UUID | None,
    optional: bool,
    lookup: ContentLookup,
) -> list[FlatSection]:
    """Flatten a lens into one or more flat sections.

    Note: Per design doc, one lens = exactly one video or article.
    We take the first section and raise if there are multiple.
    """
    if len(lens.sections) == 0:
        raise ValueError(f"Lens {lens.content_id} has no sections")
    if len(lens.sections) > 1:
        raise ValueError(
            f"Lens {lens.content_id} has multiple sections (expected exactly 1)"
        )

    section = lens.sections[0]
    segments = [_serialize_segment(s) for s in section.segments]

    if isinstance(section, LensVideoSection):
        # Resolve video source to get metadata
        # section.source may contain wiki-link brackets, use resolve_wiki_link
        _, video_key = resolve_wiki_link(section.source)
        video_meta = lookup.get_video_metadata(video_key)

        return [
            FlatLensVideoSection(
                content_id=lens.content_id,
                learning_outcome_id=learning_outcome_id,
                title=section.title,
                video_id=video_meta.get("video_id", ""),
                channel=video_meta.get("channel"),
                segments=segments,
                optional=optional,
            )
        ]

    elif isinstance(section, LensArticleSection):
        # Resolve article source to get metadata
        # section.source may contain wiki-link brackets, use resolve_wiki_link
        _, article_key = resolve_wiki_link(section.source)
        article_meta = lookup.get_article_metadata(article_key)

        return [
            FlatLensArticleSection(
                content_id=lens.content_id,
                learning_outcome_id=learning_outcome_id,
                title=section.title,
                author=article_meta.get("author"),
                source_url=article_meta.get("source_url"),
                segments=segments,
                optional=optional,
            )
        ]

    return []


def _flatten_learning_outcome(
    lo_ref: LearningOutcomeRef,
    lookup: ContentLookup,
) -> list[FlatSection]:
    """Flatten a learning outcome reference into flat sections."""
    _, lo_key = resolve_wiki_link(lo_ref.source)
    lo = lookup.get_learning_outcome(lo_key)

    sections = []
    for lens_ref in lo.lenses:
        _, lens_key = resolve_wiki_link(lens_ref.source)
        lens = lookup.get_lens(lens_key)
        sections.extend(
            _flatten_lens(
                lens,
                learning_outcome_id=lo.content_id,
                optional=lens_ref.optional or lo_ref.optional,
                lookup=lookup,
            )
        )

    return sections


def _flatten_uncategorized(
    uncategorized: UncategorizedSection,
    lookup: ContentLookup,
) -> list[FlatSection]:
    """Flatten an uncategorized section into flat sections."""
    sections = []
    for lens_ref in uncategorized.lenses:
        _, lens_key = resolve_wiki_link(lens_ref.source)
        lens = lookup.get_lens(lens_key)
        sections.extend(
            _flatten_lens(
                lens,
                learning_outcome_id=None,  # Uncategorized has no LO
                optional=lens_ref.optional,
                lookup=lookup,
            )
        )

    return sections


def _flatten_page(page: PageSection) -> FlatPageSection:
    """Convert a PageSection to a FlatPageSection."""
    segments = [_serialize_segment(s) for s in page.segments]
    return FlatPageSection(
        content_id=page.content_id,
        title=page.title,
        segments=segments,
    )


def flatten_module(module: ParsedModule, lookup: ContentLookup) -> FlattenedModule:
    """Flatten a parsed module by resolving all references.

    Args:
        module: The parsed module with LearningOutcomeRef and UncategorizedSection
        lookup: Interface for looking up referenced content

    Returns:
        FlattenedModule with all sections resolved to page/lens-video/lens-article

    Raises:
        KeyError: If any referenced content is not found (fail fast)
        ValueError: If a lens has zero or multiple sections
    """
    flat_sections: list[FlatSection] = []

    for section in module.sections:
        if isinstance(section, PageSection):
            flat_sections.append(_flatten_page(section))

        elif isinstance(section, LearningOutcomeRef):
            flat_sections.extend(_flatten_learning_outcome(section, lookup))

        elif isinstance(section, UncategorizedSection):
            flat_sections.extend(_flatten_uncategorized(section, lookup))

        # Skip other section types (Text, Article, Video, Chat - v1 types not supported)

    return FlattenedModule(
        slug=module.slug,
        title=module.title,
        content_id=module.content_id,
        sections=flat_sections,
    )
