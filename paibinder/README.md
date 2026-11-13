# `paibinder` — Python AI Binder (`v0.1.0`)

Backend context engineering engine, retrieval layer, model provider abstraction, and FastAPI SSE API for WebAgent.

## Setup

```bash
cd webagent/paibinder
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

(Or with `uv`: `uv sync --extra dev`)

## Configuration

`paibinder` resolves configuration in this order:
1. `BOT_CONFIG` environment variable (explicit YAML path)
2. `../storage/bot.yaml` (local dev instance config outside the git repo)
3. Built-in `bot.example.yaml` defaults

Copy `.env.example` to `.env` and set your provider API key (e.g. `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY`), or point `model.base_url` in `bot.yaml` to a local Ollama/vLLM server.

## Seed Knowledge Blocks (Set 3)

```bash
.venv/bin/paibinder-seed --source ../../storage/store/sample-blocks.jsonl
```

## Run the Server

```bash
.venv/bin/uvicorn paibinder.main:app --reload --port 8000
```

## Run Tests

```bash
.venv/bin/pytest
```
