import json
import sqlite3
from zipfile import ZipFile

import pytest
from pke.importer import import_archive


def archive(path, items):
    with ZipFile(path, 'w') as z:
        z.writestr('conversations.json', json.dumps(items))


def conv(text, cid='c1'):
    return {'id': cid, 'title': text, 'current_node': 'n', 'mapping': {
        'n': {'parent': None, 'children': [], 'message': {
            'id': 'm-' + cid, 'author': {'role': 'user'}, 'content': {'parts': [text]}}}}}


def test_overlapping_exports_keep_snapshots_and_canonical(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'; repo.mkdir()
    private = tmp_path / 'private'; monkeypatch.setenv('PK_DATA_DIR', str(private))
    a, b = tmp_path / 'a.zip', tmp_path / 'b.zip'
    archive(a, [conv('old')]); archive(b, [conv('new'), conv('other', 'c2')])
    assert import_archive(a, repo)['snapshots'] == 1
    result = import_archive(b, repo)
    assert result['conversations'] == 1
    assert result['snapshots'] == 2
    assert import_archive(b, repo)['already_imported']
    with sqlite3.connect(private / 'database' / 'profile.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM conversation_snapshots').fetchone()[0] == 3
        assert db.execute('SELECT body FROM messages WHERE id="m-c1"').fetchone()[0] == 'old'
        rows = db.execute('SELECT snapshot_json FROM conversation_snapshots WHERE conversation_id="c1" ORDER BY source_id').fetchall()
        assert [json.loads(r[0])['title'] for r in rows] == ['old', 'new']
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_failed_second_export_rolls_back(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'; repo.mkdir()
    private = tmp_path / 'private'; monkeypatch.setenv('PK_DATA_DIR', str(private))
    a, b = tmp_path / 'a.zip', tmp_path / 'b.zip'
    archive(a, [conv('old')]); import_archive(a, repo)
    bad = conv('bad', 'c2'); bad['mapping']['n']['message'].pop('id')
    archive(b, [conv('new'), bad])
    with pytest.raises(ValueError, match='Message missing id'):
        import_archive(b, repo)
    with sqlite3.connect(private / 'database' / 'profile.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM sources').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM conversation_snapshots').fetchone()[0] == 1
        assert db.execute('SELECT COUNT(*) FROM conversations').fetchone()[0] == 1
