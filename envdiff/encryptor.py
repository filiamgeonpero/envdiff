"""Encrypt and decrypt sensitive values in an env mapping."""
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.redactor import _key_is_sensitive

_MARKER = "enc:"


@dataclass
class EncryptResult:
    original: Dict[str, str]
    encrypted: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changed_keys)

    def summary(self) -> str:
        if not self.has_changes():
            return "No keys encrypted."
        return f"{len(self.changed_keys)} key(s) encrypted: {', '.join(sorted(self.changed_keys))}"


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def _xor_encrypt(value: str, key: bytes) -> str:
    """XOR-based encryption encoded as base64 (demo-grade, not production)."""
    raw = value.encode()
    key_stream = (key[i % len(key)] for i in range(len(raw)))
    cipher = bytes(b ^ k for b, k in zip(raw, key_stream))
    return _MARKER + base64.urlsafe_b64encode(cipher).decode()


def _xor_decrypt(value: str, key: bytes) -> str:
    if not value.startswith(_MARKER):
        return value
    cipher = base64.urlsafe_b64decode(value[len(_MARKER):])
    key_stream = (key[i % len(key)] for i in range(len(cipher)))
    return bytes(b ^ k for b, k in zip(cipher, key_stream)).decode()


def encrypt_env(
    env: Dict[str, str],
    passphrase: str,
    keys: Optional[List[str]] = None,
    sensitive_only: bool = True,
) -> EncryptResult:
    key = _derive_key(passphrase)
    encrypted: Dict[str, str] = {}
    changed: List[str] = []

    for k, v in env.items():
        should_encrypt = (
            (keys is not None and k in keys)
            or (keys is None and sensitive_only and _key_is_sensitive(k))
            or (keys is None and not sensitive_only)
        )
        if should_encrypt and not v.startswith(_MARKER):
            encrypted[k] = _xor_encrypt(v, key)
            changed.append(k)
        else:
            encrypted[k] = v

    return EncryptResult(original=dict(env), encrypted=encrypted, changed_keys=changed)


def decrypt_env(env: Dict[str, str], passphrase: str) -> Dict[str, str]:
    key = _derive_key(passphrase)
    return {k: _xor_decrypt(v, key) for k, v in env.items()}
