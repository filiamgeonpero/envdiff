"""Profile an env file: count keys, detect patterns, summarise value types."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import re

_SENSITIVE_RE = re.compile(r"(password|secret|token|api_key|apikey|private)", re.I)
_URL_RE = re.compile(r"https?://", re.I)
_NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?$")
_BOOL_RE = re.compile(r"^(true|false|yes|no|1|0)$", re.I)


@dataclass
class ProfileResult:
    env_name: str
    total_keys: int
    empty_values: List[str] = field(default_factory=list)
    sensitive_keys: List[str] = field(default_factory=list)
    url_values: List[str] = field(default_factory=list)
    numeric_values: List[str] = field(default_factory=list)
    boolean_values: List[str] = field(default_factory=list)
    uppercase_keys: int = 0
    lowercase_keys: int = 0

    def summary(self) -> str:
        lines = [
            f"Profile: {self.env_name}",
            f"  Total keys     : {self.total_keys}",
            f"  Empty values   : {len(self.empty_values)}",
            f"  Sensitive keys : {len(self.sensitive_keys)}",
            f"  URL values     : {len(self.url_values)}",
            f"  Numeric values : {len(self.numeric_values)}",
            f"  Boolean values : {len(self.boolean_values)}",
            f"  Uppercase keys : {self.uppercase_keys}",
            f"  Lowercase keys : {self.lowercase_keys}",
        ]
        return "\n".join(lines)


def profile_env(env_name: str, env: Dict[str, str]) -> ProfileResult:
    result = ProfileResult(env_name=env_name, total_keys=len(env))
    for key, value in env.items():
        if not value:
            result.empty_values.append(key)
        if _SENSITIVE_RE.search(key):
            result.sensitive_keys.append(key)
        if _URL_RE.match(value):
            result.url_values.append(key)
        if _NUMERIC_RE.match(value):
            result.numeric_values.append(key)
        if _BOOL_RE.match(value):
            result.boolean_values.append(key)
        if key == key.upper():
            result.uppercase_keys += 1
        elif key == key.lower():
            result.lowercase_keys += 1
    return result
