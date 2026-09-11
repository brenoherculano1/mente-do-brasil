"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState, useRef } from "react";

export function AppHeader() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  return (
    <header className="app-header">
      <div className="header-inner">
        <Link className="brand" href="/">
          <Image src="/brand/mente-do-brasil-mark.png" alt="" width={38} height={38} priority />
          <span>Mente do Brasil</span>
        </Link>
        <button ref={menuButton} type="button" className="mobile-menu-button" aria-expanded={menuOpen} aria-controls="main-navigation" onClick={() => setMenuOpen(!menuOpen)}>Menu</button>
        <nav id="main-navigation" aria-label="Navegação principal" className={`nav-links${menuOpen ? " is-open" : ""}`} onClick={() => setMenuOpen(false)} onKeyDown={(event) => { if (event.key === "Escape") { setMenuOpen(false); menuButton.current?.focus(); } }}>
          <Link aria-current={pathname === "/" ? "page" : undefined} href="/">
            Início
          </Link>
          <Link aria-current={pathname === "/radar" ? "page" : undefined} href="/radar">
            Regiões em atenção
          </Link>
          <Link aria-current={pathname === "/comparar" ? "page" : undefined} href="/comparar">
            Comparar
          </Link>
          <Link aria-current={pathname === "/financiamento" ? "page" : undefined} href="/financiamento">
            Recursos
          </Link>
          <Link aria-current={pathname === "/gestor" ? "page" : undefined} href="/gestor">
            Painel para gestores
          </Link>
          <Link aria-current={pathname === "/metodologia" ? "page" : undefined} href="/metodologia">
            Metodologia
          </Link>
          <Link aria-current={pathname === "/dados" ? "page" : undefined} href="/dados">
            Fontes
          </Link>
          <Link aria-current={pathname === "/sobre" ? "page" : undefined} href="/sobre">
            Sobre
          </Link>
        </nav>
      </div>
    </header>
  );
}
