"""
Loader — memory-efficient candidate loading from JSONL and JSON files.

Streams JSONL line-by-line, so the loader itself holds only one record at a time.
(Peak process RAM, ~2 GB on the 100K pool, comes from the downstream scored list
in rank.py, not from this loader.)
Also handles JSON array format for sample_candidates.json.
"""

import json
from pathlib import Path


def load_candidates(path_str: str):
    """
    Generator that yields parsed candidate dicts from a file.

    Handles two formats:
      - .jsonl: one JSON object per line (the main dataset)
      - .json:  a JSON array of objects (sample_candidates.json)

    Yields:
        dict: A single candidate record.
    """
    path = Path(path_str)

    if not path.exists():
        raise FileNotFoundError(f"Candidate file not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".jsonl":
        yield from _load_jsonl(path)
    elif suffix == ".json":
        yield from _load_json_array(path)
    else:
        # Try JSONL first (more memory efficient), fall back to JSON array
        try:
            yield from _load_jsonl(path)
        except json.JSONDecodeError:
            yield from _load_json_array(path)


def _load_jsonl(path: Path):
    """Stream a .jsonl file line-by-line."""
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed line {line_num}: {e}")


def _load_json_array(path: Path):
    """Load a JSON array file and yield each element."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data).__name__}")

    yield from data
