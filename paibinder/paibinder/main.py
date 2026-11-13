"""FastAPI HTTP and SSE streaming API for paibinder."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)

from paibinder.config import BotConfig, EnvSettings, load_config
from paibinder.context.compiler import ChatMessage, compile_context
from paibinder.models.provider import AgentDeps, create_agent, to_pydantic_history
from paibinder.retrieval.docs import detect_search_backend


class ChatRequest(BaseModel):
    """Stateless chat request payload."""

    messages: list[ChatMessage] = Field(min_length=1)


def _format_sse(event_type: str, payload: dict[str, Any]) -> str:
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _summarize_tool_result(content: Any, limit: int = 240) -> str:
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load BotConfig once at startup if not pre-configured by tests."""
    if not hasattr(app.state, "config") or app.state.config is None:
        app.state.config = load_config()
    if not hasattr(app.state, "model_override"):
        app.state.model_override = None
    yield


def create_app(
    config: BotConfig | None = None,
    model_override: Any | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    env = EnvSettings()
    application = FastAPI(title="paibinder", version="0.1.0", lifespan=lifespan)
    application.state.config = config
    application.state.model_override = model_override

    application.add_middleware(
        CORSMiddleware,
        allow_origins=env.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    async def health(request: Request) -> JSONResponse:
        cfg: BotConfig = request.app.state.config
        backend = detect_search_backend()
        docs_ok = cfg.docs_path.is_dir()

        db_status = "uninitialized"
        db_ok = True
        if cfg.store_db_path.is_file():
            try:
                conn = sqlite3.connect(cfg.store_db_path)
                conn.execute("SELECT 1").fetchone()
                conn.close()
                db_status = "ok"
            except sqlite3.Error as exc:
                db_status = f"error: {exc}"
                db_ok = False

        healthy = backend != "none" and db_ok
        status_code = 200 if healthy else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ok" if healthy else "degraded",
                "bot": cfg.bot.name,
                "model": cfg.model.name,
                "search_backend": backend,
                "docs_dir_exists": docs_ok,
                "store_db": db_status,
            },
        )

    @application.post("/api/chat")
    async def chat(payload: ChatRequest, request: Request) -> StreamingResponse:
        cfg: BotConfig = request.app.state.config
        override = getattr(request.app.state, "model_override", None)

        try:
            compiled = compile_context(cfg, payload.messages)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        agent = create_agent(
            cfg,
            system_prompt=compiled.system_prompt,
            model_override=override,
        )
        deps = AgentDeps(
            config=cfg,
            docs_dir=cfg.docs_path,
            store_db=cfg.store_db_path,
        )
        history = to_pydantic_history(compiled.history)

        async def event_stream() -> AsyncIterator[str]:
            try:
                async with agent.iter(
                    compiled.latest_user_message,
                    deps=deps,
                    message_history=history,
                ) as agent_run:
                    async for node in agent_run:
                        if Agent.is_model_request_node(node):
                            async with node.stream(agent_run.ctx) as request_stream:
                                async for event in request_stream:
                                    if isinstance(event, PartStartEvent) and isinstance(
                                        event.part, TextPart
                                    ):
                                        if event.part.content:
                                            yield _format_sse(
                                                "text_delta",
                                                {"delta": event.part.content},
                                            )
                                    elif isinstance(event, PartDeltaEvent) and isinstance(
                                        event.delta, TextPartDelta
                                    ):
                                        if event.delta.content_delta:
                                            yield _format_sse(
                                                "text_delta",
                                                {"delta": event.delta.content_delta},
                                            )
                        elif Agent.is_call_tools_node(node):
                            async with node.stream(agent_run.ctx) as handle_stream:
                                async for event in handle_stream:
                                    if isinstance(event, FunctionToolCallEvent):
                                        yield _format_sse(
                                            "tool_call",
                                            {
                                                "tool": event.part.tool_name,
                                                "args": event.part.args_as_dict(),
                                            },
                                        )
                                    elif isinstance(event, FunctionToolResultEvent):
                                        yield _format_sse(
                                            "tool_result",
                                            {
                                                "tool": event.part.tool_name,
                                                "summary": _summarize_tool_result(
                                                    event.part.content
                                                ),
                                            },
                                        )

                yield _format_sse("sources", {"sources": deps.collected_sources})
                yield _format_sse("done", {})
            except Exception as exc:  # noqa: BLE001
                yield _format_sse("error", {"message": str(exc)})
                yield _format_sse("done", {})

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return application


app = create_app()
