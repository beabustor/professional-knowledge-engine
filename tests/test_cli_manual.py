import json
import sqlite3
import sys
from pathlib import Path

from pke import cli


def test_manual_cli_and_pending(tmp_path, monkeypatch, capsys):
    private = tmp_path / 'private'
    monkeypatch.setenv('PK_DATA_DIR', str(private))
    file = tmp_path / 'input.json'
    file.write_text(json.dumps({'format': 'pke-manual-v1', 'items': [
        {'kind': 'interview', 'text': 'Ejemplo de prueba', 'origin_label': 'Test'}
    ]}), encoding='utf-8')
    monkeypatch.setattr(sys, 'argv', ['pke', 'import-manual', str(file)])
    cli.main()
    assert json.loads(capsys.readouterr().out)['inserted'] == 1
    monkeypatch.setattr(sys, 'argv', ['pke', 'pending'])
    cli.main()
    assert json.loads(capsys.readouterr().out) == {'pending_count': 1}
    monkeypatch.setattr(sys, 'argv', ['pke', 'pending', '--details'])
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result['items'][0]['text'] == 'Ejemplo de prueba'


def test_pending_without_intake_table(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv('PK_DATA_DIR', str(tmp_path / 'private'))
    from pke.storage import initialize
    initialize(Path(cli.__file__).resolve().parents[2])
    monkeypatch.setattr(sys, 'argv', ['pke', 'pending'])
    cli.main()
    assert json.loads(capsys.readouterr().out)['pending_count'] == 0
