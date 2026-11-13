"""Tests for context compiler (paibinder.context.compiler)."""

from __future__ import annotations

import pytest

from paibinder.config import BotConfig, ContextConfig
from paibinder.context.compiler import ChatMessage, compile_context, trim_history


def test_trim_history_preserves_user_boundary() -> None:
    msgs = [
        ChatMessage(role="assistant", content="orphan"),
        ChatMessage(role="user", content="u1"),
        ChatMessage(role="assistant", content="a1"),
        ChatMessage(role="user", content="u2"),
        ChatMessage(role="assistant", content="a2"),
    ]
    trimmed = trim_history(msgs, max_turns=1)
    assert [m.content for m in trimmed] == ["u2", "a2"]


def test_compile_context_builds_prompt_and_extracts_latest_user() -> None:
    cfg = BotConfig(context=ContextConfig(max_history_turns=1))
    messages = [
        ChatMessage(role="user", content="first"),
        ChatMessage(role="assistant", content="first reply"),
        ChatMessage(role="user", content="second"),
        ChatMessage(role="assistant", content="second reply"),
        ChatMessage(role="user", content="latest question"),
    ]
    compiled = compile_context(cfg, messages)
    assert "Grounding rules:" in compiled.system_prompt
    assert [m.content for m in compiled.history] == ["second", "second reply"]
    assert compiled.latest_user_message == "latest question"


def test_compile_context_requires_trailing_user_message() -> None:
    cfg = BotConfig()
    with pytest.raises(ValueError, match="role 'user'"):
        compile_context(cfg, [ChatMessage(role="assistant", content="hello")])
