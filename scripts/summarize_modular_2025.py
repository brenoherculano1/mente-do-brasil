"""Aggregate private QC caches into disclosure-safe audit evidence, not a release."""

import json

import pandas as pd

from api.services.availability import availability_2025
from scripts.acquire_modular_2025 import AUDIT, CACHE, plan
from scripts.acquire_phase3_sources import sha256, write_json


def main():
    metadata = AUDIT.parents[1] / "metadata/annual_updates/2025"
    write_json(
        metadata / "availability.json",
        {
            "reference_year": 2025,
            "public_release_status": "NOT_RELEASED",
            "observed_release_created": False,
            "geography_validated": False,
            "indicators": [item.model_dump() for item in availability_2025()],
        },
    )
    expected = plan()
    receipts = [
        json.loads((AUDIT / (i["original_filename"] + ".qc.json")).read_text()) for i in expected
    ]
    for receipt in receipts:
        if sha256(CACHE / (receipt["file"] + ".parquet")) != receipt["output_sha256"]:
            raise ValueError("QC cache hash mismatch")
    families = {}
    for family in ["ST", "LT", "PF", "SIH", "population"]:
        group = [r for r in receipts if r["family"] == family]
        families[family] = {
            "files_decoded": len(group),
            "rows_decoded": sum(r["decoded_rows"] for r in group),
            "status": "UNDER_VALIDATION",
            "regional_publication_allowed": False,
        }
    pf = pd.concat(
        [
            pd.read_parquet(CACHE / (r["file"] + ".parquet")).assign(uf=r["uf"])
            for r in receipts
            if r["family"] == "PF"
        ],
        ignore_index=True,
    )
    hours = pf.groupby("person").hours.sum()
    families["PF"].update(
        professionals=int(pf.person.nunique()),
        cross_uf_professionals=int(pf.groupby("person").uf.nunique().gt(1).sum()),
        multi_establishment_professionals=int(pf.groupby("person").CNES.nunique().gt(1).sum()),
        individual_hours_over_168=int(hours.gt(168).sum()),
        total_registered_weekly_hours=float(hours.sum()),
        exact_duplicate_links_removed=sum(
            r["exact_link_duplicates"] for r in receipts if r["family"] == "PF"
        ),
        locked_key_collision_files=[
            r["file"]
            for r in receipts
            if r["family"] == "PF" and r["key_collision_requires_review"]
        ],
        cross_file_duplicate_cache_rows=int(pf.drop(columns="uf").duplicated().sum()),
        hours_quantiles={
            str(k): float(v) for k, v in hours.quantile([0, 0.5, 0.95, 0.99, 1]).items()
        },
        cap_applied=False,
        unresolved=(
            "Individual plausibility and SUS-exclusive allocation need review; "
            "no rate or FTE published."
        ),
    )
    population = pd.read_parquet(CACHE / "POPSBR25.zip.parquet")
    families["population"].update(
        municipalities=int(population.municipality.nunique()),
        total_population=int(population.population.sum()),
        nonpositive_municipality_totals=int(
            population.groupby("municipality").population.sum().le(0).sum()
        ),
    )
    valid_codes = set(population.municipality)
    for family in ["ST", "LT", "SIH"]:
        data = pd.concat(
            [
                pd.read_parquet(CACHE / (r["file"] + ".parquet"))
                for r in receipts
                if r["family"] == family
            ]
        )
        unmatched = data.loc[~data.municipality.isin(valid_codes)]
        families[family]["municipality_codes_without_population"] = sorted(
            unmatched.municipality.unique().tolist()
        )
        if family == "SIH":
            families[family].update(
                admissions=int(data.admissions.sum()),
                admissions_without_residence_denominator=int(unmatched.admissions.sum()),
                duplicate_aih_within_files=sum(
                    r["duplicate_aih"] for r in receipts if r["family"] == family
                ),
                counting_unit="SIH processing records; not unique people",
                pooled_2023_2025="NOT_BUILT_PENDING_DENOMINATOR_AND_GEOGRAPHY",
            )
        if family == "ST":
            families[family]["cross_file_duplicate_cnes"] = int(data.CNES.duplicated().sum())
        if family == "LT":
            families[family]["duplicate_rows_within_files"] = sum(
                r["duplicate_selected_rows"] for r in receipts if r["family"] == family
            )
    write_json(
        AUDIT / "national_source_qc.json",
        {
            "files_decoded": len(receipts),
            "families": families,
            "regional_metrics_created": False,
            "geography_2025": "UNDER_VALIDATION",
            "source_rights": "PUBLIC_ACCESS_VERIFIED; VERSION_SPECIFIC_REUSE_REVIEW_PENDING",
            "status": "PARTIAL_QC_NOT_PUBLIC_READY",
        },
    )
    print(json.dumps(families, indent=2))


if __name__ == "__main__":
    main()
