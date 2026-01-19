# core/modules/tests/test_types.py
"""Tests for module types."""

from core.modules.types import ModuleRef, Meeting, Course


def test_module_ref_defaults():
    """ModuleRef should default optional to False."""
    ref = ModuleRef(slug="test-module")
    assert ref.slug == "test-module"
    assert ref.optional is False


def test_module_ref_optional():
    """ModuleRef should accept optional flag."""
    ref = ModuleRef(slug="test-module", optional=True)
    assert ref.optional is True


def test_meeting_number():
    """Meeting should store its number."""
    meeting = Meeting(number=1)
    assert meeting.number == 1


def test_course_with_progression():
    """Course should have progression list."""
    course = Course(
        slug="test",
        title="Test Course",
        progression=[
            ModuleRef(slug="module-1"),
            ModuleRef(slug="module-2", optional=True),
            Meeting(number=1),
        ],
    )
    assert len(course.progression) == 3
