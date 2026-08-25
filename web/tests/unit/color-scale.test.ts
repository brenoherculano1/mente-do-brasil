import { describe, expect, it } from "vitest";
import { colorForValue, getScaleDomain, MAP_COLORS } from "@/lib/map/color-scale";

describe("map color scale", () => {
  it("uses neutral color for zero mismatch", () => {
    const domain = getScaleDomain([-0.4, 0, 0.3]);
    expect(colorForValue(0, { scale: "diverging" }, domain)).toBe(MAP_COLORS.neutral);
  });

  it("keeps negative and positive mismatch on distinct sides", () => {
    const domain = getScaleDomain([-0.4, 0, 0.3]);
    expect(colorForValue(-0.2, { scale: "diverging" }, domain)).toBe(MAP_COLORS.negative);
    expect(colorForValue(0.2, { scale: "diverging" }, domain)).toBe(MAP_COLORS.positive);
  });

  it("does not convert null to zero", () => {
    const domain = getScaleDomain([0, 1]);
    expect(colorForValue(null, { scale: "score" }, domain)).toBe(MAP_COLORS.missing);
  });

  it("maps score values within 0-1 without missing styling", () => {
    const domain = getScaleDomain([0, 0.5, 1]);
    expect(colorForValue(0, { scale: "score" }, domain)).toBe(MAP_COLORS.scoreLow);
    expect(colorForValue(1, { scale: "score" }, domain)).toBe(MAP_COLORS.scoreHigh);
  });

  it("maps non-negative rates with sequential endpoints", () => {
    const domain = getScaleDomain([0, 2.4, 10]);
    expect(colorForValue(0, { scale: "rate" }, domain)).toBe(MAP_COLORS.rateLow);
    expect(colorForValue(10, { scale: "rate" }, domain)).toBe(MAP_COLORS.rateHigh);
  });
});
