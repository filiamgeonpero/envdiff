"""CLI entry-point for the *strip* command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.stripper import StripOptions, strip_env


def build_strip_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Remove keys from an env file that are absent from a reference file."
    if parent is not None:
        parser = parent.add_parser("strip", description=description, help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff strip", description=description)

    parser.add_argument("source", help="Env file to strip.")
    parser.add_argument("reference", help="Reference env file that defines valid keys.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report what would be removed without writing changes.",
    )
    parser.add_argument(
        "--keep-unknown",
        action="store_true",
        default=False,
        help="Keep keys not present in the reference instead of removing them.",
    )
    parser.add_argument(
        "--fail-on-changes",
        action="store_true",
        default=False,
        help="Exit with code 1 if any keys were (or would be) removed.",
    )
    return parser


def run_strip(args: argparse.Namespace) -> int:
    """Execute the strip command and return an exit code."""
    for path in (args.source, args.reference):
        if not Path(path).exists():
            print(f"envdiff strip: file not found: {path}", file=sys.stderr)
            return 2

    try:
        source_env = parse_env_file(args.source)
        reference_env = parse_env_file(args.reference)
    except EnvParseError as exc:
        print(f"envdiff strip: parse error: {exc}", file=sys.stderr)
        return 2

    options = StripOptions(
        dry_run=args.dry_run,
        keep_unknown=args.keep_unknown,
    )
    result = strip_env(source_env, set(reference_env.keys()), options)

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}{result.summary()}")

    if not args.dry_run and result.has_changes():
        out_path = Path(args.source)
        lines: List[str] = []
        for key, value in result.stripped.items():
            lines.append(f"{key}={value}\n")
        out_path.write_text("".join(lines))

    if args.fail_on_changes and result.has_changes():
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_strip_parser()
    args = parser.parse_args()
    sys.exit(run_strip(args))


if __name__ == "__main__":  # pragma: no cover
    main()
