"""Materialize accepted municipal contributions and regional flow summaries."""

import json

import pandas as pd

from scripts.build_advanced_temporal import AUDIT, CACHE, CURRENT, OUT, ROOT

VERSION = "MDB_HOSPITAL_FLOW_METHOD_1.0"


def safe_share(numerator, denominator):
    if denominator < 5 or 0 < numerator < 5 or 0 < denominator - numerator < 5:
        return None
    return numerator / denominator


def main():
    raw = pd.read_parquet(CACHE / "annual_municipal_admissions.parquet")
    raw = raw.loc[raw.year.between(2022, 2024)]
    edges = raw.groupby(["municipality", "destination"], as_index=False).admissions.sum()
    cross = pd.read_parquet(
        ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
    )
    mapping = dict(zip(cross.municipality_code_datasus6, cross.health_region_code, strict=True))
    edges["origin_region"] = edges.municipality.map(mapping)
    edges["destination_region"] = edges.destination.map(mapping)
    if edges[["origin_region", "destination_region"]].isna().any().any():
        raise ValueError("Unmapped flow municipality")
    canonical = pd.read_parquet(
        ROOT / f"data/canonical/{CURRENT}/health_regions.parquet"
    ).set_index("health_region_code")
    origins = edges.groupby("origin_region").admissions.sum().reindex(canonical.index, fill_value=0)
    if not origins.eq(canonical.psychiatric_admissions).all():
        raise ValueError("Flow origin reconciliation failed")
    if (
        len(edges) != 20907
        or edges.admissions.sum() != 695320
        or edges.admissions.lt(5).sum() != 11987
    ):
        raise ValueError("Accepted flow contribution counts changed")
    summary = []
    regional = edges.groupby(
        ["origin_region", "destination_region"], as_index=False
    ).admissions.sum()
    for code in canonical.index:
        outgoing = regional.loc[regional.origin_region.eq(code)]
        total = int(outgoing.admissions.sum())
        within = int(outgoing.loc[outgoing.destination_region.eq(code)].admissions.sum())
        across = int(
            outgoing.loc[outgoing.destination_region.str[:2].ne(code[:2])].admissions.sum()
        )
        summary.append(
            {
                "flow_version": VERSION,
                "health_region_code": code,
                "total_admissions": total if total >= 5 else None,
                "within_region_share": safe_share(within, total),
                "outflow_share": safe_share(total - within, total),
                "cross_state_outflow_share": safe_share(across, total),
                "nonsuppressed_destinations": int(outgoing.admissions.ge(5).sum()),
                "unit": "AIHs/admissions; not unique patients",
            }
        )
    # Contribution-grain suppression preserves the accepted artifact exactly.
    public = edges[["origin_region", "destination_region", "admissions"]].copy()
    public["suppressed"] = public.admissions.lt(5)
    public.loc[public.suppressed, "admissions"] = pd.NA
    reference = pd.read_csv(
        ROOT / "audit_results/scientific_correction/pooled_flow_edges_suppressed.csv",
        dtype={"origin_region": str, "destination_region": str},
    )
    pd.testing.assert_frame_equal(public[reference.columns], reference, check_dtype=False)
    public["flow_version"] = VERSION
    public["contribution_id"] = range(len(public))
    public.to_parquet(OUT / "hospitalization_flows.parquet", index=False)
    pd.DataFrame(summary).to_parquet(OUT / "health_region_flow_summary.parquet", index=False)
    result = {
        "status": "PASS",
        "contribution_rows": len(public),
        "regional_pairs": len(regional),
        "summaries": len(summary),
        "suppressed_contributions": int(public.suppressed.sum()),
        "eligible_admissions": int(origins.sum()),
        "max_origin_delta": 0,
        "public_flow_policy": "Only sum disclosed contributions; flag regional pairs with suppressed contributions as partial. Never treat partial sums as complete counts.",
    }
    (AUDIT / "flow_materialization.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
