#!/usr/bin/env python3
"""Generate expected.json for golden test fixtures using Python parser/flattener.

This script processes golden fixture input directories and generates the expected
JSON output that the TypeScript processor must match.

Usage:
    python scripts/generate_golden_expected.py [fixture_name]

    # Generate for all golden fixtures:
    python scripts/generate_golden_expected.py

    # Generate for specific fixture:
    python scripts/generate_golden_expected.py actual-content
"""

import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.cache import ContentCache, set_cache
from core.modules.markdown_parser import (
    parse_module,
    parse_course,
    parse_learning_outcome,
    parse_lens,
    ParsedLearningOutcome,
    ParsedLens,
)
from core.modules.flattener import flatten_module, ContentLookup
from core.modules.flattened_types import FlattenedModule


FIXTURES_DIR = Path(__file__).parent.parent / "content_processor" / "fixtures" / "golden"


class FixtureContentLookup(ContentLookup):
    """ContentLookup implementation that reads from fixture files."""

    def __init__(self, cache: ContentCache):
        self.cache = cache

    def get_learning_outcome(self, key: str) -> ParsedLearningOutcome:
        if key not in self.cache.parsed_learning_outcomes:
            raise KeyError(f"Learning Outcome not found: {key}")
        return self.cache.parsed_learning_outcomes[key]

    def get_lens(self, key: str) -> ParsedLens:
        if key not in self.cache.parsed_lenses:
            raise KeyError(f"Lens not found: {key}")
        return self.cache.parsed_lenses[key]


def load_fixture_files(input_dir: Path) -> dict[str, str]:
    """Load all .md files from input directory."""
    files = {}
    for md_file in input_dir.rglob("*.md"):
        rel_path = md_file.relative_to(input_dir)
        files[str(rel_path)] = md_file.read_text(encoding="utf-8")
    return files


def load_timestamp_files(input_dir: Path) -> dict[str, list[dict]]:
    """Load all .timestamps.json files."""
    timestamps = {}
    for ts_file in input_dir.rglob("*.timestamps.json"):
        # Extract video ID from filename (e.g., "kurzgesagt-ai-humanitys-final-invention")
        video_id = ts_file.stem.replace(".timestamps", "")
        timestamps[video_id] = json.loads(ts_file.read_text(encoding="utf-8"))
    return timestamps


def build_cache_from_fixture(input_dir: Path) -> ContentCache:
    """Build a ContentCache from fixture input files."""
    files = load_fixture_files(input_dir)
    timestamps = load_timestamp_files(input_dir)

    courses = {}
    parsed_learning_outcomes = {}
    parsed_lenses = {}
    articles = {}
    video_transcripts = {}

    for rel_path, content in files.items():
        path = Path(rel_path)
        stem = path.stem

        if rel_path.startswith("courses/"):
            parsed = parse_course(content)
            courses[parsed.slug] = parsed

        elif rel_path.startswith("Learning Outcomes/"):
            parsed = parse_learning_outcome(content)
            parsed_learning_outcomes[stem] = parsed

        elif rel_path.startswith("Lenses/"):
            parsed = parse_lens(content)
            parsed_lenses[stem] = parsed

        elif rel_path.startswith("articles/"):
            articles[rel_path] = content

        elif rel_path.startswith("video_transcripts/"):
            video_transcripts[rel_path] = content

    return ContentCache(
        courses=courses,
        flattened_modules={},  # Will be populated by flattener
        parsed_learning_outcomes=parsed_learning_outcomes,
        parsed_lenses=parsed_lenses,
        articles=articles,
        video_transcripts=video_transcripts,
        last_refreshed=datetime.now(),
        video_timestamps=timestamps,
    )


def flatten_modules_from_fixture(input_dir: Path, cache: ContentCache) -> dict[str, FlattenedModule]:
    """Parse and flatten all modules in the fixture."""
    files = load_fixture_files(input_dir)
    lookup = FixtureContentLookup(cache)
    flattened = {}

    for rel_path, content in files.items():
        if rel_path.startswith("modules/"):
            try:
                parsed = parse_module(content)
                flat = flatten_module(parsed, lookup)
                flattened[parsed.slug] = flat
            except Exception as e:
                # Store error in module
                parsed = parse_module(content)
                error_msg = str(e)
                if len(error_msg) > 1000:
                    error_msg = error_msg[:1000] + "..."
                flattened[parsed.slug] = FlattenedModule(
                    slug=parsed.slug,
                    title=parsed.title,
                    content_id=parsed.content_id,
                    sections=[],
                    error=error_msg,
                )

    return flattened


def serialize_for_json(obj):
    """Custom JSON serializer for dataclasses and UUIDs."""
    if isinstance(obj, UUID):
        return str(obj)
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def generate_expected_json(fixture_name: str) -> dict:
    """Generate expected.json for a golden fixture."""
    fixture_dir = FIXTURES_DIR / fixture_name
    input_dir = fixture_dir / "input"

    if not input_dir.exists():
        raise FileNotFoundError(f"Fixture input directory not found: {input_dir}")

    print(f"Processing fixture: {fixture_name}")
    print(f"  Input dir: {input_dir}")

    # Build cache from fixture files
    cache = build_cache_from_fixture(input_dir)
    set_cache(cache)

    print(f"  Loaded: {len(cache.courses)} courses, "
          f"{len(cache.parsed_learning_outcomes)} LOs, "
          f"{len(cache.parsed_lenses)} lenses, "
          f"{len(cache.articles)} articles, "
          f"{len(cache.video_transcripts)} video transcripts")

    # Flatten modules
    flattened_modules = flatten_modules_from_fixture(input_dir, cache)

    print(f"  Flattened: {len(flattened_modules)} modules")

    # Build result structure matching TypeScript ProcessResult
    result = {
        "modules": [],
        "courses": [],
        "errors": [],
    }

    # Add flattened modules
    for slug, module in flattened_modules.items():
        module_dict = {
            "slug": module.slug,
            "title": module.title,
            "contentId": str(module.content_id) if module.content_id else None,
            "sections": module.sections,
        }
        if module.error:
            module_dict["error"] = module.error
        result["modules"].append(module_dict)

    # Add courses
    for slug, course in cache.courses.items():
        course_dict = {
            "slug": course.slug,
            "title": course.title,
            "progression": [],
        }
        for item in course.progression:
            if hasattr(item, "path"):  # ModuleRef
                course_dict["progression"].append({
                    "type": "module",
                    "path": item.path,
                    "optional": item.optional,
                })
            else:  # MeetingMarker
                course_dict["progression"].append({
                    "type": "meeting",
                    "number": item.number,
                })
        result["courses"].append(course_dict)

    return result


def main():
    if len(sys.argv) > 1:
        # Process specific fixture
        fixture_names = [sys.argv[1]]
    else:
        # Process all golden fixtures
        fixture_names = [d.name for d in FIXTURES_DIR.iterdir() if d.is_dir()]

    for fixture_name in fixture_names:
        try:
            result = generate_expected_json(fixture_name)

            # Write expected.json
            output_path = FIXTURES_DIR / fixture_name / "expected.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=serialize_for_json)

            print(f"  Written: {output_path}")
            print()

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()


if __name__ == "__main__":
    main()
