"""Build a dependency graph from .env variable references."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set
import re

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


def _refs_in(value: str) -> List[str]:
    """Return all variable names referenced inside *value*."""
    return [m.group(1) or m.group(2) for m in _REF_RE.finditer(value)]


@dataclass
class GraphNode:
    key: str
    depends_on: List[str] = field(default_factory=list)
    used_by: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        deps = ", ".join(self.depends_on) or "none"
        return f"{self.key} -> [{deps}]"


@dataclass
class GraphResult:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def roots(self) -> List[str]:
        """Keys that depend on nothing."""
        return [k for k, n in self.nodes.items() if not n.depends_on]

    def leaves(self) -> List[str]:
        """Keys that nothing else depends on."""
        return [k for k, n in self.nodes.items() if not n.used_by]

    def isolated(self) -> List[str]:
        """Keys with no dependencies and no dependants."""
        return [k for k in self.roots() if k in self.leaves()]

    def cycle_keys(self) -> List[str]:
        """Return keys that participate in a dependency cycle."""
        visited: Set[str] = set()
        in_stack: Set[str] = set()
        cyclic: Set[str] = set()

        def dfs(key: str) -> None:
            if key not in self.nodes:
                return
            visited.add(key)
            in_stack.add(key)
            for dep in self.nodes[key].depends_on:
                if dep not in visited:
                    dfs(dep)
                elif dep in in_stack:
                    cyclic.add(dep)
                    cyclic.add(key)
            in_stack.discard(key)

        for k in self.nodes:
            if k not in visited:
                dfs(k)
        return sorted(cyclic)


def build_graph(env: Dict[str, str]) -> GraphResult:
    """Build a *GraphResult* from a parsed env mapping."""
    nodes: Dict[str, GraphNode] = {k: GraphNode(key=k) for k in env}

    for key, value in env.items():
        for ref in _refs_in(value):
            nodes[key].depends_on.append(ref)
            if ref in nodes:
                nodes[ref].used_by.append(key)

    return GraphResult(nodes=nodes)
