"""Tests for content cache."""

import pytest
from datetime import datetime

from core.content.cache import (
    ContentCache,
    get_cache,
    set_cache,
    clear_cache,
    CacheNotInitializedError,
)


class TestContentCache:
    """Test cache operations."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_cache()

    def test_get_cache_raises_when_not_initialized(self):
        """Should raise error when cache not initialized."""
        with pytest.raises(CacheNotInitializedError):
            get_cache()

    def test_set_and_get_cache(self):
        """Should store and retrieve cache."""
        cache = ContentCache(
            courses={},
            modules={},
            articles={},
            video_transcripts={},
            learning_outcomes={},
            lenses={},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)

        retrieved = get_cache()
        assert retrieved is cache

    def test_clear_cache(self):
        """Should clear the cache."""
        cache = ContentCache(
            courses={},
            modules={},
            articles={},
            video_transcripts={},
            learning_outcomes={},
            lenses={},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)
        clear_cache()

        with pytest.raises(CacheNotInitializedError):
            get_cache()

    def test_cache_stores_modules(self):
        """Should store and retrieve modules from cache."""
        from core.modules.markdown_parser import ParsedModule, ChatSection

        test_module = ParsedModule(
            slug="test-module",
            title="Test Module",
            sections=[
                ChatSection(
                    instructions="Test instructions",
                    hide_previous_content_from_user=False,
                    hide_previous_content_from_tutor=False,
                )
            ],
        )

        cache = ContentCache(
            courses={},
            modules={"test-module": test_module},
            articles={},
            video_transcripts={},
            learning_outcomes={},
            lenses={},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)

        retrieved = get_cache()
        assert "test-module" in retrieved.modules
        assert retrieved.modules["test-module"].title == "Test Module"

    def test_cache_stores_articles(self):
        """Should store and retrieve articles from cache."""
        cache = ContentCache(
            courses={},
            modules={},
            articles={"articles/test.md": "# Test Article\n\nSome content."},
            video_transcripts={},
            learning_outcomes={},
            lenses={},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)

        retrieved = get_cache()
        assert "articles/test.md" in retrieved.articles
        assert "# Test Article" in retrieved.articles["articles/test.md"]

    def test_cache_stores_video_transcripts(self):
        """Should store and retrieve video transcripts from cache."""
        cache = ContentCache(
            courses={},
            modules={},
            articles={},
            video_transcripts={"video_transcripts/test.md": "Transcript content"},
            learning_outcomes={},
            lenses={},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)

        retrieved = get_cache()
        assert "video_transcripts/test.md" in retrieved.video_transcripts

    def test_cache_last_refreshed(self):
        """Should track when cache was last refreshed."""
        refresh_time = datetime(2026, 1, 18, 12, 0, 0)
        cache = ContentCache(
            courses={},
            modules={},
            articles={},
            video_transcripts={},
            learning_outcomes={},
            lenses={},
            last_refreshed=refresh_time,
        )
        set_cache(cache)

        retrieved = get_cache()
        assert retrieved.last_refreshed == refresh_time

    def test_cache_stores_learning_outcomes(self):
        """Should store and retrieve learning outcomes from cache."""
        cache = ContentCache(
            courses={},
            modules={},
            articles={},
            video_transcripts={},
            learning_outcomes={
                "learning_outcomes/lo-001.md": "# Learning Outcome 001\n\nContent here."
            },
            lenses={},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)

        retrieved = get_cache()
        assert "learning_outcomes/lo-001.md" in retrieved.learning_outcomes
        assert (
            "# Learning Outcome 001"
            in retrieved.learning_outcomes["learning_outcomes/lo-001.md"]
        )

    def test_cache_stores_lenses(self):
        """Should store and retrieve lenses from cache."""
        cache = ContentCache(
            courses={},
            modules={},
            articles={},
            video_transcripts={},
            learning_outcomes={},
            lenses={"lenses/technical.md": "# Technical Lens\n\nTechnical content."},
            last_refreshed=datetime.now(),
        )
        set_cache(cache)

        retrieved = get_cache()
        assert "lenses/technical.md" in retrieved.lenses
        assert "# Technical Lens" in retrieved.lenses["lenses/technical.md"]
