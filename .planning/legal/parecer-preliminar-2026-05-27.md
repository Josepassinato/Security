# Parecer Jurídico Preliminar — 2026-05-27

> Versão pré-formal entregue por Dr. Ricardo Mendes (ainda não assinada).
> Substituída pela versão formal `parecer-012-2026.md` quando completa.

## I. Conclusão executiva

- Boa aderência aos requisitos modernos de governança, auditabilidade,
  integridade e rastreabilidade exigidos em fiscalização.
- Aderência: BACEN, LGPD/ANPD, segurança cibernética, continuidade
  operacional, resposta a incidentes.
- Maturidade incomum para ferramenta de compliance emergente.
- **Posicionamento jurídico correto**: "infraestrutura de preservação,
  consolidação e demonstração de evidências regulatórias digitais"
  (NÃO "garantia de conformidade").

## II. Admissibilidade probatória dos PDFs

**SIM, com ressalvas.**

Base jurídica:

- MP 2.200-2/2001, art. 10
- CPC, arts. 369, 411 e correlatos
- Princípios de cadeia de custódia digital
- Liberdade probatória administrativa

> "BACEN e ANPD normalmente não exigem 'forma específica de prova',
> mas sim capacidade de demonstrar diligência, integridade e governança."

**O PDF isolado NÃO é a prova principal.** A robustez nasce do conjunto:
ledger imutável + hashes + timestamps + assinatura ICP-Brasil + logs de
geração + retenção dos artefatos-fonte + reconstrução da evidência.

## III. TSA + e-CNPJ A3 — estrutura adequada e juridicamente sólida

A combinação TSA ICP-Brasil + e-CNPJ A3 é tecnicamente consistente para:
autoria, integridade, não-repúdio, anterioridade temporal.

**Significativamente superior** a PDFs comuns / assinatura visual /
DocuSign sem ICP / logs internos sem timestamp confiável.

### Limitação

TSA **NÃO certifica conteúdo**. Certifica: existência temporal,
integridade binária, e não alteração posterior. Disclaimer obrigatório.

### Recomendações (campos a incluir no PDF)

- Serial do certificado
- Cadeia ICP completa
- Fingerprint SHA-256 do documento
- Timezone UTC explícito
- Identificador único imutável do evento

## IV. Campos obrigatórios — possíveis lacunas

### 1. Pack LGPD Art. 48 — risco moderado

Faltando ou insuficiente:

- Número estimado de titulares afetados
- Categorias de dados
- Critérios de risco/dano relevante
- Identificação do encarregado (DPO)
- Medidas de mitigação
- Justificativa de eventual atraso

ANPD valoriza: narrativa operacional clara + impacto concreto + medidas adotadas.

### 2. Pack BACEN 24h

Reforçar:

- Impacto operacional
- Serviços críticos afetados
- Status de contingência
- Impacto em PIX / Open Finance
- Terceiros envolvidos
- Timeline objetiva do incidente

BACEN analisa: continuidade operacional + criticidade sistêmica + resposta executiva.

### 3. BCB 85/2021 Art. 6º — conceitualmente correto

Incluir:

- Evidência de treinamento
- Teste de mesa / tabletop
- Histórico de revisão da política
- Aprovação formal da alta administração

Fiscalização verifica: "o plano existe" + "o plano é executado".

## V. Disclaimer de mock-seal — parcialmente suficiente

Banner amarelo reduz risco operacional, mas **NÃO elimina responsabilidade**.

Sugestões cumulativas:

1. **Watermark persistente** em todas as páginas:
   "DOCUMENTO NÃO ASSINADO — AMBIENTE DE HOMOLOGAÇÃO"
2. **Campo interno booleano** obrigatório: `seal_status = mock`
3. **Bloqueio explícito** de exportação "production" sem TSA válido
4. **Cláusula contratual** proibindo uso regulatório de packs não selados

## VI. PII Redaction / ANPD

**Não usar** mascaramento irreversível simples (`***`) como padrão primário —
reduz auditabilidade.

**Melhor abordagem: pseudonimização determinística**:

- CPF → token hash consistente
- E-mail → identificador derivado
- Telefone → alias persistente

Permite: correlação investigativa, rastreabilidade, auditoria, minimização.

ANPD aceita melhor: minimização proporcional + pseudonimização +
segregação controlada + necessidade operacional demonstrável.

### Sugestão importante — 3 níveis de exportação

| Nível | Conteúdo |
|---|---|
| Internal Forensics | PII integral |
| Regulatory Submission | PII pseudonimizada |
| Executive Summary | PII removida |

"Extremamente defensável."

## VII. Principal risco jurídico do produto — comunicacional, não técnico

O sistema **NÃO deve**:

- Prometer aceitação pelo BACEN
- Sugerir certificação regulatória
- Afirmar validade automática
- Insinuar blindagem sancionatória

### Formulação correta (linguagem de venda segura)

O produto:

- Fortalece governança
- Aumenta auditabilidade
- Melhora preservação de evidências
- Reduz assimetria informacional
- Auxilia demonstração de diligência regulatória

## VIII. Opinião final preliminar

> "A estrutura documental apresentada possui fundamentos técnicos e
> jurídicos suficientemente sólidos para ser utilizada como mecanismo
> complementar de evidência regulatória em contextos de fiscalização
> BACEN e ANPD, especialmente para demonstração de diligência, integridade
> documental, rastreabilidade e resposta tempestiva a incidentes cibernéticos."

### Não substitui

- Obrigação regulatória
- Garantia de conformidade
- Governança humana, validação jurídica e controles internos

### Condições para valor probatório

- TSA ICP-Brasil
- Assinatura A3
- Política de retenção
- Pseudonimização
- Logging imutável
- Disclaimers adequados

> "A arquitetura demonstra maturidade acima da média observada em soluções
> tradicionais de GRC e incident response voltadas ao mercado financeiro."
