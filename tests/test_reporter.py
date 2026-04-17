"""Tests for envdiff.reporter module."""
import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.reporter import format_report, format_summary, ReportOptions


def make_result(missing=None, mismatched=None):
    return CompareResult(
        missing_keys=missing or [],
        mismatched_values=mismatched or [],
    )


NO_COLOR = ReportOptions(color=False)


def test_no_differences_message():
    result = make_result()
    report = format_report(result, ["dev", "prod"], NO_COLOR)
    assert "No differences found." in report


def test_report_header_contains_env_names():
    result = make_result()
    report = format_report(result, ["staging", "production"], NO_COLOR)
    assert "staging vs production" in report


def test_missing_key_appears_in_report():
    diff = KeyDiff(key="SECRET_KEY", missing_in="prod")
    result = make_result(missing=[diff])
    report = format_report(result, ["dev", "prod"], NO_COLOR)
    assert "SECRET_KEY" in report
    assert "[prod]" in report


def test_mismatched_value_appears_in_report():
    diff = KeyDiff(key="DB_HOST", value_a="localhost", value_b="db.prod.example.com")
    result = make_result(mismatched=[diff])
    report = format_report(result, ["dev", "prod"], NO_COLOR)
    assert "DB_HOST" in report
    assert "Mismatched" in report


def test_show_values_option_reveals_values():
    diff = KeyDiff(key="DB_HOST", value_a="localhost", value_b="remote")
    result = make_result(mismatched=[diff])
    opts = ReportOptions(color=False, show_values=True)
    report = format_report(result, ["dev", "prod"], opts)
    assert "localhost" in report
    assert "remote" in report


def test_hide_values_by_default():
    diff = KeyDiff(key="DB_HOST", value_a="localhost", value_b="remote")
    result = make_result(mismatched=[diff])
    report = format_report(result, ["dev", "prod"], NO_COLOR)
    assert "localhost" not in report


def test_summary_counts():
    missing = [KeyDiff(key="A", missing_in="prod")]
    mismatched = [KeyDiff(key="B", value_a="x", value_b="y"), KeyDiff(key="C", value_a="1", value_b="2")]
    result = make_result(missing=missing, mismatched=mismatched)
    summary = format_summary(result)
    assert "1 missing" in summary
    assert "2 mismatched" in summary


def test_color_codes_present_when_enabled():
    diff = KeyDiff(key="FOO", missing_in="prod")
    result = make_result(missing=[diff])
    opts = ReportOptions(color=True)
    report = format_report(result, ["dev", "prod"], opts)
    assert "\033[" in report
