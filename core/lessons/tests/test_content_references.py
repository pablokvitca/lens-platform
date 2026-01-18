# core/lessons/tests/test_content_references.py
"""Tests that verify all content referenced in lessons actually exists.

These tests catch broken references early - before users encounter missing content.
Supports both staged lessons and narrative lessons.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass

from core.lessons.loader import (
    get_available_lessons,
    load_lesson,
    load_narrative_lesson,
    LESSONS_DIR,
    LessonNotFoundError,
)
from core.lessons.content import CONTENT_DIR
from core.lessons.types import (
    ArticleStage,
    VideoStage,
    ArticleSection,
    VideoSection,
    ArticleExcerptSegment,
    VideoExcerptSegment,
)


@dataclass
class ArticleReference:
    """Unified article reference from either staged or narrative lesson."""

    lesson_slug: str
    location: str  # e.g., "stage:2" or "section:1/segment:3"
    source: str
    from_text: str | None
    to_text: str | None


@dataclass
class VideoReference:
    """Unified video reference from either staged or narrative lesson."""

    lesson_slug: str
    location: str
    source: str
    from_seconds: int
    to_seconds: int | None


def get_all_stages():
    """Get all stages from staged lessons with their lesson context."""
    stages = []
    for lesson_slug in get_available_lessons():
        try:
            lesson = load_lesson(lesson_slug)
            for i, stage in enumerate(lesson.stages):
                stages.append((lesson_slug, i, stage))
        except (LessonNotFoundError, KeyError):
            # Skip narrative lessons (they don't have stages)
            pass
    return stages


def get_article_stages():
    """Get all article stages from staged lessons."""
    return [
        (lesson_slug, stage_idx, stage)
        for lesson_slug, stage_idx, stage in get_all_stages()
        if isinstance(stage, ArticleStage)
    ]


def get_video_stages():
    """Get all video stages from staged lessons."""
    return [
        (lesson_slug, stage_idx, stage)
        for lesson_slug, stage_idx, stage in get_all_stages()
        if isinstance(stage, VideoStage)
    ]


def get_all_article_references() -> list[ArticleReference]:
    """Get all article references from both staged and narrative lessons."""
    refs = []

    for lesson_slug in get_available_lessons():
        # Try staged lesson first
        try:
            lesson = load_lesson(lesson_slug)
            for i, stage in enumerate(lesson.stages):
                if isinstance(stage, ArticleStage):
                    refs.append(
                        ArticleReference(
                            lesson_slug=lesson_slug,
                            location=f"stage:{i}",
                            source=stage.source,
                            from_text=stage.from_text,
                            to_text=stage.to_text,
                        )
                    )
            continue
        except (LessonNotFoundError, KeyError):
            pass

        # Try narrative lesson
        try:
            lesson = load_narrative_lesson(lesson_slug)
            for sec_idx, section in enumerate(lesson.sections):
                if isinstance(section, ArticleSection):
                    # The section itself references the article
                    for seg_idx, segment in enumerate(section.segments):
                        if isinstance(segment, ArticleExcerptSegment):
                            refs.append(
                                ArticleReference(
                                    lesson_slug=lesson_slug,
                                    location=f"section:{sec_idx}/segment:{seg_idx}",
                                    source=section.source,
                                    from_text=segment.from_text,
                                    to_text=segment.to_text,
                                )
                            )
        except (LessonNotFoundError, KeyError):
            pass

    return refs


def get_all_video_references() -> list[VideoReference]:
    """Get all video references from both staged and narrative lessons."""
    refs = []

    for lesson_slug in get_available_lessons():
        # Try staged lesson first
        try:
            lesson = load_lesson(lesson_slug)
            for i, stage in enumerate(lesson.stages):
                if isinstance(stage, VideoStage):
                    refs.append(
                        VideoReference(
                            lesson_slug=lesson_slug,
                            location=f"stage:{i}",
                            source=stage.source,
                            from_seconds=stage.from_seconds,
                            to_seconds=stage.to_seconds,
                        )
                    )
            continue
        except (LessonNotFoundError, KeyError):
            pass

        # Try narrative lesson
        try:
            lesson = load_narrative_lesson(lesson_slug)
            for sec_idx, section in enumerate(lesson.sections):
                if isinstance(section, VideoSection):
                    for seg_idx, segment in enumerate(section.segments):
                        if isinstance(segment, VideoExcerptSegment):
                            refs.append(
                                VideoReference(
                                    lesson_slug=lesson_slug,
                                    location=f"section:{sec_idx}/segment:{seg_idx}",
                                    source=section.source,
                                    from_seconds=segment.from_seconds,
                                    to_seconds=segment.to_seconds,
                                )
                            )
        except (LessonNotFoundError, KeyError):
            pass

    return refs


class TestArticleReferences:
    """Tests for article content references (both staged and narrative lessons)."""

    @pytest.mark.parametrize(
        "ref",
        get_all_article_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_article_file_exists(self, ref: ArticleReference):
        """Every article source in a lesson should point to an existing file."""
        article_path = CONTENT_DIR / ref.source

        assert article_path.exists(), (
            f"Lesson '{ref.lesson_slug}' {ref.location} references missing article: "
            f"'{ref.source}'\n"
            f"Expected file at: {article_path}"
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_article_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_article_from_anchor_exists(self, ref: ArticleReference):
        """If an article has a 'from' anchor, that text should exist in the file (case-insensitive)."""
        if ref.from_text is None:
            pytest.skip("No 'from' anchor specified")

        article_path = CONTENT_DIR / ref.source
        if not article_path.exists():
            pytest.skip("Article file doesn't exist (caught by other test)")

        content = article_path.read_text()

        assert ref.from_text.lower() in content.lower(), (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"'from' anchor text not found in article '{ref.source}'\n"
            f"Looking for: \"{ref.from_text[:80]}...\"\n"
            f"This anchor text doesn't appear in the article content."
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_article_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_article_from_anchor_unique(self, ref: ArticleReference):
        """The 'from' anchor must be unique in the article (case-insensitive)."""
        if ref.from_text is None:
            pytest.skip("No 'from' anchor specified")

        article_path = CONTENT_DIR / ref.source
        if not article_path.exists():
            pytest.skip("Article file doesn't exist (caught by other test)")

        content = article_path.read_text()
        count = content.lower().count(ref.from_text.lower())

        assert count == 1, (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"'from' anchor appears {count} times (case-insensitive) in '{ref.source}'\n"
            f"Anchor: \"{ref.from_text[:80]}...\"\n"
            f"Anchors must be unique to avoid ambiguity."
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_article_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_article_to_anchor_exists(self, ref: ArticleReference):
        """If an article has a 'to' anchor, that text should exist in the file (case-insensitive)."""
        if ref.to_text is None:
            pytest.skip("No 'to' anchor specified")

        article_path = CONTENT_DIR / ref.source
        if not article_path.exists():
            pytest.skip("Article file doesn't exist (caught by other test)")

        content = article_path.read_text()

        assert ref.to_text.lower() in content.lower(), (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"'to' anchor text not found in article '{ref.source}'\n"
            f"Looking for: \"{ref.to_text[:80]}...\"\n"
            f"This anchor text doesn't appear in the article content."
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_article_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_article_to_anchor_unique(self, ref: ArticleReference):
        """The 'to' anchor must be unique in the article (case-insensitive)."""
        if ref.to_text is None:
            pytest.skip("No 'to' anchor specified")

        article_path = CONTENT_DIR / ref.source
        if not article_path.exists():
            pytest.skip("Article file doesn't exist (caught by other test)")

        content = article_path.read_text()
        count = content.lower().count(ref.to_text.lower())

        assert count == 1, (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"'to' anchor appears {count} times (case-insensitive) in '{ref.source}'\n"
            f"Anchor: \"{ref.to_text[:80]}...\"\n"
            f"Anchors must be unique to avoid ambiguity."
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_article_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_article_anchor_order(self, ref: ArticleReference):
        """The 'from' anchor should appear before the 'to' anchor."""
        if ref.from_text is None or ref.to_text is None:
            pytest.skip("Both anchors needed for order test")

        article_path = CONTENT_DIR / ref.source
        if not article_path.exists():
            pytest.skip("Article file doesn't exist (caught by other test)")

        content = article_path.read_text()

        from_idx = content.find(ref.from_text)
        to_idx = content.find(ref.to_text)

        if from_idx == -1 or to_idx == -1:
            pytest.skip("Anchors don't exist (caught by other tests)")

        assert from_idx < to_idx, (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"'from' anchor appears AFTER 'to' anchor in '{ref.source}'\n"
            f"'from' at position {from_idx}, 'to' at position {to_idx}"
        )


class TestVideoReferences:
    """Tests for video transcript references (both staged and narrative lessons)."""

    @pytest.mark.parametrize(
        "ref",
        get_all_video_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_video_transcript_file_exists(self, ref: VideoReference):
        """Every video source in a lesson should point to an existing transcript."""
        transcript_path = CONTENT_DIR / ref.source

        assert transcript_path.exists(), (
            f"Lesson '{ref.lesson_slug}' {ref.location} references missing transcript: "
            f"'{ref.source}'\n"
            f"Expected file at: {transcript_path}"
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_video_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_video_timestamps_file_exists(self, ref: VideoReference):
        """Every video transcript should have a corresponding timestamps JSON file."""
        transcript_path = CONTENT_DIR / ref.source
        if not transcript_path.exists():
            pytest.skip("Transcript file doesn't exist (caught by other test)")

        timestamps_path = transcript_path.with_suffix(".timestamps.json")

        assert timestamps_path.exists(), (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"Missing timestamps file for '{ref.source}'\n"
            f"Expected: {timestamps_path.name}"
        )

    @pytest.mark.parametrize(
        "ref",
        get_all_video_references(),
        ids=lambda r: f"{r.lesson_slug}:{r.location}" if hasattr(r, "lesson_slug") else str(r),
    )
    def test_video_time_range_valid(self, ref: VideoReference):
        """Video from_seconds should be less than to_seconds when both are set."""
        if ref.to_seconds is None:
            pytest.skip("No end time specified")

        assert ref.from_seconds < ref.to_seconds, (
            f"Lesson '{ref.lesson_slug}' {ref.location}: "
            f"Invalid time range: from={ref.from_seconds}s, to={ref.to_seconds}s\n"
            f"Start time must be before end time."
        )


class TestContentDirectoryStructure:
    """Tests for overall content directory structure."""

    def test_articles_directory_exists(self):
        """Articles directory should exist."""
        articles_dir = CONTENT_DIR / "articles"
        assert articles_dir.exists(), f"Articles directory not found: {articles_dir}"

    def test_video_transcripts_directory_exists(self):
        """Video transcripts directory should exist."""
        transcripts_dir = CONTENT_DIR / "video_transcripts"
        assert transcripts_dir.exists(), (
            f"Video transcripts directory not found: {transcripts_dir}"
        )

    def test_lessons_directory_exists(self):
        """Lessons directory should exist."""
        assert LESSONS_DIR.exists(), f"Lessons directory not found: {LESSONS_DIR}"

    def test_at_least_one_lesson_exists(self):
        """Should have at least one lesson defined."""
        lessons = get_available_lessons()
        assert len(lessons) > 0, "No lessons found in lessons directory"

    def test_at_least_one_article_exists(self):
        """Should have at least one article file."""
        articles_dir = CONTENT_DIR / "articles"
        articles = list(articles_dir.glob("*.md")) if articles_dir.exists() else []
        assert len(articles) > 0, "No article files found"

    def test_at_least_one_transcript_exists(self):
        """Should have at least one video transcript file."""
        transcripts_dir = CONTENT_DIR / "video_transcripts"
        transcripts = (
            list(transcripts_dir.glob("*.md")) if transcripts_dir.exists() else []
        )
        assert len(transcripts) > 0, "No video transcript files found"


class TestUnusedContent:
    """Tests to identify potentially unused content files."""

    def test_report_unreferenced_articles(self):
        """Report articles that exist but aren't referenced by any lesson.

        This is a warning, not a failure - unused articles might be intentional.
        """
        articles_dir = CONTENT_DIR / "articles"
        if not articles_dir.exists():
            pytest.skip("Articles directory doesn't exist")

        # Get all article files
        all_articles = {f.name for f in articles_dir.glob("*.md")}

        # Get all referenced articles
        referenced_articles = set()
        for _, _, stage in get_article_stages():
            # Extract filename from source path like "articles/foo.md"
            if stage.source.startswith("articles/"):
                referenced_articles.add(stage.source.replace("articles/", ""))

        unreferenced = all_articles - referenced_articles

        if unreferenced:
            # Just report, don't fail - unreferenced articles might be intentional
            print(f"\nNote: {len(unreferenced)} article(s) not referenced by any lesson:")
            for article in sorted(unreferenced):
                print(f"  - {article}")

    def test_report_unreferenced_transcripts(self):
        """Report video transcripts that exist but aren't referenced by any lesson.

        This is a warning, not a failure - unused transcripts might be intentional.
        """
        transcripts_dir = CONTENT_DIR / "video_transcripts"
        if not transcripts_dir.exists():
            pytest.skip("Video transcripts directory doesn't exist")

        # Get all transcript files
        all_transcripts = {f.name for f in transcripts_dir.glob("*.md")}

        # Get all referenced transcripts
        referenced_transcripts = set()
        for _, _, stage in get_video_stages():
            # Extract filename from source path like "video_transcripts/foo.md"
            if stage.source.startswith("video_transcripts/"):
                referenced_transcripts.add(
                    stage.source.replace("video_transcripts/", "")
                )

        unreferenced = all_transcripts - referenced_transcripts

        if unreferenced:
            # Just report, don't fail - unreferenced transcripts might be intentional
            print(
                f"\nNote: {len(unreferenced)} transcript(s) not referenced by any lesson:"
            )
            for transcript in sorted(unreferenced):
                print(f"  - {transcript}")
