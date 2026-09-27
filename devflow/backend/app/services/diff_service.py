"""
Unified Git diff parser.

Parses raw unified diff text (as produced by `git diff`) into structured
objects that the downstream analyzers and AI service can consume.

Never passes raw full-repo content — only the changed hunks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


# ─────────────────────────────────────────────────────────────────────────────
# Types
# ─────────────────────────────────────────────────────────────────────────────

class FileStatus(str, Enum):
    ADDED    = "added"
    DELETED  = "deleted"
    MODIFIED = "modified"
    RENAMED  = "renamed"
    BINARY   = "binary"


class LineType(str, Enum):
    ADD     = "add"
    REMOVE  = "remove"
    CONTEXT = "context"
    HEADER  = "header"


# Language detection by file extension
_EXT_TO_LANG: dict[str, str] = {
    ".py":    "python",
    ".js":    "javascript",
    ".jsx":   "javascript",
    ".ts":    "typescript",
    ".tsx":   "typescript",
    ".java":  "java",
    ".go":    "go",
    ".rs":    "rust",
    ".c":     "c",
    ".cpp":   "cpp",
    ".cs":    "csharp",
    ".rb":    "ruby",
    ".php":   "php",
    ".sh":    "shell",
    ".yaml":  "yaml",
    ".yml":   "yaml",
    ".json":  "json",
    ".sql":   "sql",
    ".md":    "markdown",
    ".html":  "html",
    ".css":   "css",
}


def _detect_language(path: str) -> str:
    dot = path.rfind(".")
    if dot == -1:
        return "unknown"
    return _EXT_TO_LANG.get(path[dot:].lower(), "unknown")


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DiffLine:
    line_type: LineType
    old_line:  int | None   # None for added lines and hunk headers
    new_line:  int | None   # None for removed lines and hunk headers
    content:   str          # raw line content without the leading +/-/ prefix


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header:    str          # the @@ ... @@ line verbatim
    lines:     list[DiffLine] = field(default_factory=list)

    @property
    def additions(self) -> int:
        return sum(1 for l in self.lines if l.line_type == LineType.ADD)

    @property
    def deletions(self) -> int:
        return sum(1 for l in self.lines if l.line_type == LineType.REMOVE)


@dataclass
class ChangedFile:
    path:       str
    old_path:   str | None          # set only for renames
    status:     FileStatus
    language:   str
    additions:  int = 0
    deletions:  int = 0
    hunks:      list[Hunk] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path":       self.path,
            "old_path":   self.old_path,
            "status":     self.status.value,
            "language":   self.language,
            "additions":  self.additions,
            "deletions":  self.deletions,
            "hunks": [
                {
                    "old_start": h.old_start,
                    "old_count": h.old_count,
                    "new_start": h.new_start,
                    "new_count": h.new_count,
                    "header":    h.header,
                    "lines": [
                        {
                            "line_type": l.line_type.value,
                            "old_line":  l.old_line,
                            "new_line":  l.new_line,
                            "content":   l.content,
                        }
                        for l in h.lines
                    ],
                }
                for h in self.hunks
            ],
        }


@dataclass
class ParsedDiff:
    files:     list[ChangedFile] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0

    def to_dict(self) -> dict:
        return {
            "files":     [f.to_dict() for f in self.files],
            "additions": self.additions,
            "deletions": self.deletions,
            "hunks":     [h for f in self.files for h in f.hunks],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Regex patterns
# ─────────────────────────────────────────────────────────────────────────────

_RE_DIFF_HEADER  = re.compile(r"^diff --git a/(.+?) b/(.+?)$")
_RE_NEW_FILE     = re.compile(r"^new file mode")
_RE_DELETED_FILE = re.compile(r"^deleted file mode")
_RE_RENAME_FROM  = re.compile(r"^rename from (.+)$")
_RE_RENAME_TO    = re.compile(r"^rename to (.+)$")
_RE_BINARY       = re.compile(r"^Binary files .+ differ$")
_RE_HUNK_HEADER  = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)"
)


# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_diff(raw_diff: str) -> ParsedDiff:
    """
    Parse a raw unified diff string into a :class:`ParsedDiff`.

    Args:
        raw_diff: Output of ``git diff`` or a GitHub compare API payload.

    Returns:
        Structured :class:`ParsedDiff` ready for the analyzer pipeline.
    """
    result = ParsedDiff()
    lines  = raw_diff.splitlines()
    i      = 0
    n      = len(lines)

    current_file: ChangedFile | None = None
    current_hunk: Hunk | None = None
    old_line_no = 0
    new_line_no = 0

    while i < n:
        line = lines[i]

        # ── New file diff block ─────────────────────────────────────────────
        m = _RE_DIFF_HEADER.match(line)
        if m:
            if current_file is not None:
                _finalise_file(current_file)
                result.files.append(current_file)

            a_path = m.group(1)
            b_path = m.group(2)
            current_file = ChangedFile(
                path=b_path,
                old_path=None,
                status=FileStatus.MODIFIED,
                language=_detect_language(b_path),
            )
            current_hunk = None
            i += 1
            continue

        if current_file is None:
            i += 1
            continue

        # ── File-level meta lines ───────────────────────────────────────────
        if _RE_NEW_FILE.match(line):
            current_file.status = FileStatus.ADDED
            i += 1
            continue

        if _RE_DELETED_FILE.match(line):
            current_file.status = FileStatus.DELETED
            i += 1
            continue

        m = _RE_RENAME_FROM.match(line)
        if m:
            current_file.old_path = m.group(1)
            current_file.status   = FileStatus.RENAMED
            i += 1
            continue

        m = _RE_RENAME_TO.match(line)
        if m:
            current_file.path     = m.group(1)
            current_file.language = _detect_language(m.group(1))
            i += 1
            continue

        if _RE_BINARY.match(line):
            current_file.status = FileStatus.BINARY
            i += 1
            continue

        # Skip --- and +++ file header lines
        if line.startswith("--- ") or line.startswith("+++ "):
            i += 1
            continue

        # ── Hunk header ─────────────────────────────────────────────────────
        m = _RE_HUNK_HEADER.match(line)
        if m:
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) is not None else 1

            current_hunk = Hunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
                header=line,
            )
            current_file.hunks.append(current_hunk)
            old_line_no = old_start
            new_line_no = new_start
            i += 1
            continue

        # ── Diff content lines ──────────────────────────────────────────────
        if current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                dl = DiffLine(
                    line_type=LineType.ADD,
                    old_line=None,
                    new_line=new_line_no,
                    content=line[1:],
                )
                current_hunk.lines.append(dl)
                new_line_no += 1

            elif line.startswith("-") and not line.startswith("---"):
                dl = DiffLine(
                    line_type=LineType.REMOVE,
                    old_line=old_line_no,
                    new_line=None,
                    content=line[1:],
                )
                current_hunk.lines.append(dl)
                old_line_no += 1

            elif line.startswith(" "):
                dl = DiffLine(
                    line_type=LineType.CONTEXT,
                    old_line=old_line_no,
                    new_line=new_line_no,
                    content=line[1:],
                )
                current_hunk.lines.append(dl)
                old_line_no += 1
                new_line_no += 1

        i += 1

    # Finalise last file
    if current_file is not None:
        _finalise_file(current_file)
        result.files.append(current_file)

    # Roll up totals
    result.additions = sum(f.additions for f in result.files)
    result.deletions = sum(f.deletions for f in result.files)

    return result


def _finalise_file(f: ChangedFile) -> None:
    """Compute per-file addition/deletion totals from parsed hunks."""
    f.additions = sum(h.additions for h in f.hunks)
    f.deletions = sum(h.deletions for h in f.hunks)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_changed_lines(file: ChangedFile) -> Iterator[DiffLine]:
    """Yield every added or removed line across all hunks of a file."""
    for hunk in file.hunks:
        for line in hunk.lines:
            if line.line_type in (LineType.ADD, LineType.REMOVE):
                yield line


def reconstruct_new_source(file: ChangedFile) -> str:
    """
    Reconstruct the post-patch source from context + added lines.
    Useful for feeding a single file's new content to an analyzer
    without sending the full repo.
    """
    parts: list[str] = []
    for hunk in file.hunks:
        for dl in hunk.lines:
            if dl.line_type in (LineType.ADD, LineType.CONTEXT):
                parts.append(dl.content)
    return "\n".join(parts)
