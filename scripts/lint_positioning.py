#!/usr/bin/env python3
"""
Anti-tagline + positioning drift linter.

Scans public-facing files for phrases banned by docs/pt-br/POSITIONING.md §8.
Returns non-zero exit code if any banned phrase is found.

Wire into CI:
    python3 scripts/lint_positioning.py

Run against a subset (e.g. one PR):
    python3 scripts/lint_positioning.py path/to/file1.md path/to/file2.tsx

Override (only ever for vendor/upstream content we don't control):
    add the phrase + path to ALLOWLIST below, with a short reason.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Phrases banned in any customer-facing public copy.
# Match is case-insensitive, whole-phrase, with word boundaries where helpful.
BANNED: list[tuple[str, str]] = [
    (r"\bAI[- ]powered\b",        "anti-tagline §8 — generic AI-slop"),
    (r"\balimentad[oa] por IA\b", "anti-tagline §8 — same as AI-powered, PT"),
    (r"\brevolutioniz[ea]\b",     "anti-tagline §8 — generic SaaS phrase"),
    (r"\brevolucione\b",          "anti-tagline §8 — PT version"),
    (r"\bmodern SIEM\b",          "anti-tagline §8 — we are not a SIEM"),
    (r"\bend[- ]to[- ]end cyber\b", "anti-tagline §8 — vague"),
    (r"\bcompliance copilot\b",   "anti-tagline §8 — Stark AI/Idwall surface, not ours"),
    (r"\bSIEM moderno\b",         "anti-tagline §8 — PT version"),
    (r"\btransform your security\b", "anti-tagline §8"),
    (r"\btransforme sua segurança\b", "anti-tagline §8 — PT version"),
]

# Files / paths to scan. Globs relative to repo root.
SCAN_GLOBS = [
    "README.md",
    "package.json",
    "docs/pt-br/POSITIONING.md",   # canonical — should not contain banned phrases except inside §8 itself
    "docs/pt-br/**/*.md",
    "apps/web/src/app/**/*.tsx",
    "apps/web/src/components/landing/**/*.tsx",
    ".github/PULL_REQUEST_TEMPLATE/**/*.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
]

# Paths to skip even if they match a scan glob.
SKIP = {
    "node_modules", ".next", ".turbo", "dist", "build", "_archive",
}

# Allowlist: (file_path_substring, phrase_regex) — pair must match.
# Use sparingly. Add a one-line reason.
ALLOWLIST: list[tuple[str, str]] = [
    # POSITIONING.md §8 lists anti-taglines as examples (negative space).
    ("docs/pt-br/POSITIONING.md", r"\bAI[- ]powered\b"),
    ("docs/pt-br/POSITIONING.md", r"\brevolutioniz[ea]\b"),
    ("docs/pt-br/POSITIONING.md", r"\bmodern SIEM\b"),
    ("docs/pt-br/POSITIONING.md", r"\bend[- ]to[- ]end cyber\b"),
    ("docs/pt-br/POSITIONING.md", r"\bcompliance copilot\b"),
    # CONTRIBUTING.md / AGENTS.md reference POSITIONING.md anti-tagline list verbatim.
    ("CONTRIBUTING.md", r"\bAI[- ]powered\b"),
    ("AGENTS.md", r"\bAI[- ]powered\b"),
    ("AGENTS.md", r"\brevolutioniz[ea]\b"),
    ("AGENTS.md", r"\bmodern SIEM\b"),
    # The linter itself contains the banned phrases as data — allow.
    ("scripts/lint_positioning.py", "ANY"),
    # DisqualifierBR ironizes "AI-powered cyber" as anti-ICP example (POSITIONING §6).
    ("apps/web/src/components/landing/br/DisqualifierBR.tsx", r"\bAI[- ]powered\b"),
    # pitch-deck.md disqualifier section uses "AI-powered cyber" ironically.
    ("docs/pt-br/pitch-deck.md", r"\bAI[- ]powered\b"),
]


def is_allowlisted(path: Path, phrase: str) -> bool:
    rel = str(path.relative_to(ROOT))
    for sub, pattern in ALLOWLIST:
        if sub in rel and (pattern == "ANY" or pattern == phrase):
            return True
    return False


def should_scan(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP:
        return False
    return path.is_file()


def iter_files(args: list[str]) -> list[Path]:
    if args:
        out: list[Path] = []
        for a in args:
            p = (ROOT / a).resolve() if not os.path.isabs(a) else Path(a)
            if p.is_file() and should_scan(p):
                out.append(p)
        return out

    out: list[Path] = []
    for g in SCAN_GLOBS:
        for p in ROOT.glob(g):
            if should_scan(p):
                out.append(p)
    return sorted(set(out))


def main(argv: list[str]) -> int:
    files = iter_files(argv[1:])
    if not files:
        print("lint_positioning: no files matched", file=sys.stderr)
        return 0

    violations: list[tuple[Path, int, str, str]] = []  # (path, lineno, phrase, reason)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, reason in BANNED:
            if is_allowlisted(path, pattern):
                continue
            for m in re.finditer(pattern, text, flags=re.IGNORECASE):
                lineno = text.count("\n", 0, m.start()) + 1
                violations.append((path, lineno, m.group(0), reason))

    if not violations:
        print(f"lint_positioning: OK — scanned {len(files)} file(s), zero banned phrases")
        return 0

    print(f"lint_positioning: {len(violations)} violation(s)\n", file=sys.stderr)
    for path, lineno, phrase, reason in violations:
        rel = path.relative_to(ROOT)
        print(f"  {rel}:{lineno}  '{phrase}'  → {reason}", file=sys.stderr)
    print(
        "\nFix: rewrite using positioning anchored in docs/pt-br/POSITIONING.md.",
        file=sys.stderr,
    )
    print(
        "If the phrase is legitimately needed (vendor doc, allowlisted reference), "
        "add an entry to ALLOWLIST in scripts/lint_positioning.py.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
