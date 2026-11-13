"""Tests for paibinder.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from paibinder.config import load_config


def test_load_config_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("BOT_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.bot.name == "WebAgent"
    assert cfg.context.max_history_turns == 10
    assert cfg.retrieval.max_results == 5


def test_load_config_from_bot_config_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom_yaml = tmp_path / "custom-bot.yaml"
    custom_yaml.write_text(
        """
bot:
  name: "CustomBot"
  persona: "Custom persona."
model:
  name: "ollama:llama3.2"
  base_url: "http://localhost:11434/v1"
  temperature: 0.5
storage:
  docs_dir: "./docs"
  store_db: "./store/custom.db"
context:
  max_history_turns: 4
retrieval:
  max_results: 3
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("BOT_CONFIG", str(custom_yaml))

    cfg = load_config()
    assert cfg.bot.name == "CustomBot"
    assert cfg.model.name == "ollama:llama3.2"
    assert cfg.model.base_url == "http://localhost:11434/v1"
    assert cfg.context.max_history_turns == 4
    assert cfg.retrieval.max_results == 3
    assert cfg.docs_path == (tmp_path / "docs").resolve()
    assert cfg.store_db_path == (tmp_path / "store" / "custom.db").resolve()


def test_load_config_missing_env_file_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("BOT_CONFIG", str(tmp_path / "nonexistent.yaml"))
    with pytest.raises(FileNotFoundError):
        load_config()
