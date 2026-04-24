"""Tag keys in an env dict with user-defined labels for categorisation."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional, Set


@dataclass
class TagRule:
    """A pattern → tag mapping."""
    pattern: str   # glob-style, e.g. 'DB_*' or 'SECRET'
    tag: str


@dataclass
class TaggedKey:
    key: str
    tags: Set[str] = field(default_factory=set)

    def __str__(self) -> str:
        tag_str = ", ".join(sorted(self.tags)) if self.tags else "(none)"
        return f"{self.key}: [{tag_str}]"


@dataclass
class TagResult:
    env_name: str
    tagged: List[TaggedKey] = field(default_factory=list)

    def by_tag(self, tag: str) -> List[TaggedKey]:
        """Return all keys that carry *tag*."""
        return [t for t in self.tagged if tag in t.tags]

    def all_tags(self) -> Set[str]:
        """Return the union of every tag seen in this result."""
        result: Set[str] = set()
        for t in self.tagged:
            result |= t.tags
        return result

    def summary(self) -> str:
        total = len(self.tagged)
        tagged_count = sum(1 for t in self.tagged if t.tags)
        return (
            f"{self.env_name}: {total} keys, "
            f"{tagged_count} tagged, "
            f"{total - tagged_count} untagged"
        )


def tag_env(
    env: Dict[str, str],
    rules: List[TagRule],
    env_name: str = "env",
) -> TagResult:
    """Apply *rules* to every key in *env* and return a :class:`TagResult`."""
    tagged: List[TaggedKey] = []
    for key in env:
        matched: Set[str] = set()
        for rule in rules:
            if fnmatch(key, rule.pattern):
                matched.add(rule.tag)
        tagged.append(TaggedKey(key=key, tags=matched))
    return TagResult(env_name=env_name, tagged=tagged)


def tag_envs(
    envs: Dict[str, Dict[str, str]],
    rules: List[TagRule],
) -> Dict[str, TagResult]:
    """Convenience wrapper — tag every env in *envs*."""
    return {name: tag_env(data, rules, env_name=name) for name, data in envs.items()}
