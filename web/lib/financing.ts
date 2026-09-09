import type { FinancingRecord } from "@/types/api";

export function summarizeFinancing(records: FinancingRecord[], uf: string) {
  const scoped = records.filter((row) => !uf || row.uf === uf);
  const observed = scoped.filter((row) => row.total_health_expenditure_brl !== null);
  return {
    total: observed.length > 0
      ? observed.reduce((sum, row) => sum + (row.total_health_expenditure_brl ?? 0), 0)
      : null,
    observed: observed.length,
    expected: scoped.length,
  };
}
