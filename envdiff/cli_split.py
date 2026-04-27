"""CLI entry-point for the *split* command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError
from envdiff.splitter import SplitOptions, split_env


def build_split_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Split a prefixed .env file into per-environment files.")
    parser = parent.add_parser("split", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Merged .env file to split")
    parser.add_argument(
        "--envs", required=True, nargs="+", metavar="ENV",
        help="Environment names to split on (e.g. prod dev staging)",
    )
    parser.add_argument("--sep", default="__", help="Prefix separator (default: __)")
    parser.add_argument(
        "--no-strip", dest="strip", action="store_false", default=True,
        help="Keep the env prefix in output keys",
    )
    parser.add_argument(
        "--fallback", default=None, metavar="ENV",
        help="Environment that receives unmatched keys",
    )
    parser.add_argument(
        "--outdir", default=".", metavar="DIR",
        help="Directory to write output files (default: current dir)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing files")
    return parser


def run_split(args: argparse.Namespace) -> int:
    src = Path(args.file)
    try:
        merged = parse_env_file(src)
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2

    opts = SplitOptions(
        envs=args.envs,
        prefix_sep=args.sep,
        strip_prefix=args.strip,
        fallback_env=args.fallback,
    )
    result = split_env(merged, opts)

    outdir = Path(args.outdir)
    for env, keys in result.envs.items():
        lines = [f"{k}={v}" for k, v in sorted(keys.items())]
        out_path = outdir / f".env.{env}"
        if args.dry_run:
            print(f"# {out_path}")
            print("\n".join(lines) or "(empty)")
        else:
            outdir.mkdir(parents=True, exist_ok=True)
            out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"wrote {out_path} ({len(keys)} key(s))")

    if result.has_unmatched():
        print(f"warning: {len(result.unmatched)} unmatched key(s): {', '.join(result.unmatched)}",
              file=sys.stderr)

    print(result.summary())
    return 0


def main() -> None:  # pragma: no cover
    parser = build_split_parser()
    sys.exit(run_split(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
