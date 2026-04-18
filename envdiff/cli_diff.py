"""CLI sub-command: line-level diff between two .env files."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from envdiff.differ import diff_files


def build_diff_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Show line-level diff between two .env files"
    if subparsers is not None:
        p = subparsers.add_parser("diff", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff diff", description=desc)
    p.add_argument("file_a", help="First .env file")
    p.add_argument("file_b", help="Second .env file")
    p.add_argument(
        "--only-changes",
        action="store_true",
        help="Print only changed lines",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when differences are found",
    )
    return p


def run_diff(args: argparse.Namespace) -> int:
    path_a = Path(args.file_a)
    path_b = Path(args.file_b)

    for p in (path_a, path_b):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    text_a = path_a.read_text()
    text_b = path_b.read_text()
    result = diff_files(str(path_a), text_a, str(path_b), text_b)

    print(f"--- {result.name_a}")
    print(f"+++ {result.name_b}")

    lines = result.changed_lines() if args.only_changes else result.lines
    for dl in lines:
        print(str(dl))

    if not result.has_changes:
        print("No differences found.")

    if args.exit_code and result.has_changes:
        return 1
    return 0


def main(argv=None) -> None:
    parser = build_diff_parser()
    args = parser.parse_args(argv)
    sys.exit(run_diff(args))


if __name__ == "__main__":
    main()
