// src/parser/sections.ts
import type { ContentError } from '../index.js';

export interface ParsedSection {
  type: string;
  title: string;
  rawType: string;
  fields: Record<string, string>;
  body: string;
  line: number;
}

export interface SectionsResult {
  sections: ParsedSection[];
  errors: ContentError[];
}

// Valid section types per file type (exported for use by other parsers)
export const MODULE_SECTION_TYPES = new Set(['learning outcome', 'page', 'uncategorized']);
export const LO_SECTION_TYPES = new Set(['lens', 'test']);
// Lens sections: input headers are `### Article:`, `### Video:`, `### Page:`
// Output types are `lens-article`, `lens-video`, `page` (v2 format)
export const LENS_SECTION_TYPES = new Set(['page', 'article', 'video']);

// Map input section names to output types for Lens files
export const LENS_OUTPUT_TYPE: Record<string, string> = {
  'page': 'page',
  'article': 'lens-article',
  'video': 'lens-video',
};

// Header pattern is parameterized by level (1-4)
function makeSectionPattern(level: number): RegExp {
  const hashes = '#'.repeat(level);
  // Match: ^#{level} <type>: <title>$
  // Captures: group 1 = type, group 2 = title
  return new RegExp(`^${hashes}\\s+([^:]+):\\s*(.*)$`, 'i');
}

// Pattern to detect any header at the specified level (for unrecognized header detection)
// Matches: ^#{level} <anything>
function makeAnyHeaderPattern(level: number): RegExp {
  const hashes = '#'.repeat(level);
  // Match any header at this level that has content after the hashes
  return new RegExp(`^${hashes}\\s+(.+)$`, 'i');
}

export function parseSections(
  content: string,
  headerLevel: 1 | 2 | 3 | 4,
  validTypes: Set<string>,
  file: string = ''
): SectionsResult {
  const SECTION_HEADER_PATTERN = makeSectionPattern(headerLevel);
  const ANY_HEADER_PATTERN = makeAnyHeaderPattern(headerLevel);
  const lines = content.split('\n');
  const sections: ParsedSection[] = [];
  const errors: ContentError[] = [];

  let currentSection: ParsedSection | null = null;
  let currentBody: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = i + 1;

    const headerMatch = line.match(SECTION_HEADER_PATTERN);

    if (headerMatch) {
      // Save previous section
      if (currentSection) {
        currentSection.body = currentBody.join('\n');
        const { warnings } = parseFields(currentSection, file);
        errors.push(...warnings);
        sections.push(currentSection);
      }

      const rawType = headerMatch[1].trim();
      const normalizedType = rawType.toLowerCase();
      const title = headerMatch[2].trim();

      if (!validTypes.has(normalizedType)) {
        errors.push({
          file,
          line: lineNum,
          message: `Unknown section type: ${rawType}`,
          suggestion: `Valid types: ${[...validTypes].join(', ')}`,
          severity: 'error',
        });
      }

      currentSection = {
        type: normalizedType.replaceAll(' ', '-'),
        title,
        rawType,
        fields: {},
        body: '',
        line: lineNum,
      };
      currentBody = [];
    } else {
      // Check for unrecognized headers at this level
      const anyHeaderMatch = line.match(ANY_HEADER_PATTERN);
      if (anyHeaderMatch) {
        const headerContent = anyHeaderMatch[1].trim();
        errors.push({
          file,
          line: lineNum,
          message: `Unrecognized header: "${line.trim()}"`,
          suggestion: `Valid section format: ${'#'.repeat(headerLevel)} Type: Title (valid types: ${[...validTypes].join(', ')})`,
          severity: 'error',
        });
      }

      if (currentSection) {
        currentBody.push(line);
      }
    }
  }

  // Don't forget last section
  if (currentSection) {
    currentSection.body = currentBody.join('\n');
    const { warnings } = parseFields(currentSection, file);
    errors.push(...warnings);
    sections.push(currentSection);
  }

  return { sections, errors };
}

const FIELD_PATTERN = /^(\w+)::\s*(.*)$/;

interface ParseFieldsResult {
  warnings: ContentError[];
}

function parseFields(section: ParsedSection, file: string): ParseFieldsResult {
  const lines = section.body.split('\n');
  const warnings: ContentError[] = [];
  const seenFields = new Set<string>();
  let currentField: string | null = null;
  let currentValue: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNum = section.line + i + 1; // +1 because body starts after header

    // Check for sub-header first - starts a new scope for field tracking
    if (line.match(/^#{1,6}\s/)) {
      // Save current field if any
      if (currentField) {
        section.fields[currentField] = currentValue.join('\n').trim();
        currentField = null;
        currentValue = [];
      }
      // Reset seenFields for the new sub-section scope
      seenFields.clear();
      continue;
    }

    const match = line.match(FIELD_PATTERN);

    if (match) {
      // Save previous field if any
      if (currentField) {
        section.fields[currentField] = currentValue.join('\n').trim();
      }

      currentField = match[1];
      const inlineValue = match[2].trim();
      currentValue = inlineValue ? [inlineValue] : [];

      // Check for duplicate field
      if (seenFields.has(currentField)) {
        warnings.push({
          file,
          line: lineNum,
          message: `Duplicate field '${currentField}' (previous value will be overwritten)`,
          suggestion: `Remove the duplicate '${currentField}::' definition`,
          severity: 'warning',
        });
      }
      seenFields.add(currentField);
    } else if (currentField) {
      // Continue multiline value
      currentValue.push(line);
    }
  }

  // Save final field
  if (currentField) {
    section.fields[currentField] = currentValue.join('\n').trim();
  }

  return { warnings };
}
