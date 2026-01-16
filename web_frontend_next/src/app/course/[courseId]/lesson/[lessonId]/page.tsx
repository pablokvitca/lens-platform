"use client";

import { useParams } from "next/navigation";
import UnifiedLesson from "@/views/UnifiedLesson";

export default function LessonPage() {
  const params = useParams();
  const courseId = (params?.courseId as string) ?? "default";
  const lessonId = (params?.lessonId as string) ?? "";

  if (!lessonId) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return <UnifiedLesson courseId={courseId} lessonSlug={lessonId} />;
}
