import { describe, expect, it } from "vitest";
import { toneForDirection, toneForMetric, toneForMismatch } from "@/lib/indicator-tone";

describe("indicator tones", () => {
  it("respects the direction of need and capacity indicators", () => {
    expect(toneForDirection(0.9, "need")).toBe("attention");
    expect(toneForDirection(0.9, "capacity")).toBe("favorable");
    expect(toneForDirection(0.5, "capacity")).toBe("neutral");
  });

  it("does not treat every positive number as favorable", () => {
    expect(toneForMismatch(0.2)).toBe("attention");
    expect(toneForMismatch(-0.2)).toBe("favorable");
    expect(toneForMetric("suicide_asmr", 8, 0.9)).toBe("attention");
  });
});
