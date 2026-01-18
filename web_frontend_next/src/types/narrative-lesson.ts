// web_frontend_next/src/types/narrative-lesson.ts

/**
 * Types for NarrativeLesson format.
 *
 * Key difference from unified-lesson: segments within a section allow
 * interleaving of text, content excerpts, and chat.
 *
 * The API bundles all content (article excerpts, video transcripts) directly
 * in the response - no separate fetching needed.
 */

// Segment types within a section
export type TextSegment = {
  type: "text";
  content: string; // Markdown content (authored)
};

export type ArticleExcerptSegment = {
  type: "article-excerpt";
  content: string; // Pre-extracted content from API
};

export type VideoExcerptSegment = {
  type: "video-excerpt";
  from: number; // seconds
  to: number; // seconds
  transcript: string; // Transcript text from API
};

export type ChatSegment = {
  type: "chat";
  instructions: string;
  showUserPreviousContent: boolean;
  showTutorPreviousContent: boolean;
};

export type NarrativeSegment =
  | TextSegment
  | ArticleExcerptSegment
  | VideoExcerptSegment
  | ChatSegment;

// Metadata for article sections
export type ArticleMeta = {
  title: string;
  author: string | null;
  sourceUrl: string | null;
};

// Metadata for video sections
export type VideoMeta = {
  title: string;
  channel: string | null;
};

// Section types (one progress marker each)
export type NarrativeTextSection = {
  type: "text";
  content: string;
};

export type NarrativeArticleSection = {
  type: "article";
  meta: ArticleMeta;
  segments: NarrativeSegment[];
};

export type NarrativeVideoSection = {
  type: "video";
  videoId: string;
  meta: VideoMeta;
  segments: NarrativeSegment[];
};

export type NarrativeSection =
  | NarrativeTextSection
  | NarrativeArticleSection
  | NarrativeVideoSection;

// Full lesson definition
export type NarrativeLesson = {
  slug: string;
  title: string;
  sections: NarrativeSection[];
};
