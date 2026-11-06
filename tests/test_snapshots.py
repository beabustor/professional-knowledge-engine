import json
import sqlite3
from pathlib import Path

import pytest

from pke.snapshots import list_versions, read_snapshot, read_snapshot_active_path


def db_fixture(path: Path):
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE sources (id INTEGER PRIMARY KEY, source_name TEXT, sha256 TEXT, imported_at TEXT);
            CREATE TABLE conversation_snapshots (source_id INTEGER, conversation_id TEXT, snapshot_json TEXT,
                PRIMARY KEY (source_id, conversation_id));
        ''')
        for source_id, label, selected in ((1, 'old', 'a'), (2, 'new', 'b')):
            db.execute('INSERT INTO sources VALUES (?, ?, ?, ?)', (source_id, label, f'hash-{source_id}', f'date-{source_id}'))
            obj = {'id': 'c1', 'current_node': selected, 'mapping': {
                'root': {'parent': None, 'message': None},
                'a': {'parent': 'root', 'message': {'content': {'parts': ['old']}}},
                'b': {'parent': 'root', 'message': {'content': {'parts': ['new']}}},
            }}
            db.execute('INSERT INTO conversation_snapshots VALUES (?, ?, ?)', (source_id, 'c1', json.dumps(obj)))


def test_version_selection_and_branches(tmp_path):
    path = tmp_path / 'db.sqlite'
    db_fixture(path)
    versions = list_versions(path, 'c1')
    assert [v['source_id'] for v in versions] == [1, 2]
    assert [item['node_id'] for item in read_snapshot_active_path(path, 'c1', 1)] == ['root', 'a']
    assert [item['node_id'] for item in read_snapshot_active_path(path, 'c1', 2)] == ['root', 'b']
    assert read_snapshot(path, 'c1', 1)['current_node'] == 'a'
    with pytest.raises(ValueError, match='not found'):
        read_snapshot(path, 'c1', 3)
    assert list_versions(path, 'missing') == []


def test_reject_corrupt_snapshot_and_broken_path(tmp_path):
    path = tmp_path / 'db.sqlite'
    db_fixture(path)
    with sqlite3.connect(path) as db:
        db.execute('UPDATE conversation_snapshots SET snapshot_json=? WHERE source_id=1', (json.dumps({'id': 'wrong'}),))
    with pytest.raises(ValueError, match='identity'):
        read_snapshot(path, 'c1', 1)
    with sqlite3.connect(path) as db:
        db.execute('UPDATE conversation_snapshots SET snapshot_json=? WHERE source_id=1',
                   (json.dumps({'id': 'c1', 'mapping': {'a': {'parent': 'missing'}}, 'current_node': 'a'}),))
    with pytest.raises(ValueError, match='Missing'):
        read_snapshot_active_path(path, 'c1', 1)
