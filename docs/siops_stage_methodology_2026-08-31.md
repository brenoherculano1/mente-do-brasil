# SIOPS Stage Methodology

The annual SIOPS period is `2`, defined by the official metadata as the sixth
bimestre / annual period. For Indicator 2.1, the Ministry documentation states
that the annual calculation uses the empenhada expenditure stage (with liquidada
in the first five bimesters). The headline annual stage is therefore
`empenhada`.

The raw municipal Natureza file contains hierarchical parent and child rows and
must not be summed indiscriminately. The official report layer is used instead:
Indicator 2.1 for the per-capita result and the `grupo=17` `Total` row from the
official municipal expenditure report for the total amount. Raw CSV releases are
retained as tertiary audit provenance and are not modified.

Official sources:

- [SIOPS API metadata](https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SIOPS/MetaDados.pdf)
- [Ministry SIOPS technical notes](https://www.gov.br/saude/pt-br/acesso-a-informacao/siops/indicadores/notas-tecnicas)
- [SIOPS/FNS downloads](https://portalfns.saude.gov.br/siops/siops-downloads/)
