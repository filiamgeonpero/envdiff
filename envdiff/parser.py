"""Parser for .env files."""

from pathlib import Path
from typing import Dict, Optional


class EnvParseError(Exception):
    """Raised when a .env file cannot be parsed."""


def parse_env_file(filepath: str | Path) -> Dict[str, Optional[str]]:
    """
    Parse a .env file and return a dict of key-value pairs.

    - Ignores blank lines and comments (lines starting with '#').
    - Supports keys with no value (e.g. 'MY_KEY' or 'MY_KEY=').
    - Strips surrounding quotes from values.

    Args:
        filepath: Path to the .env file.

    Returns:
        Dictionary mapping variable names to their values (or None if absent).

    Raises:
        EnvParseError: If the file cannot be read or contains an invalid line.
    """
    path = Path(filepath)
    if not path.exists():
        raise EnvParseError(f"File not found: {filepath}")

    env: Dict[str, Optional[str]] = {}

    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                # Key with no value
                key = line.strip()
                if not key.isidentifier():
                    raise EnvParseError(
                        f"Invalid key '{key}' at line {lineno} in {filepath}"
                    )
                env[key] = None
                continue

            key, _, value = line.partition("=")
            key = key.strip()

            if not key:
                raise EnvParseError(f"Empty key at line {lineno} in {filepath}")

            value = value.strip()
            # Strip matching surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]

            env[key] = value if value else None

    return env
