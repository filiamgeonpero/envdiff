"""Tests for envdiff.auditor."""
import json
import pytest
from pathlib import Path

from envdiff.auditor import (
    AuditEntry,
    AuditError,
    AuditLog,
    diff_to_audit,
    load_audit,
    save_audit,
)


# ---------------------------------------------------------------------------
# AuditEntry
# ---------------------------------------------------------------------------

def test_entry_str_added():
    e = AuditEntry(key="FOO", old_value=None, new_value="bar", env_file=".env")
    assert "added" in str(e)
    assert "FOO" in str(e)


def test_entry_str_removed():
    e = AuditEntry(key="FOO", old_value="bar", new_value=None, env_file=".env")
    assert "removed" in str(e)


def test_entry_str_changed():
    e = AuditEntry(key="FOO", old_value="old", new_value="new", env_file=".env")
    assert "changed" in str(e)


def test_entry_roundtrip():
    e = AuditEntry(key="X", old_value="1", new_value="2", env_file="prod.env",
                   timestamp="2024-01-01T00:00:00+00:00", author="alice")
    assert AuditEntry.from_dict(e.to_dict()) == e


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

def _make_log() -> AuditLog:
    log = AuditLog()
    log.record(AuditEntry("A", None, "1", ".env.dev"))
    log.record(AuditEntry("B", "old", "new", ".env.prod"))
    log.record(AuditEntry("A", "1", "2", ".env.dev"))
    return log


def test_for_key_filters_correctly():
    log = _make_log()
    assert len(log.for_key("A")) == 2


def test_for_file_filters_correctly():
    log = _make_log()
    assert len(log.for_file(".env.prod")) == 1


def test_summary_empty():
    assert "No audit" in AuditLog().summary()


def test_summary_non_empty():
    log = _make_log()
    s = log.summary()
    assert "A" in s and "B" in s


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    p = tmp_path / "audit.json"
    save_audit(_make_log(), p)
    assert p.exists()


def test_save_load_roundtrip(tmp_path):
    p = tmp_path / "audit.json"
    log = _make_log()
    save_audit(log, p)
    loaded = load_audit(p)
    assert len(loaded.entries) == len(log.entries)
    assert loaded.entries[0].key == log.entries[0].key


def test_load_missing_raises(tmp_path):
    with pytest.raises(AuditError, match="not found"):
        load_audit(tmp_path / "nope.json")


def test_load_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not-json")
    with pytest.raises(AuditError, match="Invalid"):
        load_audit(p)


def test_load_wrong_version_raises(tmp_path):
    p = tmp_path / "old.json"
    p.write_text(json.dumps({"version": 99, "entries": []}))
    with pytest.raises(AuditError, match="Unsupported"):
        load_audit(p)


# ---------------------------------------------------------------------------
# diff_to_audit
# ---------------------------------------------------------------------------

def test_diff_detects_addition():
    entries = diff_to_audit({}, {"FOO": "bar"}, ".env")
    assert len(entries) == 1
    assert entries[0].old_value is None
    assert entries[0].new_value == "bar"


def test_diff_detects_removal():
    entries = diff_to_audit({"FOO": "bar"}, {}, ".env")
    assert entries[0].new_value is None


def test_diff_detects_change():
    entries = diff_to_audit({"K": "v1"}, {"K": "v2"}, ".env")
    assert entries[0].old_value == "v1" and entries[0].new_value == "v2"


def test_diff_no_change_empty():
    assert diff_to_audit({"K": "v"}, {"K": "v"}, ".env") == []
