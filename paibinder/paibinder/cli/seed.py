"""CLI seed command to ingest JSONL or Markdown snippets into Set 3 store.db."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paibinder.config import load_config
from paibinder.retrieval.store import BlockInput, connect_db, upsert_blocks


def load_blocks_from_jsonl(path: Path) -> list[BlockInput]:
    """Parse newline-delimited JSON records into BlockInput objects."""
    blocks: list[BlockInput] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        data = json.loads(stripped)
        if "id" not in data:
            data["id"] = f"{path.stem}:{line_no}"
        if "title" not in data:
            data["title"] = data["id"]
        if "source" not in data:
            data["source"] = path.name
        blocks.append(BlockInput.model_validate(data))
    return blocks


def load_block_from_markdown(path: Path) -> BlockInput:
    """Load a single markdown snippet file as one BlockInput."""
    text = path.read_text(encoding="utf-8").strip()
    first_heading = next(
        (ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("#")),
        path.stem,
    )
    return BlockInput(
        id=path.stem,
        title=first_heading,
        content=text,
        tags=[],
        source=path.name,
    )


def collect_blocks(source: Path) -> list[BlockInput]:
    """Collect blocks from a .jsonl file, .md file, or directory of both."""
    if source.is_file():
        if source.suffix == ".jsonl":
            return load_blocks_from_jsonl(source)
        if source.suffix == ".md":
            return [load_block_from_markdown(source)]
        raise ValueError(f"Unsupported seed file type: {source}")

    if source.is_dir():
        blocks: list[BlockInput] = []
        for item in sorted(source.rglob("*")):
            if item.is_file() and item.suffix == ".jsonl":
                blocks.extend(load_blocks_from_jsonl(item))
            elif item.is_file() and item.suffix == ".md":
                blocks.append(load_block_from_markdown(item))
        return blocks

    raise FileNotFoundError(f"Seed source not found: {source}")


def main(argv: list[str] | None = None) -> int:
    """Entrypoint for `paibinder-seed`."""
    parser = argparse.ArgumentParser(
        prog="paibinder-seed",
        description="Seed short-form knowledge blocks into store.db.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to a .jsonl file, .md file, or directory containing them.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Optional override for store.db path (defaults to configured storage.store_db).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to bot.yaml config file.",
    )
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    db_path = args.db.resolve() if args.db else cfg.store_db_path
    blocks = collect_blocks(args.source)

    conn = connect_db(db_path)
    try:
        stats = upsert_blocks(conn, blocks)
    finally:
        conn.close()

    print(
        f"Seeded {db_path}: inserted={stats.inserted}, "
        f"updated={stats.updated}, skipped={stats.skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
