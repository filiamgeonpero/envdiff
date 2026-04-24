"""Tests for envdiff.grapher."""
import pytest
from envdiff.grapher import build_graph, _refs_in


# ---------------------------------------------------------------------------
# _refs_in helpers
# ---------------------------------------------------------------------------

def test_no_refs_returns_empty():
    assert _refs_in("hello world") == []


def test_brace_ref_detected():
    assert _refs_in("${FOO}") == ["FOO"]


def test_dollar_ref_detected():
    assert _refs_in("$BAR") == ["BAR"]


def test_multiple_refs_detected():
    refs = _refs_in("${HOST}:${PORT}")
    assert refs == ["HOST", "PORT"]


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------

def test_isolated_key_has_no_deps():
    result = build_graph({"FOO": "bar"})
    assert result.nodes["FOO"].depends_on == []
    assert result.nodes["FOO"].used_by == []


def test_dependency_recorded():
    result = build_graph({"HOST": "localhost", "URL": "http://${HOST}/path"})
    assert "HOST" in result.nodes["URL"].depends_on


def test_used_by_recorded():
    result = build_graph({"HOST": "localhost", "URL": "http://${HOST}/path"})
    assert "URL" in result.nodes["HOST"].used_by


def test_roots_returns_keys_with_no_deps():
    result = build_graph({"A": "plain", "B": "${A}"})
    assert "A" in result.roots()
    assert "B" not in result.roots()


def test_leaves_returns_keys_with_no_used_by():
    result = build_graph({"A": "plain", "B": "${A}"})
    assert "B" in result.leaves()
    assert "A" not in result.leaves()


def test_isolated_keys():
    result = build_graph({"SOLO": "value", "A": "plain", "B": "${A}"})
    assert "SOLO" in result.isolated()
    assert "A" not in result.isolated()
    assert "B" not in result.isolated()


def test_no_cycle_returns_empty():
    result = build_graph({"A": "plain", "B": "${A}"})
    assert result.cycle_keys() == []


def test_direct_cycle_detected():
    result = build_graph({"A": "${B}", "B": "${A}"})
    cycles = result.cycle_keys()
    assert "A" in cycles
    assert "B" in cycles


def test_self_reference_cycle():
    result = build_graph({"A": "${A}"})
    assert "A" in result.cycle_keys()


def test_external_ref_not_in_nodes():
    """A reference to a key not in the env should not crash."""
    result = build_graph({"URL": "http://${EXTERNAL_HOST}"})
    assert "EXTERNAL_HOST" not in result.nodes
    assert "EXTERNAL_HOST" in result.nodes["URL"].depends_on
