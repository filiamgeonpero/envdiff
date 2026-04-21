"""CLI entry-point: envdiff resolve — expand ${VAR} references in a .env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.resolver import resolve_env


def build_resolve_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff resolve",
        description="Expand \${VAR} references inside a .env file and report unresolved ones.",
    )
    parser = (
        parent.add_parser("resolve", **kwargs)  # type: ignore[arg-type]
        if parent is not None
        else argparse.ArgumentParser(**kwargs)  # type: ignore[arg-type]
    )
    parser.add_argument("file", help="Path to the .env file to resolve.")
    parser.add_argument(
        "--show-resolved",
        action="store_true",
        help="Print the fully resolved key=value pairs.",
    )
    parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help="Exit with code 1 if any references could not be resolved.",
    )
    return parser


def run_resolve(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = resolve_env(env)

    if result.issues:
        print("Unresolved references:")
        for issue in result.issues:
            print(f"  {issue}")
    else:
        print("All references resolved successfully.")

    if args.show_resolved:
        print("\nResolved values:")
        for key, value in result.resolved.items():
            print(f"  {key}={value}")

    if args.fail_on_unresolved and not result.ok:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_resolve_parser()
    args = parser.parse_args()
    sys.exit(run_resolve(args))


if __name__ == "__main__":  # pragma: no cover
    main()
