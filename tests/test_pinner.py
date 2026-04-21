"""Tests for envdiff.pinner — pin and drift detection."""

import json
import time
from pathlib import Path

import pytest

from envdiff.pinner import (
    PIN_VERSION,
    DriftItem,
    DriftResult,
    PinError,
    detect_drift,
    load_pin,
    save_pin,
)


# ---------------------------------------------------------------------------
# save_pin / load_pin
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    pin_file = tmp_path / "prod.pin.json"
    save_pin({"KEY": "value"}, pin_file)
    assert pin_file.exists()


def test_save_and_load_roundtrip(tmp_path):
    env = {"DB_HOST": "localhost", "PORT": "5432"}
    pin_file = tmp_path / "env.pin.json"
    save_pin(env, pin_file)
    loaded = load_pin(pin_file)
    assert loaded == env


def test_saved_file_contains_version(tmp_path):
    pin_file = tmp_path / "env.pin.json"
    save_pin({"A": "1"}, pin_file)
    data = json.loads(pin_file.read_text())
    assert data["version"] == PIN_VERSION


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(PinError, match="not found"):
        load_pin(tmp_path / "nonexistent.pin.json")


def test_load_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.pin.json"
    bad.write_text("not json{{{")
    with pytest.raises(PinError, match="Invalid JSON"):
        load_pin(bad)


def test_load_wrong_version_raises(tmp_path):
    pin_file = tmp_path / "old.pin.json"
    pin_file.write_text(json.dumps({"version": 99, "entries": []}))
    with pytest.raises(PinError, match="Unsupported pin version"):
        load_pin(pin_file)


# ---------------------------------------------------------------------------
# detect_drift
# ---------------------------------------------------------------------------

def test_no_drift_when_identical():
    pinned = {"HOST": "localhost", "PORT": "5432"}
    result = detect_drift(pinned, pinned.copy(), env_name="staging")
    assert not result.has_drift


def test_changed_value_is_drifted():
    pinned = {"HOST": "localhost"}
    current = {"HOST": "prod.example.com"}
    result = detect_drift(pinned, current)
    assert result.has_drift
    assert result.drifted[0].key == "HOST"
    assert result.drifted[0].pinned_value == "localhost"
    assert result.drifted[0].current_value == "prod.example.com"


def test_missing_key_in_current_is_drifted():
    pinned = {"SECRET": "abc123"}
    result = detect_drift(pinned, {}, env_name="prod")
    assert result.has_drift
    assert result.drifted[0].current_value is None


def test_extra_key_in_current_not_flagged():
    pinned = {"A": "1"}
    current = {"A": "1", "B": "2"}
    result = detect_drift(pinned, current)
    assert not result.has_drift


def test_drift_item_str_missing():
    item = DriftItem(key="TOKEN", pinned_value="old", current_value=None)
    assert "MISSING" in str(item)


def test_drift_item_str_changed():
    item = DriftItem(key="HOST", pinned_value="old", current_value="new")
    assert "old" in str(item) and "new" in str(item)


def test_summary_no_drift():
    result = DriftResult(env_name="dev")
    assert "no drift" in result.summary()


def test_summary_with_drift():
    result = DriftResult(env_name="prod", drifted=[
        DriftItem(key="DB", pinned_value="old", current_value="new")
    ])
    summary = result.summary()
    assert "prod" in summary
    assert "1 drifted" in summary
