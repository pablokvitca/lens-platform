// web_frontend_next/src/app/narrative/[lessonId]/page.tsx
"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import NarrativeLesson from "@/views/NarrativeLesson";
import type { NarrativeLesson as NarrativeLessonType } from "@/types/narrative-lesson";

// TODO: Replace with actual API call
async function fetchNarrativeLesson(
  slug: string,
): Promise<NarrativeLessonType | null> {
  // Placeholder - will need API endpoint
  console.log("Fetching narrative lesson:", slug);
  return null;
}

export default function NarrativeLessonPage() {
  const params = useParams();
  const lessonId = (params?.lessonId as string) ?? "";

  const [lesson, setLesson] = useState<NarrativeLessonType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!lessonId) return;

    async function load() {
      try {
        const data = await fetchNarrativeLesson(lessonId);
        setLesson(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load lesson");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [lessonId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading lesson...</p>
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error ?? "Lesson not found"}</p>
          <a href="/" className="text-blue-600 hover:underline">
            Go home
          </a>
        </div>
      </div>
    );
  }

  return <NarrativeLesson lesson={lesson} />;
}
