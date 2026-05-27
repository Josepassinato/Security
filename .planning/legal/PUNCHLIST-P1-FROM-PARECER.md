# Punch-list P1 derivada do Parecer Jurídico Nº 012/2026

> Lista executável de ajustes técnicos que o Dr. Ricardo Mendes apontou
> como necessários para que os Evidence Packs sejam admissíveis em
> produção. Cada item cita o trecho do parecer que o motiva.

---

## 🔴 P1 — Bloqueantes pro piloto comercial

### 1. Renomear pack LGPD + corrigir prazo (parecer II.2)

**Motivação**: prazo "48h" no nome está **legalmente errado** desde Res. CD/ANPD 15/2024 (prazo correto: 3 dias úteis).

- [ ] Renomear `customizations/compliance/evidence-packs/lgpd-art-48-anpd-48h.yaml`
      → `lgpd-art-48-anpd-15-2024.yaml`
- [ ] Atualizar `pack_id`, `title`, banner
- [ ] Atualizar regulation_code para citar `LGPD Art. 48 c/c Res. ANPD 15/2024`
- [ ] Atualizar `reporting_period` se aplicável
- [ ] Atualizar refs em tests (`test_evidence_packs_endpoint.py`, `test_evidence_pack_pipeline.py`)
- [ ] Atualizar landing/docs públicas que citem o prazo

### 2. Pack LGPD — 5 campos faltantes (parecer II.4)

Adicionar queries no YAML pra:

- [ ] Número estimado de titulares afetados (`config_state` key ou novo `query_type`)
- [ ] Categorias de dados pessoais (sensíveis vs não-sensíveis)
- [ ] Descrição dos riscos aos titulares (dano material/moral)
- [ ] Medidas técnicas e administrativas de contenção/mitigação
- [ ] Dados completos do DPO (nome, e-mail, telefone, canal de contato)

Renderer deve expor cada um na tabela de conformidade do PDF.

### 3. Headers de PDF — campos probatórios (parecer V — preliminar)

- [ ] Serial do certificado e-CNPJ no PDF
- [ ] Cadeia ICP completa (issuer chain) no PDF
- [ ] Fingerprint SHA-256 do documento final
- [ ] **Timezone UTC explícito** em todos os timestamps
- [ ] Identificador único imutável do evento (validar exposição atual)

### 4. Mock seal — defense-in-depth (parecer V preliminar + II.5)

- [ ] Watermark persistente em TODAS as páginas do PDF mock:
      *"DOCUMENTO NÃO ASSINADO — AMBIENTE DE HOMOLOGAÇÃO"*
- [ ] Campo `seal_status: "mock"|"production"` no JSON da bundle
- [ ] Em produção: REMOVER banner amarelo + watermark (parecer II.5)
- [ ] Endpoint `/download.pdf` rejeita com 403 se `seal_status=mock` em
      env produção (env flag)

### 5. PII pseudonimização determinística (parecer II.6 + VI preliminar)

**Substitui** o atual guard que apenas refuse `include_redacted_pii=True`.

- [ ] Implementar pseudonimizer: `pseudonimize(value, tenant_id, kind) →
      f"{kind}_{HMAC_SHA256(salt_tenant, value)[:16]}"`
- [ ] Salt por tenant armazenado em `tenant.pii_redaction_salt` (gerado
      no provision, nunca exposto via API)
- [ ] Chave de reversão (mapeamento hash→valor original) guardada com
      acesso restrito ao DPO ou responsável legal (vault separado)
- [ ] Remover o `raise EvidencePackError` no MockRuntime.ledger_export
      quando `include_redacted_pii=True` — substituir pelo redactor real
- [ ] Atualizar test `test_compile_refuses_when_pii_redaction_requested`
      para testar **comportamento correto** ao invés de refusal

### 6. 3 níveis de exportação (parecer VI preliminar)

Schema novo no pack:

```yaml
export_levels:
  - internal_forensics      # PII integral
  - regulatory_submission   # PII pseudonimizada
  - executive_summary       # PII removida
```

- [ ] Adicionar enum `ExportLevel` no schema
- [ ] Compilador respeita `export_level` no compile/preview/download
- [ ] Renderer marca o nível no PDF (header)
- [ ] Endpoint POST `/compile?level=...` (default `regulatory_submission`)

---

## 🟡 P2 — Hardening pós-MVP

### 7. Pack BCB 85 — campo "diretor responsável" (parecer II.4)

- [ ] Adicionar query `config_state` pra `compliance.designated_director`
- [ ] Citar Art. 7º da Res. BCB 85/2021 no pack

### 8. Pack BCB 85 — evidências de execução (parecer IV preliminar)

- [ ] Evidência de treinamento da equipe (query no ledger)
- [ ] Registro de teste de mesa/tabletop
- [ ] Histórico de revisão da política
- [ ] Aprovação formal da alta administração

### 9. Pack Bacen 24h — campos operacionais (parecer IV preliminar)

- [ ] Impacto operacional (descrição livre)
- [ ] Serviços críticos afetados (lista)
- [ ] Status de contingência
- [ ] Impacto em PIX / Open Finance específico
- [ ] Terceiros envolvidos (vendors, parceiros)
- [ ] Timeline objetiva do incidente

### 10. Revisão copy comercial (parecer VII preliminar)

**Anti-claims** que NUNCA podem aparecer:

- ~~"Garante aceitação Bacen"~~
- ~~"Certifica conformidade"~~
- ~~"Blindagem regulatória"~~

**Pro-claims**: fortalece governança / aumenta auditabilidade /
preservação de evidências / reduz assimetria informacional /
demonstração de diligência regulatória.

- [ ] Varrer `apps/web/src/components/landing/br/SovereignLlmBR.tsx`
- [ ] Varrer `README.md` público
- [ ] Varrer `apps/web/src/components/settings/EvidencePacksView.tsx`

---

## ⚪ Bloqueios externos (não-engenharia)

- [ ] Conta SafeWeb TSA (R$ 60-150/mês)
- [ ] e-CNPJ A3 (R$ 250/ano)
- [ ] Cláusula contratual elaborada pelo Dr. Ricardo (parecer II.5 + IV)
- [ ] Termo de aceite final do honorário com Dr. Ricardo
- [ ] **Aplicar migration 046** em prod (hash chain)

---

## Estimativa de esforço

- Items 1-6: **5-7 dias eng** (1 dev sênior)
- Items 7-10: **3-5 dias eng** + 1 dia revisão de copy
- Total: **2 sprints** (10 dias úteis) pra ficar pronto pra piloto comercial

---

## Como saber que terminou

1. Os 3 packs compilam, geram PDF, e o Dr. Ricardo valida o PDF resultante
   numa call de calibração de 1-2h
2. Tests do CARD-016 sobem de 58 pra ~75 (com PII tests reais)
3. Tag `legal/v1.0` no repo aponta pro commit que fecha o punch-list
4. Versão final do parecer assinada digitalmente arquivada em `.planning/legal/`
