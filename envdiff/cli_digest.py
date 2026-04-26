"""CLI entry-point for the digest sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envdiff.digester import digest_files


def build_digest_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Compute and compare SHA-256 digests of .env files."
    if parent is not None:
        parser = parent.add_parser("digest", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff digest", description=description)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to digest.",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 when digests differ.",
    )
    parser.add_argument(
        "--short",
        action="store_true",
        default=False,
        help="Print only the summary line.",
    )
    return parser


def run_digest(args: argparse.Namespace) -> int:
    paths: List[Path] = []
    for raw in args.files:
        p = Path(raw)
        if not p.exists():
            print(f"error: file not found: {raw}", file=sys.stderr)
            return 2
        paths.append(p)

    result = digest_files(paths)

    if not args.short:
        for entry in result.entries:
            print(f"  {entry}")
        print()

    print(result.summary())

    if args.fail_on_diff and not result.all_match:
        return 1
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_digest_parser()
    args = parser.parse_args(argv)
    sys.exit(run_digest(args))


if __name__ == "__main__":
    main()
