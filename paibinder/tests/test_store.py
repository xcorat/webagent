"""Tests for Set 3 SQLite FTS5 storage and retrieval (paibinder.retrieval.store)."""

from __future__ import annotations

from pathlib import Path

from paibinder.retrieval.store import BlockInput, connect_db, init_schema, search_fts, upsert_blocks


def test_upsert_blocks_deduplicates_and_updates(tmp_path: Path) -> None:
    db_path = tmp_path / "store.db"
    conn = connect_db(db_path)
    try:
        init_schema(conn)
        initial = [
            BlockInput(
                id="blk-1",
                title="API Port",
                content="The backend listens on port 8000 by default.",
                tags=["api", "port"],
                source="faq.jsonl",
            ),
            BlockInput(
                id="blk-2",
                title="Seed Command",
                content="Run paibinder-seed to ingest short blocks.",
                tags=["cli"],
                source="faq.jsonl",
            ),
        ]
        stats1 = upsert_blocks(conn, initial)
        assert stats1.inserted == 2
        assert stats1.updated == 0
        assert stats1.skipped == 0

        # Re-upserting identical content skips both
        stats2 = upsert_blocks(conn, initial)
        assert stats2.inserted == 0
        assert stats2.updated == 0
        assert stats2.skipped == 2

        # Modifying one block updates only that block
        modified = [
            BlockInput(
                id="blk-1",
                title="API Port",
                content="The backend listens on port 8080 in production.",
                tags=["api", "port"],
                source="faq.jsonl",
            ),
            initial[1],
        ]
        stats3 = upsert_blocks(conn, modified)
        assert stats3.inserted == 0
        assert stats3.updated == 1
        assert stats3.skipped == 1

        hits = search_fts(conn, "port 8080", limit=5)
        assert len(hits) == 1
        assert hits[0].id == "blk-1"
        assert "8080" in hits[0].content
    finally:
        conn.close()


def test_search_fts_handles_punctuation_safely(tmp_path: Path) -> None:
    conn = connect_db(tmp_path / "store.db")
    try:
        upsert_blocks(
            conn,
            [
                BlockInput(
                    id="blk-v1",
                    title="Version v0.1.0",
                    content="Initial release uses SQLite FTS5.",
                )
            ],
        )
        hits = search_fts(conn, "v0.1.0 (FTS5)?", limit=5)
        assert len(hits) == 1
        assert hits[0].id == "blk-v1"
    finally:
        conn.close()
