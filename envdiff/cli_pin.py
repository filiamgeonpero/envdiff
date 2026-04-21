"""CLI entry point for the `envdiff pin` command.

Usage:
  envdiff-pin save <file> --output <pin-file>
  envdiff-pin check <file> --pin <pin-file> [--fail-on-drift]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import EnvParseError, parse_env_file
from envdiff.pinner import PinError, detect_drift, load_pin, save_pin


def build_pin_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-pin",
        description="Pin env values and detect drift over time.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    save_p = sub.add_parser("save", help="Pin current values from an env file.")
    save_p.add_argument("file", help="Path to the .env file to pin.")
    save_p.add_argument("--output", required=True, help="Destination pin file (.pin.json).")

    check_p = sub.add_parser("check", help="Compare current env file against a pin.")
    check_p.add_argument("file", help="Path to the current .env file.")
    check_p.add_argument("--pin", required=True, help="Path to the pin file to compare against.")
    check_p.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit with code 1 when drift is detected.",
    )

    return parser


def run_pin(args: argparse.Namespace) -> int:
    if args.command == "save":
        try:
            env = parse_env_file(Path(args.file))
        except (EnvParseError, FileNotFoundError) as exc:
            print(f"Error reading env file: {exc}", file=sys.stderr)
            return 2
        save_pin(env, Path(args.output))
        print(f"Pinned {len(env)} key(s) to {args.output}")
        return 0

    # command == "check"
    try:
        current = parse_env_file(Path(args.file))
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"Error reading env file: {exc}", file=sys.stderr)
        return 2

    try:
        pinned = load_pin(Path(args.pin))
    except PinError as exc:
        print(f"Error loading pin file: {exc}", file=sys.stderr)
        return 2

    env_name = Path(args.file).name
    result = detect_drift(pinned, current, env_name=env_name)
    print(result.summary())

    if result.has_drift and args.fail_on_drift:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_pin_parser()
    args = parser.parse_args()
    sys.exit(run_pin(args))


if __name__ == "__main__":  # pragma: no cover
    main()
