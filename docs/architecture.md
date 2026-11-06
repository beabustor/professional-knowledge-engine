# Technical architecture — v0.4b

## Boundary and components

Public Git repository (`src/pke`, tests, documentation) → local CLI → configured private directory (`PK_DATA_DIR`) → SQLite. ZIP archives and SQLite must stay outside the public repository. No network/API calls are required for inventory or import.

- `storage.py`: validates private path and initializes SQLite tables.
- `inspector.py`: inventories ZIP metadata using `ijson` when available; writes aggregate report under `evaluations/`.
- `importer.py`: SHA-256 archive identification, incremental conversation parsing and SQLite persistence.
- `branches.py`: reconstructs root-to-`current_node` path from parent pointers; rejects broken or cyclic paths.
- `cli.py`: `init`, `inspect`, `import` commands.

## SQLite data model

- `sources`: ZIP provenance, filename, SHA-256, import timestamp.
- `conversations`: logical conversation ID, first-import source, title, creation timestamp.
- `messages`: canonical message ID, conversation ID, role, extracted text and timestamp.
- `conversation_graph`: canonical selected `current_node`.
- `conversation_nodes`: canonical raw node JSON, parent/children and optional message ID.
- `conversation_snapshots`: `(source_id, conversation_id)` primary key and complete conversation JSON as observed in each newly imported ZIP.
- `claims`, `claim_evidence`, `reconciliation_events`: preliminary evidence/reconciliation schema, **not an implemented extraction workflow**.

`conversation_snapshots.conversation_id` references `conversations.id`; snapshots of an existing conversation do not update canonical rows. The first-import representation is therefore not necessarily the latest version. Legacy imports are not automatically backfilled into snapshots.

## Import semantics

1. Compute SHA-256 for the ZIP; identical archives are treated as already imported.
2. Check archive member size limits and locate exactly one `conversations.json`.
3. Parse the JSON incrementally using `ijson.items(stream, 'item', use_float=True)`; each conversation, including its mapping, is materialized in memory.
4. For new conversation IDs, insert canonical conversation, graph, nodes and messages.
5. For every conversation in a new ZIP, insert a full JSON snapshot linked to that source.
6. Database changes for the import are committed together or rolled back on failure. Schema creation occurs before the import transaction and is not a full migration framework.

**Caveats:** the importer does not compare snapshots at the node level or update canonical rows; no explicit version selection exists. Extremely large individual conversations may exhaust memory. No automated backup or encryption is implemented.

## Branches and evidence

A ChatGPT mapping can contain alternative branches and nodes without messages. `active_path` follows parent references from `current_node`, retaining the selected chain and rejecting missing/cyclic links. `read_active_path` currently reads the **canonical** node graph only, not later snapshots.

Source text is not automatically a validated professional claim. Future extraction must distinguish user statements from assistant statements, evidence from hypotheses, and job requirements from actual experience. Claim audit invariants and version-aware evidence links remain future work.

## Security and validation

- Keep private data outside Git; inspect staged changes before push.
- ZIPs may contain sensitive content. Do not publish personal fixtures or SQLite.
- Synthetic test suite: 13 passed on the maintainer's Windows environment after v0.4b; no real export has been validated.
- Before a real import, create a recoverable private SQLite backup and validate rollback, integrity and compatibility on temporary copies.
