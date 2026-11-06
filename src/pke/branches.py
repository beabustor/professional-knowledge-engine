"""Deterministic reconstruction of the selected ChatGPT conversation path.

Does not assume every node contains a message. Does not modify stored data.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def active_path(mapping: dict, current_node: str | None) -> list[str]:
    """Return root-to-current node IDs, rejecting broken/cyclic parent chains."""
    if not current_node:
        return []
    if not isinstance(mapping, dict):
        raise ValueError('Invalid conversation mapping')
    path = []
    seen = set()
    node_id = current_node
    while node_id is not None:
        if node_id in seen:
            raise ValueError('Cycle in active conversation path')
        if node_id not in mapping:
            raise ValueError(f'Missing active path node: {node_id}')
        seen.add(node_id)
        path.append(node_id)
        node = mapping[node_id]
        if not isinstance(node, dict):
            raise ValueError(f'Invalid node: {node_id}')
        parent = node.get('parent')
        if parent is not None and not isinstance(parent, str):
            raise ValueError(f'Invalid parent for node: {node_id}')
        node_id = parent
    path.reverse()
    return path


def read_active_path(db_path: Path, conversation_id: str) -> list[dict]:
    """Read selected nodes from SQLite; retain message-less nodes and raw content."""
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            'SELECT current_node FROM conversation_graph WHERE conversation_id=?',
            (conversation_id,),
        ).fetchone()
        if row is None:
            raise ValueError('Unknown conversation')
        nodes = conn.execute(
            'SELECT node_id, raw_node_json FROM conversation_nodes WHERE conversation_id=?',
            (conversation_id,),
        ).fetchall()
    mapping = {node_id: json.loads(raw) for node_id, raw in nodes}
    return [{'node_id': node_id, 'node': mapping[node_id]} for node_id in active_path(mapping, row[0])]
