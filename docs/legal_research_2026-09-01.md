# Licensing and Attribution Review

Checked on 2026-09-01. This is a conservative operational review, not a formal legal opinion.

The Ministry of Health open-data page describes federal open data as machine-readable information made available under open licensing for reuse with source credit. The current SUS portal and official transparency pages identify SIM, SIH and CNES data as publicly accessible. These general statements do not establish one blanket dataset-specific Creative Commons license for every legacy DATASUS file. Therefore, no raw SIM, SIH, CNES or POPSVS file is redistributed.

The SIOPS catalog was verified at `https://dados.gov.br/dados/conjuntos-dados/siops`. Its dataset-specific license field was not populated in the accessible catalog state. SIOPS is therefore `LOW` confidence for raw redistribution, which is set to `NO`; only locked regional aggregates are distributed with explicit attribution and caveats.

The IBGE publication *Malha Municipal Digital e Áreas Territoriais 2023: Informações Técnicas e Legais* documents a license compatible with CC BY 4.0 for that identified product. The Mente do Brasil locked provenance does not identify the exact municipal mesh version sufficiently to connect that legal statement to the bytes used. Geometry downloads and the public geometry API are therefore excluded from this release.

WHO data.who.int terms generally use CC BY 4.0 with additional mandatory terms, attribution, no endorsement, and restrictions on the WHO name and emblem. Mente do Brasil distributes only the methodological reference and derived ASMR, not a WHO publication, logo, or numeric source table.

Official evidence:

- Ministério da Saúde: `https://www.gov.br/saude/pt-br/acesso-a-informacao/dados-abertos/dados-abertos`
- Portal de Dados Abertos do SUS: `https://dadosabertos.saude.gov.br/`
- SIOPS catalog: `https://dados.gov.br/dados/conjuntos-dados/siops`
- IBGE technical/legal publication: `https://www.ibge.gov.br/biblioteca/visualizacao/livros/liv102152.pdf`
- WHO dataset terms: `https://data.who.int/about/data/terms-and-conditions`
