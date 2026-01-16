"use client";

import { useParams } from "next/navigation";
import UnifiedLesson from "@/views/UnifiedLesson";

export default function LegacyLessonPage() {
  const params = useParams();
  const lessonId = (params?.lessonId as string) ?? "";

  if (!lessonId) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return <UnifiedLesson lessonSlug={lessonId} />;
}
