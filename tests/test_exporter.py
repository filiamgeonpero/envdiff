"""Tests for envdiff.exporter module."""
import csv
import io
import json
import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.exporter import export_result


def make_result():
    diffs = [
        KeyDiff(key="DB_HOST", missing_in=["staging"]),
        KeyDiff(key="PORT", values={"dev": "3000", "staging": "4000"}),
    ]
    return CompareResult(env_names=["dev", "staging"], diffs=diffs)


def test_json_export_contains_envs():
    result = make_result()
    output = export_result(result, "json")
    data = json.loads(output)
    assert data["envs"] == ["dev", "staging"]


def test_json_export_contains_diffs():
    result = make_result()
    data = json.loads(export_result(result, "json"))
    keys = [d["key"] for d in data["diffs"]]
    assert "DB_HOST" in keys
    assert "PORT" in keys


def test_json_missing_diff_structure():
    result = make_result()
    data = json.loads(export_result(result, "json"))
    db = next(d for d in data["diffs"] if d["key"] == "DB_HOST")
    assert db["missing_in"] == ["staging"]
    assert db["values"] is None


def test_json_mismatch_diff_structure():
    result = make_result()
    data = json.loads(export_result(result, "json"))
    port = next(d for d in data["diffs"] if d["key"] == "PORT")
    assert port["values"] == {"dev": "3000", "staging": "4000"}


def test_csv_export_has_header():
    result = make_result()
    output = export_result(result, "csv")
    reader = csv.reader(io.StringIO(output))
    header = next(reader)
    assert header == ["key", "type", "detail"]


def test_csv_export_missing_row():
    result = make_result()
    output = export_result(result, "csv")
    assert "DB_HOST" in output
    assert "missing" in output


def test_csv_export_mismatch_row():
    result = make_result()
    output = export_result(result, "csv")
    assert "PORT" in output
    assert "mismatch" in output


def test_unsupported_format_raises():
    result = make_result()
    with pytest.raises(ValueError, match="Unsupported format"):
        export_result(result, "xml")  # type: ignore
