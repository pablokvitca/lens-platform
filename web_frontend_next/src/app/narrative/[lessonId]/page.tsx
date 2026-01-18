// web_frontend_next/src/app/narrative/[lessonId]/page.tsx
"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import Link from "next/link";
import NarrativeLesson from "@/views/NarrativeLesson";
import type { NarrativeLesson as NarrativeLessonType } from "@/types/narrative-lesson";

// Hardcoded test lesson for development
const TEST_LESSON: NarrativeLessonType = {
  format: "narrative",
  slug: "narrative-test",
  title: "Test Narrative Lesson",
  sections: [
    {
      type: "article",
      source: "articles/tim-urban-artificial-intelligence-revolution-1.md",
      label: "The AI Revolution",
      segments: [
        {
          type: "text",
          content: `Welcome to this lesson on the AI Revolution.

We'll be reading Tim Urban's famous essay from Wait But Why.
Pay attention to the concept of "Die Progress Units" - it's a
memorable way to think about accelerating change.`,
        },
        {
          type: "article-excerpt",
          from: "What does it feel like to stand here?",
          to: "## The Far Future—Coming Soon",
        },
        {
          type: "text",
          content: `**Reflection question:**

Urban describes bringing someone from 1750 to today. What do you
think would shock them most - and what might they adapt to quickly?`,
        },
        {
          type: "chat",
        },
        {
          type: "article-excerpt",
          from: "## The Far Future—Coming Soon",
          to: "## What Is AI?",
        },
        {
          type: "text",
          content: `Urban introduces the idea of **exponential thinking** vs **linear thinking**.

This is one of the most common mistakes people make when predicting
the future of AI. Let's make sure you understand it.`,
        },
        {
          type: "chat",
        },
      ],
    },
    {
      type: "video",
      videoId: "pYXy-A4siMw",
      label: "AI Explained",
      segments: [
        {
          type: "text",
          content: `Now let's watch a video that covers similar ground with some
additional visual explanations.`,
        },
        {
          type: "video-excerpt",
          from: 0,
          to: 180,
        },
        {
          type: "text",
          content: `**Quick check:** What's the key difference between ANI and AGI?`,
        },
        {
          type: "chat",
        },
        {
          type: "text",
          content: `## Summary

Key takeaways from this lesson:
- Progress is exponential, not linear
- We're currently in the ANI era
- The AGI → ASI transition could be rapid`,
        },
      ],
    },
  ],
};

// TODO: Replace with actual API call
async function fetchNarrativeLesson(
  slug: string,
): Promise<NarrativeLessonType | null> {
  // Return hardcoded test lesson for development
  if (slug === "narrative-test") {
    return TEST_LESSON;
  }
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
          <Link href="/" className="text-blue-600 hover:underline">
            Go home
          </Link>
        </div>
      </div>
    );
  }

  return <NarrativeLesson lesson={lesson} />;
}
