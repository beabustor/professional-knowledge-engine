import json
import sqlite3
from pathlib import Path
from zipfile import ZipFile

import pytest
from pke.importer import import_archive


def test_import_idempotent_and_graph(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    private = tmp_path / 'private'
    monkeypatch.setenv('PK_DATA_DIR', str(private))
    archive = tmp_path / 'test.zip'
    data = [{'id': 'c1', 'title': 'Example', 'create_time': 1, 'current_node': 'n2',
             'mapping': {'n0': {'id': 'n0', 'parent': None, 'children': ['n1'], 'message': None},
                         'n1': {'id': 'n1', 'parent': 'n0', 'children': ['n2'], 'message':
                                {'id': 'm1', 'author': {'role': 'user'}, 'content': {'parts': ['Hi']}}},
                         'n2': {'id': 'n2', 'parent': 'n1', 'children': [], 'message':
                                {'id': 'm2', 'author': {'role': 'assistant'}, 'content': {'parts': ['Hello']}}}}}]
    with ZipFile(archive, 'w') as z:
        z.writestr('conversations.json', json.dumps(data))
    result = import_archive(archive, repo)
    assert result['conversations'] == 1
    assert result['nodes'] == 3
    assert result['messages'] == 2
    assert import_archive(archive, repo)['already_imported'] is True
    with sqlite3.connect(private / 'database' / 'profile.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM messages').fetchone()[0] == 2
        assert db.execute('SELECT current_node FROM conversation_graph').fetchone()[0] == 'n2'
        assert db.execute('SELECT parent_id FROM conversation_nodes WHERE node_id="n2"').fetchone()[0] == 'n1'


def test_import_rolls_back_on_bad_message(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    private = tmp_path / 'private'
    monkeypatch.setenv('PK_DATA_DIR', str(private))
    archive = tmp_path / 'bad.zip'
    with ZipFile(archive, 'w') as z:
        z.writestr('conversations.json', json.dumps([{'id': 'c1', 'mapping': {'n': {'message': {'content': {'parts': ['x']}}}}}]))
    with pytest.raises(ValueError, match='Message missing id'):
        import_archive(archive, repo)
    with sqlite3.connect(private / 'database' / 'profile.sqlite') as db:
        assert db.execute('SELECT COUNT(*) FROM sources').fetchone()[0] == 0
