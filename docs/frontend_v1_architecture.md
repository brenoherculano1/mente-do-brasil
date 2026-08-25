# Frontend V1 Architecture

Status: `FRONTEND_FOUNDATION_V1` is a local vertical slice, not the complete
public website.

## Information Architecture

Implemented:

- `/`: Explorar o Brasil.
- `/dados`: Dados e versões.
- `/regiao/[codigo]`: Perfil da Região de Saúde.
- `/metodologia`: Como medimos.

Reserved for later UX review:

- `/estado/[uf]`
- `/dados`
- `/sobre`

## User Journey

The primary journey is:

1. Buscar território.
2. Entender o sinal.
3. Ver o que compõe o resultado.
4. Contextualizar.
5. Return to the map for further exploration.

## Design Principles

The interface is a public territorial data product, not a landing page,
commercial funnel, generic dashboard, or ranking. The map is the primary surface.
Visual language is restrained, legible, and contemporary, with centralized design
tokens in `app/globals.css`.

## Map Behavior

The national map uses MapLibre GL JS with no paid basemap or token. The frontend
requests only:

```text
GET /api/v1/map/health-regions?metric={metric}&include_geometry=true&geometry_profile=overview
```

The `full` geometry profile is intentionally not used in normal frontend
rendering. Map interaction includes hover tooltip, click selection, persistent
selection outline, pan, zoom controls, and a linked selected-region summary.

## Indicator Behavior

Allowed map indicators are restricted to the API contract:

- `mismatch_score`
- `need_score`
- `capacity_score`
- `suicide_asmr`
- `psychiatric_admission_rate`
- `caps_rate`
- `mental_health_beds_sus_rate`
- `psychiatrist_fte_rate`

Color domains are computed only for visual rendering from values returned by the
API. The frontend does not persist or present those domains as scientific
classification.

## Claim Discipline

The frontend does not recalculate percentiles, Need, Capacity, Mismatch, rates,
Moran, LISA, or flags. It does not label Mismatch as deficit, access, quality, or
unmet need. Null values are not converted to zero.

## Search

The search field supports Health Region name/code through
`GET /api/v1/health-regions?q=`. For municipalities, this slice supports direct
7-digit IBGE code lookup through
`GET /api/v1/municipalities/{municipality_code_ibge}/health-region`.

Free-text municipality search is intentionally not implemented because the API
does not expose that endpoint in V1.

## Region Profile

The profile page uses:

```text
GET /api/v1/health-regions/{health_region_code}
```

It presents the semantic API response without decomposing or changing the
scientific model:

- territory;
- Need components and score;
- Capacity components and score;
- Mismatch;
- spatial context for Mismatch;
- data quality observations when flags exist.

## Responsive Strategy

Desktop uses a two-column explorer with controls and supporting context on the
left and a large national map on the right. Mobile stacks header, intro, search,
metric selector, map, selected-region summary, legend/explanations, and the
accessible list in that order, so the map remains the primary surface.

## Accessibility

The app uses semantic landmarks, labels, visible focus, button/link semantics,
and a collapsed accessible region list so the map is not the only navigation
path. The complete 439-region list is available on demand and can be filtered by
name, UF, or Health Region code without pushing the map below the fold by
default. Tooltips are built with DOM nodes and `textContent`, not injected HTML;
duplicate information is available through search and profile pages.

## API Dependency

The API base URL is centralized in `lib/api/config.ts` and configured by:

```text
NEXT_PUBLIC_MDB_API_BASE_URL
```

Default local value:

```text
http://127.0.0.1:8000
```

## Intentionally Not Implemented

This slice does not include login, deployment, analytics, rankings, chatbot, CMS,
download center, comparison tools, peer regions, trend charts, full state pages,
about pages, or any scientific recalculation.
