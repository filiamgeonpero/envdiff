"""Formatting and reporting of comparison results."""
from dataclasses import dataclass
from typing import List
from envdiff.comparator import CompareResult


ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_GREEN = "\033[32m"
ANSI_RESET = "\033[0m"


@dataclass
class ReportOptions:
    color: bool = True
    show_values: bool = False


def _c(text: str, code: str, options: ReportOptions) -> str:
    if options.color:
        return f"{code}{text}{ANSI_RESET}"
    return text


def format_report(result: CompareResult, env_names: List[str], options: ReportOptions = None) -> str:
    if options is None:
        options = ReportOptions()

    lines = []
    label = " vs ".join(env_names)
    lines.append(f"envdiff report: {label}")
    lines.append("-" * 40)

    if not result.has_differences():
        lines.append(_c("No differences found.", ANSI_GREEN, options))
        return "\n".join(lines)

    if result.missing_keys:
        lines.append("Missing keys:")
        for diff in result.missing_keys:
            msg = f"  [{diff.missing_in}] {diff.key}"
            lines.append(_c(msg, ANSI_RED, options))

    if result.mismatched_values:
        lines.append("Mismatched values:")
        for diff in result.mismatched_values:
            if options.show_values:
                msg = f"  {diff.key}: {diff.value_a!r} != {diff.value_b!r}"
            else:
                msg = f"  {diff.key}"
            lines.append(_c(msg, ANSI_YELLOW, options))

    return "\n".join(lines)


def format_summary(result: CompareResult) -> str:
    missing = len(result.missing_keys)
    mismatched = len(result.mismatched_values)
    return f"Summary: {missing} missing key(s), {mismatched} mismatched value(s)."
