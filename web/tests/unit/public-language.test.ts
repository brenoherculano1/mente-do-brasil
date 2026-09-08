import { describe, expect, it } from "vitest";
import { publicLanguage } from "@/lib/public-language";

describe("publicLanguage", () => {
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
});
