"""Evidence Pack renderer — HTML and PDF outputs of a sealed bundle.

Pattern mirrors ``services.digest_html`` + ``services.digest_pdf``:

* :func:`render_evidence_html` — pure Python, inline CSS, no Jinja2.
  Same bundle in, same HTML out. Deterministic across runs.
* :func:`render_evidence_pdf` — wraps the HTML through WeasyPrint.
  Graceful fallback when the native Cairo/Pango stack is missing
  (e.g. macOS dev without Homebrew bottles) — raises
  :class:`WeasyPrintUnavailableError` so the caller can decide.

The HTML targets the auditor's reading experience:
  * Editorial typography (Fraunces serif for headers, Inter for body),
  * Bacen-formal layout with article reference + obligation paraphrase
    above the structured evidence,
  * Footer with TSA + signature receipts + Merkle chain link.

The HTML is **self-contained** (no external assets) so it can be
emailed, saved offline, or rendered by any tooling that consumes
HTML — including the auditor's own browser.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from app.evidence_pack.compiler import EvidenceBundle
from app.evidence_pack.schema import EvidencePack
from app.evidence_pack.signer import is_mock_signature
from app.evidence_pack.tsa import is_mock_token


__all__ = [
    "render_evidence_html",
    "render_evidence_pdf",
    "WeasyPrintUnavailableError",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class WeasyPrintUnavailableError(RuntimeError):
    """Raised when WeasyPrint's native stack is not available."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _fmt_datetime(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _pretty_json(payload: Any) -> str:
    """Render a structured payload as readable JSON for the auditor pane."""
    return html.escape(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------


_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #1a1a1a;
  background: #ffffff;
  margin: 0;
  padding: 32pt 36pt;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3 {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 500;
  letter-spacing: -0.015em;
  margin: 0 0 8pt 0;
}

h1 { font-size: 22pt; line-height: 1.15; }
h2 { font-size: 14pt; line-height: 1.2; margin-top: 18pt; }
h3 { font-size: 11pt; line-height: 1.25; margin-top: 12pt; color: #444444; }

p { margin: 0 0 8pt 0; max-width: 64em; }

em { font-style: italic; color: #6b3a1a; }

.eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5pt;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #6b665b;
  margin-bottom: 6pt;
}

.regulation {
  border-left: 2pt solid #6b3a1a;
  padding: 4pt 0 4pt 12pt;
  margin: 12pt 0 24pt 0;
}

.regulation .code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9pt;
  color: #6b3a1a;
}

.requirement {
  background: #faf7f0;
  border: 0.5pt solid #d8d2c4;
  padding: 12pt 14pt;
  margin: 12pt 0;
  font-size: 10.5pt;
}

.step {
  break-inside: avoid;
  border-top: 0.5pt solid #d8d2c4;
  padding-top: 10pt;
  margin-top: 16pt;
}

.step-label {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 500;
  font-size: 12pt;
  color: #1a1a1a;
}

pre.evidence-json {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5pt;
  line-height: 1.45;
  background: #f7f4ef;
  border: 0.5pt solid #d8d2c4;
  padding: 8pt 10pt;
  margin: 6pt 0 10pt 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.seal-section {
  margin-top: 24pt;
  border-top: 2pt solid #1a1a1a;
  padding-top: 12pt;
  page-break-before: always;
}

.seal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18pt;
  font-size: 9.5pt;
  margin-top: 10pt;
}

.seal-grid dt {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8pt;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #6b665b;
  margin-top: 6pt;
}

.seal-grid dd {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5pt;
  margin: 2pt 0 0 0;
  word-break: break-all;
}

.warning {
  background: #fff3e0;
  border: 0.5pt solid #c2410c;
  color: #7c2d12;
  padding: 8pt 10pt;
  font-size: 9.5pt;
  margin: 12pt 0;
}

.cross-references {
  margin-top: 16pt;
  font-size: 9.5pt;
  color: #444444;
}

.cross-references ul { margin: 4pt 0; padding-left: 18pt; }

footer {
  margin-top: 28pt;
  padding-top: 10pt;
  border-top: 0.5pt solid #d8d2c4;
  font-size: 8.5pt;
  color: #6b665b;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.08em;
}

@page {
  size: A4;
  margin: 16mm 18mm;
}

/* P1.4 — Persistent watermark for mock seals.
 *
 * Per Parecer Jurídico Nº 012/2026, the warning banner reduces
 * operational risk but does NOT eliminate it. A user who scrolls past
 * the banner could still mistake a mock-sealed PDF for a real one. A
 * watermark stamped on every page makes that misclassification
 * essentially impossible.
 *
 * Uses ``position: fixed`` — WeasyPrint repeats fixed-position blocks
 * on every page (the same trick used for headers/footers).
 */
.watermark {
  position: fixed;
  top: 50%;
  left: 0;
  width: 100%;
  text-align: center;
  transform: translateY(-50%) rotate(-30deg);
  font-family: 'JetBrains Mono', monospace;
  font-weight: bold;
  font-size: 36pt;
  color: rgba(180, 90, 20, 0.18);
  letter-spacing: 0.04em;
  pointer-events: none;
  z-index: 9999;
  line-height: 1.3;
}
.watermark .small {
  display: block;
  font-size: 13pt;
  margin-top: 4pt;
  letter-spacing: 0.12em;
}
"""


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------


def render_evidence_html(
    *,
    pack: EvidencePack,
    bundle: EvidenceBundle,
) -> str:
    """Render the sealed bundle as a self-contained HTML document.

    The HTML is the canonical artifact: it is what the auditor reads,
    what gets converted to PDF, and what the verifier hashes against
    the chain entry.

    Args:
        pack: The original validated pack.
        bundle: The sealed bundle from the compiler.

    Returns:
        A complete HTML5 document as a string.
    """
    meta = pack.meta
    has_mock_seal = is_mock_token(bundle.timestamp.token_der) or is_mock_signature(
        bundle.signature.signature_der
    )

    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '  <meta charset="utf-8">',
        f"  <title>Evidence Pack — {_esc(meta.regulation_code)} {_esc(meta.article)}</title>",
        f"  <style>{_CSS}</style>",
        "</head>",
        "<body>",
        # Header
        '  <div class="eyebrow">01 — pacote de evidências</div>',
        f"  <h1>{_esc(meta.title)}</h1>",
        '  <div class="regulation">',
        f'    <div class="code">{_esc(meta.regulation_code)} · {_esc(meta.article)}'
        + (f" · {_esc(meta.sub_item)}" if meta.sub_item else "")
        + "</div>",
        f"    <p>{_esc(meta.requirement)}</p>",
        "  </div>",
    ]

    if has_mock_seal:
        parts.append(
            '  <div class="watermark">DOCUMENTO NÃO ASSINADO'
            '<span class="small">AMBIENTE DE HOMOLOGAÇÃO</span>'
            '</div>'
        )
        parts.append(
            '  <div class="warning">'
            "⚠ Este pacote contém timestamp OU assinatura de mock (dev). "
            "Não é admissível em fiscalização ou em juízo. Configure "
            "<code>SAFEWEB_TSA_API_KEY</code> e <code>ECNPJ_PKCS12_PATH</code> "
            "antes de gerar o artefato real."
            "</div>"
        )

    # Window
    parts.append(
        f'  <div class="eyebrow">período coberto</div>'
        f"  <p>{_esc(_fmt_datetime(bundle.window_start))}  →  "
        f"{_esc(_fmt_datetime(bundle.window_end))}</p>"
    )

    # Evidence steps
    parts.append('  <h2>Evidência coletada</h2>')
    for step in pack.evidence_queries:
        value = bundle.data.get(step.label)
        parts.extend(
            [
                '  <div class="step">',
                f'    <div class="step-label">{_esc(step.label)}</div>',
                f'    <div class="eyebrow">tipo: {_esc(step.type.value)}</div>',
                f'    <pre class="evidence-json">{_pretty_json(value)}</pre>',
                "  </div>",
            ]
        )

    # Cross-references
    if pack.cross_references:
        parts.append('  <div class="cross-references">')
        parts.append("    <h3>Mapeamento de controles cruzados</h3>")
        parts.append("    <ul>")
        for ref in pack.cross_references:
            parts.append(f"      <li>{_esc(ref)}</li>")
        parts.append("    </ul>")
        parts.append("  </div>")

    # Sealing receipts
    parts.append('  <section class="seal-section">')
    parts.append('    <div class="eyebrow">02 — cadeia probatória</div>')
    parts.append("    <h2>Receitas criptográficas</h2>")
    parts.append(
        "    <p>Os receitas abaixo permitem que um auditor independente "
        "verifique, sem acesso à infraestrutura da Quarry, que o "
        "artefato existia neste instante e não foi alterado depois.</p>"
    )
    parts.append('    <dl class="seal-grid">')
    parts.extend(
        [
            f"      <dt>SHA-256 do conteúdo</dt><dd>{_esc(bundle.data_digest_hex)}</dd>",
            f"      <dt>Timestamp (TSA)</dt><dd>{_esc(bundle.timestamp.tsa_name)}<br>"
            f"{_esc(_fmt_datetime(bundle.timestamp.stamped_at))}</dd>",
            f"      <dt>Token TSA (hex)</dt><dd>{_esc(bundle.timestamp.token_der.hex()[:128])}…</dd>",
            f"      <dt>Assinatura digital</dt><dd>{_esc(bundle.signature.signer_subject)}<br>"
            f"{_esc(_fmt_datetime(bundle.signature.signed_at))}</dd>",
            f"      <dt>Algoritmo</dt><dd>{_esc(bundle.signature.digest_algorithm)}</dd>",
            f"      <dt>Cadeia Merkle — entrada anterior</dt>"
            f"<dd>{_esc(bundle.prev_chain_entry_hash_hex)}</dd>",
            f"      <dt>Cadeia Merkle — esta entrada</dt>"
            f"<dd>{_esc(bundle.hash_chain_entry_hash_hex)}</dd>",
        ]
    )
    parts.append("    </dl>")
    parts.append("  </section>")

    # Footer
    parts.append("  <footer>")
    parts.append(
        f"    Gerado em {_esc(_fmt_datetime(bundle.generated_at))} · "
        f"Pack ID {_esc(bundle.pack_id)} · "
        f"Quarry — Bacen Evidence Engine"
    )
    parts.append("  </footer>")

    parts.append("</body></html>")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# PDF renderer (WeasyPrint wrapper)
# ---------------------------------------------------------------------------


def render_evidence_pdf(
    *,
    pack: EvidencePack,
    bundle: EvidenceBundle,
) -> bytes:
    """Render the bundle as a PDF byte string.

    Uses WeasyPrint to convert the HTML produced by
    :func:`render_evidence_html`. WeasyPrint needs Cairo/Pango/GLib
    installed natively; on systems without that stack we raise
    :class:`WeasyPrintUnavailableError` so the caller can fall back
    (or send the HTML as a download).
    """
    html_doc = render_evidence_html(pack=pack, bundle=bundle)
    try:
        from weasyprint import HTML  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise WeasyPrintUnavailableError(
            "WeasyPrint is not installed in this environment. "
            "Install with: pip install 'weasyprint>=62'."
        ) from exc
    except OSError as exc:  # pragma: no cover
        # WeasyPrint raises OSError when libcairo/pango cannot load.
        raise WeasyPrintUnavailableError(
            f"WeasyPrint native stack unavailable: {exc}. "
            "Install Cairo/Pango/GLib system libraries."
        ) from exc

    return HTML(string=html_doc).write_pdf()
