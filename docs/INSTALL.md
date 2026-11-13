# Installing & Using WebAgent

## 1. Local Engine Setup

```bash
cd webagent/paibinder
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Optional environment configuration (`.env`):

```env
BOT_CONFIG=../storage/bot.yaml
OPENAI_API_KEY=...
```

---

## 2. Custom Project Layout

Keep your bot's data and configuration completely separate from the `webagent` engine so upgrades never touch your content:

```text
my-custom-bot/
├── bot.yaml            # persona, model, storage paths (./docs, ./store/store.db)
├── .env                # API keys + BOT_CONFIG=./bot.yaml
├── docs/               # Set 1: long-form markdown files
└── store/
    └── store.db        # Set 3: SQLite FTS5 knowledge blocks
```

Seed blocks and run the server pointing at your instance config:

```bash
BOT_CONFIG=./bot.yaml paibinder-seed --source ./blocks.jsonl
BOT_CONFIG=./bot.yaml uvicorn paibinder.main:app --port 8000
```

---

## 3. Consuming & Updating `webagent`

Choose the workflow that matches whether you customize engine code:

### Option A — Versioned Dependency *(Recommended when using the engine as-is)*

Pin `paibinder` to a git tag in your project's `pyproject.toml` (or `requirements.txt`):

```toml
dependencies = [
    "paibinder @ git+https://github.com/<org>/webagent.git@v0.1.0#subdirectory=paibinder",
]
```

**Update:** Bump the tag (`v0.1.0` → `v0.2.0`) and run `pip install --upgrade` (or `uv sync --upgrade`).

### Option B — Upstream Remote / Fork *(When customizing UI or adding routes/tools)*

Clone `webagent` into your project repository and track the original repo as `upstream`:

```bash
git remote add upstream https://github.com/<org>/webagent.git
```

Keep custom tools or routes in separate modules and keep `bot.yaml` / `storage/` outside git (or in `.gitignore`).

**Update:**

```bash
git fetch upstream
git merge upstream/v0.2.0   # or: git rebase upstream/main
```

### Option C — Git Submodule *(Single monorepo with pinned engine)*

Embed `webagent/` inside your project repo alongside `bot.yaml` and `storage/`:

```bash
git submodule add https://github.com/<org>/webagent.git webagent
```

**Update:**

```bash
git -C webagent fetch --tags
git -C webagent checkout v0.2.0
git add webagent
```
