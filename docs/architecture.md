# Architecture (initial)

Public package (GitHub) -> reads configured private data directory -> SQLite.

Future pipeline: archive inventory -> normalization -> claim extraction -> evidence validation -> reconciliation -> profile items -> job requirements -> clarification -> CV/learning reports.

Original source files must be preserved. Claims and reconciliation events are append-only in intent; enforcing audit invariants and adding migrations are future work. The current schema is **not** the final data model.

Security: never commit private data, API keys or logs; .gitignore is defense-in-depth, not a security boundary. Use synthetic tests and review every staged diff before pushing.
