"""CLI sub-command: envdiff lint <file> [<file> ...]"""
from __future__ import annotations
import sys
from argparse import ArgumentParser, Namespace
from envdiff.linter import lint_env_file


def build_lint_parser(sub) -> None:
    """Attach the 'lint' sub-command to an existing subparsers object."""
    p: ArgumentParser = sub.add_parser(
        "lint",
        help="Lint one or more .env files for style and correctness issues.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env file(s) to lint")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any warnings are present (in addition to errors).",
    )
    p.set_defaults(func=run_lint)


def _print_issues(filepath: str, result) -> None:
    """Print lint issues for a single file to stdout."""
    if not result.issues:
        print(f"{filepath}: OK")
        return
    print(f"{filepath}:")
    for issue in result.issues:
        print(f"  {issue}")


def run_lint(args: Namespace) -> int:
    """Run the lint command, returning an exit code."""
    any_error = False
    any_warning = False

    for filepath in args.files:
        try:
            result = lint_env_file(filepath)
        except FileNotFoundError:
            print(f"error: file not found: {filepath}", file=sys.stderr)
            return 2

        _print_issues(filepath, result)

        if result.errors:
            any_error = True
        if result.warnings:
            any_warning = True

    if any_error:
        return 1
    if args.strict and any_warning:
        return 1
    return 0


def main(argv=None) -> None:
    parser = ArgumentParser(prog="envdiff-lint", description="Lint .env files.")
    subs = parser.add_subparsers()
    build_lint_parser(subs)

    # Allow direct invocation without sub-command token
    parser.add_argument("files", nargs="*", metavar="FILE")
    parser.add_argument("--strict", action="store_true")
    parser.set_defaults(func=run_lint)

    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
