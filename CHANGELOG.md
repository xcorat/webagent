# Changelog

All notable changes to `webagent` are documented in this file.

## [0.1.0] - 2026-11-12

Initial minimal, cloneable end-to-end chatbot release (`paibinder` + `ui`).

### Added
- **Backend (`paibinder`):**
  - Config resolution (`BOT_CONFIG` -> `../storage/bot.yaml` -> `bot.example.yaml`) and `.env` settings (`EnvSettings`, including `LOG_LEVEL` startup config & masked API key diagnostics).
  - Set 1 retrieval (`paibinder.retrieval.docs`): `ripgrep` (`rg`) search with `grep` fallback and path-confined `read_doc_slice`.
  - Set 3 retrieval (`paibinder.retrieval.store`): SQLite `blocks` + `blocks_fts` (`FTS5` BM25) with SHA-256 `content_hash` deduplication and `paibinder-seed` CLI (`paibinder.cli.seed`).
  - Set 2 placeholder (`paibinder.retrieval.glossary`) reserved for post-`v0.1.0` knowledge graph & vector lookup.
  - Stateless context compiler (`paibinder.context.compiler`) and PydanticAI agent/model factory (`paibinder.models.provider`) supporting cloud and OpenAI-compatible/local `base_url` endpoints.
  - FastAPI HTTP/SSE API (`paibinder.main`): `GET /health`, `POST /api/chat` (`text_delta`, `tool_call`, `tool_result`, `sources`, `error`, `done`), and static UI serving from `UI_DIST_DIR` / `ui/build` / `ui/dist`.
  - Offline unit and API test suite (`paibinder/tests/`, 15 tests using `TestModel`).
- **Frontend (`ui`):**
  - Vite + Svelte 5 + Tailwind CSS v4 + `shadcn-svelte` chat interface (`App.svelte`, `ChatContainer`, `MessageBubble`, `PromptInput`, `ToolActivity`, `SourcesList`).
  - `ReadableStream` SSE client (`src/lib/api/client.ts`) and Svelte 5 rune store (`src/lib/state/chat.svelte.ts`) with `localStorage` thread persistence.
  - Global theming (`src/themes/*.css`, `src/lib/state/theme.svelte.ts`, `ThemeSwitcher.svelte`) supporting colors, typography, radii, and surface shadows with `system`, `light`, `dark`, `paper`, `terminal`, and `ocean` presets plus `VITE_DEFAULT_THEME`.
  - Vite dev proxy for `/api/*` and `/health`, and static production build to `ui/dist/`.
- **Documentation & Licensing:**
  - `README.md`, `docs/README.md`, `docs/INSTALL.md` (custom bot layouts & upgrade workflows), `paibinder/README.md`, `ui/README.md`, and `LICENSE` (GPL-3.0).
