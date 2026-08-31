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

No raw value was edited, capped, deleted, or imputed. Full national acquisition
uses the official report layer with a resumable, bounded client. The financing
layer remains pending until the snapshot has complete coverage and the
Indicator 2.1 sample reconciliation is complete.
