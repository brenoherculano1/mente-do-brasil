"""Locked identifiers and structural constants for the initial release."""

GEOGRAPHY_VERSION = "BR_HEALTH_REGIONS_END2024_V1"
METHOD_VERSION = "MDB_METHOD_1.0"
RELEASE_ID = "MDB_ANALYTICAL_2024_1"

EXPECTED_MUNICIPALITY_COUNT = 5570
EXPECTED_HEALTH_REGION_COUNT = 439

VALID_UFS = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}

LOCKED_SPATIAL_RESULTS = {
    "global_moran_i": 0.525494388844,
    "pseudo_p": 0.0001,
    "permutations": 9999,
    "seed": 20260823,
    "weights": "queen_contiguity",
    "row_standardized": True,
    "islands": 0,
    "lisa_fdr_significant": 135,
    "hh": 60,
    "ll": 66,
    "hl": 4,
    "lh": 5,
}

INVALID_SPATIAL_VALUES = {
    "old_global_moran_i": 0.218740812099,
}
