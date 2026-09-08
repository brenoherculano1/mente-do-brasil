const EXACT_LABELS: Record<string, string> = {
  SMALL_SUICIDE_COUNT: "Poucos óbitos no período; interpretar a taxa com cautela.",
  ZERO_REGISTERED_BEDS: "Nenhum leito registrado na medida utilizada.",
};

export function publicLanguage(text: string) {
  if (EXACT_LABELS[text]) return EXACT_LABELS[text];
  return text
    .replaceAll("Need Score", "Índice de necessidade")
    .replaceAll("Capacity Score", "Índice de estrutura")
    .replaceAll("Mismatch", "diferença entre necessidade e capacidade")
    .replaceAll("Need", "necessidade")
    .replaceAll("Capacity", "estrutura")
    .replaceAll("Psiquiatras FTE", "Jornadas equivalentes de psiquiatras")
    .replaceAll("FTE", "jornadas equivalentes")
    .replaceAll("release", "conjunto de dados")
    .replaceAll("dos peers", "das regiões semelhantes")
    .replaceAll("Peers", "Regiões semelhantes")
    .replaceAll("peers", "regiões semelhantes");
}
