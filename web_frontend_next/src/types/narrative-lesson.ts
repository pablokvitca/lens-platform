// web_frontend_next/src/types/narrative-lesson.ts

/**
 * Types for NarrativeLesson format.
 *
 * Key difference from unified-lesson: segments within a section allow
 * interleaving of text, content excerpts, and chat.
 */

import type { ChatMessage, ArticleData } from "./unified-lesson";

// Segment types within a section
export type TextSegment = {
  type: "text";
  content: string; // Markdown content (authored)
};

export type ArticleExcerptSegment = {
  type: "article-excerpt";
  from: string;
  to: string;
};

export type VideoExcerptSegment = {
  type: "video-excerpt";
  from: number; // seconds
  to: number;   // seconds
};

export type ChatSegment = {
  type: "chat";
};

export type NarrativeSegment =
  | TextSegment
  | ArticleExcerptSegment
  | VideoExcerptSegment
  | ChatSegment;

// Section types (one progress marker each)
export type NarrativeArticleSection = {
  type: "article";
  source: string;
  label: string; // Progress sidebar label
  segments: NarrativeSegment[];
};

export type NarrativeVideoSection = {
  type: "video";
  videoId: string;
  label: string; // Progress sidebar label
  segments: NarrativeSegment[];
};

export type NarrativeSection = NarrativeArticleSection | NarrativeVideoSection;

// Full lesson definition
export type NarrativeLesson = {
  format: "narrative";
  slug: string;
  title: string;
  sections: NarrativeSection[];
};

// Runtime state
export type NarrativeLessonState = {
  lesson: NarrativeLesson;
  messages: ChatMessage[];
  currentSectionIndex: number; // Derived from scroll position
  sessionId: number | null;
  // Article content keyed by source path
  articleContent: Record<string, ArticleData>;
};
