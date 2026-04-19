"""CLI entry-point for the profile sub-command."""
from __future__ import annotations
import argparse
import sys
from envdiff.parser import parse_env_file, EnvParseError
from envdiff.profiler import profile_env


def build_profile_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    desc = "Show a statistical profile of one or more .env files."
    if parent is not None:
        p = parent.add_parser("profile", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff profile", description=desc)
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to profile")
    p.add_argument("--names", nargs="+", metavar="NAME", help="Optional display names (one per file)")
    return p


def run_profile(args: argparse.Namespace) -> int:
    names = args.names or []
    for idx, path in enumerate(args.files):
        name = names[idx] if idx < len(names) else path
        try:
            env = parse_env_file(path)
        except EnvParseError as exc:
            print(f"Error parsing {path}: {exc}", file=sys.stderr)
            return 2
        except FileNotFoundError:
            print(f"File not found: {path}", file=sys.stderr)
            return 2
        result = profile_env(name, env)
        print(result.summary())
        if idx < len(args.files) - 1:
            print()
    return 0


def main() -> None:  # pragma: no cover
    parser = build_profile_parser()
    args = parser.parse_args()
    sys.exit(run_profile(args))


if __name__ == "__main__":  # pragma: no cover
    main()
