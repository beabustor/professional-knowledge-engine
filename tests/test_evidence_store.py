import json
import sqlite3
import pytest
from pke.evidence_store import record_evidence, read_evidence


def fixture(tmp_path):
    path = tmp_path / 'evidence.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE sources(id INTEGER PRIMARY KEY, source_name TEXT, sha256 TEXT);
        CREATE TABLE conversation_snapshots(source_id INTEGER, conversation_id TEXT,
            snapshot_json TEXT, PRIMARY KEY(source_id, conversation_id));
        ''')
        for sid, phrase in ((1, 'Usé Neo4j'), (2, 'Estudié Neo4j')):
            db.execute('INSERT INTO sources VALUES(?,?,?)', (sid, f'export{sid}.zip', f'hash{sid}'))
            snap = {'id':'c1','current_node':'n','mapping':{'n':{
                'parent':None,'message':{'id':'m1','author':{'role':'user'},
                'content':{'parts':[phrase]}}}}}
            db.execute('INSERT INTO conversation_snapshots VALUES(?,?,?)',
                       (sid,'c1',json.dumps(snap)))
    return path


def fields(sid=1, start=4, end=9):
    return dict(conversation_id='c1',source_id=sid,node_id='n',message_id='m1',
                part_index=0,start=start,end=end,exact_quote='Neo4j')


def test_persists_and_deduplicates(tmp_path):
    db = fixture(tmp_path)
    first = record_evidence(db, **fields())
    assert first == record_evidence(db, **fields())
    assert read_evidence(db, first)['exact_quote'] == 'Neo4j'
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM verified_evidence').fetchone()[0] == 1


def test_versions_and_wrong_quote(tmp_path):
    db = fixture(tmp_path)
    first = record_evidence(db, **fields())
    second = record_evidence(db, **fields(2, 8, 13))
    assert first != second
    assert read_evidence(db, second)['source_id'] == 2
    with pytest.raises(ValueError, match='does not match'):
        record_evidence(db, **fields(2))


def test_detects_tampered_snapshot(tmp_path):
    db = fixture(tmp_path)
    evidence_id = record_evidence(db, **fields())
    with sqlite3.connect(db) as conn:
        snap = json.loads(conn.execute('SELECT snapshot_json FROM conversation_snapshots WHERE source_id=1').fetchone()[0])
        snap['mapping']['n']['message']['content']['parts'][0] = 'No usé Neo4j'
        conn.execute('UPDATE conversation_snapshots SET snapshot_json=? WHERE source_id=1', (json.dumps(snap),))
    with pytest.raises(ValueError, match='does not match'):
        read_evidence(db, evidence_id)
