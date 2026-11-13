"""Set 2 retrieval placeholder: Semantic Glossary / Knowledge Graph (post-v0.1.0)."""

from __future__ import annotations

import sqlite3
from pydantic import BaseModel, Field


class GlossaryTerm(BaseModel):
    """Canonical term entry reserved for Set 2 KG + vector lookup."""

    term: str
    aliases: list[str] = Field(default_factory=list)
    definition: str = ""
    related_terms: list[str] = Field(default_factory=list)


def lookup_term(conn: sqlite3.Connection, term: str, limit: int = 5) -> list[GlossaryTerm]:
    """Placeholder interface for Set 2 glossary lookup (deferred to post-v0.1.0)."""
    _ = (conn, term, limit)
    return []
