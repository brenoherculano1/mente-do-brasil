import { describe, expect, it } from "vitest";
import { HISTORICAL_YEARS, historicalYear, validateHistoricalResponse, type HistoricalResponse } from "@/lib/historical";

describe("historical selection contract", () => {
  it("defaults only an absent year to 2024", () => {
    expect(historicalYear()).toBe(2024);
    expect(HISTORICAL_YEARS).toEqual([2022, 2023, 2024]);
    for (const year of HISTORICAL_YEARS) expect(historicalYear(String(year))).toBe(year);
    for (const value of ["", "2025", "2021", "invalid", ["2022", "2024"]]) expect(historicalYear(value)).toBeNull();
  });
  it("rejects current-year responses for a historical request", () => {
    expect(() => validateHistoricalResponse({ reference_year: 2024 } as HistoricalResponse, 2022)).toThrow();
    expect(() => validateHistoricalResponse({ reference_year: 2022, count: 0 } as HistoricalResponse, 2022)).toThrow();
  });
});
