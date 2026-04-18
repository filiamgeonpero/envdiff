"""Tests for envdiff.differ module."""
import pytest
from envdiff.differ import diff_files, FileDiff, DiffLine


ENV_A = """DB_HOST=localhost
DB_PORT=5432
DEBUG=true
"""

ENV_B = """DB_HOST=localhost
DB_PORT=5433
NEW_KEY=value
"""


def test_identical_files_have_no_changes():
    result = diff_files("a", ENV_A, "b", ENV_A)
    assert not result.has_changes


def test_changed_value_detected():
    result = diff_files("a", ENV_A, "b", ENV_B)
    assert result.has_changes


def test_changed_lines_count():
    result = diff_files("a", ENV_A, "b", ENV_B)
    changed = result.changed_lines()
    assert len(changed) >= 2


def test_file_names_stored():
    result = diff_files("prod.env", ENV_A, "staging.env", ENV_B)
    assert result.name_a == "prod.env"
    assert result.name_b == "staging.env"


def test_equal_lines_tag():
    result = diff_files("a", ENV_A, "b", ENV_B)
    equal_lines = [l for l in result.lines if l.tag == "equal"]
    assert any(l.content_a == "DB_HOST=localhost" for l in equal_lines)


def test_delete_tag_present_when_line_removed():
    result = diff_files("a", ENV_A, "b", ENV_B)
    tags = {l.tag for l in result.lines}
    assert "delete" in tags or "replace" in tags


def test_insert_tag_present_when_line_added():
    result = diff_files("a", ENV_A, "b", ENV_B)
    tags = {l.tag for l in result.lines}
    assert "insert" in tags or "replace" in tags


def test_str_equal_line():
    dl = DiffLine(0, 0, "equal", "KEY=val", "KEY=val")
    assert str(dl) == "  KEY=val"


def test_str_delete_line():
    dl = DiffLine(0, None, "delete", "KEY=val", None)
    assert str(dl) == "- KEY=val"


def test_str_insert_line():
    dl = DiffLine(None, 0, "insert", None, "KEY=val")
    assert str(dl) == "+ KEY=val"


def test_empty_files_no_changes():
    result = diff_files("a", "", "b", "")
    assert not result.has_changes
    assert result.lines == []
