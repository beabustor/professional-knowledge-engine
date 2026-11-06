"""Command line entry point."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .storage import initialize, private_dir
from .inspector import inspect_archive, save_report
from .importer import import_archive


def main() -> None:
    parser = argparse.ArgumentParser(prog='pke', description='Professional Knowledge Engine')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init', help='Initialize the private SQLite database')
    inspect = sub.add_parser('inspect', help='Inspect export ZIP locally; no API or import')
    inspect.add_argument('zip_path', type=Path)
    importing = sub.add_parser('import', help='Import ChatGPT ZIP into private SQLite')
    importing.add_argument('zip_path', type=Path)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    if args.command == 'init':
        print(f'Private database initialized: {initialize(repo_root)}')
    elif args.command == 'import':
        print(json.dumps(import_archive(args.zip_path, repo_root), ensure_ascii=False, indent=2))
    elif args.command == 'inspect':
        private = private_dir(repo_root)
        report = inspect_archive(args.zip_path)
        destination = save_report(report, private)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f'Private report saved: {destination}')


if __name__ == '__main__':
    main()
