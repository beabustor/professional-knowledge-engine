"""Offline, transactional ChatGPT conversation import. No network calls."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from .inspector import MAX_MEMBER_BYTES, MAX_TOTAL_BYTES
from .storage import initialize

GRAPH_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation_graph (
    conversation_id TEXT PRIMARY KEY REFERENCES conversations(id),
    current_node TEXT
);
CREATE TABLE IF NOT EXISTS conversation_nodes (
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    node_id TEXT NOT NULL,
    parent_id TEXT,
    children_json TEXT NOT NULL,
    message_id TEXT,
    raw_node_json TEXT NOT NULL,
    PRIMARY KEY (conversation_id, node_id)
);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON conversation_nodes(conversation_id, parent_id);
"""


def _timestamp(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    return str(value)


def _text(message):
    content = message.get('content') or {}
    if not isinstance(content, dict):
        return None
    parts = content.get('parts') or []
    return '\n'.join(p for p in parts if isinstance(p, str)) or None


def import_archive(zip_path: Path, repo_root: Path) -> dict:
    zip_path = Path(zip_path).expanduser().resolve(strict=True)
    if zip_path.suffix.lower() != '.zip':
        raise ValueError('Expected a ZIP file')
    with ZipFile(zip_path) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if any(m.file_size > MAX_MEMBER_BYTES for m in members) or sum(m.file_size for m in members) > MAX_TOTAL_BYTES:
            raise ValueError('Archive exceeds safety limits')
        matches = [m for m in members if Path(m.filename).name == 'conversations.json']
        if len(matches) != 1:
            raise ValueError('Expected exactly one conversations.json')
        if matches[0].file_size > 100 * 1024**2:
            raise ValueError('Large exports are not yet supported by the importer; use inspect first')
        with archive.open(matches[0]) as stream:
            conversations = json.load(stream)
    if not isinstance(conversations, list):
        raise ValueError('conversations.json must be a list')
    hasher = hashlib.sha256()
    with zip_path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    db_path = initialize(repo_root)
    counts = {'conversations': 0, 'nodes': 0, 'messages': 0, 'already_imported': False}
    with sqlite3.connect(db_path) as connection:
        connection.execute('PRAGMA foreign_keys=ON')
        connection.executescript(GRAPH_SCHEMA)
        if connection.execute('SELECT 1 FROM sources WHERE sha256=?', (digest,)).fetchone():
            counts['already_imported'] = True
            return counts
        with connection:
            source_id = connection.execute(
                'INSERT INTO sources(source_type,source_name,sha256) VALUES (?,?,?)',
                ('chatgpt_export', zip_path.name, digest),
            ).lastrowid
            for conversation in conversations:
                if not isinstance(conversation, dict) or not conversation.get('id'):
                    raise ValueError('Conversation missing id')
                cid = str(conversation['id'])
                mapping = conversation.get('mapping') or {}
                if not isinstance(mapping, dict):
                    raise ValueError('Invalid conversation mapping')
                connection.execute(
                    'INSERT INTO conversations(id,source_id,title,created_at) VALUES (?,?,?,?)',
                    (cid, source_id, conversation.get('title'), _timestamp(conversation.get('create_time'))),
                )
                connection.execute(
                    'INSERT INTO conversation_graph(conversation_id,current_node) VALUES (?,?)',
                    (cid, conversation.get('current_node')),
                )
                counts['conversations'] += 1
                for key, node in mapping.items():
                    if not isinstance(node, dict):
                        raise ValueError('Invalid mapping node')
                    node_id = str(key)
                    message = node.get('message')
                    mid = None
                    if isinstance(message, dict):
                        mid = message.get('id')
                        if not mid:
                            raise ValueError('Message missing id')
                        mid = str(mid)
                        connection.execute(
                            'INSERT INTO messages(id,conversation_id,role,body,created_at) VALUES (?,?,?,?,?)',
                            (mid, cid, (message.get('author') or {}).get('role') or 'unknown',
                             _text(message), _timestamp(message.get('create_time'))),
                        )
                        counts['messages'] += 1
                    connection.execute(
                        'INSERT INTO conversation_nodes(conversation_id,node_id,parent_id,children_json,message_id,raw_node_json) '
                        'VALUES (?,?,?,?,?,?)',
                        (cid, node_id, node.get('parent'), json.dumps(node.get('children') or []),
                         mid, json.dumps(node, ensure_ascii=False)),
                    )
                    counts['nodes'] += 1
    return counts
