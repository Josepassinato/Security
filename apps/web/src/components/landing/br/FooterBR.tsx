import Link from 'next/link';

export function FooterBR() {
  return (
    <footer className="bg-[#1a1a1a] px-5 py-12 text-[#a09a8e] sm:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <p className="font-serif text-sm text-[#f4efe5]">
          Quarry · uma operação da{' '}
          <a
            href="https://increasetrainer.com"
            className="border-b border-[#a09a8e] no-underline hover:border-[#f4efe5] hover:text-[#f4efe5]"
            rel="noreferrer"
          >
            Increase Trainer Inc.
          </a>
        </p>

        <ul className="flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] uppercase tracking-[0.16em]">
          <li>
            <Link
              href="/"
              className="text-[#a09a8e] no-underline hover:text-[#f4efe5]"
            >
              versão internacional ↗
            </Link>
          </li>
          <li>
            <Link
              href="/demo-cinematografica"
              className="text-[#a09a8e] no-underline hover:text-[#f4efe5]"
            >
              demo
            </Link>
          </li>
          <li>
            <Link
              href="/br/pld-ft"
              className="text-[#a09a8e] no-underline hover:text-[#f4efe5]"
            >
              PLD/FT
            </Link>
          </li>
          <li>
            <a
              href="mailto:contato@quarry.dev"
              className="text-[#a09a8e] no-underline hover:text-[#f4efe5]"
            >
              contato
            </a>
          </li>
          <li className="text-[#6b665b]">
            © 2026
          </li>
        </ul>
      </div>
    </footer>
  );
}
