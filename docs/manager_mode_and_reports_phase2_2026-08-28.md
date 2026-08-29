# Manager Workbench and Territorial Reports - Phase 2

Status: implemented and validated locally.

This phase adds a descriptive manager layer over the locked `MDB_ANALYTICAL_2024_1`
release. It does not add scientific variables, recompute canonical indicators,
change geographies, change the territorial intelligence model, or create a public
release.

## Scope

- Manager route: `/gestor`
- Manager API: `/api/v1/manager/health-regions/{health_region_code}`
- Compare API: `/api/v1/manager/compare?codes=12001,31001`
- Territorial report PDF: `/api/v1/health-regions/{health_region_code}/report.pdf`
- Metadata:
  - `MDB_MANAGER_MODE_1.0`
  - `MDB_TERRITORIAL_REPORT_1.0`
  - `MDB_INVESTIGATION_GUIDE_1.0`
  - `MDB_MANAGER_BRIEF_1.0`

## ManagerBrief Contract

`ManagerBrief` is a compact, deterministic narrative payload assembled from
existing serving and analytics tables. It includes region identity, locked
release metadata, existing Need/Capacity/Mismatch values, existing Radar signals,
existing Mismatch decomposition, existing peer benchmark summaries, spatial
context, quality cautions, and deterministic investigation questions.

The API computes `report_content_sha256` from canonical JSON with sorted keys and
without timestamps or request identifiers. The hash is used by the PDF response
ETag and cache key.

## Investigation Guide

The investigation guide is descriptive. It generates questions from existing
signals and never creates recommendations, causal claims, rankings, or resource
allocation instructions.

The guide contains 14 deterministic rules. Each brief returns 3 to 8 questions.
All 439 health regions were validated for duplicate questions and forbidden claim
language.

## Compare Mode

Compare mode accepts 2 to 4 health regions. It preserves user-selected order and
does not rank, score, or select a winner. It displays the same backend-provided
metrics available in the ManagerBrief contract.

## Territorial PDF

The PDF is generated server-side using ReportLab. It is A4, 5 pages, selectable
text, no external runtime, no JavaScript, and no frontend screenshot capture.

The PDF includes:

1. Cover and territorial summary
2. Attention signals and mismatch decomposition
3. Need and Capacity indicators
4. Peer benchmark and spatial context
5. Investigation questions, limitations, sources, and citation

The response uses:

- `Content-Type: application/pdf`
- `Content-Disposition: attachment`
- `Cache-Control: public, max-age=60, s-maxage=900, stale-while-revalidate=3600`
- `ETag` derived from content hash and generator version
- `X-Robots-Tag: noindex`

## Public Release Boundary

No PDF URLs are included in sitemap generation. `/gestor` is included as a public
application route, but individual report URLs are not indexed.

The public release status remains `NOT_RELEASED`.

## Validation Artifacts

Primary audit outputs are stored in `audit_results/`.

Visual and PDF QC outputs are stored in:

`docs/manager_mode_qc_2026-08-28/`

The validation package for external review is generated under `audit_packages/`
after commit.
