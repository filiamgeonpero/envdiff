"""Tests for envdiff.tagger."""
import pytest
from envdiff.tagger import TagRule, TaggedKey, TagResult, tag_env, tag_envs


RULES = [
    TagRule(pattern="DB_*", tag="database"),
    TagRule(pattern="*SECRET*", tag="sensitive"),
    TagRule(pattern="*TOKEN*", tag="sensitive"),
    TagRule(pattern="FEATURE_*", tag="feature-flag"),
]


def make_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_SECRET_KEY": "abc123",
        "API_TOKEN": "tok",
        "FEATURE_DARK_MODE": "true",
        "LOG_LEVEL": "info",
    }


def test_all_keys_present_in_result():
    env = make_env()
    result = tag_env(env, RULES, env_name="prod")
    keys = {t.key for t in result.tagged}
    assert keys == set(env.keys())


def test_db_keys_tagged_database():
    result = tag_env(make_env(), RULES)
    db_tagged = result.by_tag("database")
    assert {t.key for t in db_tagged} == {"DB_HOST", "DB_PORT"}


def test_sensitive_keys_tagged():
    result = tag_env(make_env(), RULES)
    sensitive = result.by_tag("sensitive")
    assert {t.key for t in sensitive} == {"APP_SECRET_KEY", "API_TOKEN"}


def test_feature_flag_tagged():
    result = tag_env(make_env(), RULES)
    ff = result.by_tag("feature-flag")
    assert len(ff) == 1
    assert ff[0].key == "FEATURE_DARK_MODE"


def test_untagged_key_has_empty_tags():
    result = tag_env(make_env(), RULES)
    log_entries = [t for t in result.tagged if t.key == "LOG_LEVEL"]
    assert len(log_entries) == 1
    assert log_entries[0].tags == set()


def test_all_tags_returns_union():
    result = tag_env(make_env(), RULES)
    assert result.all_tags() == {"database", "sensitive", "feature-flag"}


def test_all_tags_empty_rules():
    result = tag_env(make_env(), [])
    assert result.all_tags() == set()


def test_summary_contains_env_name():
    result = tag_env(make_env(), RULES, env_name="staging")
    assert "staging" in result.summary()


def test_summary_counts():
    result = tag_env(make_env(), RULES, env_name="prod")
    # LOG_LEVEL is untagged; all others match at least one rule
    assert "1 untagged" in result.summary()


def test_tagged_key_str():
    tk = TaggedKey(key="DB_HOST", tags={"database"})
    assert "DB_HOST" in str(tk)
    assert "database" in str(tk)


def test_tagged_key_no_tags_str():
    tk = TaggedKey(key="LOG_LEVEL", tags=set())
    assert "(none)" in str(tk)


def test_tag_envs_multi():
    envs = {
        "dev": {"DB_HOST": "localhost", "LOG_LEVEL": "debug"},
        "prod": {"DB_HOST": "db.prod", "API_TOKEN": "tok"},
    }
    results = tag_envs(envs, RULES)
    assert set(results.keys()) == {"dev", "prod"}
    assert results["dev"].env_name == "dev"
    assert results["prod"].env_name == "prod"
    assert any(t.key == "API_TOKEN" for t in results["prod"].by_tag("sensitive"))


def test_empty_env_returns_empty_tagged():
    result = tag_env({}, RULES, env_name="empty")
    assert result.tagged == []
    assert result.all_tags() == set()
