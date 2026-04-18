"""Lint .env files for common style and correctness issues."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class LintIssue:
    line_number: int
    key: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line_number}: {self.key} — {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def lint_env_file(path: str) -> LintResult:
    """Read a .env file and return a LintResult with any style/correctness issues."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    with open(path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip("\n")
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            if "=" not in line:
                result.issues.append(LintIssue(lineno, "", "line has no '=' separator", "error"))
                continue

            key, _, value = line.partition("=")
            key = key.strip()

            if not key:
                result.issues.append(LintIssue(lineno, key, "empty key", "error"))
                continue

            if key != key.upper():
                result.issues.append(LintIssue(lineno, key, "key is not uppercase", "warning"))

            if " " in key:
                result.issues.append(LintIssue(lineno, key, "key contains spaces", "error"))

            if value != value.strip():
                result.issues.append(LintIssue(lineno, key, "value has leading or trailing whitespace", "warning"))

            if key in seen_keys:
                result.issues.append(LintIssue(
                    lineno, key,
                    f"duplicate key (first seen on line {seen_keys[key]})",
                    "error"
                ))
            else:
                seen_keys[key] = lineno

    return result
