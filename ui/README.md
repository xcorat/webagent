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
