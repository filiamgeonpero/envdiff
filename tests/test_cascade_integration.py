"""End-to-end integration tests for the cascade feature.

Verifies that parser → cascader → CLI all work together correctly.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.parser import parse_env_file
from envdiff.cascader import cascade_envs


def write_env(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_parsed_files_cascade_correctly(tmp_path):
    base = write_env(tmp_path, "base.env", "DB_HOST=localhost\nDEBUG=true\n")
    prod = write_env(tmp_path, "prod.env", "DB_HOST=prod-db\n")

    named = [
        ("base.env", parse_env_file(base)),
        ("prod.env", parse_env_file(prod)),
    ]
    result = cascade_envs(named)
    resolved = result.resolved()

    assert resolved["DB_HOST"] == "prod-db"
    assert resolved["DEBUG"] == "true"


def test_quoted_values_survive_cascade(tmp_path):
    base = write_env(tmp_path, "base.env", 'MSG="hello world"\n')
    prod = write_env(tmp_path, "prod.env", 'MSG="goodbye world"\n')

    named = [
        ("base.env", parse_env_file(base)),
        ("prod.env", parse_env_file(prod)),
    ]
    result = cascade_envs(named)
    assert result.resolved()["MSG"] == "goodbye world"


def test_three_layer_cascade(tmp_path):
    base = write_env(tmp_path, "base.env", "A=base\nB=base\nC=base\n")
    stage = write_env(tmp_path, "stage.env", "B=stage\n")
    prod = write_env(tmp_path, "prod.env", "C=prod\n")

    named = [
        ("base.env", parse_env_file(base)),
        ("stage.env", parse_env_file(stage)),
        ("prod.env", parse_env_file(prod)),
    ]
    result = cascade_envs(named)
    resolved = result.resolved()

    assert resolved["A"] == "base"
    assert resolved["B"] == "stage"
    assert resolved["C"] == "prod"


def test_exclusive_key_identified_across_real_files(tmp_path):
    base = write_env(tmp_path, "base.env", "COMMON=1\nBASE_ONLY=x\n")
    prod = write_env(tmp_path, "prod.env", "COMMON=2\n")

    named = [
        ("base.env", parse_env_file(base)),
        ("prod.env", parse_env_file(prod)),
    ]
    result = cascade_envs(named)
    assert "BASE_ONLY" in result.exclusive
    assert result.exclusive["BASE_ONLY"] == "base.env"
