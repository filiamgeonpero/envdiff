"""Tests for envdiff.templater."""
from __future__ import annotations

from envdiff.merger import MergeResult
from envdiff.templater import TemplateOptions, build_template


def make_merge(values: dict) -> MergeResult:
    return MergeResult(
        envs=["dev", "prod"],
        values=values,
    )


def test_total_keys_counted():
    mr = make_merge({"A": {"dev": "1", "prod": "1"}, "B": {"dev": "2", "prod": "2"}})
    result = build_template(mr)
    assert result.total_keys == 2


def test_placeholder_used_by_default():
    mr = make_merge({"KEY": {"dev": "val", "prod": "val"}})
    result = build_template(mr)
    assert "KEY=<FILL_ME>" in result.lines


def test_custom_placeholder():
    mr = make_merge({"KEY": {"dev": "val", "prod": "val"}})
    opts = TemplateOptions(placeholder="CHANGEME")
    result = build_template(mr, opts)
    assert "KEY=CHANGEME" in result.lines


def test_include_values_uses_first_present_value():
    mr = make_merge({"KEY": {"dev": "hello", "prod": "hello"}})
    opts = TemplateOptions(include_values=True)
    result = build_template(mr, opts)
    assert "KEY=hello" in result.lines


def test_missing_in_any_counted():
    mr = make_merge({
        "PRESENT": {"dev": "1", "prod": "1"},
        "MISSING": {"dev": "1", "prod": None},
    })
    result = build_template(mr)
    assert result.missing_in_any == 1


def test_comment_added_for_missing_key():
    mr = make_merge({"SECRET": {"dev": "x", "prod": None}})
    opts = TemplateOptions(add_comments=True)
    result = build_template(mr, opts)
    rendered = result.render()
    assert "# missing in: prod" in rendered


def test_no_comment_when_disabled():
    mr = make_merge({"SECRET": {"dev": "x", "prod": None}})
    opts = TemplateOptions(add_comments=False)
    result = build_template(mr, opts)
    assert not any(line.startswith("#") for line in result.lines)


def test_render_ends_with_newline():
    mr = make_merge({"A": {"dev": "1", "prod": "1"}})
    result = build_template(mr)
    assert result.render().endswith("\n")


def test_group_by_prefix_inserts_section_header():
    mr = make_merge({
        "DB_HOST": {"dev": "localhost", "prod": "db.prod"},
        "DB_PORT": {"dev": "5432", "prod": "5432"},
        "APP_NAME": {"dev": "myapp", "prod": "myapp"},
    })
    opts = TemplateOptions(group_by_prefix=True, add_comments=True)
    result = build_template(mr, opts)
    rendered = result.render()
    assert "# --- APP ---" in rendered
    assert "# --- DB ---" in rendered


def test_include_values_falls_back_to_placeholder_when_all_none():
    mr = make_merge({"GHOST": {"dev": None, "prod": None}})
    opts = TemplateOptions(include_values=True, placeholder="??")
    result = build_template(mr, opts)
    assert "GHOST=??" in result.lines
