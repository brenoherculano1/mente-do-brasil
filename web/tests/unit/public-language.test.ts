import { describe, expect, it } from "vitest";
import {
  describeCompositeScore,
  describeMismatch,
  describePercentile,
  publicLanguage,
} from "@/lib/public-language";

describe("publicLanguage", () => {
  it.each([[0.01, "1 ponto acima"], [-0.01, "1 ponto acima"], [0.02, "2 pontos acima"], [-0.02, "2 pontos acima"], [0, "0 pontos de diferença"]])("inflects points for %s", (value, expected) => {
    expect(describeMismatch(Number(value))).toContain(expected);
  });
  it("translates technical analytical terms for public surfaces", () => {
    expect(publicLanguage("Need Score acima dos peers no release atual")).toBe(
      "Índice de necessidade acima das regiões semelhantes no conjunto de dados atual",
    );
    expect(publicLanguage("Psiquiatras FTE e Mismatch")).toBe(
      "Jornadas equivalentes de psiquiatras e diferença entre necessidade e capacidade",
    );
  });

  it("expands internal quality flags into plain-language cautions", () => {
    expect(publicLanguage("SMALL_SUICIDE_COUNT")).toContain("interpretar a taxa com cautela");
    expect(publicLanguage("ZERO_REGISTERED_BEDS")).toContain("Nenhum leito registrado");
  });

  it("explains percentiles without calling them performance rankings", () => {
    expect(describePercentile(0.89, "capacity")).toContain("valores mais altos");
    expect(describePercentile(0.89, "capacity")).toContain("não uma nota de qualidade");
    expect(describePercentile(0.18, "need")).toContain("valores mais baixos");
  });

  it("explains composite scores and mismatch without inventing shortages", () => {
    expect(describeCompositeScore(0.46, "capacity")).toContain("46 pontos");
    expect(describeMismatch(-0.14)).toContain("estrutura registrada está 14 pontos acima");
    expect(describeMismatch(-0.14)).toContain("não informa quantos CAPS");
  });
});
