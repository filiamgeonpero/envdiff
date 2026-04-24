"""CLI entry-point: envdiff graph — show variable dependency graph."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.grapher import build_graph, GraphResult


def build_graph_parser(subparsers=None) -> argparse.ArgumentParser:  # type: ignore[assignment]
    desc = "Display the dependency graph for variables in a .env file."
    if subparsers is not None:
        p = subparsers.add_parser("graph", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff graph", description=desc)
    p.add_argument("file", help="Path to the .env file to analyse.")
    p.add_argument(
        "--cycles-only",
        action="store_true",
        help="Only report keys that participate in a cycle.",
    )
    p.add_argument(
        "--roots",
        action="store_true",
        help="List root keys (no dependencies).",
    )
    p.add_argument(
        "--leaves",
        action="store_true",
        help="List leaf keys (nothing depends on them).",
    )
    return p


def _print_graph(result: GraphResult, *, cycles_only: bool, roots: bool, leaves: bool) -> None:
    if cycles_only:
        cycles = result.cycle_keys()
        if cycles:
            print("Cyclic keys:")
            for k in cycles:
                print(f"  {k}")
        else:
            print("No cycles detected.")
        return

    if roots:
        print("Root keys (no dependencies):")
        for k in sorted(result.roots()):
            print(f"  {k}")
        return

    if leaves:
        print("Leaf keys (used by nothing):")
        for k in sorted(result.leaves()):
            print(f"  {k}")
        return

    print("Dependency graph:")
    for key in sorted(result.nodes):
        node = result.nodes[key]
        deps = ", ".join(node.depends_on) if node.depends_on else "-"
        print(f"  {key}: depends_on=[{deps}]")

    cycles = result.cycle_keys()
    if cycles:
        print(f"\nWarning: cycles detected among: {', '.join(cycles)}")


def run_graph(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    try:
        env = parse_env_file(path)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = build_graph(env)
    _print_graph(
        result,
        cycles_only=args.cycles_only,
        roots=args.roots,
        leaves=args.leaves,
    )
    return 0


def main() -> None:  # pragma: no cover
    parser = build_graph_parser()
    args = parser.parse_args()
    sys.exit(run_graph(args))


if __name__ == "__main__":  # pragma: no cover
    main()
