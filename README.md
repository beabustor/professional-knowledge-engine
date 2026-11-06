# Professional Knowledge Engine

Privacy-first, evidence-grounded Python tooling to reconstruct professional experience from conversation archives. **Early-stage data infrastructure, not a CV generator or an automated competence assessor.**

## Implemented (v0.4b)

- `init`: initialize a private SQLite database outside the repository.
- `inspect`: inventory a ChatGPT export ZIP locally and save aggregate metadata to the private directory; no message text in the report.
- `import`: stream `conversations.json` with `ijson` and import raw conversation nodes and messages into SQLite.
- Preserve alternative conversation branches and the selected `current_node`; reconstruct the selected path via the Python functions `pke.branches.active_path` and `read_active_path` (not yet a CLI command).
- Detect an identical previously imported ZIP using its SHA-256; preserve complete per-export conversation snapshots for overlapping ZIPs.

**Versioning limitation:** canonical conversation/message/node records represent the first imported version. Later versions are stored in `conversation_snapshots` but are not yet projected into canonical tables or exposed through a version-selection CLI. Existing pre-v0.4b imports are not retroactively added to the snapshot table.

## Windows setup (PowerShell)

From the repository directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PK_DATA_DIR = "$HOME\Documents\professional-knowledge-private"
python -m pke.cli init
python -m pytest -q
```

`PK_DATA_DIR` **must be outside** the Git repository. Set it again in each new PowerShell session, unless configured securely elsewhere.

## Commands

After activation and setting `PK_DATA_DIR`:

```powershell
python -m pke.cli inspect "C:\path\to\chatgpt-export.zip"
python -m pke.cli import "C:\path\to\chatgpt-export.zip"
```

`inspect` saves `evaluations/archive_inventory.json` under `PK_DATA_DIR`. `import` writes to `database/profile.sqlite` under `PK_DATA_DIR`. **Do not import a personal archive until a private database backup has been made and the real-export validation is complete.** Neither command uploads the archive to a service.

## Privacy and evidence principles

- Never commit ZIP exports, private databases, logs containing personal data, credentials, or reports.
- Source conversations are evidence to examine, not automatic proof of professional capability. Assistant-authored claims must not be attributed to the user.
- Preserve provenance, uncertainty, negative evidence and corrections; LLM extraction, when introduced, must be reviewable.
- `.gitignore` is a precaution, not a privacy guarantee. Review `git diff --cached` before publishing.

## Verification and limitations

- **13 tests passed** on the maintainer's Windows environment using synthetic data for v0.4b; no real personal ChatGPT export has been validated.
- The importer streams **one conversation at a time**, not individual nodes within a conversation; unusually large single conversations can still consume substantial memory.
- Archive size limits remain in place; attachments and multimodal data are retained as raw JSON where present, not interpreted.
- No version-selection reader, encrypted backup, automatic migration backup, professional claim extraction, job matching or CV generation yet.

See [project status](PROJECT_STATUS.md) and [technical architecture](docs/architecture.md).
