"""CLI entry-point: envdiff deduplicate

Usage examples
--------------
  envdiff-deduplicate .env
  envdiff-deduplicate .env --strategy first
  envdiff-deduplicate .env --strategy error
  envdiff-deduplicate .env --output .env.clean
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.deduplicator import Strategy, DeduplicateError, deduplicate_env


def build_deduplicate_parser(parent: argparse._SubParsersAction | None = None):
    description = "Detect and resolve duplicate keys inside a single .env file."
    if parent is not None:
        parser = parent.add_parser("deduplicate", description=description)
    else:
        parser = argparse.ArgumentParser(
            prog="envdiff-deduplicate", description=description
        )
    parser.add_argument("file", help="Path to the .env file to process.")
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in Strategy],
        default=Strategy.LAST.value,
        help="How to resolve duplicates: first, last (default), or error.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write deduplicated env to this file (default: print to stdout).",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress summary output.",
    )
    return parser


def run_deduplicate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    raw_pairs: list[tuple[str, str]] = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            raw_pairs.append((key.strip(), value.strip()))

    strategy = Strategy(args.strategy)

    try:
        result = run_deduplicate._deduplicate(raw_pairs, strategy)
    except DeduplicateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(result.summary())

    output_lines = [f"{k}={v}" for k, v in result.env.items()]
    output_text = "\n".join(output_lines) + "\n"

    if args.output:
        Path(args.output).write_text(output_text)
    else:
        print(output_text, end="")

    return 0


# Allow tests to monkey-patch the deduplication call.
run_deduplicate._deduplicate = deduplicate_env  # type: ignore[attr-defined]


def main() -> None:  # pragma: no cover
    parser = build_deduplicate_parser()
    args = parser.parse_args()
    sys.exit(run_deduplicate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
