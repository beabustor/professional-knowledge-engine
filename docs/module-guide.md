# Module guide and dependency contracts (v0.5b)

This document describes the code as implemented, not an aspirational architecture.

## Call graph

```text
python -m pke.cli / pke
  init ---------> storage.initialize -> private SQLite
  inspect ------> storage.private_dir -> inspector.inspect_archive -> inspector.save_report
  import -------> importer.import_archive -> storage.initialize -> SQLite
  import-manual -> manual_ingest.import_manual_json -> storage.initialize -> SQLite
  pending ------> storage.private_dir -> manual_ingest.list_manual_items -> SQLite

Python API (not exposed by CLI):
  snapshots.list_versions/read_snapshot/read_snapshot_active_path
    -> SQLite / branches.active_path
  branches.read_active_path -> canonical SQLite graph / branches.active_path
  provenance.verify_quote -> snapshots.read_snapshot + branches.active_path + sources table
  evidence_store.record_evidence/read_evidence -> provenance.verify_quote + SQLite
```

## Modules

| Module | Responsibility | Important dependencies / constraints |
| --- | --- | --- |
| `cli.py` | Parse commands and print results | Dispatches to modules; `pending --details` prints sensitive text |
| `storage.py` | Validate `PK_DATA_DIR` and initialize base tables | SQLite stored outside repository; not a migration/backup system |
| `inspector.py` | Inventory ZIP and write private report | Does not assess professional competence |
| `importer.py` | Import ZIP with archive hash and per-conversation snapshots | `ijson`, `storage`; first version stays canonical |
| `branches.py` | Trace selected conversation path | Parent pointers; rejects cycles and missing parents |
| `snapshots.py` | Select explicit source version of a conversation | No fallback to canonical; reads snapshot JSON |
| `provenance.py` | Check literal quote at exact string offsets | Snapshot and active path; authentic quote is not necessarily true |
| `evidence_store.py` | Persist/recheck verified quote references | Verifies before insertion; SQLite table created on first write |
| `manual_ingest.py` | Validate/import selected JSON notes | All manual items are self-reported, pending review |

## Data and provenance

- ZIPs are deduplicated by whole-archive SHA-256. Different archives can contain overlapping conversations; snapshots retain the version for each `(source_id, conversation_id)`.
- `messages`, `conversation_nodes` and `conversation_graph` are canonical **first-import** records; do not mistake them for the latest export.
- `verified_evidence` stores a quote, offsets, source ID/hash, message ID/role, part hash and active-path flag. The reader rechecks the snapshot. It does **not** prove professional competence.
- `manual_intake` stores `kind`, `text`, `context`, `origin_label`, digest, `self_reported` provenance and `pending` review status. The origin label is not authenticated. Identical normalized records are deduplicated; semantically similar records are not.
- Existing `claims`, `claim_evidence`, `reconciliation_events` are preliminary tables, not an operational extraction or reconciliation workflow.

## Manual JSON contract

```json
{
  "format": "pke-manual-v1",
  "items": [
    {
      "kind": "interview",
      "text": "Example of a professional observation (synthetic)",
      "context": "Optional context",
      "origin_label": "User-selected note"
    }
  ]
}
```

`kind` must be one of `experience`, `training`, `knowledge`, `project`, `interview`, `correction`, `other`. Files: at most 2 MiB, 1–100 items; text at most 12,000 characters, context 2,000, origin label 300. All records are validated before writes. A manually imported note is **not** verified evidence from an export.

## Operational safety

- Never place personal ZIPs, SQLite, private reports or secrets in Git. Set `PK_DATA_DIR` outside the repository.
- Before first real export, back up SQLite and test recovery. No automatic backup, encryption, schema migration framework or real-export compatibility test is implemented.
- `pending --details` reveals private text in the terminal. Use `pending` for a count-only view.
- No model APIs or autonomous agents are called in v0.5b.

## Future model orchestration (not implemented)

Keep provider adapters separate from evidence verification. A processing run should record input hashes, model/provider identifiers, prompt version, output schema version, validation result, cost/latency when available, and review status. Reject unsupported claims and never treat a model's response as proof. Test fake adapters before real API calls. This is a design direction, **not** a present capability.
