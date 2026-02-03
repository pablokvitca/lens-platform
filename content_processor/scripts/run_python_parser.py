#!/usr/bin/env python3
"""
Run the Python parser/flattener on a fixture directory and output JSON.

Usage:
    python scripts/run_python_parser.py fixtures/golden/software-demo/input
"""

import json
import sys
import re
from datetime import datetime
from pathlib import Path

# Add the repo root to sys.path so we can import core modules
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from core.content.cache import ContentCache, set_cache, clear_cache
from core.modules.markdown_parser import (
    parse_module,
    parse_course,
    parse_learning_outcome,
    parse_lens,
)
from core.modules.flattener import flatten_module, ContentLookup
from core.modules.path_resolver import extract_filename_stem


class FixtureContentLookup(ContentLookup):
    """Content lookup for fixture files."""

    def __init__(self, learning_outcomes, lenses):
        self._learning_outcomes = learning_outcomes
        self._lenses = lenses

    def get_learning_outcome(self, key):
        if key not in self._learning_outcomes:
            raise KeyError(f"Learning outcome not found: {key}")
        return self._learning_outcomes[key]

    def get_lens(self, key):
        if key not in self._lenses:
            raise KeyError(f"Lens not found: {key}")
        return self._lenses[key]


def extract_video_id_from_url(url: str) -> str:
    """Extract YouTube video ID from a URL."""
    match = re.search(
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)",
        url,
    )
    if match:
        return match.group(1)
    return ""


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from text."""
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        return {}

    metadata = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            metadata[key] = value
    return metadata


def load_fixture(input_dir: Path):
    """Load a fixture directory into the cache format."""
    modules_dir = input_dir / "modules"
    courses_dir = input_dir / "courses"
    lo_dir = input_dir / "Learning Outcomes"
    lenses_dir = input_dir / "Lenses"
    articles_dir = input_dir / "articles"
    transcripts_dir = input_dir / "video_transcripts"

    # Load articles
    articles = {}
    if articles_dir.exists():
        for f in articles_dir.glob("*.md"):
            path = f"articles/{f.name}"
            articles[path] = f.read_text(encoding="utf-8")

    # Load video transcripts and timestamps
    video_transcripts = {}
    video_timestamps = {}
    if transcripts_dir.exists():
        for f in transcripts_dir.glob("*.md"):
            path = f"video_transcripts/{f.name}"
            content = f.read_text(encoding="utf-8")
            video_transcripts[path] = content

            # Check for corresponding .timestamps.json
            timestamps_file = f.with_suffix("").with_suffix(".timestamps.json")
            if timestamps_file.exists():
                timestamps_data = json.loads(timestamps_file.read_text(encoding="utf-8"))
                # Extract video_id from frontmatter
                metadata = parse_frontmatter(content)
                video_id = metadata.get("video_id", "")
                if not video_id and metadata.get("url"):
                    video_id = extract_video_id_from_url(metadata["url"])
                if video_id:
                    video_timestamps[video_id] = timestamps_data
                    print(f"  Loaded timestamps for video {video_id}", file=sys.stderr)

    # Load and parse learning outcomes
    parsed_learning_outcomes = {}
    if lo_dir.exists():
        for f in lo_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                parsed = parse_learning_outcome(content)
                stem = f.stem
                parsed_learning_outcomes[stem] = parsed
            except Exception as e:
                print(f"Warning: Failed to parse LO {f}: {e}", file=sys.stderr)

    # Load and parse lenses
    parsed_lenses = {}
    if lenses_dir.exists():
        for f in lenses_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                parsed = parse_lens(content)
                stem = f.stem
                parsed_lenses[stem] = parsed
            except Exception as e:
                print(f"Warning: Failed to parse lens {f}: {e}", file=sys.stderr)

    # Load and parse modules
    raw_modules = {}
    if modules_dir.exists():
        for f in modules_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                parsed = parse_module(content)
                raw_modules[parsed.slug] = parsed
            except Exception as e:
                print(f"Warning: Failed to parse module {f}: {e}", file=sys.stderr)

    # Load and parse courses
    courses = {}
    if courses_dir.exists():
        for f in courses_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                parsed = parse_course(content)
                courses[parsed.slug] = parsed
            except Exception as e:
                print(f"Warning: Failed to parse course {f}: {e}", file=sys.stderr)

    return {
        "articles": articles,
        "video_transcripts": video_transcripts,
        "video_timestamps": video_timestamps,
        "parsed_learning_outcomes": parsed_learning_outcomes,
        "parsed_lenses": parsed_lenses,
        "raw_modules": raw_modules,
        "courses": courses,
    }


def flatten_modules(fixture_data):
    """Flatten all modules using the fixture data."""
    # Create cache
    cache = ContentCache(
        courses=fixture_data["courses"],
        flattened_modules={},  # Will be populated
        parsed_learning_outcomes=fixture_data["parsed_learning_outcomes"],
        parsed_lenses=fixture_data["parsed_lenses"],
        articles=fixture_data["articles"],
        video_transcripts=fixture_data["video_transcripts"],
        last_refreshed=datetime.now(),
        video_timestamps=fixture_data["video_timestamps"],
    )
    set_cache(cache)

    # Create lookup
    lookup = FixtureContentLookup(
        learning_outcomes=fixture_data["parsed_learning_outcomes"],
        lenses=fixture_data["parsed_lenses"],
    )

    # Flatten modules
    flattened_modules = []
    errors = []
    for slug, module in fixture_data["raw_modules"].items():
        try:
            flattened = flatten_module(module, lookup)
            flattened_modules.append(flattened)
        except Exception as e:
            errors.append({
                "file": f"modules/{slug}.md",
                "message": str(e),
                "severity": "error",
            })

    # Format courses for output
    formatted_courses = []
    for slug, course in fixture_data["courses"].items():
        progression = []
        for item in course.progression:
            if hasattr(item, "path"):  # ModuleRef
                progression.append({
                    "type": "module",
                    "slug": item.path.split("/")[-1],
                    "optional": item.optional,
                })
            elif hasattr(item, "number"):  # MeetingMarker
                progression.append({
                    "type": "meeting",
                    "number": item.number,
                })
        formatted_courses.append({
            "slug": course.slug,
            "title": course.title,
            "progression": progression,
        })

    clear_cache()
    return flattened_modules, formatted_courses, errors


def format_section_for_output(section):
    """Convert a section dict to match TypeScript output format."""
    # The Python flattener already outputs mostly correct format
    # But we need to convert some field names
    if section["type"] == "video":
        # Rename 'type' from 'video' to 'lens-video' to match TS
        section["type"] = "lens-video"
        # Remove videoId from output (not in TS format)
        if "videoId" in section:
            del section["videoId"]
    elif section["type"] == "article":
        # Rename 'type' from 'article' to 'lens-article' to match TS
        section["type"] = "lens-article"
    return section


def format_module_for_output(flattened):
    """Convert FlattenedModule to dict matching TypeScript output format."""
    sections = [format_section_for_output(s) for s in flattened.sections]
    return {
        "slug": flattened.slug,
        "title": flattened.title,
        "contentId": str(flattened.content_id) if flattened.content_id else None,
        "sections": sections,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_python_parser.py <input_dir>", file=sys.stderr)
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    if not input_dir.exists():
        print(f"Error: Directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading fixture from: {input_dir}", file=sys.stderr)
    fixture_data = load_fixture(input_dir)

    print(f"Flattening {len(fixture_data['raw_modules'])} modules...", file=sys.stderr)
    modules, courses, errors = flatten_modules(fixture_data)

    # Format output
    output = {
        "modules": [format_module_for_output(m) for m in modules],
        "courses": courses,
        "errors": errors,
    }

    # Print JSON to stdout
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
