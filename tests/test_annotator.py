import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.annotator import annotate_result, AnnotatedKey


def make_result(envs: dict, diffs=None) -> CompareResult:
    env_names = list(envs.keys())
    return CompareResult(env_names=env_names, envs=envs, diffs=diffs or [])


def test_all_keys_present_in_annotation():
    result = make_result({"dev": {"A": "1", "B": "2"}, "prod": {"A": "1", "B": "2"}})
    ann = annotate_result(result)
    keys = [k.key for k in ann.keys]
    assert "A" in keys
    assert "B" in keys


def test_ok_status_for_matching_keys():
    result = make_result({"dev": {"A": "1"}, "prod": {"A": "1"}})
    ann = annotate_result(result)
    assert ann.keys[0].status == "ok"


def test_missing_status_for_missing_key():
    diff = KeyDiff(key="B", env_name="prod", is_missing=True, values={})
    result = make_result({"dev": {"A": "1", "B": "2"}, "prod": {"A": "1"}}, diffs=[diff])
    ann = annotate_result(result)
    b_key = next(k for k in ann.keys if k.key == "B")
    assert b_key.status == "missing"
    assert "prod" in b_key.envs_missing


def test_mismatch_status_for_different_values():
    diff = KeyDiff(key="A", env_name="prod", is_missing=False, values={"dev": "1", "prod": "2"})
    result = make_result({"dev": {"A": "1"}, "prod": {"A": "2"}}, diffs=[diff])
    ann = annotate_result(result)
    a_key = next(k for k in ann.keys if k.key == "A")
    assert a_key.status == "mismatch"
    assert a_key.envs_missing == []


def test_by_status_filters_correctly():
    diff = KeyDiff(key="B", env_name="prod", is_missing=True, values={})
    result = make_result({"dev": {"A": "1", "B": "2"}, "prod": {"A": "1"}}, diffs=[diff])
    ann = annotate_result(result)
    assert len(ann.by_status("ok")) == 1
    assert len(ann.by_status("missing")) == 1
    assert len(ann.by_status("mismatch")) == 0


def test_summary_string():
    diff = KeyDiff(key="B", env_name="prod", is_missing=True, values={})
    result = make_result({"dev": {"A": "1", "B": "2"}, "prod": {"A": "1"}}, diffs=[diff])
    ann = annotate_result(result)
    summary = ann.summary()
    assert "ok=1" in summary
    assert "missing=1" in summary
    assert "mismatch=0" in summary


def test_str_representation_of_annotated_key():
    key = AnnotatedKey(key="FOO", values={"dev": "bar", "prod": None}, status="missing", envs_missing=["prod"])
    s = str(key)
    assert "FOO" in s
    assert "MISSING" in s
    assert "<missing>" in s


def test_keys_sorted_alphabetically():
    result = make_result({"dev": {"Z": "1", "A": "2"}, "prod": {"Z": "1", "A": "2"}})
    ann = annotate_result(result)
    assert ann.keys[0].key == "A"
    assert ann.keys[1].key == "Z"
