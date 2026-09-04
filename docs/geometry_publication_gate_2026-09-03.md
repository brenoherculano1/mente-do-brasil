# Geometry publication gate

Status: `PASS_EXACT_SOURCE_PROVENANCE` for derived browser display only.

The locked Health Region geometry was generated from the official IBGE 2023 municipal
digital mesh (`BR_Municipios_2023.zip`), filtered to the 5,570 municipalities in the
locked population universe and dissolved with the locked end-2024 Health Region
crosswalk. The resulting locked GeoPackage was not changed.

The frozen ZIP and the file currently served at the official IBGE URL have different
container SHA-256 values. A member-level comparison found all seven archived files to
be byte-identical, including the shapefile components and the technical/legal PDF. The
container difference is therefore not a source-data difference.

The accompanying official IBGE document states licensing compatible with CC BY 4.0,
including redistribution, adaptation, and commercial use with attribution. The public
map must credit: "Fonte da geometria municipal - IBGE, Malha Municipal Digital 2023;
adaptação e agregação por Mente do Brasil."

This gate permits public display of `MDB_WEB_GEOMETRY_V1`. It does not authorize adding
geometry to the immutable `MDB_OPEN_DATA_2024_1` ZIP or to the public Open Data API.
Detailed hashes, URLs, and comparison evidence are recorded in
`metadata/legal/ibge_geometry_publication_gate_v1.yaml`.
