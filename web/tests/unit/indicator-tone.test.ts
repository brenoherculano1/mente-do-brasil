import { describe, expect, it } from "vitest";
import { relativeBandLabel, toneLabel, toneForDirection, toneForMetric, toneForMismatch } from "@/lib/indicator-tone";
import { publicLanguage } from "@/lib/public-language";

describe("indicator tones", () => {
  it("describes relative position without judging adequacy", () => {
    expect(relativeBandLabel(0.15)).toBe("Faixa relativa baixa");
    expect(relativeBandLabel(0.68)).toBe("Faixa relativa intermediária");
    expect(relativeBandLabel(0.8)).toBe("Faixa relativa alta");
    for (const tone of ["favorable", "attention", "neutral"] as const) {
      expect(toneLabel(tone)).not.toMatch(/favorável|melhor|pior|adequad/i);
    }
  });
  it("translates manager labels without changing the spatial category", () => {
    expect(publicLanguage("Financing")).toBe("Recursos de saúde");
    expect(publicLanguage("Flow")).toBe("Fluxos de atendimento");
    expect(publicLanguage("LISA significativo: low-low")).toBe("LISA significativo: valores baixos na região e nos vizinhos");
  });
  it("respects the direction of need and capacity indicators", () => {
    expect(toneForDirection(0.9, "need")).toBe("attention");
    expect(toneForDirection(0.9, "capacity")).toBe("favorable");
    expect(toneForDirection(0.5, "capacity")).toBe("neutral");
  });

  it("does not treat every positive number as favorable", () => {
    expect(toneForMismatch(0.2)).toBe("neutral");
    expect(toneForMismatch(-0.2)).toBe("neutral");
    expect(toneForMetric("suicide_asmr", 8, 0.9)).toBe("attention");
  });
});
