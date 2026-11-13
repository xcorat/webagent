# WebAgent UI (`webagent/ui`)

Vite + Svelte 5 + Tailwind CSS v4 + `shadcn-svelte` chat frontend for `paibinder`.

## Development

```bash
pnpm install
pnpm dev
```

`vite.config.ts` proxies `/api/*` and `/health` to `http://127.0.0.1:8000` (where `paibinder` runs).

## Production Build

```bash
pnpm build
```

Outputs static assets to `dist/`, which `paibinder` automatically serves at `/` when present.

## Type Checking

```bash
pnpm check
```

## Theming

Global themes control colors, fonts (`--font-sans`, `--font-mono`), corner radii (`--radius-*`), and surface shadows (`--shadow-xs`).

- **Built-in presets:** `system`, `light`, `dark`, `paper`, `terminal`, `ocean` (switchable from the header `ThemeSwitcher` and persisted in `localStorage` under `webagent:theme`).
- **Instance default:** Set `VITE_DEFAULT_THEME=<id>` at build time to choose the fallback theme for a bot instance when no user preference is saved.
- **Adding a theme:**
  1. Create `src/themes/<id>.css` scoping `[data-theme="<id>"] { ... }` with your token overrides.
  2. `@import "./themes/<id>.css";` in `src/app.css`.
  3. Register its metadata (`id`, `label`, `description`, `swatches`) in `THEMES` inside `src/lib/state/theme.svelte.ts`.
