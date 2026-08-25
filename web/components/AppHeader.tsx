"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function AppHeader() {
  const pathname = usePathname();
  return (
    <header className="app-header">
      <div className="header-inner">
        <Link className="brand" href="/">
          Mente do Brasil
        </Link>
        <nav aria-label="Navegação principal" className="nav-links">
          <Link aria-current={pathname === "/" ? "page" : undefined} href="/">
            Explorar
          </Link>
          <Link aria-current={pathname === "/metodologia" ? "page" : undefined} href="/metodologia">
            Metodologia
          </Link>
          <span className="muted-link" aria-disabled="true">
            Dados
          </span>
          <span className="muted-link" aria-disabled="true">
            Sobre
          </span>
        </nav>
      </div>
    </header>
  );
}
