// web_frontend_next/src/types/index.ts
// Re-export all types for cleaner imports

// Unified lesson types
export type {
  ArticleStage,
  VideoStage,
  ChatStage,
  Stage,
  Lesson,
  ChatMessage,
  PendingMessage,
  PreviousStageInfo,
  ArticleMetadata,
  ArticleData,
  SessionState,
} from "./unified-lesson";

// Narrative lesson types
export type {
  TextSegment,
  ArticleExcerptSegment,
  VideoExcerptSegment,
  ChatSegment,
  NarrativeSegment,
  ArticleMeta,
  VideoMeta,
  NarrativeTextSection,
  NarrativeArticleSection,
  NarrativeVideoSection,
  NarrativeSection,
  NarrativeLesson,
} from "./narrative-lesson";

// Course types
export * from "./course";

// Facilitator types
export * from "./facilitator";

// Signup types
export * from "./signup";
