# core/lessons/course_loader.py
"""Load course definitions from YAML files."""

import yaml
from pathlib import Path

from .types import Course, Module, NextLesson
from .loader import load_lesson, LessonNotFoundError


class CourseNotFoundError(Exception):
    """Raised when a course cannot be found."""
    pass


COURSES_DIR = Path(__file__).parent.parent.parent / "educational_content" / "courses"


def load_course(course_id: str) -> Course:
    """Load a course by ID from the courses directory."""
    course_path = COURSES_DIR / f"{course_id}.yaml"

    if not course_path.exists():
        raise CourseNotFoundError(f"Course not found: {course_id}")

    with open(course_path) as f:
        data = yaml.safe_load(f)

    modules = [
        Module(
            id=m["id"],
            title=m["title"],
            lessons=m["lessons"],
        )
        for m in data["modules"]
    ]

    return Course(
        id=data["id"],
        title=data["title"],
        modules=modules,
    )


def get_all_lesson_ids(course_id: str) -> list[str]:
    """Get flat list of all lesson IDs in course order."""
    course = load_course(course_id)
    lesson_ids = []
    for module in course.modules:
        lesson_ids.extend(module.lessons)
    return lesson_ids


def get_next_lesson(course_id: str, current_lesson_id: str) -> NextLesson | None:
    """Get the next lesson after the current one."""
    lesson_ids = get_all_lesson_ids(course_id)

    try:
        current_index = lesson_ids.index(current_lesson_id)
    except ValueError:
        return None  # Lesson not in this course

    next_index = current_index + 1
    if next_index >= len(lesson_ids):
        return None  # End of course

    next_lesson_id = lesson_ids[next_index]

    try:
        next_lesson = load_lesson(next_lesson_id)
        return NextLesson(
            lesson_id=next_lesson_id,
            lesson_title=next_lesson.title,
        )
    except LessonNotFoundError:
        return None
