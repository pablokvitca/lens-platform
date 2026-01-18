// web_frontend_next/src/components/narrative-lesson/ProgressSidebar.tsx
"use client";

import { StageIcon } from "@/components/unified-lesson/StageProgressBar";
import type { NarrativeSection } from "@/types/narrative-lesson";

/**
 * Derive a human-readable label for a section.
 * - Text sections: "Section N"
 * - Article/Video sections: use meta.title or fallback to "article N" / "video N"
 */
function getSectionLabel(section: NarrativeSection, index: number): string {
  if (section.type === "text") {
    return `Section ${index + 1}`;
  }
  return section.meta.title || `${section.type} ${index + 1}`;
}

type ProgressSidebarProps = {
  sections: NarrativeSection[];
  currentSectionIndex: number;
  /** Progress through current section (0-1) */
  scrollProgress: number;
  onSectionClick: (index: number) => void;
};

/**
 * Vertical progress sidebar showing article/video icons.
 * Fixed to left edge, shows progress through lesson.
 */
export default function ProgressSidebar({
  sections,
  currentSectionIndex,
  scrollProgress,
  onSectionClick,
}: ProgressSidebarProps) {
  return (
    <div className="fixed left-4 top-1/2 -translate-y-1/2 z-40 flex flex-col items-center">
      {sections.map((section, index) => {
        const isCompleted = index < currentSectionIndex;
        const isCurrent = index === currentSectionIndex;
        const isFuture = index > currentSectionIndex;

        return (
          <div key={index} className="flex flex-col items-center">
            {/* Connector line (except before first) */}
            {index > 0 && (
              <div
                className="w-0.5 h-6"
                style={{
                  backgroundColor:
                    isCompleted || isCurrent ? "#3b82f6" : "#d1d5db",
                  // Partial fill for current section
                  ...(isCurrent && index > 0
                    ? {
                        background: `linear-gradient(to bottom, #3b82f6 ${scrollProgress * 100}%, #d1d5db ${scrollProgress * 100}%)`,
                      }
                    : {}),
                }}
              />
            )}

            {/* Section icon */}
            <button
              onClick={() => onSectionClick(index)}
              className={`
                w-10 h-10 rounded-full flex items-center justify-center
                transition-all duration-150
                ${
                  isCompleted
                    ? "bg-blue-500 text-white"
                    : isCurrent
                      ? "bg-blue-500 text-white ring-2 ring-offset-2 ring-blue-500"
                      : "bg-gray-200 text-gray-500"
                }
                ${isFuture ? "opacity-50" : ""}
                hover:scale-110
              `}
              title={getSectionLabel(section, index)}
            >
              <StageIcon type={section.type} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
