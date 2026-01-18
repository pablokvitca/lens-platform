"""
Type definitions for lesson stages and sessions.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ArticleStage:
    """Display a section of a markdown article."""

    type: Literal["article"]
    source: str  # Path to article markdown file
    from_text: str | None = None  # None means full article
    to_text: str | None = None
    optional: bool = False  # Whether this stage can be skipped
    minutes: int | None = (
        None  # Manual override for reading time (auto-calculated if None)
    )
    introduction: str | None = None  # Lens Academy intro note


@dataclass
class VideoStage:
    """Display a YouTube video clip."""

    type: Literal["video"]
    source: str  # Path to transcript markdown file
    from_seconds: int = 0
    to_seconds: int | None = None  # None means to end
    optional: bool = False  # Whether this stage can be skipped
    introduction: str | None = None  # Lens Academy intro note


@dataclass
class ChatStage:
    """Active discussion with AI tutor."""

    type: Literal["chat"]
    instructions: str  # Instructions for the AI tutor
    show_user_previous_content: bool = True  # Show previous article/video to user in UI
    show_tutor_previous_content: bool = (
        True  # Include previous content in tutor's context
    )


Stage = ArticleStage | VideoStage | ChatStage


# --- Narrative Lesson Types ---


@dataclass
class TextSegment:
    """Standalone authored text."""

    type: Literal["text"]
    content: str


@dataclass
class ArticleExcerptSegment:
    """Extract from parent article."""

    type: Literal["article-excerpt"]
    from_text: str
    to_text: str


@dataclass
class VideoExcerptSegment:
    """Extract from parent video."""

    type: Literal["video-excerpt"]
    from_seconds: int
    to_seconds: int


@dataclass
class ChatSegment:
    """Interactive chat within a section."""

    type: Literal["chat"]
    instructions: str
    show_user_previous_content: bool = True
    show_tutor_previous_content: bool = True


NarrativeSegment = (
    TextSegment | ArticleExcerptSegment | VideoExcerptSegment | ChatSegment
)


@dataclass
class TextSection:
    """Standalone text section (no child segments)."""

    type: Literal["text"]
    content: str


@dataclass
class ArticleSection:
    """Article section with segments."""

    type: Literal["article"]
    source: str
    segments: list[NarrativeSegment]


@dataclass
class VideoSection:
    """Video section with segments."""

    type: Literal["video"]
    source: str
    segments: list[NarrativeSegment]


NarrativeSection = TextSection | ArticleSection | VideoSection


@dataclass
class NarrativeLesson:
    """A narrative-format lesson definition."""

    slug: str
    title: str
    sections: list[NarrativeSection]


@dataclass
class Lesson:
    """A complete lesson definition."""

    slug: str
    title: str
    stages: list[Stage]


@dataclass
class LessonRef:
    """Reference to a lesson in a course progression."""

    slug: str
    optional: bool = False


@dataclass
class Meeting:
    """A meeting marker in the course progression."""

    number: int


ProgressionItem = LessonRef | Meeting


@dataclass
class Course:
    """A complete course definition."""

    slug: str
    title: str
    progression: list[ProgressionItem]


@dataclass
class NextLesson:
    """Information about the next lesson."""

    lesson_slug: str
    lesson_title: str


# DEPRECATED: Keep Module for backward compatibility until other code is updated
@dataclass
class Module:
    """A module within a course. DEPRECATED - use progression instead."""

    id: str
    title: str
    lessons: list[str]  # List of lesson slugs
    due_by_meeting: int | None = (
        None  # Which meeting this module should be completed by
    )
