# core/modules/tests/test_flattener.py
"""Tests for module flattening logic."""

from datetime import datetime
from uuid import UUID

import pytest

from core.content.cache import ContentCache, set_cache, clear_cache
from core.modules.flattener import flatten_module, ContentLookup
from core.modules.markdown_parser import (
    ParsedModule,
    ParsedLearningOutcome,
    ParsedLens,
    PageSection,
    LearningOutcomeRef,
    UncategorizedSection,
    LensRef,
    LensVideoSection,
    LensArticleSection,
    TextSegment,
)


class MockContentLookup(ContentLookup):
    """Mock content lookup for testing."""

    def __init__(
        self,
        learning_outcomes: dict[str, ParsedLearningOutcome] | None = None,
        lenses: dict[str, ParsedLens] | None = None,
    ):
        self._learning_outcomes = learning_outcomes or {}
        self._lenses = lenses or {}

    def get_learning_outcome(self, key: str) -> ParsedLearningOutcome:
        if key not in self._learning_outcomes:
            raise KeyError(f"Learning outcome not found: {key}")
        return self._learning_outcomes[key]

    def get_lens(self, key: str) -> ParsedLens:
        if key not in self._lenses:
            raise KeyError(f"Lens not found: {key}")
        return self._lenses[key]


@pytest.fixture(autouse=True)
def setup_cache():
    """Set up a minimal cache for bundling functions."""
    cache = ContentCache(
        courses={},
        flattened_modules={},
        parsed_learning_outcomes={},
        parsed_lenses={},
        articles={
            "articles/background.md": """---
title: Background
author: Jane
sourceUrl: https://example.com
---

# Background

Some background content here.
"""
        },
        video_transcripts={
            "video_transcripts/kurzgesagt.md": """---
url: https://www.youtube.com/watch?v=abc123
channel: Kurzgesagt
title: AI Safety Intro
---

00:00 - 01:00
This is the transcript.
"""
        },
        last_refreshed=datetime.now(),
    )
    set_cache(cache)
    yield
    clear_cache()


def test_flatten_module_with_page_section():
    """Page sections pass through with type 'page'."""
    module = ParsedModule(
        slug="intro",
        title="Introduction",
        content_id=UUID("00000000-0000-0000-0000-000000000001"),
        sections=[
            PageSection(
                title="Welcome",
                content_id=UUID("00000000-0000-0000-0000-000000000002"),
                segments=[TextSegment(content="Hello world")],
            ),
        ],
    )

    lookup = MockContentLookup()
    result = flatten_module(module, lookup)

    assert result.slug == "intro"
    assert len(result.sections) == 1
    assert result.sections[0]["type"] == "page"
    assert result.sections[0]["title"] == "Welcome"


def test_flatten_module_expands_learning_outcome():
    """Learning outcome refs are expanded into lens sections."""
    lo = ParsedLearningOutcome(
        content_id=UUID("00000000-0000-0000-0000-000000000010"),
        lenses=[LensRef(source="[[../Lenses/Video Lens]]", optional=False)],
    )

    lens = ParsedLens(
        content_id=UUID("00000000-0000-0000-0000-000000000020"),
        sections=[
            LensVideoSection(
                title="AI Safety Intro",
                source="[[../video_transcripts/kurzgesagt]]",
                segments=[],
            ),
        ],
    )

    module = ParsedModule(
        slug="intro",
        title="Introduction",
        content_id=UUID("00000000-0000-0000-0000-000000000001"),
        sections=[
            LearningOutcomeRef(
                source="[[../Learning Outcomes/AI Risks]]", optional=False
            ),
        ],
    )

    lookup = MockContentLookup(
        learning_outcomes={"AI Risks": lo},
        lenses={"Video Lens": lens},
    )

    result = flatten_module(module, lookup)

    assert len(result.sections) == 1
    assert result.sections[0]["type"] == "video"
    assert result.sections[0]["learningOutcomeId"] == str(
        UUID("00000000-0000-0000-0000-000000000010")
    )
    assert result.sections[0]["videoId"] == "abc123"


def test_flatten_module_expands_uncategorized():
    """Uncategorized sections expand lenses with learning_outcome_id=None."""
    lens = ParsedLens(
        content_id=UUID("00000000-0000-0000-0000-000000000020"),
        sections=[
            LensArticleSection(
                title="Background Reading",
                source="[[../articles/background]]",
                segments=[],
            ),
        ],
    )

    module = ParsedModule(
        slug="intro",
        title="Introduction",
        content_id=UUID("00000000-0000-0000-0000-000000000001"),
        sections=[
            UncategorizedSection(
                lenses=[LensRef(source="[[../Lenses/Background]]", optional=True)],
            ),
        ],
    )

    lookup = MockContentLookup(
        lenses={"Background": lens},
    )

    result = flatten_module(module, lookup)

    assert len(result.sections) == 1
    assert result.sections[0]["type"] == "article"
    assert result.sections[0]["learningOutcomeId"] is None  # Uncategorized
    assert result.sections[0]["optional"] is True


def test_flatten_module_fails_on_missing_reference():
    """Missing references raise KeyError (fail fast)."""
    module = ParsedModule(
        slug="intro",
        title="Introduction",
        content_id=UUID("00000000-0000-0000-0000-000000000001"),
        sections=[
            LearningOutcomeRef(
                source="[[../Learning Outcomes/Missing]]", optional=False
            ),
        ],
    )

    lookup = MockContentLookup()  # Empty

    with pytest.raises(KeyError, match="Learning outcome not found"):
        flatten_module(module, lookup)
