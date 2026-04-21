"""Tests for envdiff.resolver."""
import pytest
from envdiff.resolver import ResolveIssue, ResolveResult, resolve_env


def test_no_references_returns_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = resolve_env(env)
    assert result.resolved == env
    assert result.ok


def test_simple_reference_expanded():
    env = {"BASE": "http://example.com", "URL": "${BASE}/api"}
    result = resolve_env(env)
    assert result.resolved["URL"] == "http://example.com/api"
    assert result.ok


def test_multiple_references_in_one_value():
    env = {"SCHEME": "https", "HOST": "example.com", "FULL": "${SCHEME}://${HOST}"}
    result = resolve_env(env)
    assert result.resolved["FULL"] == "https://example.com"


def test_unresolved_reference_creates_issue():
    env = {"URL": "${MISSING}/path"}
    result = resolve_env(env)
    assert not result.ok
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.key == "URL"
    assert issue.ref == "MISSING"


def test_unresolved_reference_leaves_placeholder_intact():
    env = {"URL": "${MISSING}/path"}
    result = resolve_env(env)
    assert result.resolved["URL"] == "${MISSING}/path"


def test_multiple_unresolved_references_all_reported():
    env = {"VAL": "${A}-${B}"}
    result = resolve_env(env)
    refs = {i.ref for i in result.issues}
    assert refs == {"A", "B"}


def test_self_reference_is_unresolved():
    env = {"LOOP": "${LOOP}"}
    result = resolve_env(env)
    # LOOP is defined but its own value references itself — single-pass means
    # we look up the *original* value, which is "${LOOP}", not yet resolved.
    # The key exists so it resolves to "${LOOP}" (its raw value).
    assert result.resolved["LOOP"] == "${LOOP}"


def test_empty_env_returns_empty_result():
    result = resolve_env({})
    assert result.resolved == {}
    assert result.ok


def test_ok_summary_message():
    result = resolve_env({"A": "1", "B": "2"})
    assert "resolved successfully" in result.summary()


def test_error_summary_message():
    result = resolve_env({"A": "${MISSING}"})
    assert "unresolved" in result.summary()


def test_issue_str_contains_key_and_ref():
    issue = ResolveIssue(key="MY_KEY", ref="UNDEFINED")
    text = str(issue)
    assert "MY_KEY" in text
    assert "UNDEFINED" in text


def test_non_reference_dollar_sign_unchanged():
    env = {"PRICE": "$100"}
    result = resolve_env(env)
    assert result.resolved["PRICE"] == "$100"
    assert result.ok
