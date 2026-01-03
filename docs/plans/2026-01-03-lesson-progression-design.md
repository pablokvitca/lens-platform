# Lesson Progression Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** When a user completes a lesson, show a modal prompting them to continue to the next lesson.

**Architecture:** Course manifests define modules containing lessons. New API endpoint resolves next lesson. Frontend shows completion modal with navigation.

**Tech Stack:** Python/FastAPI backend, React/TypeScript frontend, YAML course manifests

---

## Task 1: Course Types

**Files:**
- Modify: `core/lessons/types.py`

**Step 1: Add course dataclasses**

Add to end of `core/lessons/types.py`:

```python
@dataclass
class Module:
    """A module within a course."""
    id: str
    title: str
    lessons: list[str]  # List of lesson IDs


@dataclass
class Course:
    """A complete course definition."""
    id: str
    title: str
    modules: list[Module]


@dataclass
class NextLesson:
    """Information about the next lesson."""
    lesson_id: str
    lesson_title: str
```

**Step 2: Commit**

```bash
jj commit -m "feat: add Course, Module, NextLesson types"
```

---

## Task 2: Course Loader - Failing Tests

**Files:**
- Create: `core/lessons/tests/test_courses.py`

**Step 1: Write failing tests**

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest core/lessons/tests/test_courses.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.lessons.course_loader'"

**Step 3: Commit**

```bash
jj commit -m "test: add failing tests for course loader"
```

---

## Task 3: Course Loader - Implementation

**Files:**
- Create: `core/lessons/course_loader.py`
- Create: `educational_content/courses/default.yaml`

**Step 1: Create course manifest**

```yaml
# educational_content/courses/default.yaml
id: default
title: AI Safety Fundamentals

modules:
  - id: foundations
    title: Foundations
    lessons:
      - intro-to-ai-safety
      - intelligence-feedback-loop
```

**Step 2: Implement course loader**

```python
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
```

**Step 3: Run tests to verify they pass**

Run: `pytest core/lessons/tests/test_courses.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
jj commit -m "feat: implement course loader with manifest"
```

---

## Task 4: Validation Tests - Unique IDs and Manifest Validity

**Files:**
- Modify: `core/lessons/tests/test_courses.py`

**Step 1: Add validation tests**

Append to `core/lessons/tests/test_courses.py`:

```python
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
```

**Step 2: Run tests**

Run: `pytest core/lessons/tests/test_courses.py -v`
Expected: All PASS

**Step 3: Commit**

```bash
jj commit -m "test: add validation for unique lesson IDs and manifest integrity"
```

---

## Task 5: API Endpoint - Failing Test

**Files:**
- Create: `web_api/tests/test_courses_api.py`

**Step 1: Write failing test**

```python
# web_api/tests/test_courses_api.py
"""Tests for course API endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_get_next_lesson():
    """Should return next lesson info."""
    response = client.get("/api/courses/default/next-lesson?current=intro-to-ai-safety")
    assert response.status_code == 200
    data = response.json()
    assert data["nextLessonId"] == "intelligence-feedback-loop"
    assert data["nextLessonTitle"] == "Intelligence Feedback Loop"


def test_get_next_lesson_end_of_course():
    """Should return null at end of course."""
    response = client.get("/api/courses/default/next-lesson?current=intelligence-feedback-loop")
    assert response.status_code == 200
    data = response.json()
    assert data is None


def test_get_next_lesson_invalid_course():
    """Should return 404 for invalid course."""
    response = client.get("/api/courses/nonexistent/next-lesson?current=intro-to-ai-safety")
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `pytest web_api/tests/test_courses_api.py -v`
Expected: FAIL with 404 (endpoint doesn't exist)

**Step 3: Commit**

```bash
jj commit -m "test: add failing tests for course API endpoint"
```

---

## Task 6: API Endpoint - Implementation

**Files:**
- Create: `web_api/routes/courses.py`
- Modify: `main.py` (add route)

**Step 1: Implement endpoint**

```python
# web_api/routes/courses.py
"""Course API routes."""

from fastapi import APIRouter, HTTPException, Query

from core.lessons.course_loader import (
    get_next_lesson,
    CourseNotFoundError,
)

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/{course_id}/next-lesson")
async def get_next_lesson_endpoint(
    course_id: str,
    current: str = Query(..., description="Current lesson ID"),
):
    """Get the next lesson after the current one."""
    try:
        result = get_next_lesson(course_id, current)
    except CourseNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course not found: {course_id}")

    if result is None:
        return None

    return {
        "nextLessonId": result.lesson_id,
        "nextLessonTitle": result.lesson_title,
    }
