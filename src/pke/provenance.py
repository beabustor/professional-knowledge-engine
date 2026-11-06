"""Verify literal evidence against an explicitly selected immutable snapshot.

Read-only: no SQL schema changes, no LLM, and no fallback to canonical rows.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from .snapshots import read_snapshot
from .branches import active_path


def verify_quote(db_path: Path, *, conversation_id: str, source_id: int,
                 node_id: str, message_id: str, part_index: int,
                 start: int, end: int, exact_quote: str,
                 require_active_path: bool = True) -> dict:
    """Verify a literal substring using Python string offsets [start:end].

    Offsets are Unicode code-point indices, not byte offsets. Only string parts
    from message.content.parts are supported. This is evidence of text origin,
    not evidence that the statement is factually true.
    """
    if not isinstance(source_id, int) or isinstance(source_id, bool) or source_id < 1:
        raise ValueError('Invalid source_id')
    for label, value in [('part_index', part_index), ('start', start), ('end', end)]:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f'Invalid {label}')
    if end <= start or not isinstance(exact_quote, str) or not exact_quote:
        raise ValueError('Invalid quote range or text')
    snapshot = read_snapshot(db_path, conversation_id, source_id)
    mapping = snapshot.get('mapping')
    if not isinstance(mapping, dict) or node_id not in mapping:
        raise ValueError('Node not found in snapshot')
    if require_active_path and node_id not in active_path(mapping, snapshot.get('current_node')):
        raise ValueError('Node is not on selected active path')
    node = mapping[node_id]
    if not isinstance(node, dict) or not isinstance(node.get('message'), dict):
        raise ValueError('Node has no message')
    message = node['message']
    if str(message.get('id')) != message_id:
        raise ValueError('Message identity mismatch')
    content = message.get('content')
    parts = content.get('parts') if isinstance(content, dict) else None
    if not isinstance(parts, list) or part_index >= len(parts) or not isinstance(parts[part_index], str):
        raise ValueError('Text part not found')
    text = parts[part_index]
    if end > len(text) or text[start:end] != exact_quote:
        raise ValueError('Quote does not match snapshot text')
    with sqlite3.connect(db_path) as db:
        row = db.execute('SELECT sha256, source_name FROM sources WHERE id=?', (source_id,)).fetchone()
    if row is None:
        raise ValueError('Source not found')
    return {
        'source_id': source_id, 'source_sha256': row[0], 'source_name': row[1],
        'conversation_id': conversation_id, 'node_id': node_id,
        'message_id': message_id, 'message_role': (message.get('author') or {}).get('role', 'unknown'),
        'part_index': part_index, 'start': start, 'end': end,
        'exact_quote': exact_quote,
        'part_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'on_active_path': node_id in active_path(mapping, snapshot.get('current_node')),
    }
