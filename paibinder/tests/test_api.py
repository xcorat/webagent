"""Offline API and agent loop tests using FastAPI TestClient and PydanticAI TestModel."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic_ai.models.test import TestModel

from paibinder.config import BotConfig, StorageConfig
from paibinder.main import create_app
from paibinder.retrieval.store import BlockInput, connect_db, upsert_blocks


def _parse_sse(raw_text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for chunk in raw_text.strip().split("\n\n"):
        if not chunk.strip():
            continue
        event_type = ""
        data_line = "{}"
        for line in chunk.splitlines():
            if line.startswith("event: "):
                event_type = line[len("event: ") :].strip()
            elif line.startswith("data: "):
                data_line = line[len("data: ") :].strip()
        events.append((event_type, json.loads(data_line)))
    return events


def test_health_and_chat_sse_stream(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide\n\nWebAgent runs on port 8000.\n", encoding="utf-8")

    db_path = tmp_path / "store" / "store.db"
    conn = connect_db(db_path)
    try:
        upsert_blocks(
            conn,
            [
                BlockInput(
                    id="blk-1",
                    title="Port",
                    content="Default port is 8000.",
                    source="seed.jsonl",
                )
            ],
        )
    finally:
        conn.close()

    cfg = BotConfig(
        storage=StorageConfig(
            docs_dir=str(docs_dir),
            store_db=str(db_path),
        )
    )
    app = create_app(config=cfg, model_override=TestModel())

    with TestClient(app) as client:
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["status"] == "ok"
        assert health_data["docs_dir_exists"] is True
        assert health_data["store_db"] == "ok"

        chat_resp = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "What port does WebAgent use?"},
                ]
            },
        )
        assert chat_resp.status_code == 200
        assert "text/event-stream" in chat_resp.headers["content-type"]

        events = _parse_sse(chat_resp.text)
        event_types = [ev[0] for ev in events]
        assert "tool_call" in event_types
        assert "tool_result" in event_types
        assert "text_delta" in event_types
        assert "sources" in event_types
        assert event_types[-1] == "done"
