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
MDB_API_INTERNAL_BASE_URL=http://127.0.0.1:8000
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
- `/dados`: Static release transparency page with dataset inventory, versions,
  provenance, data dictionary, and publication policy.
- `/metodologia`: Static, readable explanation of the locked method, sources,
  denominators, percentiles, spatial analysis, flags, limitations, and versions.
- `/regiao/[codigo]`: Health Region profile using the API semantic profile
  endpoint.

## Future Routes

- `/estado/[uf]`
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

The E2E suite runs against `npm run start`, so run `npm run build` first. It
also expects Docker/PostgreSQL and the local FastAPI API to be running.

## Architecture

Browser API access is centralized in `lib/api/client.ts` and uses same-origin
`/api/v1/...` paths. Server-rendered pages use `lib/api/server.ts` with the
server-only `MDB_API_INTERNAL_BASE_URL`. Formatting is centralized in
`lib/format.ts`. Map color rules are in `lib/map/color-scale.ts` and are visual
only; the frontend does not recalculate scientific metrics, percentiles,
Moran/LISA, flags, rates, Need, Capacity, or Mismatch.
