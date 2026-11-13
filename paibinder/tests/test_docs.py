"""Tests for Set 1 retrieval (paibinder.retrieval.docs)."""

from __future__ import annotations

from pathlib import Path

import pytest

from paibinder.retrieval.docs import _search_with_grep, read_doc_slice, search_docs


@pytest.fixture()
def sample_docs(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text(
        "# Deployment Guide\n\nLine 3: Use port 8080.\nLine 4: Set BOT_CONFIG.\nLine 5: Done.\n",
        encoding="utf-8",
    )
    sub = docs / "sub"
    sub.mkdir()
    (sub / "faq.md").write_text(
        "# FAQ\n\nQ: How to reset?\nA: Run paibinder-seed again.\n",
        encoding="utf-8",
    )
    return docs


def test_search_docs_finds_matches(sample_docs: Path) -> None:
    matches = search_docs(sample_docs, "BOT_CONFIG", max_results=5)
    assert len(matches) == 1
    assert matches[0].path == "guide.md"
    assert matches[0].line_number == 4
    assert "BOT_CONFIG" in matches[0].line_text


def test_search_with_grep_fallback(sample_docs: Path) -> None:
    matches = _search_with_grep(sample_docs.resolve(), "paibinder-seed", max_results=5)
    assert len(matches) == 1
    assert matches[0].path == "sub/faq.md"
    assert matches[0].line_number == 4


def test_read_doc_slice_clamps_bounds(sample_docs: Path) -> None:
    doc_slice = read_doc_slice(sample_docs, "guide.md", start_line=2, end_line=99)
    assert doc_slice.start_line == 2
    assert doc_slice.end_line == 5
    assert doc_slice.total_lines == 5
    assert "3: Line 3: Use port 8080." in doc_slice.content


def test_read_doc_slice_rejects_path_traversal(sample_docs: Path, tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret", encoding="utf-8")

    with pytest.raises(ValueError, match="Access denied"):
        read_doc_slice(sample_docs, "../secret.txt", 1, 10)
