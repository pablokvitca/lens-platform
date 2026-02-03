export interface ProcessResult {
  modules: FlattenedModule[];
  courses: Course[];
  errors: ContentError[];
}

export interface FlattenedModule {
  slug: string;
  title: string;
  contentId: string | null;
  sections: Section[];
  error?: string;
  warnings?: string[];
}

export interface Course {
  slug: string;
  title: string;
  progression: ProgressionItem[];
  error?: string;
}

export interface Section {
  type: 'page' | 'lens-video' | 'lens-article';
  meta: SectionMeta;
  segments: Segment[];
  optional?: boolean;
  contentId?: string;
  learningOutcomeId?: string | null;
  videoId?: string;  // video sections only
}

export interface SectionMeta {
  title?: string;
  author?: string;      // article sections only
  sourceUrl?: string;   // article sections only
  channel?: string;     // video sections only
}

export interface ProgressionItem {
  type: 'module' | 'meeting';
  slug?: string;
  number?: number;
  optional?: boolean;
}

export interface ContentError {
  file: string;
  line?: number;
  message: string;
  suggestion?: string;
  severity: 'error' | 'warning';
}

// Segment types with their specific fields
export interface TextSegment {
  type: 'text';
  content: string;
  optional?: boolean;
}

export interface ChatSegment {
  type: 'chat';
  instructions?: string;
  hidePreviousContentFromUser?: boolean;
  hidePreviousContentFromTutor?: boolean;
  optional?: boolean;
}

export interface ArticleExcerptSegment {
  type: 'article-excerpt';
  content: string;              // Extracted excerpt content
  collapsed_before?: string;    // Content between previous excerpt and this one (snake_case for Python compat)
  collapsed_after?: string;     // Content after this excerpt to end/next excerpt
  optional?: boolean;
}

export interface VideoExcerptSegment {
  type: 'video-excerpt';
  from: number;                 // Start time in seconds
  to: number | null;            // End time in seconds (null = until end)
  transcript: string;           // Extracted transcript content
  optional?: boolean;
}

export type Segment = TextSegment | ChatSegment | ArticleExcerptSegment | VideoExcerptSegment;

export function processContent(files: Map<string, string>): ProcessResult {
  // Stub - will be implemented via TDD
  return {
    modules: [],
    courses: [],
    errors: [],
  };
}
