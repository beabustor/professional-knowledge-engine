# Professional Knowledge Engine — project status

## Released on `main`

- **v0.1–v0.2:** privacy-first Python scaffold, private SQLite initialization, offline export inspection.
- **v0.3:** transactional synthetic ZIP import into SQLite; raw nodes, messages, branch relationships and selected `current_node` preserved; identical ZIP recognized by SHA-256.
- **v0.4a:** deterministic active-path reconstruction in `pke.branches` with detection of missing nodes and cycles. Python API only.
- **v0.4b:** incremental JSON parsing with `ijson`; complete per-export `conversation_snapshots` for overlapping conversation IDs. First imported version remains canonical.

## Verification

- On Windows, `python -m pytest -q`: **13 passed** after v0.4b installation.
- Synthetic fixtures only. No real personal export, large-scale stress test, or production-grade migration validation yet.

## Important design details

- ZIP files are deduplicated by archive SHA-256; a different ZIP can contain a new snapshot of an existing conversation.
- Canonical `conversations`, `messages`, `conversation_nodes` and `conversation_graph` remain first-seen records. Later snapshots are retained but not selected by the existing branch reader.
- Legacy v0.3 conversations are not retroactively copied to `conversation_snapshots`.
- Import writes source/snapshot rows transactionally; schema creation occurs before the import transaction.
- `ijson` avoids loading all conversations at once, but one exceptionally large conversation still uses memory.
- `PK_DATA_DIR` must be outside Git. Back up `profile.sqlite` before any real import; no automatic encrypted backup.

## Not implemented

- Version selection and version-aware branch reading; canonical projection or reconciliation of snapshots.
- Real-export compatibility testing, streaming stress tests, per-conversation memory limits.
- Attachment/multimodal interpretation, professional schema discovery, claim extraction/verification, job matching and CV generation.

## Next decisions and work

1. Verify integrity, rollback, snapshots and migration behavior on temporary databases; test a realistic export safely.
2. Design version-aware readers and an explicit canonical projection policy without overwriting evidence.
3. Discover a professional knowledge schema using conversation evidence and job-posting vocabulary, keeping requirements separate from demonstrated skills.
