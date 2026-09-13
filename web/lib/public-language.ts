const EXACT_LABELS: Record<string, string> = {
  SMALL_SUICIDE_COUNT: "Poucos óbitos no período; interpretar a taxa com cautela.",
  ZERO_REGISTERED_BEDS: "Nenhum leito registrado na medida utilizada.",
  Financing: "Recursos de saúde",
  Flow: "Fluxos de atendimento",
  Base: "Contexto territorial",
};

export type IndicatorDirection = "need" | "capacity";

export function describePercentile(percentile: number, direction: IndicatorDirection) {
  const position = Math.round(Math.max(0, Math.min(1, percentile)) * 100);
  const subject = direction === "need" ? "sinal medido" : "registro de estrutura";
  const band =
    position >= 80
      ? "está entre os valores mais altos do país"
      : position <= 20
        ? "está entre os valores mais baixos do país"
        : position >= 60
          ? "está acima da maior parte das regiões"
          : position <= 40
            ? "está abaixo da maior parte das regiões"
            : "está próximo ao centro da distribuição nacional";
  return `${position} de 100: o ${subject} ${band}. É uma posição relativa, não uma nota de qualidade nem uma classificação entre melhores e piores.`;
}

export function describeCompositeScore(value: number, direction: IndicatorDirection) {
  const label = direction === "need" ? "necessidade medida" : "estrutura registrada";
  return `${formatSignedPoints(value, false)} na escala relativa: resume a posição combinada da ${label} diante das demais regiões; não representa uma quantidade física.`;
}

export function describeMismatch(value: number) {
  const points = Math.round(Math.abs(value) * 100);
  if (points === 0) {
    return "0 pontos de diferença: necessidade medida e estrutura registrada ocupam posições nacionais semelhantes.";
  }
  const relation = value > 0
    ? `a necessidade medida está ${points} ${points === 1 ? "ponto" : "pontos"} acima da estrutura registrada`
    : `a estrutura registrada está ${points} ${points === 1 ? "ponto" : "pontos"} acima da necessidade medida`;
  return `${formatSignedPoints(value, true)} na escala relativa: ${relation}. O índice não informa quantos CAPS, leitos ou profissionais faltam.`;
}

function formatSignedPoints(value: number, signed: boolean) {
  const points = Math.round(value * 100);
  const prefix = signed && points > 0 ? "+" : "";
  return `${prefix}${points} ${Math.abs(points) === 1 ? "ponto" : "pontos"}`;
}

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
    .replaceAll("peers", "regiões semelhantes")
    .replaceAll("high-high", "valores altos na região e nos vizinhos")
    .replaceAll("low-low", "valores baixos na região e nos vizinhos")
    .replaceAll("high-low", "valor alto na região e baixo nos vizinhos")
    .replaceAll("low-high", "valor baixo na região e alto nos vizinhos");
}
