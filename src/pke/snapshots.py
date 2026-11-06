"""Read archived conversation versions without changing canonical evidence."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .branches import active_path


def list_versions(db_path: Path, conversation_id: str) -> list[dict]:
    """Return imported snapshots ordered by source ID (import order)."""
    with sqlite3.connect(db_path) as db:
        rows = db.execute(
            """SELECT s.id, s.source_name, s.sha256, s.imported_at
               FROM conversation_snapshots AS cs
               JOIN sources AS s ON s.id = cs.source_id
               WHERE cs.conversation_id = ? ORDER BY s.id""",
            (conversation_id,),
        ).fetchall()
    return [dict(zip(('source_id', 'source_name', 'sha256', 'imported_at'), row)) for row in rows]


def read_snapshot(db_path: Path, conversation_id: str, source_id: int) -> dict:
    """Read exactly one snapshot, never silently fall back to canonical data."""
    with sqlite3.connect(db_path) as db:
        row = db.execute(
            "SELECT snapshot_json FROM conversation_snapshots WHERE conversation_id=? AND source_id=?",
            (conversation_id, source_id),
        ).fetchone()
    if row is None:
        raise ValueError('Snapshot not found for conversation and source')
    snapshot = json.loads(row[0])
    if not isinstance(snapshot, dict) or str(snapshot.get('id')) != conversation_id:
        raise ValueError('Invalid stored snapshot identity')
    return snapshot


def read_snapshot_active_path(db_path: Path, conversation_id: str, source_id: int) -> list[dict]:
    """Reconstruct selected path of an explicit version, retaining message-less nodes."""
    snapshot = read_snapshot(db_path, conversation_id, source_id)
    mapping = snapshot.get('mapping')
    if not isinstance(mapping, dict):
        raise ValueError('Invalid snapshot mapping')
    return [{'node_id': nid, 'node': mapping[nid]}
            for nid in active_path(mapping, snapshot.get('current_node'))]
