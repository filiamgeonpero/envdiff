"""CLI entry-point for the 'tag' subcommand."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.tagger import TagRule, tag_env


def build_tag_parser(sub: "argparse._SubParsersAction | None" = None) -> argparse.ArgumentParser:
    kwargs = dict(
        prog="envdiff tag",
        description="Tag env-file keys with user-defined labels.",
    )
    parser = sub.add_parser("tag", **kwargs) if sub else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file to tag.")
    parser.add_argument(
        "--rule",
        dest="rules",
        metavar="PATTERN=TAG",
        action="append",
        default=[],
        help="Tagging rule in PATTERN=TAG form (glob patterns supported). "
             "May be repeated.",
    )
    parser.add_argument(
        "--tag",
        dest="filter_tag",
        metavar="TAG",
        default=None,
        help="Only show keys that carry this tag.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a one-line summary instead of per-key output.",
    )
    return parser


def _parse_rules(raw: List[str]) -> List[TagRule]:
    rules: List[TagRule] = []
    for item in raw:
        if "=" not in item:
            print(f"[error] invalid rule (expected PATTERN=TAG): {item!r}", file=sys.stderr)
            sys.exit(2)
        pattern, tag = item.split("=", 1)
        rules.append(TagRule(pattern=pattern.strip(), tag=tag.strip()))
    return rules


def run_tag(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except EnvParseError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"[error] file not found: {args.file}", file=sys.stderr)
        return 2

    rules = _parse_rules(args.rules)
    result = tag_env(env, rules, env_name=args.file)

    if args.summary:
        print(result.summary())
        return 0

    entries = result.by_tag(args.filter_tag) if args.filter_tag else result.tagged
    if not entries:
        print("(no keys matched)")
        return 0

    for tk in entries:
        print(tk)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_tag_parser()
    args = parser.parse_args()
    sys.exit(run_tag(args))


if __name__ == "__main__":  # pragma: no cover
    main()
