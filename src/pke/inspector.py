"""Read-only, metadata-only inventory of a ChatGPT export ZIP."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, BadZipFile

try:
    import ijson
except ImportError:
    ijson = None

MAX_MEMBER_BYTES = 4 * 1024**3
MAX_TOTAL_BYTES = 12 * 1024**3


def inspect_archive(path: Path) -> dict:
    path = path.expanduser().resolve(strict=True)
    if not path.is_file() or not path.name.lower().endswith('.zip'):
        raise ValueError('Expected an existing .zip file')
    try:
        with ZipFile(path) as archive:
            members = [i for i in archive.infolist() if not i.is_dir()]
            if any(i.file_size > MAX_MEMBER_BYTES for i in members) or sum(i.file_size for i in members) > MAX_TOTAL_BYTES:
                raise ValueError('Archive exceeds inspection safety limits')
            matches = [i for i in members if Path(i.filename).name == 'conversations.json']
            if len(matches) != 1:
                raise ValueError(f'Expected exactly one conversations.json; found {len(matches)}')
            roles = Counter()
            conversations = messages = user_messages = text_parts = 0
            missing_ids = missing_timestamps = 0
            if ijson is None and matches[0].file_size > 100 * 1024**2:
                raise RuntimeError('Large export requires ijson: python -m pip install ijson')
            with archive.open(matches[0]) as stream:
                conversations_iter = (ijson.items(stream, 'item') if ijson is not None else iter(json.load(stream)))
                for conversation in conversations_iter:
                    conversations += 1
                    if not conversation.get('id'):
                        missing_ids += 1
                    if conversation.get('create_time') is None:
                        missing_timestamps += 1
                    mapping = conversation.get('mapping') or {}
                    for node in mapping.values():
                        msg = node.get('message') if isinstance(node, dict) else None
                        if not isinstance(msg, dict):
                            continue
                        messages += 1
                        role = (msg.get('author') or {}).get('role') or 'unknown'
                        roles[role] += 1
                        if role == 'user':
                            user_messages += 1
                        content = msg.get('content') or {}
                        if isinstance(content, dict):
                            text_parts += sum(isinstance(part, str) for part in (content.get('parts') or []))
            return {
                'format': 'chatgpt-export-inventory-v1',
                'inspected_at_utc': datetime.now(timezone.utc).isoformat(),
                'archive_bytes': path.stat().st_size,
                'archive_members': len(members),
                'conversation_count': conversations,
                'message_count': messages,
                'user_message_count': user_messages,
                'message_roles': dict(sorted(roles.items())),
                'string_content_parts': text_parts,
                'conversations_missing_id': missing_ids,
                'conversations_missing_create_time': missing_timestamps,
                'notes': [
                    'Counts mapping nodes containing messages, including possible alternative branches.',
                    'Does not inspect attachment contents or reconstruct the active conversation path.',
                    'No message text, titles, file paths or personal identifiers are included in this report.',
                ],
            }
    except BadZipFile as exc:
        raise ValueError('Invalid ZIP archive') from exc


def save_report(report: dict, private_root: Path) -> Path:
    destination = private_root / 'evaluations' / 'archive_inventory.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return destination
