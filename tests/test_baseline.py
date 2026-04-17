"""Tests for envdiff.baseline."""
import json
import pytest
from pathlib import Path
from envdiff.baseline import BaselineError, load_baseline, save_baseline, BASELINE_VERSION


def test_save_creates_file(tmp_path):
    p = tmp_path / "baseline.json"
    save_baseline({"A": "1"}, p)
    assert p.exists()


def test_save_and_load_roundtrip(tmp_path):
    env = {"HOST": "localhost", "PORT": "5432"}
    p = tmp_path / "baseline.json"
    save_baseline(env, p)
    loaded = load_baseline(p)
    assert loaded == env


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(BaselineError, match="not found"):
        load_baseline(tmp_path / "missing.json")


def test_load_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(BaselineError, match="Invalid JSON"):
        load_baseline(p)


def test_load_wrong_version_raises(tmp_path):
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps({"version": 99, "env": {}}), encoding="utf-8")
    with pytest.raises(BaselineError, match="Unsupported baseline version"):
        load_baseline(p)


def test_load_missing_env_field_raises(tmp_path):
    p = tmp_path / "baseline.json"
    p.write_text(json.dumps({"version": BASELINE_VERSION}), encoding="utf-8")
    with pytest.raises(BaselineError, match="missing or not a dict"):
        load_baseline(p)


def test_saved_file_contains_version(tmp_path):
    p = tmp_path / "baseline.json"
    save_baseline({"X": "y"}, p)
    raw = json.loads(p.read_text())
    assert raw["version"] == BASELINE_VERSION
