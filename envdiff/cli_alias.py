"""CLI entry point: resolve key aliases across .env files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.aliaser import AliasMap, apply_aliases
from envdiff.parser import parse_env_file, EnvParseError


def build_alias_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff alias",
        description="Resolve aliased keys in .env files to their canonical names.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to process")
    p.add_argument(
        "--alias",
        action="append",
        metavar="CANONICAL=ALIAS[,ALIAS...]",
        default=[],
        dest="aliases",
        help="Define an alias mapping, e.g. DATABASE_URL=DB_URL,DB_CONNECTION",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-file summaries; only print final counts.",
    )
    return p


def _build_alias_map(alias_specs: list[str]) -> AliasMap:
    am = AliasMap()
    for spec in alias_specs:
        if "=" not in spec:
            print(f"Warning: ignoring malformed alias spec '{spec}'", file=sys.stderr)
            continue
        canonical, _, rest = spec.partition("=")
        aliases = [a.strip() for a in rest.split(",") if a.strip()]
        am.add(canonical.strip(), *aliases)
    return am


def run_alias(args: argparse.Namespace) -> int:
    alias_map = _build_alias_map(args.aliases)
    total_renames = 0

    for filepath in args.files:
        path = Path(filepath)
        try:
            env = parse_env_file(path)
        except EnvParseError as exc:
            print(f"Error parsing {filepath}: {exc}", file=sys.stderr)
            return 2
        except FileNotFoundError:
            print(f"File not found: {filepath}", file=sys.stderr)
            return 2

        result = apply_aliases(env, alias_map)
        total_renames += result.rename_count

        if not args.quiet:
            print(f"[{filepath}] {result.summary()}")

    if args.quiet or len(args.files) > 1:
        print(f"Total aliases resolved: {total_renames}")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_alias_parser()
    args = parser.parse_args()
    sys.exit(run_alias(args))


if __name__ == "__main__":  # pragma: no cover
    main()
