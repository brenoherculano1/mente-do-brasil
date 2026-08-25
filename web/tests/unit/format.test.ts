import { describe, expect, it } from "vitest";
import { formatInteger, formatPercentile, formatScore } from "@/lib/format";

describe("formatters", () => {
  it("formats population with pt-BR separators", () => {
    expect(formatInteger(212583)).toBe("212.583");
  });

  it("formats percentiles from API 0-1 values", () => {
    expect(formatPercentile(0.72)).toBe("72º percentil");
  });

  it("formats mismatch with sign and two decimals", () => {
    expect(formatScore(0.237194832, true)).toBe("+0,24");
  });
});
