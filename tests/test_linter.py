"""Tests for envdiff.linter."""
import os
import pytest
from envdiff.linter import lint_env_file, LintResult


def write_env(tmp_path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_clean_file_has_no_issues(tmp_path):
    path = write_env(tmp_path, ".env", "KEY=value\nOTHER=123\n")
    result = lint_env_file(path)
    assert result.issues == []
    assert result.ok


def test_lowercase_key_is_warning(tmp_path):
    path = write_env(tmp_path, ".env", "mykey=value\n")
    result = lint_env_file(path)
    assert any(i.key == "mykey" and "uppercase" in i.message for i in result.warnings)


def test_missing_equals_is_error(tmp_path):
    path = write_env(tmp_path, ".env", "BADLINE\n")
    result = lint_env_file(path)
    assert any(i.severity == "error" and "no '='" in i.message for i in result.issues)
    assert not result.ok


def test_duplicate_key_is_error(tmp_path):
    path = write_env(tmp_path, ".env", "KEY=a\nKEY=b\n")
    result = lint_env_file(path)
    errors = result.errors
    assert any("duplicate" in i.message for i in errors)


def test_whitespace_in_value_is_warning(tmp_path):
    path = write_env(tmp_path, ".env", "KEY= value \n")
    result = lint_env_file(path)
    assert any("whitespace" in i.message for i in result.warnings)


def test_key_with_space_is_error(tmp_path):
    path = write_env(tmp_path, ".env", "MY KEY=value\n")
    result = lint_env_file(path)
    assert any("spaces" in i.message for i in result.errors)


def test_comments_and_blanks_ignored(tmp_path):
    path = write_env(tmp_path, ".env", "# comment\n\nKEY=val\n")
    result = lint_env_file(path)
    assert result.issues == []


def test_lint_issue_str_format(tmp_path):
    path = write_env(tmp_path, ".env", "mykey=val\n")
    result = lint_env_file(path)
    issue = result.warnings[0]
    text = str(issue)
    assert "WARNING" in text
    assert "mykey" in text


def test_ok_false_when_errors_present(tmp_path):
    path = write_env(tmp_path, ".env", "KEY=a\nKEY=b\n")
    result = lint_env_file(path)
    assert not result.ok


def test_ok_true_when_only_warnings(tmp_path):
    path = write_env(tmp_path, ".env", "lower=val\n")
    result = lint_env_file(path)
    assert result.ok
    assert len(result.warnings) > 0


def test_lint_nonexistent_file_raises():
    """lint_env_file should raise FileNotFoundError for a missing file."""
    with pytest.raises(FileNotFoundError):
        lint_env_file("/nonexistent/path/.env")
