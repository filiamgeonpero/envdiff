"""CLI entry-point for the patch sub-command."""
from __future__ import annotations

import argparse
import sys
from typing import Dict

from envdiff.patcher import patch_env_file


def build_patch_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Apply key=value patches to an env file."
    if parent is not None:
        p = parent.add_parser("patch", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff-patch", description=desc)
    p.add_argument("file", help="Path to the .env file to patch")
    p.add_argument(
        "patches",
        nargs="+",
        metavar="KEY=VALUE",
        help="One or more key=value pairs to apply",
    )
    p.add_argument(
        "--no-add",
        action="store_true",
        help="Do not add keys that are missing from the file",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to disk",
    )
    return p


def _parse_patches(raw: list[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            print(f"error: invalid patch '{item}' — expected KEY=VALUE", file=sys.stderr)
            sys.exit(2)
        key, _, val = item.partition("=")
        result[key.strip()] = val
    return result


def run_patch(args: argparse.Namespace) -> int:
    patch = _parse_patches(args.patches)
    try:
        result = patch_env_file(
            args.file,
            patch,
            add_missing=not args.no_add,
            dry_run=args.dry_run,
        )
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    prefix = "[dry-run] " if args.dry_run else ""
    print(f"{prefix}{args.file}: {result.summary()}")
    if args.dry_run and result.has_changes:
        print(result.content, end="")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_patch_parser()
    args = parser.parse_args()
    sys.exit(run_patch(args))


if __name__ == "__main__":  # pragma: no cover
    main()
