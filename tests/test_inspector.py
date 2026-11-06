import json
from zipfile import ZipFile
import pytest
from pke.inspector import inspect_archive, save_report


def test_inventory_no_content_leak(tmp_path):
    archive = tmp_path / 'export.zip'
    conversations = [{
        'id': 'secret-id', 'create_time': 123,
        'title': 'private title',
        'mapping': {
            'a': {'message': {'author': {'role': 'user'}, 'content': {'parts': ['private health details']}}},
            'b': {'message': {'author': {'role': 'assistant'}, 'content': {'parts': ['reply']}}},
            'c': {'message': None},
        },
    }]
    with ZipFile(archive, 'w') as z:
        z.writestr('conversations.json', json.dumps(conversations))
    report = inspect_archive(archive)
    assert report['conversation_count'] == 1
    assert report['message_count'] == 2
    assert report['user_message_count'] == 1
    assert report['string_content_parts'] == 2
    output = save_report(report, tmp_path / 'private')
    saved = output.read_text()
    assert 'private health details' not in saved
    assert 'private title' not in saved
    assert 'secret-id' not in saved
    assert str(archive) not in saved


def test_missing_conversations_json(tmp_path):
    archive = tmp_path / 'export.zip'
    with ZipFile(archive, 'w') as z:
        z.writestr('other.json', '[]')
    with pytest.raises(ValueError, match='conversations.json'):
        inspect_archive(archive)


def test_invalid_zip(tmp_path):
    archive = tmp_path / 'export.zip'
    archive.write_text('not a zip')
    with pytest.raises(ValueError, match='Invalid ZIP'):
        inspect_archive(archive)
