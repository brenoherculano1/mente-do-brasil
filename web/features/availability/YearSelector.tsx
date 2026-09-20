"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { HISTORICAL_YEARS, type HistoricalYear } from "@/lib/historical";

export function YearSelector({ year }: { year: HistoricalYear }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  return <div className="edition-selector">
    <label htmlFor="edition-year">Ano de referência</label>
    <select className="input" id="edition-year" value={year} onChange={(event) => {
      const next = new URLSearchParams(params.toString());
      next.set("ano", event.target.value);
      router.push(`${pathname}?${next.toString()}`, { scroll: false });
    }}>
      {HISTORICAL_YEARS.map((value) => <option key={value} value={value}>{value}</option>)}
    </select>
    <span>Necessidade: {year - 2}–{year}. Estrutura: dezembro de {year}. Geografia histórica preservada.</span>
  </div>;
}
