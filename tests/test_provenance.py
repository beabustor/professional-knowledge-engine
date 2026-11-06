import json
import sqlite3

import pytest

from pke.provenance import verify_quote


def fixture_db(tmp_path):
    path = tmp_path / 'db.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE sources (id INTEGER PRIMARY KEY, source_name TEXT, sha256 TEXT);
            CREATE TABLE conversation_snapshots (source_id INTEGER, conversation_id TEXT, snapshot_json TEXT,
                PRIMARY KEY (source_id, conversation_id));
        ''')
        for sid, body in [(1, 'Usé Neo4j'), (2, 'Estudié Neo4j')]:
            db.execute('INSERT INTO sources VALUES (?, ?, ?)', (sid, f'export-{sid}.zip', f'hash-{sid}'))
            snap = {'id': 'c1', 'current_node': 'selected', 'mapping': {
                'root': {'parent': None, 'message': None},
                'selected': {'parent': 'root', 'message': {'id': 'm1', 'author': {'role': 'user'},
                             'content': {'parts': [body, 'Otro fragmento']}}},
                'alternative': {'parent': 'root', 'message': {'id': 'm2', 'author': {'role': 'assistant'},
                                'content': {'parts': ['No seleccionado']}}},
            }}
            db.execute('INSERT INTO conversation_snapshots VALUES (?, ?, ?)', (sid, 'c1', json.dumps(snap)))
    return path


def args(db):
    return dict(db_path=db, conversation_id='c1', source_id=1, node_id='selected',
                message_id='m1', part_index=0, start=4, end=9, exact_quote='Neo4j')


def test_verified_quote_has_version_and_message_provenance(tmp_path):
    db = fixture_db(tmp_path)
    result = verify_quote(**args(db))
    assert result['source_sha256'] == 'hash-1'
    assert result['message_role'] == 'user'
    assert result['on_active_path'] is True
    assert len(result['part_sha256']) == 64
    assert verify_quote(**{**args(db), 'source_id': 2, 'start': 8, 'end': 13})['source_id'] == 2


def test_rejects_wrong_version_quote_and_message(tmp_path):
    db = fixture_db(tmp_path)
    with pytest.raises(ValueError, match='does not match'):
        verify_quote(**{**args(db), 'source_id': 2})
    with pytest.raises(ValueError, match='identity'):
        verify_quote(**{**args(db), 'message_id': 'wrong'})
    with pytest.raises(ValueError, match='Text part'):
        verify_quote(**{**args(db), 'part_index': 4})


def test_rejects_unselected_branch_by_default(tmp_path):
    db = fixture_db(tmp_path)
    kwargs = {**args(db), 'node_id': 'alternative', 'message_id': 'm2',
              'start': 0, 'end': 2, 'exact_quote': 'No'}
    with pytest.raises(ValueError, match='active path'):
        verify_quote(**kwargs)
    assert verify_quote(**kwargs, require_active_path=False)['on_active_path'] is False
