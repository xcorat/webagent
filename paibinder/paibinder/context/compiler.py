"""Minimal stateless context compiler for v0.1.0."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from paibinder.config import BotConfig

GROUNDING_INSTRUCTIONS = (
    "Grounding rules:\n"
    "- Use the retrieval tools (search_docs, read_doc_slice, search_blocks) to verify facts "
    "before answering.\n"
    "- Cite the exact source file path and line range (for docs) or block ID and title "
    "(for blocks) that support your answer.\n"
    "- If the knowledge base does not contain the answer, say so clearly instead of guessing."
)


class ChatMessage(BaseModel):
    """Single message in the client-supplied conversation history."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class CompiledContext(BaseModel):
    """Compiled system prompt, trimmed prior history, and latest user prompt."""

    system_prompt: str
    history: list[ChatMessage]
    latest_user_message: str


def trim_history(messages: list[ChatMessage], max_turns: int) -> list[ChatMessage]:
    """Keep at most max_turns user+assistant pairs, starting on a user message."""
    if max_turns <= 0 or not messages:
        return []

    max_messages = max_turns * 2
    trimmed = messages[-max_messages:]
    while trimmed and trimmed[0].role != "user":
        trimmed = trimmed[1:]
    return list(trimmed)


def compile_context(bot_config: BotConfig, messages: list[ChatMessage]) -> CompiledContext:
    """Compile system prompt and trimmed history for a single stateless request."""
    if not messages:
        raise ValueError("messages must not be empty.")
    if messages[-1].role != "user":
        raise ValueError("The final message must have role 'user'.")

    persona = bot_config.bot.persona.strip()
    system_prompt = f"{persona}\n\n{GROUNDING_INSTRUCTIONS}" if persona else GROUNDING_INSTRUCTIONS

    prior_history = trim_history(messages[:-1], bot_config.context.max_history_turns)
    return CompiledContext(
        system_prompt=system_prompt,
        history=prior_history,
        latest_user_message=messages[-1].content,
    )
