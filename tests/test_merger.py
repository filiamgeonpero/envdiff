"""Tests for envdiff.merger."""
import pytest
from envdiff.merger import MergeOptions, MergeResult, merge_envs


ENV_A = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
ENV_B = {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc"}


def test_all_keys_collected():
    result = merge_envs({"a": ENV_A, "b": ENV_B})
    assert set(result.keys) == {"HOST", "PORT", "DEBUG", "SECRET"}


def test_key_order_preserves_first_seen():
    result = merge_envs({"a": ENV_A, "b": ENV_B})
    assert result.keys[0] == "HOST"
    assert result.keys[1] == "PORT"


def test_values_contain_all_envs():
    result = merge_envs({"a": ENV_A, "b": ENV_B})
    host_entries = dict(result.values["HOST"])
    assert host_entries["a"] == "localhost"
    assert host_entries["b"] == "prod.example.com"


def test_missing_key_recorded_as_none():
    result = merge_envs({"a": ENV_A, "b": ENV_B})
    debug_entries = dict(result.values["DEBUG"])
    assert debug_entries["a"] == "true"
    assert debug_entries["b"] is None


def test_template_contains_all_keys():
    result = merge_envs({"a": ENV_A, "b": ENV_B})
    template = result.as_template(MergeOptions(comment_source=False))
    for key in ["HOST", "PORT", "DEBUG", "SECRET"]:
        assert key in template


def test_template_placeholder_for_missing():
    result = merge_envs({"a": {"ONLY_A": "val"}, "b": {}})
    opts = MergeOptions(fill_missing=True, placeholder="CHANGE_ME", comment_source=False)
    template = result.as_template(opts)
    assert "ONLY_A=val" in template


def test_template_comment_source():
    result = merge_envs({"staging": {"KEY": "1"}, "prod": {}})
    template = result.as_template(MergeOptions(comment_source=True))
    assert "# from staging" in template


def test_empty_envs_returns_empty_result():
    result = merge_envs({})
    assert result.keys == []
    assert result.values == {}


def test_single_env_roundtrip():
    result = merge_envs({"only": {"A": "1", "B": "2"}})
    assert result.keys == ["A", "B"]
    assert dict(result.values["A"])["only"] == "1"
