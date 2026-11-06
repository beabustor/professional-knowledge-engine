# Documentation policy

Every feature change should update documentation **in the same commit** as its implementation:

1. Update root `README.md` if commands, installation or user workflow change.
2. Update `docs/module-guide.md` if module responsibility, function contracts, dependencies or call paths change.
3. Update `docs/architecture.md` if storage schema, provenance, security boundaries or major design decisions change.
4. Update `PROJECT_STATUS.md` with implemented, verified, and pending work; distinguish synthetic tests from real-data validation.
5. Add concise Python docstrings for public functions and comments only where intent or invariants are non-obvious. Avoid copying long documentation into every file.
6. Run `python -m pytest -q` and inspect `git diff --cached --check` before commit; never commit private data.

Document actual behavior, known limitations and compatibility assumptions. Do not mark features complete based only on design notes.
