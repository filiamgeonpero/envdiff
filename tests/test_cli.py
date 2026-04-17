"""Integration tests for the envdiff CLI."""
import pytest
from pathlib import Path
from envdiff.cli import main


def write_env(tmp_path, filename, content):
    p = tmp_path / filename
    p.write_text(content)
    return str(p)


def test_no_differences_exit_zero(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=value\n")
    assert main([a, b]) == 0


def test_differences_exit_zero_without_flag(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=other\n")
    assert main([a, b]) == 0


def test_differences_exit_one_with_flag(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    b = write_env(tmp_path, ".env.b", "KEY=other\n")
    assert main([a, b, "--exit-code"]) == 1


def test_missing_file_returns_2(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=value\n")
    assert main([a, "/nonexistent/.env"]) == 2


def test_too_few_files_exits_nonzero(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "KEY=val\n")
    with pytest.raises(SystemExit) as exc:
        main([a])
    assert exc.value.code != 0


def test_no_color_flag_accepted(tmp_path):
    a = write_env(tmp_path, ".env.a", "KEY=val\n")
    b = write_env(tmp_path, ".env.b", "KEY=val\n")
    assert main([a, b, "--no-color"]) == 0


def test_show_values_flag(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "DB=localhost\n")
    b = write_env(tmp_path, ".env.b", "DB=remote\n")
    main([a, b, "--no-color", "--show-values"])
    captured = capsys.readouterr()
    assert "localhost" in captured.out


def test_summary_flag_prints_summary(tmp_path, capsys):
    a = write_env(tmp_path, ".env.a", "A=1\n")
    b = write_env(tmp_path, ".env.b", "B=2\n")
    main([a, b, "--no-color", "--summary"])
    captured = capsys.readouterr()
    assert "Summary:" in captured.out
