import json
import sqlite3

import pytest

from pke.manual_ingest import import_manual_json, list_manual_items


def setup(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    monkeypatch.setenv('PK_DATA_DIR', str(tmp_path / 'private'))
    path = tmp_path / 'notes.json'
    return repo, path


def write(path, items):
    path.write_text(json.dumps({'format': 'pke-manual-v1', 'items': items}), encoding='utf-8')


def item(text='Participé en un proyecto con Neo4j'):
    return {'kind': 'experience', 'text': text, 'origin_label': 'Entrevista personal', 'context': 'Relato propio'}


def test_idempotency_and_provenance(tmp_path, monkeypatch):
    repo, path = setup(tmp_path, monkeypatch)
    write(path, [item()])
    assert import_manual_json(path, repo)['inserted'] == 1
    result = import_manual_json(path, repo)
    assert result['inserted'] == 0 and result['duplicates'] == 1
    db = tmp_path / 'private/database/profile.sqlite'
    rows = list_manual_items(db)
    assert len(rows) == 1
    assert rows[0]['provenance_status'] == 'self_reported'
    assert rows[0]['review_status'] == 'pending'


def test_atomic_rejection(tmp_path, monkeypatch):
    repo, path = setup(tmp_path, monkeypatch)
    write(path, [item(), {'kind': 'invalid', 'text': 'bad', 'origin_label': 'x'}])
    with pytest.raises(ValueError, match='kind'):
        import_manual_json(path, repo)
    assert not (tmp_path / 'private/database/profile.sqlite').exists()


def test_distinct_versions_and_no_personal_export_claim(tmp_path, monkeypatch):
    repo, path = setup(tmp_path, monkeypatch)
    write(path, [item('Estudié Neo4j'), item('Usé Neo4j')])
    assert import_manual_json(path, repo)['inserted'] == 2
    db = tmp_path / 'private/database/profile.sqlite'
    with sqlite3.connect(db) as connection:
        assert connection.execute('SELECT COUNT(*) FROM manual_intake').fetchone()[0] == 2
        assert {x[0] for x in connection.execute('SELECT provenance_status FROM manual_intake')} == {'self_reported'}
