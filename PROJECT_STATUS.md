# Professional Knowledge Engine — status

## Implemented
- Public Python project scaffold and private SQLite directory guard.
- Offline ZIP inventory (`inspect`).
- Offline ZIP import (`import`) for small exports (up to 100 MiB uncompressed conversations.json), storing messages and full raw mapping nodes with parent/children and current_node.
- Transactional import, duplicate ZIP detection via SHA-256.

## Verified in development environment
- `PYTHONPATH=src python -m pytest -q`: 8 passed.
- Synthetic export: 2 conversations, 8 mapping nodes, 6 messages imported.

## Limitations / next tasks
- Importer currently loads conversations.json into memory; streaming required before real large exports.
- Exact reimport of identical ZIP is idempotent, but overlapping conversations from different ZIPs are rejected rather than reconciled.
- Active path reconstruction and attachment extraction are not implemented.
- No LLM claim extraction yet; no real personal export tested.
- Local private backup/encryption still pending.
- Validate real-world schema variants and improve robustness before production use.

## Privacy
Public repository contains code and synthetic fixtures only. Keep personal exports and SQLite database outside the repository.
