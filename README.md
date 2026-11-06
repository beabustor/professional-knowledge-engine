# Professional Knowledge Engine

Privacy-first, evidence-grounded tooling for reconstructing professional experience from conversation archives. **Early scaffold, not a working CV generator.**

## Design principles

- Raw personal conversations and profile databases stay **outside Git**.
- Preserve original sources and evidence; never equate an assistant's statement with a user's professional claim.
- Keep claims, limitations, uncertainties and corrections distinct.
- Treat LLM output as untrusted proposals requiring validation.
- Public tests use synthetic data only.

## Windows setup (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PK_DATA_DIR = "$HOME\Documents\professional-knowledge-private"
python -m pke.cli init
python -m pytest -q
```

**Never** set `PK_DATA_DIR` inside this repository. The `init` command refuses it.

## Status

Only the initial project scaffold and a minimal SQLite schema are implemented. No conversation import, LLM processing, evidence reconciliation, job matching or CV generation is implemented yet.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) and [docs/architecture.md](docs/architecture.md).

## Inspect a ChatGPT export locally (no network/API calls)

After activating the virtual environment and setting `PK_DATA_DIR`:

```powershell
python -m pke.cli inspect "C:\path\to\your\chatgpt-export.zip"
```

The command prints aggregate counts and saves `evaluations/archive_inventory.json` in the private data folder. It does not extract or upload conversations. **Do not publish the ZIP or private report.** For large exports, `ijson` is installed as a project dependency to avoid loading the entire conversation file into memory.

## Publish code to GitHub

Create a public, empty repository called `professional-knowledge-engine` (do not initialize it with a README). Then, in the local project directory:

```powershell
git init
git branch -M main
git status --short
git add .gitignore .env.example README.md PROJECT_STATUS.md pyproject.toml src tests docs
git diff --cached --name-only
git commit -m "Initial privacy-first scaffold and export inspector"
git remote add origin https://github.com/YOUR_USERNAME/professional-knowledge-engine.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Inspect staged files carefully before committing. Do not add private exports, databases, logs or credentials.
