import pytest
from pke.branches import active_path, read_active_path
from pke.importer import import_archive
import json
from zipfile import ZipFile


def test_selected_branch_excludes_alternative():
    mapping = {
        'root': {'parent': None, 'message': None},
        'user': {'parent': 'root', 'message': {'id': 'm1'}},
        'discarded': {'parent': 'user', 'message': {'id': 'm2'}},
        'selected': {'parent': 'user', 'message': {'id': 'm3'}},
    }
    assert active_path(mapping, 'selected') == ['root', 'user', 'selected']
    assert active_path(mapping, None) == []


def test_rejects_cycle_and_missing_parent():
    with pytest.raises(ValueError, match='Cycle'):
        active_path({'a': {'parent': 'b'}, 'b': {'parent': 'a'}}, 'a')
    with pytest.raises(ValueError, match='Missing'):
        active_path({'a': {'parent': 'missing'}}, 'a')


def test_reads_selected_branch_from_imported_sqlite(tmp_path, monkeypatch):
    repo = tmp_path / 'repo'
    repo.mkdir()
    private = tmp_path / 'private'
    monkeypatch.setenv('PK_DATA_DIR', str(private))
    nodes = {
        'root': {'parent': None, 'children': ['user'], 'message': None},
        'user': {'parent': 'root', 'children': ['old', 'new'], 'message': {'id': 'u1', 'author': {'role': 'user'}, 'content': {'parts': ['question']}}},
        'old': {'parent': 'user', 'children': [], 'message': {'id': 'a1', 'author': {'role': 'assistant'}, 'content': {'parts': ['discarded']}}},
        'new': {'parent': 'user', 'children': [], 'message': {'id': 'a2', 'author': {'role': 'assistant'}, 'content': {'parts': ['selected']}}},
    }
    zip_path = tmp_path / 'sample.zip'
    with ZipFile(zip_path, 'w') as archive:
        archive.writestr('conversations.json', json.dumps([{'id': 'c1', 'current_node': 'new', 'mapping': nodes}]))
    import_archive(zip_path, repo)
    path = read_active_path(private / 'database' / 'profile.sqlite', 'c1')
    assert [item['node_id'] for item in path] == ['root', 'user', 'new']
    assert path[-1]['node']['message']['content']['parts'] == ['selected']
