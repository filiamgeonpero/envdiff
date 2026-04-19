"""Tests for envdiff.patcher."""
from pathlib import Path
import pytest
from envdiff.patcher import patch_env_file, PatchResult


def write_env(tmp_path: Path, name: str, text: str) -> str:
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def test_update_existing_key(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\nPORT=5432\n")
    result = patch_env_file(f, {"PORT": "9999"})
    assert "PORT=9999" in result.content
    assert "PORT" in result.updated


def test_unchanged_keys_preserved(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\nPORT=5432\n")
    result = patch_env_file(f, {"PORT": "9999"})
    assert "HOST=localhost" in result.content


def test_add_missing_key(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    result = patch_env_file(f, {"NEW_KEY": "hello"})
    assert "NEW_KEY=hello" in result.content
    assert "NEW_KEY" in result.added


def test_add_missing_disabled(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    result = patch_env_file(f, {"NEW_KEY": "hello"}, add_missing=False)
    assert "NEW_KEY" not in result.content
    assert not result.added


def test_dry_run_does_not_write(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    patch_env_file(f, {"HOST": "remotehost"}, dry_run=True)
    assert Path(f).read_text() == "HOST=localhost\n"


def test_dry_run_result_has_changes(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    result = patch_env_file(f, {"HOST": "remotehost"}, dry_run=True)
    assert result.has_changes
    assert "HOST" in result.updated


def test_comments_preserved(tmp_path):
    f = write_env(tmp_path, ".env", "# comment\nHOST=localhost\n")
    result = patch_env_file(f, {"HOST": "newhost"})
    assert "# comment" in result.content


def test_summary_no_changes(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    result = patch_env_file(f, {})
    assert result.summary() == "no changes"


def test_summary_with_changes(tmp_path):
    f = write_env(tmp_path, ".env", "HOST=localhost\n")
    result = patch_env_file(f, {"HOST": "x", "NEW": "y"})
    s = result.summary()
    assert "updated" in s
    assert "added" in s


def test_file_written_to_disk(tmp_path):
    f = write_env(tmp_path, ".env", "KEY=old\n")
    patch_env_file(f, {"KEY": "new"})
    assert Path(f).read_text() == "KEY=new\n"
