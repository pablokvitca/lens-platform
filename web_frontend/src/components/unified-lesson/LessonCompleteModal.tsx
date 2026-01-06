import { Link } from "react-router-dom";

interface Props {
  isOpen: boolean;
  lessonTitle?: string;
}

export default function LessonCompleteModal({ isOpen, lessonTitle }: Props) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl text-center">
        <div className="text-5xl mb-4">🎉</div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">
          Lesson Complete!
        </h2>
        <p className="text-gray-600 mb-6">
          {lessonTitle ? `You've finished "${lessonTitle}".` : "Great work!"}{" "}
          Ready to continue your AI safety journey?
        </p>
        <div className="flex flex-col gap-3">
          <Link
            to="/signup"
            className="w-full bg-indigo-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-indigo-700 transition-colors"
          >
            Join the Full Course
          </Link>
          <Link
            to="/"
            className="w-full text-gray-600 py-2 px-4 hover:text-gray-800 transition-colors"
          >
            Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
