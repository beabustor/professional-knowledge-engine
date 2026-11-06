# Professional Knowledge Engine — status

## Implemented
- Privacy-first Python project, SQLite storage outside Git repository.
- Offline ZIP inventory (`inspect`) and transactional ZIP import (`import`) for small exports.
- Raw mapping nodes, parent/children and `current_node` preserved.
- v0.4a: deterministic selected-branch reconstruction (`pke.branches.active_path` and `read_active_path`), without changing SQLite schema.

## Verified in development environment
- `PYTHONPATH=src python -m pytest -q`: 11 passed (including active path, alternative branch, broken links, cycles, SQLite roundtrip).
- Synthetic ZIP import tested previously; no real personal export validated.

## Known limitations
- Active path reconstruction is available as a Python function, not yet a CLI command or full conversation view.
- Existing imported data may have invalid `current_node`/parent chains; reconstruction raises errors rather than silently guessing.
- Reimport of a different ZIP containing the same conversation IDs still fails; versioned snapshots/provenance needed.
- `conversations.json` is loaded into memory and limited to 100 MiB; streaming not yet implemented.
- Attachments and multimodal content are preserved in raw JSON nodes but not interpreted.
- No professional knowledge extraction or profile schema implemented yet.
- No private encrypted backup configured.

## Next
1. Versioned import and overlapping exports, with migration and tests.
2. Streaming/large-export support and real-export compatibility.
3. Schema discovery from professional experience and job advertisements, without conflating requirements with personal capabilities.
