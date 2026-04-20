"""CLI entry point for the template generation command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.merger import merge_envs, MergeOptions
from envdiff.parser import parse_env_file, EnvParseError
from envdiff.templater import TemplateOptions, build_template


def build_template_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff template",
        description="Generate a .env template from one or more env files.",
    )
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to merge")
    p.add_argument(
        "--include-values",
        action="store_true",
        help="Use first found value instead of placeholder",
    )
    p.add_argument(
        "--placeholder",
        default="<FILL_ME>",
        metavar="TEXT",
        help="Placeholder text for missing values (default: <FILL_ME>)",
    )
    p.add_argument(
        "--no-comments",
        action="store_true",
        help="Suppress comment annotations in output",
    )
    p.add_argument(
        "--group-by-prefix",
        action="store_true",
        help="Group keys by their underscore-delimited prefix",
    )
    p.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write template to FILE instead of stdout",
    )
    return p


def run_template(args: argparse.Namespace) -> int:
    envs: dict[str, dict[str, str]] = {}
    for path in args.files:
        try:
            envs[path] = parse_env_file(path)
        except EnvParseError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2

    merge_result = merge_envs(envs, MergeOptions())
    opts = TemplateOptions(
        include_values=args.include_values,
        placeholder=args.placeholder,
        add_comments=not args.no_comments,
        group_by_prefix=args.group_by_prefix,
    )
    template = build_template(merge_result, opts)
    rendered = template.render()

    if args.output:
        Path(args.output).write_text(rendered)
        print(f"Template written to {args.output} ({template.total_keys} keys).")
    else:
        sys.stdout.write(rendered)

    return 0


def main() -> None:
    parser = build_template_parser()
    args = parser.parse_args()
    sys.exit(run_template(args))


if __name__ == "__main__":
    main()
