"""Generate web route inventory from locked canonical artifacts."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_HEALTH_REGIONS = ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet"
OUTPUT = ROOT / "web/lib/public-route-inventory.ts"


def main() -> int:
    table = pq.read_table(CANONICAL_HEALTH_REGIONS, columns=["health_region_code", "uf"])
    frame = table.to_pandas()
    if len(frame) != 439 or frame["health_region_code"].nunique() != 439:
        raise RuntimeError("Canonical health-region route source must contain 439 unique regions.")
    states = sorted(frame["uf"].unique().tolist())
    if len(states) != 27:
        raise RuntimeError("Canonical health-region route source must contain 27 UFs.")
    regions = sorted(frame["health_region_code"].astype(str).tolist())
    content = "\n".join(
        [
            "// Generated from data/canonical/MDB_ANALYTICAL_2024_1/health_regions.parquet.",
            "// Do not edit manually; run scripts/generate_public_route_inventory.py.",
            "",
            f"export const PUBLIC_ROUTE_UFS = {states!r} as const;",
            "",
            f"export const PUBLIC_ROUTE_HEALTH_REGION_CODES = {regions!r} as const;",
            "",
        ]
    )
    OUTPUT.write_text(content.replace("'", '"'), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
