# Project status — v0.5b

## Implemented

- v0.1–v0.2: private data directory, SQLite scaffold, ZIP inspection.
- v0.3: transactional ZIP import, source SHA-256, conversation graph.
- v0.4a: active branch reconstruction.
- v0.4b: streaming per-conversation parsing, versioned snapshots.
- v0.4c: explicit snapshot readers.
- v0.4d: literal quote verification with version/node/message/offset provenance.
- v0.4e: persistent verified evidence references and rechecking.
- v0.5a: incremental manual JSON intake with exact deduplication and pending status.
- v0.5b: `import-manual`, `pending`, `pending --details` CLI commands.

## Verification

- Maintainer reported **26 passed** after v0.5b using synthetic tests.
- No real ChatGPT export validation, large-data performance tests, disaster recovery drill or production-grade schema migration test.
- The documentation-only update does not add application functionality.

## Known limitations

- The first imported conversation version remains canonical; later versions are snapshots. Old pre-snapshot imports are not backfilled automatically.
- One conversation is still materialized in memory during ZIP import.
- Manual intake is self-reported and does not prove a claim or authenticate its origin label.
- Verified textual provenance is not the same as verified professional competence.
- No automatic private DB backup, encryption or model invocation.
- No automated extraction, conflict reconciliation, job matching or CV generation.

## Next steps

1. Validate real-export format and restore-from-backup workflow on private copies.
2. Add incremental processing states and a documented, testable provider-neutral model contract.
3. Evaluate extraction accuracy and human review before storing professional claims.

See [module guide](docs/module-guide.md) and [documentation policy](docs/documentation-policy.md).
