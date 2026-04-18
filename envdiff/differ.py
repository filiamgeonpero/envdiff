"""Line-level diff between two .env file contents."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class DiffLine:
    line_no_a: int | None
    line_no_b: int | None
    tag: str  # 'equal', 'replace', 'insert', 'delete'
    content_a: str | None
    content_b: str | None

    def __str__(self) -> str:
        if self.tag == "equal":
            return f"  {self.content_a}"
        if self.tag == "delete":
            return f"- {self.content_a}"
        if self.tag == "insert":
            return f"+ {self.content_b}"
        if self.tag == "replace":
            return f"- {self.content_a}\n+ {self.content_b}"
        return ""


@dataclass
class FileDiff:
    name_a: str
    name_b: str
    lines: List[DiffLine] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(l.tag != "equal" for l in self.lines)

    def changed_lines(self) -> List[DiffLine]:
        return [l for l in self.lines if l.tag != "equal"]


def diff_files(name_a: str, text_a: str, name_b: str, text_b: str) -> FileDiff:
    """Produce a line-level diff between two .env file texts."""
    import difflib

    lines_a = text_a.splitlines()
    lines_b = text_b.splitlines()
    matcher = difflib.SequenceMatcher(None, lines_a, lines_b, autojunk=False)
    result = FileDiff(name_a=name_a, name_b=name_b)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset, line in enumerate(lines_a[i1:i2]):
                result.lines.append(
                    DiffLine(i1 + offset, j1 + offset, "equal", line, line)
                )
        elif tag == "delete":
            for offset, line in enumerate(lines_a[i1:i2]):
                result.lines.append(
                    DiffLine(i1 + offset, None, "delete", line, None)
                )
        elif tag == "insert":
            for offset, line in enumerate(lines_b[j1:j2]):
                result.lines.append(
                    DiffLine(None, j1 + offset, "insert", None, line)
                )
        elif tag == "replace":
            for offset in range(max(i2 - i1, j2 - j1)):
                ca = lines_a[i1 + offset] if i1 + offset < i2 else None
                cb = lines_b[j1 + offset] if j1 + offset < j2 else None
                la = i1 + offset if ca is not None else None
                lb = j1 + offset if cb is not None else None
                result.lines.append(DiffLine(la, lb, "replace", ca, cb))
    return result
