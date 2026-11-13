# WebAgent Documentation

## Architecture

`webagent` separates shared engine code from instance-specific knowledge:

- **`paibinder/` (Backend):** Compiles context, exposes retrieval tools to a PydanticAI agent, and streams responses over HTTP/SSE.
- **`ui/` (Frontend):** Lightweight Svelte chat client.
- **External `storage/` (Per-Bot Data):**
  - **Set 1 (`docs/`):** Long-form markdown files searched via `ripgrep` (with automatic `grep` fallback) and read in targeted line slices.
  - **Set 3 (`store/store.db`):** Short-form dynamic text blocks indexed in SQLite `FTS5` (BM25) with SHA-256 `content_hash` deduplication.

## Configuration

`paibinder` loads configuration in the following order:

1. `BOT_CONFIG` environment variable (explicit YAML path)
2. `../storage/bot.yaml` (local instance config outside the git repo)
3. Built-in `paibinder/bot.example.yaml` defaults

Secrets (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) are loaded from `.env` or process environment variables. Local OpenAI-compatible or Ollama servers can be configured by setting `model.base_url` in `bot.yaml`.

## Seeding Short Blocks (Set 3)

Ingest `.jsonl` or `.md` snippet files into `store.db` without duplicating unchanged rows:

```bash
paibinder-seed --source path/to/blocks.jsonl
```

## HTTP & SSE API

- **`GET /health`** — Returns readiness status, active search backend (`rg` or `grep`), and SQLite store status.
- **`POST /api/chat`** — Accepts `{ "messages": [{ "role": "user" | "assistant", "content": "..." }] }` and streams `text/event-stream` events:
  - `text_delta` — Streamed assistant text chunks
  - `tool_call` — Retrieval tool name and arguments
  - `tool_result` — Summarized tool output
  - `sources` — Normalized citations (doc paths + line ranges, block IDs/titles)
  - `error` — Structured error message
  - `done` — Stream completion signal
