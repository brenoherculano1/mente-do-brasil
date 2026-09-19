"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

export function YearSelector({ year, preview }: { year: number; preview: boolean }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  return <div className="edition-selector">
    <label htmlFor="edition-year">Ano de referência</label>
    <select id="edition-year" value={year} onChange={(event) => {
      const next = new URLSearchParams(params.toString());
      next.set("ano", event.target.value);
      router.push(`${pathname}?${next.toString()}`, { scroll: false });
    }}>
      <option value="2024">2024</option>
      {preview && <option value="2025">2025</option>}
    </select>
    <span>{year === 2024 ? "Dados de referência de 2024" : "Disponibilidade por indicador"}</span>
  </div>;
}
