"""Command-line interface for envdiff."""
import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.comparator import compare
from envdiff.reporter import format_report, format_summary, ReportOptions


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help="Two or more .env files to compare")
    p.add_argument("--no-color", action="store_true", help="Disable colored output")
    p.add_argument("--show-values", action="store_true", help="Show differing values in output")
    p.add_argument("--summary", action="store_true", help="Print summary line at the end")
    p.add_argument("--exit-code", action="store_true", help="Exit with code 1 if differences found")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if len(args.files) < 2:
        parser.error("At least two files are required.")

    envs = {}
    for filepath in args.files:
        path = Path(filepath)
        try:
            envs[path.name] = parse_env_file(path)
        except FileNotFoundError:
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            return 2
        except EnvParseError as exc:
            print(f"Error parsing {filepath}: {exc}", file=sys.stderr)
            return 2

    names = list(envs.keys())
    env_list = list(envs.values())

    # Compare first file against all others
    base_name, base_env = names[0], env_list[0]
    has_any_diff = False

    options = ReportOptions(color=not args.no_color, show_values=args.show_values)

    for i in range(1, len(names)):
        result = compare(base_env, env_list[i], base_name, names[i])
        print(format_report(result, [base_name, names[i]], options))
        if args.summary:
            print(format_summary(result))
        if result.has_differences():
            has_any_diff = True

    if args.exit_code and has_any_diff:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
