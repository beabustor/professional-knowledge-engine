# Technical architecture — v0.5b

## Trust boundary

Public repository (Python code/tests/docs) -> local CLI -> `PK_DATA_DIR` outside repository -> private SQLite. ZIP inventory, import and manual intake are offline. No model APIs are called.

## Component flows

See [module guide](module-guide.md) for a detailed call graph, responsibilities and interfaces.

- `cli.py` dispatches to `storage`, `inspector`, `importer` or `manual_ingest`.
- `importer` writes sources, canonical conversations/nodes/messages and per-source snapshots.
- `branches` reads canonical graph or supplies path reconstruction to `snapshots` and `provenance`.
- `provenance` verifies literal substrings of a selected snapshot and retrieves source SHA-256.
- `evidence_store` persists and rechecks those exact references.
- `manual_ingest` stores selected JSON notes separately as unverified self-reports.

## Data model

- `sources`: archive identity and SHA-256.
- `conversations`, `messages`, `conversation_graph`, `conversation_nodes`: first-import canonical representation.
- `conversation_snapshots`: raw conversation JSON keyed by `(source_id, conversation_id)`.
- `verified_evidence`: quote reference, text offsets, role, source hash, part hash, selected-path status.
- `manual_intake`: exact-deduplicated note, origin label, `self_reported` provenance, `pending` review status.
- `claims`, `claim_evidence`, `reconciliation_events`: preliminary schema only; no operational extraction pipeline.

## Import and consistency

ZIP SHA-256 prevents identical archive reimport. `ijson` processes one conversation at a time, but a very large conversation can still consume significant memory. New ZIP versions retain snapshots without overwriting canonical rows. Import records are transactional; schema creation precedes import transactions. Manual intake validates the whole JSON before writing and uses unique digest constraints.

## Provenance limits

`verify_quote` checks message identity, exact Unicode character offsets, role and optional active-path membership against a selected snapshot. It does not establish that a claim is true. Manual notes do not have equivalent snapshot verification and must never be presented as such.

## Safety and gaps

Private SQLite and exports must never be staged or pushed to Git. `pending --details` prints sensitive text. Automatic backups, encrypted storage, formal migrations, real-export testing, LLM adapters, job matching and CV generation are **not implemented**. The last reported synthetic suite result was 26 passing tests on Windows.
