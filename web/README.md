# Mente do Brasil Web

Frontend V1 vertical slice for the local Mente do Brasil explorer.

## Stack

- Next.js App Router
- React
- TypeScript
- MapLibre GL JS
- Vitest
- Playwright

## Environment

Copy `.env.example` to `.env.local` only for local overrides. Do not commit
`.env.local`.

```bash
NEXT_PUBLIC_MDB_API_BASE_URL=http://127.0.0.1:8000
```

## Local Run

Terminal 1:

```bash
docker compose up -d
```

Terminal 2:

```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Terminal 3:

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:3000`.

## Implemented Routes

- `/`: Explorer with national overview map, metric selector, territorial
  search, selected-region panel, and accessible region list.
- `/regiao/[codigo]`: Health Region profile using the API semantic profile
  endpoint.

## Future Routes

- `/estado/[uf]`
- `/metodologia`
- `/dados`
- `/sobre`

These are navigation placeholders only in this vertical slice.

## Tests

```bash
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:e2e
```

The E2E suite expects Docker/PostgreSQL and the local FastAPI API to be running.

## Architecture

API access is centralized in `lib/api`. Formatting is centralized in
`lib/format.ts`. Map color rules are in `lib/map/color-scale.ts` and are visual
only; the frontend does not recalculate scientific metrics, percentiles,
Moran/LISA, flags, rates, Need, Capacity, or Mismatch.
