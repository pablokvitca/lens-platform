# core/lessons/tests/test_courses.py
"""Tests for course loader."""

import pytest
from core.lessons.course_loader import (
    load_course,
    get_next_lesson,
    get_all_lesson_ids,
    CourseNotFoundError,
)


def test_load_existing_course():
    """Should load a course from YAML file."""
    course = load_course("default")
    assert course.id == "default"
    assert course.title == "AI Safety Fundamentals"
    assert len(course.modules) > 0
    assert len(course.modules[0].lessons) > 0


def test_load_nonexistent_course():
    """Should raise CourseNotFoundError for unknown course."""
    with pytest.raises(CourseNotFoundError):
        load_course("nonexistent-course")


def test_get_next_lesson_within_module():
    """Should return next lesson in same module."""
    result = get_next_lesson("default", "intro-to-ai-safety")
    assert result is not None
    assert result.lesson_id == "intelligence-feedback-loop"


def test_get_next_lesson_end_of_course():
    """Should return None at end of course."""
    # Get the last lesson ID
    all_lessons = get_all_lesson_ids("default")
    last_lesson = all_lessons[-1]
    result = get_next_lesson("default", last_lesson)
    assert result is None


def test_get_next_lesson_unknown_lesson():
    """Should return None for lesson not in course."""
    result = get_next_lesson("default", "nonexistent-lesson")
    assert result is None


def test_get_all_lesson_ids():
    """Should return flat list of all lesson IDs in order."""
    lesson_ids = get_all_lesson_ids("default")
    assert isinstance(lesson_ids, list)
    assert "intro-to-ai-safety" in lesson_ids
    assert "intelligence-feedback-loop" in lesson_ids
    # Order should be intro first
    assert lesson_ids.index("intro-to-ai-safety") < lesson_ids.index("intelligence-feedback-loop")


from core.lessons.loader import get_available_lessons, load_lesson


def test_all_lessons_have_unique_ids():
    """All lesson YAML files should have unique IDs."""
    lesson_files = get_available_lessons()
    ids_seen = {}

    for lesson_file in lesson_files:
        lesson = load_lesson(lesson_file)
        if lesson.id in ids_seen:
            pytest.fail(
                f"Duplicate lesson ID '{lesson.id}' found in "
                f"'{lesson_file}.yaml' and '{ids_seen[lesson.id]}.yaml'"
            )
        ids_seen[lesson.id] = lesson_file


def test_course_manifest_references_existing_lessons():
    """All lesson IDs in course manifest should exist as files."""
    course = load_course("default")
    available = set(get_available_lessons())

    for module in course.modules:
        for lesson_id in module.lessons:
            if lesson_id not in available:
                pytest.fail(
                    f"Course 'default' references non-existent lesson: '{lesson_id}' "
                    f"in module '{module.id}'"
                )
