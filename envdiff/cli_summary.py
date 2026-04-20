"""CLI entry-point for the `envdiff summary` sub-command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.comparator import compare_envs
from envdiff.differ_summary import summarise_many, MultiSummary
from envdiff.parser import parse_env_file, EnvParseError


def build_summary_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Summarise differences across multiple .env file pairs."
    )
    if parent is not None:
        parser = parent.add_parser("summary", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff summary", **kwargs)

    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Two or more .env files to compare in sequence (a vs b, b vs c, …).",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        default=False,
        help="Exit with code 1 if any differences are found.",
    )
    return parser


def _print_summary(ms: MultiSummary) -> None:
    if not ms.any_differences:
        print("All env pairs are identical.")
        return

    for pair in ms.pairs:
        status = "OK" if (pair.missing_count == 0 and pair.mismatch_count == 0) else "DIFF"
        print(
            f"[{status}] {pair.env_a} vs {pair.env_b}: "
            f"{pair.missing_count} missing, {pair.mismatch_count} mismatched, "
            f"{pair.match_count} matching (of {pair.total_keys} differing keys)"
        )

    worst = ms.worst_pair()
    if worst:
        print(
            f"\nWorst pair: {worst.env_a} vs {worst.env_b} "
            f"({worst.missing_count + worst.mismatch_count} total issues)"
        )


def run_summary(args: argparse.Namespace) -> int:
    if len(args.files) < 2:
        print("error: provide at least two files to compare.", file=sys.stderr)
        return 2

    paths = [Path(f) for f in args.files]
    envs = []
    for p in paths:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
        try:
            envs.append((p.name, parse_env_file(str(p))))
        except EnvParseError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    results = []
    for (name_a, env_a), (name_b, env_b) in zip(envs, envs[1:]):
        results.append(compare_envs(env_a, name_a, env_b, name_b))

    ms = summarise_many(results)
    _print_summary(ms)
    return 1 if (args.fail_on_diff and ms.any_differences) else 0


def main() -> None:  # pragma: no cover
    parser = build_summary_parser()
    args = parser.parse_args()
    sys.exit(run_summary(args))


if __name__ == "__main__":  # pragma: no cover
    main()
