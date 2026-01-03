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
