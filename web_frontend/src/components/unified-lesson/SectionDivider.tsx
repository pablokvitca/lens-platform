// web_frontend/src/components/unified-lesson/SectionDivider.tsx
import { StageIcon } from "./StageProgressBar";

type SectionDividerProps = {
  type: "video" | "article" | "chat";
};

export default function SectionDivider({ type }: SectionDividerProps) {
  // Chat stages use the article icon
  const iconType = type === "chat" ? "article" : type;

  return (
    <div className="flex items-center gap-3 px-6 py-4">
      <div className="flex-1 border-t border-gray-300" />
      <div className="flex items-center justify-center w-8 h-8 rounded-full border border-gray-300 bg-white text-gray-500">
        <StageIcon type={iconType} small />
      </div>
      <div className="flex-1 border-t border-gray-300" />
    </div>
  );
}
