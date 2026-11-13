"""Set 3 storage and FTS5 BM25 retrieval over SQLite."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS blocks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL,
    embedding_model TEXT DEFAULT NULL,
    updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS blocks_fts USING fts5(
    title,
    content,
    tags,
    content='blocks',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS blocks_ai AFTER INSERT ON blocks BEGIN
    INSERT INTO blocks_fts(rowid, title, content, tags)
    VALUES (new.rowid, new.title, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS blocks_ad AFTER DELETE ON blocks BEGIN
    INSERT INTO blocks_fts(blocks_fts, rowid, title, content, tags)
    VALUES ('delete', old.rowid, old.title, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS blocks_au AFTER UPDATE ON blocks BEGIN
    INSERT INTO blocks_fts(blocks_fts, rowid, title, content, tags)
    VALUES ('delete', old.rowid, old.title, old.content, old.tags);
    INSERT INTO blocks_fts(rowid, title, content, tags)
    VALUES (new.rowid, new.title, new.content, new.tags);
END;
"""

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class BlockInput(BaseModel):
    """Input record for upserting a short-form text block."""

    id: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    source: str = ""


class BlockHit(BaseModel):
    """Search result from FTS5 block retrieval."""

    id: str
    title: str
    content: str
    tags: list[str]
    source: str
    score: float


class UpsertStats(BaseModel):
    """Summary counts from an upsert_blocks operation."""

    inserted: int = 0
    updated: int = 0
    skipped: int = 0


def connect_db(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with row factory and WAL mode enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize Set 3 tables, FTS5 virtual table, and sync triggers."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def compute_content_hash(title: str, content: str, tags: str, source: str) -> str:
    """Compute deterministic SHA-256 hash for change detection."""
    payload = "\x00".join((title, content, tags, source)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalize_tags(tags: list[str] | str) -> str:
    if isinstance(tags, str):
        parts = [t.strip() for t in tags.split(",") if t.strip()]
    else:
        parts = [t.strip() for t in tags if t.strip()]
    return ", ".join(parts)


def upsert_blocks(conn: sqlite3.Connection, blocks: Iterable[BlockInput]) -> UpsertStats:
    """Insert or update blocks, skipping rows whose content_hash is unchanged."""
    init_schema(conn)
    stats = UpsertStats()
    now = datetime.now(timezone.utc).isoformat()

    for block in blocks:
        tags_str = _normalize_tags(block.tags)
        digest = compute_content_hash(block.title, block.content, tags_str, block.source)
        existing = conn.execute(
            "SELECT content_hash FROM blocks WHERE id = ?",
            (block.id,),
        ).fetchone()

        if existing is None:
            conn.execute(
                """
                INSERT INTO blocks (id, title, content, tags, source, content_hash, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (block.id, block.title, block.content, tags_str, block.source, digest, now),
            )
            stats.inserted += 1
        elif existing["content_hash"] != digest:
            conn.execute(
                """
                UPDATE blocks
                SET title = ?, content = ?, tags = ?, source = ?, content_hash = ?, updated_at = ?
                WHERE id = ?
                """,
                (block.title, block.content, tags_str, block.source, digest, now, block.id),
            )
            stats.updated += 1
        else:
            stats.skipped += 1

    conn.commit()
    return stats


def _build_fts_query(raw_query: str) -> str:
    """Sanitize a free-text query into safe FTS5 OR-joined tokens."""
    tokens = _TOKEN_RE.findall(raw_query)
    if not tokens:
        return ""
    return " OR ".join(f'"{tok}"' for tok in tokens)


def search_fts(conn: sqlite3.Connection, query: str, limit: int = 5) -> list[BlockHit]:
    """Search blocks using SQLite FTS5 BM25 ranking."""
    fts_query = _build_fts_query(query)
    if not fts_query or limit <= 0:
        return []

    rows = conn.execute(
        """
        SELECT
            b.id,
            b.title,
            b.content,
            b.tags,
            b.source,
            bm25(blocks_fts) AS rank
        FROM blocks_fts
        JOIN blocks b ON b.rowid = blocks_fts.rowid
        WHERE blocks_fts MATCH ?
        ORDER BY rank ASC
        LIMIT ?
        """,
        (fts_query, limit),
    ).fetchall()

    hits: list[BlockHit] = []
    for row in rows:
        tags_list = [t.strip() for t in row["tags"].split(",") if t.strip()]
        # bm25() returns negative values where more negative = better match; negate for readability.
        hits.append(
            BlockHit(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                tags=tags_list,
                source=row["source"],
                score=-float(row["rank"]),
            )
        )
    return hits
