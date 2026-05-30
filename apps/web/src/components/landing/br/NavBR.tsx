'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

export function NavBR() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={
        'fixed inset-x-0 top-0 z-50 transition-colors duration-200 ' +
        (scrolled
          ? 'border-b border-[#d8d2c4] bg-[#f7f4ef]/90 backdrop-blur'
          : 'border-b border-transparent bg-transparent')
      }
    >
      <nav
        aria-label="Navegação principal"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8"
      >
        <Link
          href="/br"
          className="flex items-baseline gap-2 text-[#1a1a1a] no-underline"
          aria-label="Quarry para fintechs brasileiras"
        >
          <span className="font-serif text-xl font-medium tracking-tight">Quarry</span>
          <span className="text-[11px] uppercase tracking-[0.18em] text-[#6b665b]">
            · fintechs br
          </span>
        </Link>

        <ul className="hidden items-center gap-6 sm:flex">
          <li>
            <a
              href="/br#proporcao"
              className="text-sm text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              proporção
            </a>
          </li>
          <li>
            <a
              href="/br#bacen"
              className="text-sm text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              bacen
            </a>
          </li>
          <li>
            <Link
              href="/br/pld-ft"
              className="text-sm text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              PLD/FT
            </Link>
          </li>
          <li>
            <a
              href="/br#benchmark"
              className="text-sm text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              benchmark
            </a>
          </li>
          <li>
            <a
              href="/br#custo"
              className="text-sm text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              custo
            </a>
          </li>
          <li>
            <a
              href="/br#para-quem-nao-e"
              className="text-sm text-[#3a362e] no-underline hover:text-[#1a1a1a]"
            >
              limites
            </a>
          </li>
          <li>
            <Link
              href="/demo-cinematografica"
              className="text-sm italic text-[#1a1a1a] no-underline hover:underline"
            >
              ver a plataforma →
            </Link>
          </li>
        </ul>

        <Link
          href="/"
          className="hidden text-[11px] uppercase tracking-[0.16em] text-[#6b665b] no-underline hover:text-[#1a1a1a] sm:inline-block"
          aria-label="Versão internacional open-source"
        >
          en / oss ↗
        </Link>
      </nav>
    </header>
  );
}
