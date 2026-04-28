"""CLI entry-point for encrypting/decrypting .env file values."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.encryptor import decrypt_env, encrypt_env
from envdiff.parser import EnvParseError, parse_env_file


def build_encrypt_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-encrypt",
        description="Encrypt or decrypt sensitive values in a .env file.",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--passphrase",
        required=True,
        help="Passphrase used to derive the encryption key",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument(
        "--decrypt",
        action="store_true",
        default=False,
        help="Decrypt values instead of encrypting them",
    )
    p.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Encrypt only these specific keys (default: all sensitive keys)",
    )
    p.add_argument(
        "--all",
        dest="all_keys",
        action="store_true",
        default=False,
        help="Encrypt all keys, not just sensitive ones",
    )
    p.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Overwrite the source file with the result",
    )
    return p


def run_encrypt(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        env = parse_env_file(str(path))
    except EnvParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.decrypt:
        result_env = decrypt_env(env, args.passphrase)
        changed = sum(1 for k in env if env[k] != result_env[k])
        print(f"Decrypted {changed} key(s).")
    else:
        result = encrypt_env(
            env,
            args.passphrase,
            keys=args.keys,
            sensitive_only=not args.all_keys,
        )
        result_env = result.encrypted
        print(result.summary())

    if args.in_place:
        lines = [f"{k}={v}" for k, v in result_env.items()]
        path.write_text("\n".join(lines) + "\n")
        print(f"Written to {path}")
    else:
        for k, v in result_env.items():
            print(f"{k}={v}")

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_encrypt(build_encrypt_parser().parse_args()))
