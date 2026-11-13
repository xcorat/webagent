# WebAgent Repository Instructions

`webagent` is a modular, cloneable agentic AI knowledge retriever and disseminator designed to be duplicated across many specialized bot instances.

## Repository Structure

- `paibinder/` — **Python AI Binder**: backend context engineering engine, retrieval layer, model provider abstraction, and HTTP/SSE API.
- `ui/` — **Svelte Frontend**: clean, lightweight chat UI.
- `docs/` — **Project Documentation**: public architecture, setup, and usage docs (do not place internal dev-only planning notes here).

## Core Architecture & Design Rules

1. **Modular Context Engineering (`paibinder/`):**
   - Assemble prompts via composable context stages/providers (persona/grounding rules, retrieved knowledge, conversation history) rather than one hardcoded monolithic prompt.
   - Keep `ModelProvider` abstracted behind configuration so cloud APIs and local models (Ollama, vLLM, llama.cpp) can be swapped cleanly.
2. **Storage & Retrieval Model (Optimized for Short General Data):**
   - **Set 1 (`docs/`):** Long-form markdown files retrieved via `ripgrep` (`rg`) + targeted slice reading.
   - **Set 2 (`store.db`):** Lightweight Knowledge Graph / semantic glossary (terms, aliases, definitions, typed edges) in SQLite + vector lookup.
   - **Set 3 (`store.db`):** High-volume short-form dynamic text blocks using SQLite hybrid search (`FTS5` BM25 + `sqlite-vec` + RRF).
   - Storage location must be configurable (e.g., via env/config) so each cloned bot points to its own instance storage without modifying engine code.
3. **Cloneability:**
   - Keep engine code strictly separate from instance-specific prompts, knowledge data, and runtime `.db` artifacts.

## Current Scope Guardrails (`v0.1.0`)

- Focus strictly on a **minimal, working chatbot** over the storage layer.
- **Do not add yet:** slash `/commands`, MCP / FastMCP integrations, frontend UI plugins (plotting/testing overlays), or multi-agent pipelines—these are reserved for post-`v0.1.0` milestones.
