"""Persist verified text provenance, independently of professional claims or LLMs."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from .provenance import verify_quote

SCHEMA = """
CREATE TABLE IF NOT EXISTS verified_evidence (
 id INTEGER PRIMARY KEY,
 source_id INTEGER NOT NULL REFERENCES sources(id),
 conversation_id TEXT NOT NULL,
 node_id TEXT NOT NULL,
 message_id TEXT NOT NULL,
 part_index INTEGER NOT NULL,
 start_offset INTEGER NOT NULL,
 end_offset INTEGER NOT NULL,
 exact_quote TEXT NOT NULL,
 part_sha256 TEXT NOT NULL,
 source_sha256 TEXT NOT NULL,
 message_role TEXT NOT NULL,
 on_active_path INTEGER NOT NULL CHECK(on_active_path IN (0,1)),
 recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 UNIQUE(source_id, conversation_id, node_id, message_id, part_index, start_offset, end_offset, exact_quote)
);
"""


def record_evidence(db_path: Path, *, conversation_id: str, source_id: int,
                    node_id: str, message_id: str, part_index: int,
                    start: int, end: int, exact_quote: str) -> int:
    """Validate before insertion; idempotent for the same exact reference."""
    evidence = verify_quote(db_path, conversation_id=conversation_id, source_id=source_id,
                            node_id=node_id, message_id=message_id, part_index=part_index,
                            start=start, end=end, exact_quote=exact_quote)
    with sqlite3.connect(db_path) as db:
        db.execute('PRAGMA foreign_keys=ON')
        with db:
            db.execute(SCHEMA)
            db.execute('''INSERT OR IGNORE INTO verified_evidence
                (source_id, conversation_id, node_id, message_id, part_index,
                 start_offset, end_offset, exact_quote, part_sha256, source_sha256,
                 message_role, on_active_path)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                (source_id, conversation_id, node_id, message_id, part_index,
                 start, end, exact_quote, evidence['part_sha256'],
                 evidence['source_sha256'], evidence['message_role'],
                 int(evidence['on_active_path'])))
            row = db.execute('''SELECT id FROM verified_evidence WHERE
                source_id=? AND conversation_id=? AND node_id=? AND message_id=?
                AND part_index=? AND start_offset=? AND end_offset=? AND exact_quote=?''',
                (source_id, conversation_id, node_id, message_id, part_index,
                 start, end, exact_quote)).fetchone()
            return row[0]


def read_evidence(db_path: Path, evidence_id: int) -> dict:
    """Return stored evidence and recheck against its original snapshot."""
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute('SELECT * FROM verified_evidence WHERE id=?', (evidence_id,)).fetchone()
    if row is None:
        raise ValueError('Evidence not found')
    saved = dict(row)
    current = verify_quote(db_path, conversation_id=saved['conversation_id'],
                           source_id=saved['source_id'], node_id=saved['node_id'],
                           message_id=saved['message_id'], part_index=saved['part_index'],
                           start=saved['start_offset'], end=saved['end_offset'],
                           exact_quote=saved['exact_quote'])
    for key in ('part_sha256', 'source_sha256', 'message_role'):
        if saved[key] != current[key]:
            raise ValueError(f'Evidence provenance changed: {key}')
    if saved['on_active_path'] != int(current['on_active_path']):
        raise ValueError('Evidence active path changed')
    return saved
