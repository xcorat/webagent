# WebAgent

A lightweight, cloneable agentic AI knowledge retriever and disseminator.

`webagent` keeps the engine strictly separate from per-bot knowledge and configuration, so a single codebase can power many specialized assistants.

## Layout

- `paibinder/` — Python AI Binder (context compiler, retrieval tools, PydanticAI model wiring, FastAPI SSE API)
- `ui/` — Svelte chat frontend
- `docs/` — Architecture, configuration, and API documentation

## Quickstart (`paibinder`)

```bash
cd paibinder
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Optional: configure API keys or local Ollama/OpenAI-compatible endpoint
cp .env.example .env

# Seed short-form knowledge blocks into SQLite FTS5
.venv/bin/paibinder-seed --source ../../storage/store/sample-blocks.jsonl

# Start the API server
.venv/bin/uvicorn paibinder.main:app --reload --port 8000
```

Run the offline test suite:

```bash
cd paibinder && .venv/bin/pytest
```

See [docs/INSTALL.md](docs/INSTALL.md) for custom project setup and upgrade workflows, and [docs/README.md](docs/README.md) for architecture and API details.

## License

Licensed under the [GNU General Public License v3.0](LICENSE).