```

**Step 2: Register route in main.py**

Find the line that includes routes (e.g., `app.include_router(...)`) and add:

```python
from web_api.routes.courses import router as courses_router
app.include_router(courses_router)
```

**Step 3: Run tests**

Run: `pytest web_api/tests/test_courses_api.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
jj commit -m "feat: add /api/courses/{id}/next-lesson endpoint"
```

---

## Task 7: Frontend - Update Routing

**Files:**
- Modify: `web_frontend/src/App.tsx`
- Modify: `web_frontend/src/pages/UnifiedLesson.tsx`

**Step 1: Add course route in App.tsx**

Change the lesson route from:
```tsx
<Route path="/lesson/:lessonId" element={<UnifiedLesson />} />
```

To:
```tsx
<Route path="/lesson/:lessonId" element={<UnifiedLesson />} />
<Route path="/course/:courseId/lesson/:lessonId" element={<UnifiedLesson />} />
```

**Step 2: Update UnifiedLesson to extract courseId**

In `UnifiedLesson.tsx`, update the useParams:

```tsx
const { courseId, lessonId } = useParams<{ courseId?: string; lessonId: string }>();
```

**Step 3: Commit**

```bash
jj commit -m "feat: add /course/:courseId/lesson/:lessonId route"
```

---

## Task 8: Frontend - API Function for Next Lesson

**Files:**
- Modify: `web_frontend/src/api/lessons.ts`

**Step 1: Add getNextLesson function**

Append to `web_frontend/src/api/lessons.ts`:

```typescript
export async function getNextLesson(
  courseId: string,
  currentLessonId: string
): Promise<{ nextLessonId: string; nextLessonTitle: string } | null> {
  const res = await fetch(
    `${API_BASE}/api/courses/${courseId}/next-lesson?current=${currentLessonId}`
  );
  if (!res.ok) throw new Error("Failed to fetch next lesson");
  return res.json();
}
```

**Step 2: Commit**

```bash
jj commit -m "feat: add getNextLesson API function"
```

---

## Task 9: Frontend - Completion Modal Component

**Files:**
- Create: `web_frontend/src/components/unified-lesson/LessonCompleteModal.tsx`

**Step 1: Create modal component**

```tsx
// web_frontend/src/components/unified-lesson/LessonCompleteModal.tsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getNextLesson } from "../../api/lessons";

type Props = {
  courseId: string | undefined;
  lessonId: string;
  isOpen: boolean;
};

export default function LessonCompleteModal({ courseId, lessonId, isOpen }: Props) {
  const navigate = useNavigate();
  const [nextLesson, setNextLesson] = useState<{
    nextLessonId: string;
    nextLessonTitle: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isOpen || !courseId) return;

    setLoading(true);
    getNextLesson(courseId, lessonId)
      .then(setNextLesson)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [isOpen, courseId, lessonId]);

  if (!isOpen) return null;

  const handleContinue = () => {
    if (nextLesson && courseId) {
      navigate(`/course/${courseId}/lesson/${nextLesson.nextLessonId}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          Lesson Complete
        </h2>

        {loading && <p className="text-gray-500">Loading...</p>}

        {error && (
          <p className="text-gray-600">
            Something went wrong. Please try refreshing the page.
          </p>
        )}

        {!loading && !error && !courseId && (
          <p className="text-gray-600">
            More lessons coming soon.
          </p>
        )}

        {!loading && !error && courseId && nextLesson === null && (
          <p className="text-gray-600">
            You've completed the course! More lessons coming soon.
          </p>
        )}

        {!loading && !error && nextLesson && (
          <button
            onClick={handleContinue}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Continue to: {nextLesson.nextLessonTitle}
          </button>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Commit**

```bash
jj commit -m "feat: add LessonCompleteModal component"
```

---

## Task 10: Frontend - Wire Up Modal

**Files:**
- Modify: `web_frontend/src/pages/UnifiedLesson.tsx`

**Step 1: Import modal**

Add import at top:
```tsx
import LessonCompleteModal from "../components/unified-lesson/LessonCompleteModal";
```

**Step 2: Track completion state**

The session already has `completed` field. Add modal visibility based on `session.completed` and `!session.current_stage`.

**Step 3: Add modal to JSX**

Before the closing `</div>` of the main component, add:

```tsx
<LessonCompleteModal
  courseId={courseId}
  lessonId={lessonId!}
  isOpen={session.completed || !session.current_stage}
/>
```

**Step 4: Test manually**

Run: `python main.py --dev`
Navigate to: `http://localhost:5174/course/default/lesson/intro-to-ai-safety`
Complete the lesson and verify modal appears.

**Step 5: Commit**

```bash
jj commit -m "feat: show LessonCompleteModal on lesson completion"
```

---

## Task 11: Update exports

**Files:**
- Modify: `core/lessons/__init__.py`

**Step 1: Export new functions**

Add to `core/lessons/__init__.py`:

```python
from .course_loader import (
    load_course,
    get_next_lesson,
    get_all_lesson_ids,
    CourseNotFoundError,
)
```

**Step 2: Commit**

```bash
jj commit -m "feat: export course loader functions"
```

---

## Summary

After all tasks:
- Course manifest at `educational_content/courses/default.yaml`
- Course types in `core/lessons/types.py`
- Course loader at `core/lessons/course_loader.py`
- API endpoint at `/api/courses/{id}/next-lesson`
- New route `/course/:courseId/lesson/:lessonId`
- Completion modal shows next lesson button
- Tests for unique IDs and manifest validity
