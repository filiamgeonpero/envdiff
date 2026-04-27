"""CLI commands for the audit trail feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.auditor import AuditError, AuditLog, diff_to_audit, load_audit, save_audit
from envdiff.parser import EnvParseError, parse_env_file


def build_audit_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff audit",
        description="Record and display an audit trail of .env changes.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="Record changes between two env files into an audit log")
    rec.add_argument("old", help="Previous .env file")
    rec.add_argument("new", help="Updated .env file")
    rec.add_argument("--log", default=".envdiff_audit.json", help="Path to audit log file")
    rec.add_argument("--env-name", default=None, help="Label for the env file in the log")

    show = sub.add_parser("show", help="Display the audit log")
    show.add_argument("--log", default=".envdiff_audit.json", help="Path to audit log file")
    show.add_argument("--key", default=None, help="Filter by key name")
    show.add_argument("--file", default=None, dest="env_file", help="Filter by env file label")

    return p


def run_audit(args: argparse.Namespace) -> int:
    if args.command == "record":
        return _run_record(args)
    if args.command == "show":
        return _run_show(args)
    return 1


def _run_record(args: argparse.Namespace) -> int:
    try:
        old_env = parse_env_file(Path(args.old))
        new_env = parse_env_file(Path(args.new))
    except (EnvParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    label = args.env_name or args.new
    new_entries = diff_to_audit(old_env, new_env, label)

    log_path = Path(args.log)
    if log_path.exists():
        try:
            log = load_audit(log_path)
        except AuditError as exc:
            print(f"error loading audit log: {exc}", file=sys.stderr)
            return 2
    else:
        log = AuditLog()

    for entry in new_entries:
        log.record(entry)

    save_audit(log, log_path)
    print(f"Recorded {len(new_entries)} change(s) to {log_path}")
    return 0


def _run_show(args: argparse.Namespace) -> int:
    try:
        log = load_audit(Path(args.log))
    except AuditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    entries = log.entries
    if args.key:
        entries = [e for e in entries if e.key == args.key]
    if args.env_file:
        entries = [e for e in entries if e.env_file == args.env_file]

    if not entries:
        print("No matching audit entries.")
        return 0

    for entry in entries:
        print(entry)
    return 0


def main() -> None:  # pragma: no cover
    parser = build_audit_parser()
    args = parser.parse_args()
    sys.exit(run_audit(args))


if __name__ == "__main__":  # pragma: no cover
    main()
