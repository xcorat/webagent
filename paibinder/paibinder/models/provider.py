"""PydanticAI agent factory and retrieval tool bindings."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from paibinder.config import BotConfig, ModelConfig
from paibinder.context.compiler import ChatMessage
from paibinder.retrieval.docs import read_doc_slice as _read_doc_slice
from paibinder.retrieval.docs import search_docs as _search_docs
from paibinder.retrieval.store import connect_db, init_schema, search_fts


@dataclass
class AgentDeps:
    """Per-request dependencies injected into PydanticAI tool contexts."""

    config: BotConfig
    docs_dir: Path
    store_db: Path
    collected_sources: list[dict[str, Any]] = field(default_factory=list)
    _seen_keys: set[tuple[Any, ...]] = field(default_factory=set, repr=False)

    def add_source(self, source: dict[str, Any]) -> None:
        """Record a normalized citation without duplicates."""
        key = (
            source.get("type"),
            source.get("path") or source.get("id"),
            source.get("start_line"),
            source.get("end_line"),
        )
        if key not in self._seen_keys:
            self._seen_keys.add(key)
            self.collected_sources.append(source)


def to_pydantic_history(history: list[ChatMessage]) -> list[ModelMessage]:
    """Convert ChatMessage history into PydanticAI ModelMessage objects."""
    converted: list[ModelMessage] = []
    for msg in history:
        if msg.role == "user":
            converted.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
        else:
            converted.append(ModelResponse(parts=[TextPart(content=msg.content)]))
    return converted


def build_model(model_config: ModelConfig) -> Any:
    """Resolve a PydanticAI model from ModelConfig, supporting custom base_url."""
    if not model_config.base_url:
        return model_config.name

    # Strip provider prefix (e.g. "ollama:llama3.2" or "openai:gpt-4o-mini") for OpenAI-compatible URLs
    model_name = model_config.name.split(":", 1)[-1]
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    return OpenAIChatModel(
        model_name=model_name,
        provider=OpenAIProvider(base_url=model_config.base_url),
    )


def create_agent(
    config: BotConfig,
    system_prompt: str = "",
    model_override: Any | None = None,
) -> Agent[AgentDeps, str]:
    """Create a PydanticAI Agent wired with Set 1 (docs) and Set 3 (blocks) tools."""
    model = model_override if model_override is not None else build_model(config.model)
    instructions = system_prompt or config.bot.persona

    agent: Agent[AgentDeps, str] = Agent(
        model=model,
        deps_type=AgentDeps,
        instructions=instructions,
        model_settings=ModelSettings(temperature=config.model.temperature),
    )

    @agent.tool
    def search_docs(ctx: RunContext[AgentDeps], query: str) -> list[dict[str, Any]]:
        """Search long-form markdown documentation for matching lines."""
        matches = _search_docs(
            ctx.deps.docs_dir,
            query,
            max_results=ctx.deps.config.retrieval.max_results,
        )
        results = [m.model_dump() for m in matches]
        for m in matches:
            ctx.deps.add_source(
                {
                    "type": "doc",
                    "path": m.path,
                    "start_line": m.line_number,
                    "end_line": m.line_number,
                }
            )
        return results

    @agent.tool
    def read_doc_slice(
        ctx: RunContext[AgentDeps],
        path: str,
        start_line: int = 1,
        end_line: int = 80,
    ) -> dict[str, Any]:
        """Read a targeted line range from a markdown file in docs/."""
        try:
            doc_slice = _read_doc_slice(
                ctx.deps.docs_dir,
                path,
                start_line=start_line,
                end_line=end_line,
            )
        except (FileNotFoundError, ValueError) as exc:
            return {"error": str(exc)}

        ctx.deps.add_source(
            {
                "type": "doc",
                "path": doc_slice.path,
                "start_line": doc_slice.start_line,
                "end_line": doc_slice.end_line,
            }
        )
        return doc_slice.model_dump()

    @agent.tool
    def search_blocks(ctx: RunContext[AgentDeps], query: str) -> list[dict[str, Any]]:
        """Search short-form dynamic knowledge blocks in SQLite FTS5."""
        if not ctx.deps.store_db.exists():
            return []
        conn = connect_db(ctx.deps.store_db)
        try:
            init_schema(conn)
            hits = search_fts(
                conn,
                query,
                limit=ctx.deps.config.retrieval.max_results,
            )
        finally:
            conn.close()

        for h in hits:
            ctx.deps.add_source(
                {
                    "type": "block",
                    "id": h.id,
                    "title": h.title,
                    "source": h.source,
                }
            )
        return [h.model_dump() for h in hits]

    return agent
