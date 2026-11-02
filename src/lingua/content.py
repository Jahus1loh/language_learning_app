"""Loads lesson JSON files and checks their structure.

A bad file is skipped and reported in `store.errors`, so one typo in a
colleague's JSON never takes the whole app down.
"""
import json
import logging
from pathlib import Path

from flask import current_app

log = logging.getLogger(__name__)

# lesson type -> (name of the item list, keys every item must have)
SCHEMA = {
    "vocabulary": ("cards", {"id", "front", "back"}),
    "reading": ("questions", {"id", "prompt", "options", "answer"}),
}


class ContentStore:
    def __init__(self, folder):
        self.lessons, self.errors = {}, []
        for path in sorted(Path(folder).glob("*.json")):
            try:
                self._add(json.loads(path.read_text(encoding="utf-8")))
            except KeyError as e:
                self._fail(path, f"missing key {e}")
            except ValueError as e:  # includes JSONDecodeError
                self._fail(path, e)

    def _fail(self, path, msg):
        self.errors.append(f"{path.name}: {msg}")
        log.warning("Skipped %s: %s", path.name, msg)

    def _add(self, lesson):
        kind, _, _ = lesson["type"], lesson["id"], lesson["title"]
        if kind not in SCHEMA:
            raise ValueError(f"unknown type '{kind}'")
        field, keys = SCHEMA[kind]
        if not lesson[field]:
            raise ValueError(f"'{field}' is empty")
        for item in lesson[field]:
            missing = keys - item.keys()
            if missing:
                raise ValueError(f"item {item.get('id', '?')} lacks {sorted(missing)}")
        self.lessons[(kind, lesson["id"])] = lesson

    def all(self, kind):
        return [l for (k, _), l in self.lessons.items() if k == kind]

    def get(self, kind, lesson_id):
        return self.lessons.get((kind, lesson_id))


def store():
    return current_app.extensions["store"]
