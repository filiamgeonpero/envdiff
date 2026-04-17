"""Validate .env keys against a required schema."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class KeyRule:
    required: bool = True
    pattern: Optional[str] = None  # regex the value must match
    allow_empty: bool = False


@dataclass
class ValidationError:
    key: str
    env_name: str
    message: str

    def __str__(self) -> str:
        return f"[{self.env_name}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    def add(self, key: str, env_name: str, message: str) -> None:
        self.errors.append(ValidationError(key=key, env_name=env_name, message=message))


def validate_env(
    env: Dict[str, str],
    schema: Dict[str, KeyRule],
    env_name: str = "env",
) -> ValidationResult:
    """Validate a parsed env dict against a schema of KeyRules."""
    result = ValidationResult()

    for key, rule in schema.items():
        if key not in env:
            if rule.required:
                result.add(key, env_name, "required key is missing")
            continue

        value = env[key]

        if not rule.allow_empty and value == "":
            result.add(key, env_name, "value must not be empty")
            continue

        if rule.pattern is not None and value != "":
            if not re.fullmatch(rule.pattern, value):
                result.add(
                    key,
                    env_name,
                    f"value {value!r} does not match pattern {rule.pattern!r}",
                )

    return result
