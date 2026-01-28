# web_api/tests/conftest.py
"""Pytest fixtures for web API tests.

Sets up a test cache with realistic course/module data so that API tests
can run without requiring actual content files or GitHub access.
"""

import pytest
from datetime import datetime

from core.content import ContentCache, set_cache, clear_cache
from core.modules.markdown_parser import (
    ParsedCourse,
    ParsedModule,
    ModuleRef,
    MeetingMarker,
    ChatSection,
    VideoSection,
    ArticleSection,
)


@pytest.fixture(autouse=True)
def api_test_cache():
    """Set up a test cache with a 'default' course for API tests.

    This fixture runs automatically for all tests in web_api/tests/.
    It provides a realistic course structure with multiple modules,
    meetings, and both required and optional modules.
    """
    # Create test modules with varied section types
    modules = {
        "introduction": ParsedModule(
            slug="introduction",
            title="Introduction to AI Safety",
            sections=[
                VideoSection(
                    source="video_transcripts/intro-video.md",
                    segments=[],
                ),
                ChatSection(
                    instructions="Discuss what you learned from the introduction video.",
                ),
            ],
        ),
        "core-concepts": ParsedModule(
            slug="core-concepts",
            title="Core Concepts in AI Alignment",
            sections=[
                ArticleSection(
                    source="articles/core-concepts.md",
                    segments=[],
                ),
                ChatSection(
                    instructions="Explain the core concepts in your own words.",
                ),
            ],
        ),
        "advanced-topics": ParsedModule(
            slug="advanced-topics",
            title="Advanced Topics",
            sections=[
                ChatSection(
                    instructions="Deep dive into advanced alignment topics.",
                ),
            ],
        ),
        "supplementary-reading": ParsedModule(
            slug="supplementary-reading",
            title="Supplementary Reading",
            sections=[
                ArticleSection(
                    source="articles/supplementary.md",
                    segments=[],
                    optional=True,
                ),
            ],
        ),
        "final-discussion": ParsedModule(
            slug="final-discussion",
            title="Final Discussion",
            sections=[
                ChatSection(
                    instructions="Synthesize everything you've learned.",
                ),
            ],
        ),
    }

    # Create test course with structure that exercises various test cases:
    # - module -> module (introduction -> core-concepts)
    # - module -> meeting (core-concepts -> Meeting 1)
    # - optional module (supplementary-reading)
    # - end of course (final-discussion)
    courses = {
        "default": ParsedCourse(
            slug="default",
            title="AI Safety Fundamentals",
            progression=[
                ModuleRef(path="modules/introduction"),
                ModuleRef(path="modules/core-concepts"),
                MeetingMarker(number=1),
                ModuleRef(path="modules/advanced-topics"),
                ModuleRef(path="modules/supplementary-reading", optional=True),
                MeetingMarker(number=2),
                ModuleRef(path="modules/final-discussion"),
            ],
        ),
    }

    cache = ContentCache(
        courses=courses,
        modules=modules,
        articles={},
        video_transcripts={},
        learning_outcomes={},
        lenses={},
        last_refreshed=datetime.now(),
    )
    set_cache(cache)

    yield cache

    clear_cache()
