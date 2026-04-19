"""CLI entry point for applying a rename map to an env diff report."""
import argparse
import json
import sys
from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare_envs
from envdiff.renamer import RenameMap, rename_result
from envdiff.reporter import format_report, ReportOptions


def build_rename_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-rename",
        description="Compare .env files with key renaming applied.",
    )
    p.add_argument("envfiles", nargs="+", metavar="FILE", help=".env files to compare")
    p.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        default=[],
        help="Rename a key before reporting (repeatable)",
    )
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    return p


def run_rename(args: argparse.Namespace) -> int:
    envs = {}
    for path in args.envfiles:
        try:
            envs[path] = parse_env_file(path)
        except (EnvParseError, FileNotFoundError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    rename_map = RenameMap()
    for entry in args.rename:
        if "=" not in entry:
            print(f"error: invalid rename '{entry}', expected OLD=NEW", file=sys.stderr)
            return 2
        old, new = entry.split("=", 1)
        rename_map.add(old.strip(), new.strip())

    result = compare_envs(envs)
    renamed = rename_result(result, rename_map)

    opts = ReportOptions(color=not args.no_color)
    # Build a temporary CompareResult-like object for the reporter
    from envdiff.comparator import CompareResult
    reportable = CompareResult(envs=renamed.envs, diffs=renamed.diffs, env_data=result.env_data)
    print(format_report(reportable, opts))
    return 0


def main() -> None:
    parser = build_rename_parser()
    args = parser.parse_args()
    sys.exit(run_rename(args))


if __name__ == "__main__":
    main()
