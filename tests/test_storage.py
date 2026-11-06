from pathlib import Path
import sqlite3
import pytest
from pke.storage import private_dir, initialize


def test_reject_private_data_inside_repo(tmp_path: Path):
    with pytest.raises(ValueError, match='inside'):
        private_dir(tmp_path, str(tmp_path / 'private'))


def test_requires_private_path(tmp_path: Path, monkeypatch):
    monkeypatch.delenv('PK_DATA_DIR', raising=False)
    with pytest.raises(ValueError, match='PK_DATA_DIR'):
        private_dir(tmp_path)


def test_init_creates_schema(tmp_path: Path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    db = initialize(repo, str(tmp_path / 'private'))
    assert db.exists()
    with sqlite3.connect(db) as con:
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'sources','conversations','messages','claims','claim_evidence','reconciliation_events'} <= names
