import io
import json
import struct
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.acquire_phase3_sources import download, inspect_file, schema_header, sha256


def test_html_response_is_not_a_dbc(tmp_path):
    path = tmp_path / "RDAC2001.dbc"
    path.write_bytes(b"<html>upstream error, not a database</html>")
    with pytest.raises(ValueError, match="Invalid DBF"):
        inspect_file(path)


def test_truncated_dbf_schema_is_rejected():
    header = bytearray(32)
    header[0] = 3
    struct.pack_into("<IHH", header, 4, 1, 65, 7)
    with pytest.raises(ValueError, match="Truncated"):
        schema_header(io.BytesIO(header))


def test_schema_fingerprint_changes_when_field_width_changes():
    header = bytearray(32)
    header[0] = 3
    struct.pack_into("<IHH", header, 4, 1, 65, 7)
    field = bytearray(32)
    field[:6] = b"CODMUN"
    field[11] = ord("C")
    field[16] = 6
    first = schema_header(io.BytesIO(header + field + b"\r"))
    field[16] = 7
    second = schema_header(io.BytesIO(header + field + b"\r"))
    assert first["fingerprint"] != second["fingerprint"]


def test_valid_cache_reused_without_network(tmp_path, monkeypatch):
    import scripts.acquire_phase3_sources as module

    monkeypatch.setattr(module, "RAW", tmp_path)
    folder = tmp_path / "population"
    folder.mkdir()
    path = folder / "POPSBR20.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("example.csv", "year,population\n2020,10\n")
    receipt = {"sha256": sha256(path), "cache_reused": False}
    path.with_suffix(".zip.json").write_text(json.dumps(receipt))

    def no_network(*args, **kwargs):
        raise AssertionError("A hash-matching cache must not access network")

    monkeypatch.setattr(module.subprocess, "run", no_network)
    result = download({"dataset": "population", "original_filename": path.name})
    assert result["cache_reused"]
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="CACHE_HASH_MISMATCH"):
        download({"dataset": "population", "original_filename": path.name})


def test_sim_age_unknown_is_not_zero_and_centennial_is_preserved():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from validate_phase3_source_gate import parse_age

    assert parse_age("") is None
    assert parse_age("999") is None
    assert parse_age("480") == 80
    assert parse_age("485") == 85
    assert parse_age("502") == 102
    assert parse_age("205") == 0
