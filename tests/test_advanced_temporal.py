import struct

import pandas as pd

from scripts.build_advanced_temporal import COMPONENTS, changes, score, source_rows
from scripts.validate_phase3_source_gate import selected_dbf


def test_temporal_inventory_is_complete():
    rows = source_rows()
    assert len(rows) == 2003
    assert {r["year"] for r in rows} == {2020, 2021, 2022, 2023, 2024}


def test_component_percentiles_use_ties_and_full_anchor():
    data = pd.DataFrame({c: [1, 2, 2, 4] for c in COMPONENTS})
    result = score(data)
    assert result.need_score.tolist() == [0, 0.5, 0.5, 1]
    assert result.capacity_score.tolist() == [0, 0.5, 0.5, 1]
    assert result.mismatch_score.eq(0).all()


def test_change_rules_directions_and_pairs():
    rows = []
    for year, position in ((2022, 0.25), (2023, 0.5), (2024, 0.75)):
        for code in ("11001", "11002"):
            sign = 1 if code == "11001" else -1
            row = {"year": year, "health_region_code": code}
            row.update({c: 0.5 + sign * (position - 0.5) for c in COMPONENTS.values()})
            row.update(
                {
                    "need_score": sign * position,
                    "capacity_score": -sign * position,
                    "mismatch_score": sign * position * 2,
                }
            )
            rows.append(row)
    result = changes(pd.DataFrame(rows))
    assert len(result) == 6
    assert set(zip(result.from_year, result.to_year, strict=False)) == {
        (2022, 2023),
        (2023, 2024),
        (2022, 2024),
    }
    up = result.loc[result.health_region_code.eq("11001")]
    assert up.NEED_POSITION_UP.all()
    assert up.CAPACITY_POSITION_DOWN.all()
    assert up.MISMATCH_POSITION_UP.all()
    assert up.NEED_COMPONENT_POSITION_UP.all()
    assert not up.CAPACITY_COMPONENT_POSITION_DOWN.any()
    assert up.matched_change_families.eq(4).all()
    down = result.loc[result.health_region_code.eq("11002")]
    assert down.matched_change_families.eq(1).all()
    assert down.CAPACITY_COMPONENT_POSITION_DOWN.all()
    pd.testing.assert_frame_equal(result, changes(pd.DataFrame(rows)))


def test_dbf_decoder_matches_declared_latin1(tmp_path):
    header = bytearray(32)
    header[0] = 3
    struct.pack_into("<IHH", header, 4, 1, 65, 9)
    field = bytearray(32)
    field[:4] = b"NAME"
    field[11] = ord("C")
    field[16] = 8
    target = tmp_path / "accent.dbf"
    target.write_bytes(bytes(header) + bytes(field) + b"\r" + b" Jos\xe9    " + b"\x1a")
    assert selected_dbf(target, ["NAME"]).NAME.tolist() == ["Jos\u00e9"]
