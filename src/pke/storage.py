"""Local private data directory and SQLite initialization."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    title TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL,
    body TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY,
    statement TEXT NOT NULL,
    polarity TEXT NOT NULL CHECK(polarity IN ('positive','negative','uncertain')),
    status TEXT NOT NULL DEFAULT 'unreviewed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS claim_evidence (
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    message_id TEXT NOT NULL REFERENCES messages(id),
    exact_quote TEXT NOT NULL,
    PRIMARY KEY (claim_id, message_id, exact_quote)
);
CREATE TABLE IF NOT EXISTS reconciliation_events (
    id INTEGER PRIMARY KEY,
    claim_id INTEGER NOT NULL REFERENCES claims(id),
    event_type TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def private_dir(repo_root: Path, configured: str | None = None) -> Path:
    value = configured if configured is not None else os.environ.get('PK_DATA_DIR')
    if not value:
        raise ValueError('PK_DATA_DIR is required and must point outside the repository')
    root = repo_root.resolve()
    target = Path(value).expanduser().resolve()
    if target == root or root in target.parents:
        raise ValueError('Private data directory cannot be inside the public repository')
    return target


def initialize(repo_root: Path, configured: str | None = None) -> Path:
    target = private_dir(repo_root, configured)
    db_dir = target / 'database'
    db_dir.mkdir(parents=True, exist_ok=True)
    path = db_dir / 'profile.sqlite'
    with sqlite3.connect(path) as connection:
        connection.executescript(SCHEMA)
    return path
