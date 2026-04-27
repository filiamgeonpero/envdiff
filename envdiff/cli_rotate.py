"""CLI entry-point for the key-rotation command."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.rotator import apply_rotation, rotate_env


def build_rotate_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Apply a rotation map to one or more .env files."
    if subparsers is not None:
        parser = subparsers.add_parser("rotate", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-rotate", description=desc)

    parser.add_argument("files", nargs="+", metavar="FILE", help=".env files to rotate")
    parser.add_argument(
        "--set",
        dest="patches",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Rotation entry in KEY=VALUE format (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-key output; only print summary",
    )
    return parser


def _parse_rotation_map(patches: List[str]) -> dict:
    rotation_map: dict = {}
    for patch in patches:
        if "=" not in patch:
            print(f"error: invalid rotation entry '{patch}' (expected KEY=VALUE)", file=sys.stderr)
            sys.exit(2)
        key, _, value = patch.partition("=")
        rotation_map[key.strip()] = value
    return rotation_map


def run_rotate(args: argparse.Namespace) -> int:
    rotation_map = _parse_rotation_map(args.patches)
    if not rotation_map:
        print("error: no rotation entries provided (use --set KEY=VALUE)", file=sys.stderr)
        return 2

    exit_code = 0
    for filepath in args.files:
        try:
            env = parse_env_file(filepath)
        except (EnvParseError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        result = rotate_env(env, rotation_map, env_name=filepath)
        if not args.quiet:
            for entry in result.entries:
                if entry.rotated:
                    print(f"  {entry.key}: '{entry.old_value}' -> '{entry.new_value}'")
        print(result.summary())

        if not args.dry_run and result.has_changes:
            updated = apply_rotation(env, result)
            with open(filepath, "w") as fh:
                for key, value in updated.items():
                    fh.write(f"{key}={value}\n")
            exit_code = exit_code or 0

    return exit_code


def main(argv=None) -> None:
    parser = build_rotate_parser()
    args = parser.parse_args(argv)
    sys.exit(run_rotate(args))


if __name__ == "__main__":
    main()
