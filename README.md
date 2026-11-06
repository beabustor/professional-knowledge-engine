# Professional Knowledge Engine

Privacy-first Python tooling for building an evidence-grounded professional knowledge record from ChatGPT exports and explicitly selected notes. **This is an early-stage data infrastructure project, not yet an automated competency assessor or CV generator.**

## Implemented (through v0.5b)

- Offline ZIP inventory (`inspect`) and transactional import (`import`) with per-export conversation snapshots.
- Canonical first-import conversation graph, branch traversal and explicit snapshot version readers (Python APIs).
- Exact quote verification against a chosen snapshot and persistent evidence references (Python APIs).
- Incremental manual JSON intake (`import-manual`) with exact deduplication; manual entries remain self-reported and pending review.
- Pending manual entry count (`pending`) and optional private details (`pending --details`).

## Windows PowerShell setup

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PK_DATA_DIR = "$HOME\Documents\professional-knowledge-private"
python -m pke.cli init
python -m pytest -q
```

Set `PK_DATA_DIR` again in a new terminal. It **must be outside** the public Git repository. You can run `pke` instead of `python -m pke.cli` when the installed command is available.

## Commands

```powershell
python -m pke.cli inspect "C:\path\to\chatgpt-export.zip"
python -m pke.cli import "C:\path\to\chatgpt-export.zip"
python -m pke.cli import-manual "C:\path\to\professional-notes.json"
python -m pke.cli pending
python -m pke.cli pending --details
```

The manual JSON format and allowed fields are documented in [the module guide](docs/module-guide.md). Do not use a real personal export until you have a private SQLite backup and have validated compatibility on a safe copy.

## Where information goes

- Private SQLite: `$env:PK_DATA_DIR\database\profile.sqlite`.
- Private inventory report: `$env:PK_DATA_DIR\evaluations\archive_inventory.json`.
- The public repository contains only code, tests and documentation; **never commit** exports, databases, credentials or personal notes.

## Important distinctions

- A quote verified against a snapshot proves **textual provenance**, not factual accuracy or professional competence.
- A manual note is marked `self_reported` and `pending`, not cryptographically tied to ChatGPT history.
- Identical ZIPs are skipped by SHA-256; a new ZIP may add snapshots of existing conversations. Canonical conversation rows retain their first imported version.
- No LLM, provider integration, automatic job matching, CV generation, encrypted backups or production migration system exists yet.

## Documentation

- [Module responsibilities, call graph and data contracts](docs/module-guide.md)
- [Technical architecture](docs/architecture.md)
- [Project status and verification](PROJECT_STATUS.md)
- [Documentation maintenance policy](docs/documentation-policy.md)

The suite had **26 passing synthetic tests** reported by the maintainer after v0.5b. Real ChatGPT exports and production workloads have not yet been validated.
