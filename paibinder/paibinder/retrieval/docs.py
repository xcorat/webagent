"""Set 1 retrieval: ripgrep (with grep fallback) and safe line-slice reader over docs/."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

SearchBackend = Literal["rg", "grep", "none"]


class DocMatch(BaseModel):
    """Single line match in a markdown document."""

    path: str
    line_number: int
    line_text: str


class DocSlice(BaseModel):
    """Targeted line-range slice from a markdown document."""

    path: str
    start_line: int
    end_line: int
    total_lines: int
    content: str


def detect_search_backend() -> SearchBackend:
    """Detect available CLI search backend, preferring ripgrep over grep."""
    if shutil.which("rg"):
        return "rg"
    if shutil.which("grep"):
        return "grep"
    return "none"


def _search_with_rg(root: Path, query: str, max_results: int) -> list[DocMatch]:
    cmd = ["rg", "--json", "--ignore-case", "--max-count", str(max_results), query, str(root)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode == 2:
        # Retry as fixed string if regex syntax was invalid
        cmd = [
            "rg",
            "--json",
            "--ignore-case",
            "--fixed-strings",
            "--max-count",
            str(max_results),
            query,
            str(root),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    matches: list[DocMatch] = []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "match":
            continue
        data = event["data"]
        abs_path = Path(data["path"]["text"]).resolve()
        try:
            rel_path = abs_path.relative_to(root).as_posix()
        except ValueError:
            continue
        line_num = int(data["line_number"])
        text = data["lines"]["text"].rstrip("\r\n")
        matches.append(DocMatch(path=rel_path, line_number=line_num, line_text=text))
        if len(matches) >= max_results:
            break
    return matches


def _search_with_grep(root: Path, query: str, max_results: int) -> list[DocMatch]:
    base_args = [
        "grep",
        "-rnHI",
        "-i",
        "--exclude-dir=.git",
        "--include=*.md",
        "-m",
        str(max_results),
    ]
    proc = subprocess.run(
        [*base_args, "-E", "--", query, str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 2:
        proc = subprocess.run(
            [*base_args, "-F", "--", query, str(root)],
            capture_output=True,
            text=True,
            check=False,
        )

    matches: list[DocMatch] = []
    for raw_line in proc.stdout.splitlines():
        parts = raw_line.split(":", 2)
        if len(parts) < 3:
            continue
        raw_path, raw_lnum, text = parts
        try:
            rel_path = Path(raw_path).resolve().relative_to(root).as_posix()
            line_num = int(raw_lnum)
        except (ValueError, OSError):
            continue
        matches.append(DocMatch(path=rel_path, line_number=line_num, line_text=text))
        if len(matches) >= max_results:
            break
    return matches


def search_docs(docs_dir: Path, query: str, max_results: int = 5) -> list[DocMatch]:
    """Search markdown files in docs_dir using rg (or grep fallback)."""
    query = query.strip()
    if not query or max_results <= 0 or not docs_dir.is_dir():
        return []

    root = docs_dir.resolve()
    backend = detect_search_backend()
    if backend == "rg":
        return _search_with_rg(root, query, max_results)
    if backend == "grep":
        return _search_with_grep(root, query, max_results)
    raise RuntimeError("Neither 'rg' nor 'grep' is available on PATH.")


def read_doc_slice(
    docs_dir: Path,
    rel_path: str,
    start_line: int = 1,
    end_line: int = 80,
    max_lines: int = 200,
) -> DocSlice:
    """Safely read a 1-indexed inclusive line slice from a file inside docs_dir."""
    root = docs_dir.resolve()
    target = (root / rel_path).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"Access denied: path escapes docs_dir ({rel_path})")
    if not target.is_file():
        raise FileNotFoundError(f"Document not found: {rel_path}")

    all_lines = target.read_text(encoding="utf-8").splitlines()
    total_lines = len(all_lines)
    if total_lines == 0:
        return DocSlice(
            path=target.relative_to(root).as_posix(),
            start_line=1,
            end_line=0,
            total_lines=0,
            content="",
        )

    clamped_start = max(1, min(start_line, total_lines))
    clamped_end = max(clamped_start, min(end_line, total_lines, clamped_start + max_lines - 1))
    sliced = all_lines[clamped_start - 1 : clamped_end]
    numbered = "\n".join(
        f"{idx}: {line}" for idx, line in enumerate(sliced, start=clamped_start)
    )
    return DocSlice(
        path=target.relative_to(root).as_posix(),
        start_line=clamped_start,
        end_line=clamped_end,
        total_lines=total_lines,
        content=numbered,
    )
