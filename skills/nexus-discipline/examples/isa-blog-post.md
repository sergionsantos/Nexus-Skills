---
title: "ISA — Blog Post: O Futuro da Memória em Agentes AI"
phase: observe
version: 1.0
owner: Sofia
created: 2026-05-10
migrated_to_isa: true
effort: E3
---

# ISA — Blog Post: "O Futuro da Memória em Agentes AI"

## Problem
**Quem:** Leitores técnicos que ouvem falar de "memória de agentes" mas não entendem as camadas
**O quê:** Conteúdo existente é ou muito superficial ou muito académico
**Impacto:** Nosso blog tem bounce rate de 70% em posts técnicos
**Contexto:** Lançamento do ProdutoX v2, queremos posicionamento thought-leader

## Vision
Quando um developer lê este post, consegue explicar as 3 camadas de memória
em agentes AI ao seu manager não-técnico, usando analogias do post.

**Estado ideal:**
- Leitor partilha o post no Slack da equipa
- Comentários incluem "finalmente percebi"
- 3+ backlinks de outros blogs em 30 dias

## Out of Scope
| # | Item | Porque |
|---|------|--------|
| 1 | Tutorial de implementação | Post é conceptual, não prático |
| 2 | Comparação com competidores | Foco no nosso approach |
| 3 | Código fonte | Manter post acessível |

## Principles
1. **Analogia First** — Cada conceito técnico tem analogia do dia-a-dia
   *Exemplo:* LTM = armazém, STM = secretária, episódica = fotografias
2. **Um Takeaway por Secção** — Leitor sai com 1 ideia clara de cada secção
   *Exemplo:* Secção "Porque falha" → "Sem LTM, agente é goldfish"

## Constraints
- **Tempo:** 1 semana (draft + review + publicação)
- **Formato:** 1500-2000 palavras, 5 minutos de leitura
- **SEO:** Keyword principal "agent memory architecture"
- **Tom:** Técnico mas acessível, nunca condescendente

## Goal
**Objectivo:** Post torna-se referência top-3 para "agent memory architecture"
**Métrica de sucesso:** > 5000 views orgânicos em 30 dias, > 50 partilhas
**Prazo:** 2026-05-30
**Owner:** Sofia

## Criteria (ISC)

### ISC-QUAL-1: Analogias Claras
**Descrição:** Cada camada de memória tem analogia que um não-técnico percebe
**Teste:** Ler post → pedir a alguém não-técnico para explicar as 3 camadas
**Pass:** Explicação correcta sem ajuda
**Fail:** "Não percebi" ou confunde camadas
**Prioridade:** Must
- [ ] Não-técnico consegue explicar as 3 camadas sem ajuda após ler o post

### ISC-QUAL-2: Estrutura Escaneável
**Descrição:** Leitor consegue absorver valor em 60 segundos de scan
**Teste:** Mostrar post a alguém por 60s → perguntar 3 takeaways
**Pass:** 2+ takeaways correctos
**Fail:** 0-1 takeaways
**Prioridade:** Must
- [ ] 2+ takeaways correctos identificados em teste de 60s

### ISC-PERF-1: SEO Optimizado
**Descrição:** Aparece na primeira página para "agent memory architecture"
**Teste:** Search Google em modo incógnito → verificar posição
**Pass:** Top 10
**Fail:** Página 2+
**Prioridade:** Should
- [ ] Post na posição Top 10 para "agent memory architecture" (verificar 7 dias após publicar)

### ISC-FUNC-1: Call to Action Efectivo
**Descrição:** > 5% dos leitores clicam no CTA (docs do ProdutoX)
**Teste:** Analytics → Events → CTA clicks / total pageviews
**Pass:** CTR > 5%
**Fail:** CTR < 2%
**Prioridade:** Should
- [ ] CTR do CTA > 5% (verificar 14 dias após publicar via Google Analytics)

### ISC-QUAL-3: Zero Jargão Não-Explicado
**Descrição:** Nenhum termo técnico aparece sem explicação imediata
**Teste:** Revisar manualmente cada termo técnico
**Pass:** Todos explicados na primeira ocorrência
**Fail:** Termo não-explicado encontrado
**Prioridade:** Must
- [ ] Revisão linha-a-linha: zero termos técnicos sem explicação na primeira ocorrência

## Test Strategy
| ISC | Método | Ferramenta | Frequência |
|-----|--------|-----------|------------|
| ISC-QUAL-1 | Manual | Teste com 2 não-técnicos | Antes de publicar |
| ISC-QUAL-2 | Manual | Teste de 60s com 3 pessoas | Antes de publicar |
| ISC-PERF-1 | Automático | Google Search + SEMrush | 7 dias após publicar |
| ISC-FUNC-1 | Automático | Google Analytics | 14 dias após publicar |
| ISC-QUAL-3 | Manual | Revisão linha-a-linha | Antes de publicar |

## Features
### F1 — Estrutura em 3 Camadas
**Descrição:** LTM, STM, Episódica — cada uma com analogia, problema, solução
**ISC:** ISC-QUAL-1, ISC-QUAL-2
**Prioridade:** Must

### F2 — Diagrama Visual
**Descrição:** SVG mostrando fluxo de dados entre camadas
**ISC:** ISC-QUAL-1
**Prioridade:** Should

### F3 — CTA no Final
**Descrição:** Link para docs do ProdutoX com copy específica
**ISC:** ISC-FUNC-1
**Prioridade:** Should

## Decisions
| Data | Decisão | Alternativas | Razão |
|------|---------|-------------|-------|
| 2026-05-10 | Foco em 3 camadas (não 6) | Todas as camadas do paper | Acessibilidade |
| 2026-05-10 | Diagrama SVG (não PNG) | Mermaid, Excalidraw | Escalável, dark mode |

## Changelog
| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| 2026-05-10 | 1.0 | ISA inicial | Sofia |
| 2026-06-18 | 1.1 | Migração para nexus-discipline: frontmatter phase:, ISC-tag prefix, checkbox dialect | Revisor |

## Verification
- [ ] Todos os ISC Must passam
- [ ] Test Strategy executada
- [ ] Review por: <nome> (clareza técnica)
- [ ] Aprovado por: <nome>
- [ ] Data:
