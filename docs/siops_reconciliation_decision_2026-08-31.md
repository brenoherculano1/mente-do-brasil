# SIOPS Reconciliation Decision

The raw municipal SIOPS CSV is an audit source, not a headline aggregation
table. Its Natureza codes are hierarchical, so summing parents and children
would double count. The official SIOPS calculated/report layer provides a more
reproducible resolution.

The official metadata identifies Indicator 2.1, “Despesa total com Saúde, sob a
responsabilidade do Município, por habitante”, with annual period `2` (sixth
bimestre / annual). The official methodology identifies `empenhada` as the
annual stage. The official expenditure report identifies `grupo=17` as `Total`.

The live API base and `v2/api-docs` were attempted on 2026-08-31 and reset the
connection before returning JSON. The official legacy report interface was
reachable and returned Indicator 2.1 and the group 17 Total for sample
municipalities, including 316620 and 250760. Their previously extreme raw
parent rows did not propagate to the official report output in the sample:

- 316620: raw 2024 liquidated parent value was R$ 382,587,171,024,568.00;
  official report total was R$ 120,518,766.48.
- 250760: raw 2024 paid parent value was R$ 4,719,547,615,230.72; official
  report total was R$ 3,557,245.93.

No raw value was edited, capped, deleted, or imputed. The official report-layer
acquisition attempt is complete: 16,710 municipality-years requested, 16,703
successful, seven explicitly missing. SIOPS remains PASS_WITH_LIMITATIONS.
The accepted Indicator 2.1 sample reconciliation is complete. This is not
100% national reporting coverage.

The seven missing keys are 220045/2022, 260545/2022, 260545/2023,
260545/2024, 530010/2022, 530010/2023 and 530010/2024. The regional
output has 1,317 rows, including seven partial rows with NULL headlines.

During final integration regression, an implementation defect was found in
the regional denominator join: seven-digit POPSVS municipality codes were
mapped to six-digit keys. The previous output had no populated denominators
or per-capita values. The corrected builder uses exact seven-digit IBGE keys,
rejects unmapped records, and measures covered population from reporting
municipalities. The accepted SIOPS snapshot, stage, totals and missing-record
set remain unchanged. The output hash changes for this documented bug fix;
the previous artifact remains available in commit 87cb7e5.

The previous intermediate audit ZIP also omitted AUDIT_CONTEXT.json from its
manifest. It is preserved unchanged; any replacement audit package must list
every file other than the manifest itself, including AUDIT_CONTEXT.json.
