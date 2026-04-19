import pytest
from envdiff.comparator import CompareResult, KeyDiff
from envdiff.renamer import RenameMap, RenameResult, rename_result


def make_result():
    diffs = [
        KeyDiff(key="DB_HOST", diff_type="mismatch", values={"prod": "localhost", "staging": "remotehost"}, missing_in=None),
        KeyDiff(key="API_KEY", diff_type="missing", values={}, missing_in="staging"),
    ]
    envs = ["prod", "staging"]
    data = {"prod": {"DB_HOST": "localhost", "API_KEY": "abc"}, "staging": {"DB_HOST": "remotehost"}}
    return CompareResult(envs=envs, diffs=diffs, env_data=data)


def test_rename_map_apply_known_key():
    rm = RenameMap()
    rm.add("DB_HOST", "DATABASE_HOST")
    assert rm.apply("DB_HOST") == "DATABASE_HOST"


def test_rename_map_apply_unknown_key():
    rm = RenameMap()
    assert rm.apply("UNKNOWN") == "UNKNOWN"


def test_rename_result_renames_key():
    result = make_result()
    rm = RenameMap()
    rm.add("DB_HOST", "DATABASE_HOST")
    renamed = rename_result(result, rm)
    keys = [d.key for d in renamed.diffs]
    assert "DATABASE_HOST" in keys
    assert "DB_HOST" not in keys


def test_rename_result_unchanged_key_preserved():
    result = make_result()
    rm = RenameMap()
    rm.add("DB_HOST", "DATABASE_HOST")
    renamed = rename_result(result, rm)
    keys = [d.key for d in renamed.diffs]
    assert "API_KEY" in keys


def test_rename_result_preserves_diff_type():
    result = make_result()
    rm = RenameMap()
    rm.add("DB_HOST", "DATABASE_HOST")
    renamed = rename_result(result, rm)
    diff = next(d for d in renamed.diffs if d.key == "DATABASE_HOST")
    assert diff.diff_type == "mismatch"


def test_rename_result_preserves_envs():
    result = make_result()
    rm = RenameMap()
    renamed = rename_result(result, rm)
    assert renamed.envs == ["prod", "staging"]


def test_rename_result_has_differences_true():
    result = make_result()
    renamed = rename_result(result, RenameMap())
    assert renamed.has_differences() is True


def test_rename_result_has_differences_false():
    result = CompareResult(envs=["a", "b"], diffs=[], env_data={})
    renamed = rename_result(result, RenameMap())
    assert renamed.has_differences() is False


def test_rename_multiple_keys():
    result = make_result()
    rm = RenameMap()
    rm.add("DB_HOST", "DATABASE_HOST")
    rm.add("API_KEY", "API_TOKEN")
    renamed = rename_result(result, rm)
    keys = [d.key for d in renamed.diffs]
    assert "DATABASE_HOST" in keys
    assert "API_TOKEN" in keys
