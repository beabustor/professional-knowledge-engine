"""Offline intake of explicitly selected professional notes.

Manual notes are user-supplied, NOT verified ChatGPT export evidence.
No model invocation or automatic competency certification occurs here.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .storage import initialize

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ITEMS = 100
MAX_TEXT = 12000
KINDS = {'experience', 'training', 'knowledge', 'project', 'interview', 'correction', 'other'}

SCHEMA = """
CREATE TABLE IF NOT EXISTS manual_intake (
 id INTEGER PRIMARY KEY,
 digest TEXT NOT NULL UNIQUE,
 kind TEXT NOT NULL,
 text TEXT NOT NULL,
 context TEXT,
 origin_label TEXT NOT NULL,
 provenance_status TEXT NOT NULL DEFAULT 'self_reported'
  CHECK(provenance_status = 'self_reported'),
 review_status TEXT NOT NULL DEFAULT 'pending'
  CHECK(review_status = 'pending'),
 recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def _validate(item: object) -> dict:
    if not isinstance(item, dict) or set(item) - {'kind', 'text', 'context', 'origin_label'}:
        raise ValueError('Invalid item fields')
    kind, body, origin = item.get('kind'), item.get('text'), item.get('origin_label')
    context = item.get('context', '')
    if kind not in KINDS:
        raise ValueError('Invalid kind')
    if not isinstance(body, str) or not body.strip() or len(body) > MAX_TEXT:
        raise ValueError('Invalid text')
    if not isinstance(origin, str) or not origin.strip() or len(origin) > 300:
        raise ValueError('Invalid origin_label')
    if not isinstance(context, str) or len(context) > 2000:
        raise ValueError('Invalid context')
    return {'kind': kind, 'text': body.strip(), 'context': context.strip(),
            'origin_label': origin.strip()}


def import_manual_json(file_path: Path, repo_root: Path) -> dict:
    """Import a versioned JSON document transactionally and idempotently.

    Deduplication is based on exact normalized record content; no fuzzy merging.
    The source label is descriptive, not cryptographically authenticated.
    """
    path = Path(file_path).expanduser().resolve(strict=True)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError('Manual intake file too large')
    document = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(document, dict) or set(document) != {'format', 'items'} or document['format'] != 'pke-manual-v1':
        raise ValueError('Unsupported manual intake format')
    items = document['items']
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_ITEMS:
        raise ValueError('Invalid item count')
    validated = [_validate(item) for item in items]  # Reject whole file before writes.
    db_path = initialize(repo_root)
    inserted = 0
    with sqlite3.connect(db_path) as db:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute(SCHEMA)
        with db:
            for item in validated:
                payload = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
                digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
                cursor = db.execute(
                    'INSERT OR IGNORE INTO manual_intake(digest,kind,text,context,origin_label) VALUES (?,?,?,?,?)',
                    (digest, item['kind'], item['text'], item['context'], item['origin_label']))
                inserted += cursor.rowcount
    return {'total': len(items), 'inserted': inserted, 'duplicates': len(items) - inserted,
            'provenance_status': 'self_reported', 'review_status': 'pending'}


def list_manual_items(db_path: Path) -> list[dict]:
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            'SELECT id,kind,text,context,origin_label,provenance_status,review_status,recorded_at '
            'FROM manual_intake ORDER BY id')]
