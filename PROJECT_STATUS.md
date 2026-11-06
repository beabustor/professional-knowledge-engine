# Project status

## Phase 0 — Initial scaffold

Implemented:
- Python package and CLI
- Minimal relational SQLite schema
- Refusal to place private database inside public repository
- Basic tests and project documentation

Not yet implemented:
- GitHub repository creation / first push
- Encrypted backup and secret scanning automation
- Conversation import (ZIP metadata inspector implemented)
- Claim extraction, reconciliation, profile items
- Job matching, clarification, learning paths, CV generation

## Next action

Publish reviewed code to GitHub, then run the read-only ZIP inventory on a real export locally. The inspector is implemented; its execution on a real export is not yet verified.

## Decisions

- Public GitHub repo: code, schemas, synthetic examples only.
- Private data: external local folder, with encrypted backups to be configured.
- SQLite is the initial data store; LLM provider selection deferred until measured tests.
