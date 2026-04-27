"""CLI entry-point for the *promote* command."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.promoter import promote_env


def build_promote_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    description = "Promote keys from a source .env file into a target .env file."
    if parent is not None:
        parser = parent.add_parser("promote", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-promote", description=description)

    parser.add_argument("source", help="Source .env file (authoritative)")
    parser.add_argument("target", help="Target .env file to promote into")
    parser.add_argument(
        "--keys", "-k",
        nargs="+",
        metavar="KEY",
        help="Promote only these keys (default: all source keys)",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        default=False,
        help="Skip keys that already exist in the target",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print changes without writing the target file",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        default=False,
        help="Suppress per-key output; only print the summary",
    )
    return parser


def run_promote(args: argparse.Namespace) -> int:
    try:
        source_env = parse_env_file(args.source)
    except (EnvParseError, OSError) as exc:
        print(f"error: cannot read source file '{args.source}': {exc}", file=sys.stderr)
        return 2

    try:
        target_env = parse_env_file(args.target)
    except (EnvParseError, OSError) as exc:
        print(f"error: cannot read target file '{args.target}': {exc}", file=sys.stderr)
        return 2

    result = promote_env(
        source_env,
        target_env,
        keys=args.keys,
        overwrite=not args.no_overwrite,
        source_name=args.source,
        target_name=args.target,
    )

    if not args.quiet:
        for change in result.changes:
            print(f"  {change}")
        for key in result.skipped:
            print(f"  skip: {key}")

    print(result.summary())

    if not args.dry_run and result.has_changes:
        lines: List[str] = []
        for key, value in result.promoted.items():
            lines.append(f"{key}={value}\n")
        with open(args.target, "w") as fh:
            fh.writelines(lines)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_promote_parser()
    sys.exit(run_promote(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
