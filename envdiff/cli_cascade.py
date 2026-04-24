"""CLI entry-point for the *cascade* sub-command.

Usage example::

    envdiff cascade base.env staging.env production.env

Files are applied left-to-right; the rightmost file has the highest
priority (last-writer-wins).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.cascader import cascade_envs


def build_cascade_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    description = "Cascade .env files in priority order (last file wins)."
    if parent is not None:
        parser = parent.add_parser("cascade", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff cascade", description=description)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files ordered from lowest to highest priority",
    )
    parser.add_argument(
        "--show-exclusive",
        action="store_true",
        help="list keys that appear in only one file",
    )
    parser.add_argument(
        "--show-overrides",
        action="store_true",
        help="list keys that were overridden by a later file",
    )
    return parser


def run_cascade(args: argparse.Namespace) -> int:
    named_envs = []
    for path_str in args.files:
        path = Path(path_str)
        if not path.exists():
            print(f"error: file not found: {path_str}", file=sys.stderr)
            return 2
        try:
            env = parse_env_file(path)
        except EnvParseError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        named_envs.append((path.name, env))

    result = cascade_envs(named_envs)
    print(result.summary())

    if args.show_exclusive:
        if result.exclusive:
            print("\nExclusive keys:")
            for key, source in sorted(result.exclusive.items()):
                print(f"  {key}  [{source}]")
        else:
            print("\nNo exclusive keys.")

    if args.show_overrides:
        overridden = [
            e for e in result.entries.values() if e.overridden_by
        ]
        if overridden:
            print("\nOverridden keys:")
            for entry in sorted(overridden, key=lambda e: e.key):
                print(f"  {entry}")
        else:
            print("\nNo overridden keys.")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_cascade_parser()
    args = parser.parse_args()
    sys.exit(run_cascade(args))


if __name__ == "__main__":  # pragma: no cover
    main()
