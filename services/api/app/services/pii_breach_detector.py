"""PII breach detection — heurística para acionar comunicação ANPD.

Decide se um caso ``aisoc_cases`` qualifica como vazamento de dado
pessoal sob a LGPD Art. 48 §1º. Quando ``True``, o serviço de
regulatory dispatch dispara o gerador `anpdReport.ts` em paralelo à
comunicação Bacen.

Estratégia conservadora deliberada: prefere falso-positivo (gera
rascunho ANPD que o DPO pode descartar) a falso-negativo (deixa
passar incidente notificável). O custo de uma notificação ANPD
desnecessária é zero do lado regulatório; o custo de não notificar
quando deveria pode chegar a 2% do faturamento (LGPD Art. 52 II).

A heurística olha três sinais:

1. **Categorias de dado nos achados.** Se algum achado do caso menciona
   ``customer_id``, ``cpf``, ``email``, ``telefone``, ``pix_key``,
   ``account_number`` — sinaliza exposure.
2. **Severidade + escala.** Severity ``high``/``critical`` E mais de
   N contas correlacionadas sugere exfiltração em escala.
3. **MITRE techniques específicas.** T1530 (Data from Cloud Storage),
   T1213 (Data from Information Repositories), T1567 (Exfiltration
   Over Web Service) ou T1041 (Exfiltration Over C2 Channel)
   marcam exfiltração explícita.

Qualquer sinal positivo basta — operador qualificado (DPO) decide
depois. Não é classificador: é tripwire.

LLM classifier opcional (config ``QUARRY_REGCOMM_PII_LLM=true``) cobre
o caso em que os 3 sinais não disparam mas o texto livre dos findings
sugere PII (e.g. "dados de cartão expostos"). Sem o LLM, é só
heurística — defensável pra MVP.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

# Categorias de PII rastreadas pela heurística. Compilamos regex
# case-insensitive para evitar match em substring acidental
# (e.g. ``cpfu`` não bate ``cpf``).
_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "cpf": re.compile(r"\bcpf\b", re.IGNORECASE),
    "cnpj": re.compile(r"\bcnpj\b", re.IGNORECASE),
    "customer_id": re.compile(r"\bcustomer_?id\b", re.IGNORECASE),
    "email": re.compile(r"\b(e-?mail|email)\b", re.IGNORECASE),
    "telefone": re.compile(r"\b(telefone|phone|celular|msisdn)\b", re.IGNORECASE),
    "pix_key": re.compile(r"\bpix[_ ]?key|chave[_ ]?pix\b", re.IGNORECASE),
    "account_number": re.compile(
        r"\b(account_?number|conta[_ ]?corrente|n[uú]mero da conta)\b",
        re.IGNORECASE,
    ),
    "endereco": re.compile(r"\bendere[cç]o|address|cep\b", re.IGNORECASE),
    "documento": re.compile(r"\brg|passport|passaporte|cnh\b", re.IGNORECASE),
}

# MITRE techniques que indicam exfiltração explícita.
_EXFIL_TECHNIQUES: set[str] = {
    "T1530",  # Data from Cloud Storage
    "T1213",  # Data from Information Repositories
    "T1567",  # Exfiltration Over Web Service
    "T1041",  # Exfiltration Over C2 Channel
    "T1011",  # Exfiltration Over Other Network Medium
    "T1052",  # Exfiltration Over Physical Medium
}

# Threshold de escala. Configurável por env pra fintechs com perfil
# diferente (BaaS com milhões de end-users sobe esse número).
_SCALE_THRESHOLD = int(os.environ.get("QUARRY_REGCOMM_PII_SCALE_THRESHOLD", "50"))


@dataclass(frozen=True)
class PiiBreachAssessment:
    is_pii_breach: bool
    signals: list[str]
    categories_detected: list[str]
    reason: str

    def to_jsonable(self) -> dict[str, Any]:
        return {
            "is_pii_breach": self.is_pii_breach,
            "signals": self.signals,
            "categories_detected": self.categories_detected,
            "reason": self.reason,
        }


def _scan_pii_categories(text: str) -> list[str]:
    return sorted({name for name, pat in _PII_PATTERNS.items() if pat.search(text)})


def assess(
    *,
    findings: list[dict[str, Any]],
    severity: str | None,
    accounts_correlated: int | None,
    mitre_techniques: list[str] | None,
) -> PiiBreachAssessment:
    """Avalia um caso. Não lê DB — recebe os dados já coletados pelo caller.

    Args:
        findings: lista de achados, cada um com ``title``, ``description``,
          ``evidence`` ou ``raw`` que serão escaneados por padrões de PII.
        severity: severidade agregada do caso (``critical``/``high``/...).
        accounts_correlated: número de contas envolvidas (se disponível).
        mitre_techniques: lista de techniques (e.g. ``["T1530", "T1078"]``).
    """
    signals: list[str] = []
    categories: set[str] = set()

    # Sinal 1: categorias de PII nos achados
    haystack = " ".join(
        str(v)
        for f in findings
        for v in (f.get("title"), f.get("description"), f.get("evidence"), f.get("raw"))
        if v
    )
    found_cats = _scan_pii_categories(haystack)
    if found_cats:
        signals.append("pii_categories_in_findings")
        categories.update(found_cats)

    # Sinal 2: severity alta + escala
    if severity in ("high", "critical") and (accounts_correlated or 0) >= _SCALE_THRESHOLD:
        signals.append("high_severity_at_scale")

    # Sinal 3: exfil MITRE
    technique_set = set(mitre_techniques or [])
    matched_exfil = technique_set & _EXFIL_TECHNIQUES
    if matched_exfil:
        signals.append(f"exfil_technique:{sorted(matched_exfil)}")

    is_breach = bool(signals)
    reason = (
        f"signals={signals!r} categories={sorted(categories)!r} "
        f"severity={severity!r} accounts={accounts_correlated!r} "
        f"mitre={sorted(technique_set)!r}"
    )
    return PiiBreachAssessment(
        is_pii_breach=is_breach,
        signals=signals,
        categories_detected=sorted(categories),
        reason=reason,
    )


__all__ = ["PiiBreachAssessment", "assess"]
