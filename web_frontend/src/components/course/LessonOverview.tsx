/**
 * Vertical stage list with progress line.
 * Reused in course overview main panel and in-player drawer.
 */

import type { StageInfo, LessonStatus } from "../../types/course";
import { StageIcon } from "../unified-lesson/StageProgressBar";

type LessonOverviewProps = {
  lessonTitle: string;
  stages: StageInfo[];
  status: LessonStatus;
  currentStageIndex: number | null;
  onStageClick?: (index: number) => void;
  onStartLesson?: () => void;
  showActions?: boolean;
};

export default function LessonOverview({
  lessonTitle,
  stages,
  status,
  currentStageIndex,
  onStageClick,
  onStartLesson,
  showActions = true,
}: LessonOverviewProps) {
  const effectiveCurrentIndex = currentStageIndex ?? -1;

  const getStageState = (index: number) => {
    if (status === "completed") return "completed";
    if (index < effectiveCurrentIndex) return "completed";
    if (index === effectiveCurrentIndex) return "current";
    return "future";
  };

  const getActionLabel = () => {
    if (status === "completed") return "Review Lesson";
    if (status === "in_progress") return "Continue Lesson";
    return "Start Lesson";
  };

  return (
    <div className="flex flex-col h-full">
      {/* Lesson title */}
      <h2 className="text-2xl font-bold text-slate-900 mb-6">{lessonTitle}</h2>

      {/* Stage list */}
      <div className="flex-1 overflow-y-auto">
        <div className="relative">
          {/* Progress line */}
          <div className="absolute left-4 top-4 bottom-4 w-0.5 bg-slate-200" />
          {status !== "not_started" && (
            <div
              className="absolute left-4 top-4 w-0.5 bg-blue-500 transition-all duration-300"
              style={{
                height: status === "completed"
                  ? "calc(100% - 2rem)"
                  : `calc(${((effectiveCurrentIndex + 0.5) / stages.length) * 100}% - 1rem)`,
              }}
            />
          )}

          {/* Stages */}
          <div className="space-y-4">
            {stages.map((stage, index) => {
              const state = getStageState(index);
              const isClickable = onStageClick && stage.type !== "chat";

              return (
                <div
                  key={index}
                  className={`relative flex items-start gap-4 pl-2 ${
                    isClickable ? "cursor-pointer hover:bg-slate-50 rounded-lg p-2 -ml-2" : "p-2 -ml-2"
                  }`}
                  onClick={() => isClickable && onStageClick(index)}
                >
                  {/* Progress dot */}
                  <div
                    className={`relative z-10 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                      state === "completed"
                        ? "bg-blue-500 text-white"
                        : state === "current"
                        ? "bg-blue-500 text-white ring-4 ring-blue-100"
                        : "bg-slate-200 text-slate-400"
                    }`}
                  >
                    {state === "completed" ? (
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-current" />
                    )}
                  </div>

                  {/* Stage info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <StageIcon type={stage.type} small />
                      <span
                        className={`font-medium ${
                          state === "future" ? "text-slate-400" : "text-slate-900"
                        }`}
                      >
                        {stage.title}
                      </span>
                      {stage.optional && (
                        <span className="text-xs text-slate-400 border border-slate-200 rounded px-1">
                          Optional
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-500 mt-0.5">
                      {stage.type === "chat"
                        ? "Discuss with AI tutor"
                        : stage.duration || (stage.type === "article" ? "Article" : "Video")}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Action button */}
      {showActions && onStartLesson && (
        <div className="pt-6 mt-auto border-t border-slate-100">
          <button
            onClick={onStartLesson}
            className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            {getActionLabel()}
          </button>
        </div>
      )}
    </div>
  );
}
