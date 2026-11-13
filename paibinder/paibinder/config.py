"""Configuration loading and validation for paibinder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


class BotIdentityConfig(BaseModel):
    """Identity and persona settings for a bot instance."""

    name: str = "WebAgent"
    persona: str = (
        "You are a helpful, accurate knowledge assistant. Answer questions using "
        "only verified information from the connected knowledge base."
    )


class ModelConfig(BaseModel):
    """LLM provider configuration."""

    name: str = "openai:gpt-4o-mini"
    base_url: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class StorageConfig(BaseModel):
    """Paths to Set 1 (docs) and Set 2/3 (SQLite store)."""

    docs_dir: str = "../storage/docs"
    store_db: str = "../storage/store/store.db"


class ContextConfig(BaseModel):
    """Context compilation limits."""

    max_history_turns: int = Field(default=10, ge=1)


class RetrievalConfig(BaseModel):
    """Retrieval defaults."""

    max_results: int = Field(default=5, ge=1, le=50)


class BotConfig(BaseModel):
    """Top-level validated bot configuration."""

    bot: BotIdentityConfig = Field(default_factory=BotIdentityConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    config_source: Path | None = Field(default=None, exclude=True)

    def resolve_path(self, raw_path: str) -> Path:
        """Resolve a storage path relative to the config file (or CWD for defaults)."""
        p = Path(raw_path)
        if p.is_absolute():
            return p
        if self.config_source is not None and self.config_source.name != "bot.example.yaml":
            return (self.config_source.parent / p).resolve()
        return (Path.cwd() / p).resolve()

    @property
    def docs_path(self) -> Path:
        """Resolved path to Set 1 markdown docs directory."""
        return self.resolve_path(self.storage.docs_dir)

    @property
    def store_db_path(self) -> Path:
        """Resolved path to Set 2/3 SQLite database."""
        return self.resolve_path(self.storage.store_db)


class EnvSettings(BaseSettings):
    """Environment-level settings loaded from .env and process env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_config: str | None = Field(default=None, alias="BOT_CONFIG")
    ui_dist_dir: str | None = Field(default=None, alias="UI_DIST_DIR")


def _find_config_file(explicit_path: Path | None, env_path: str | None) -> Path | None:
    """Resolve config file path according to precedence rules."""
    if explicit_path is not None:
        if not explicit_path.is_file():
            raise FileNotFoundError(f"Bot config file not found: {explicit_path}")
        return explicit_path.resolve()

    if env_path:
        candidate = Path(env_path)
        if not candidate.is_file():
            raise FileNotFoundError(f"BOT_CONFIG file not found: {candidate}")
        return candidate.resolve()

    for rel in (Path("../storage/bot.yaml"), Path("../../storage/bot.yaml")):
        if rel.is_file():
            return rel.resolve()

    example = PACKAGE_ROOT / "bot.example.yaml"
    if example.is_file():
        return example.resolve()

    return None


def load_config(config_path: Path | None = None) -> BotConfig:
    """Load and validate BotConfig using BOT_CONFIG -> ../storage/bot.yaml -> fallback."""
    env = EnvSettings()
    resolved = _find_config_file(config_path, env.bot_config)
    if resolved is None:
        return BotConfig()

    raw: dict[str, Any] = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
    cfg = BotConfig.model_validate(raw)
    cfg.config_source = resolved
    return cfg
