import pytest
from envdiff.deduplicator import (
    Strategy,
    DeduplicateError,
    DuplicateKey,
    DeduplicateResult,
    deduplicate_env,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def pairs(*items):
    """Build a list of (key, value) tuples from alternating args."""
    it = iter(items)
    return list(zip(it, it))


# ---------------------------------------------------------------------------
# basic correctness
# ---------------------------------------------------------------------------

def test_no_duplicates_returns_all_keys():
    result = deduplicate_env(pairs("A", "1", "B", "2"))
    assert result.env == {"A": "1", "B": "2"}


def test_no_duplicates_has_no_duplicate_entries():
    result = deduplicate_env(pairs("A", "1", "B", "2"))
    assert not result.has_duplicates


def test_last_strategy_keeps_last_value():
    result = deduplicate_env(
        pairs("KEY", "first", "OTHER", "x", "KEY", "last"),
        strategy=Strategy.LAST,
    )
    assert result.env["KEY"] == "last"


def test_first_strategy_keeps_first_value():
    result = deduplicate_env(
        pairs("KEY", "first", "KEY", "second"),
        strategy=Strategy.FIRST,
    )
    assert result.env["KEY"] == "first"


def test_duplicate_entry_lists_all_values():
    result = deduplicate_env(
        pairs("KEY", "a", "KEY", "b", "KEY", "c"),
        strategy=Strategy.LAST,
    )
    assert len(result.duplicates) == 1
    dup = result.duplicates[0]
    assert dup.values == ["a", "b", "c"]


def test_duplicate_entry_key_name_correct():
    result = deduplicate_env(pairs("FOO", "1", "FOO", "2"))
    assert result.duplicates[0].key == "FOO"


def test_non_duplicate_key_not_in_duplicates_list():
    result = deduplicate_env(pairs("A", "1", "B", "2", "A", "3"))
    dup_keys = [d.key for d in result.duplicates]
    assert "B" not in dup_keys


# ---------------------------------------------------------------------------
# error strategy
# ---------------------------------------------------------------------------

def test_error_strategy_raises_on_duplicate():
    with pytest.raises(DeduplicateError):
        deduplicate_env(pairs("KEY", "v1", "KEY", "v2"), strategy=Strategy.ERROR)


def test_error_strategy_ok_when_no_duplicates():
    result = deduplicate_env(pairs("A", "1", "B", "2"), strategy=Strategy.ERROR)
    assert result.env == {"A": "1", "B": "2"}


# ---------------------------------------------------------------------------
# summary / str helpers
# ---------------------------------------------------------------------------

def test_summary_no_duplicates_message():
    result = deduplicate_env(pairs("X", "1"))
    assert "No duplicate" in result.summary()


def test_summary_lists_duplicate_count():
    result = deduplicate_env(pairs("A", "1", "A", "2", "B", "x", "B", "y"))
    assert "2 duplicate" in result.summary()


def test_duplicate_key_str_contains_key_name():
    dk = DuplicateKey(key="MY_KEY", values=["old", "new"], kept="new")
    assert "MY_KEY" in str(dk)


def test_duplicate_key_str_contains_kept_value():
    dk = DuplicateKey(key="K", values=["a", "b"], kept="b")
    assert "'b'" in str(dk)
