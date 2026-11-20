---
title: "ISA-Research: [NOME DO TÓPICO]"
description: "Ideal State Artifact para research profundo e investigação"
date: [YYYY-MM-DD]
category: research
tags: [isa, research, deep-dive, nexus]
effort: [E3-E5]
phase: observe
mode: FULL
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-Research: [NOME DO TÓPICO]

> **Versão:** Research
> **Para:** Research profundo, investigação, due diligence, literature review
> **Output:** Relatório estruturado com fontes verificáveis
> **Processo:** nexus-discipline (7 fases). Ao avançar de fase: edita `phase:` no frontmatter.

---

## 1. Problem

[Que pergunta precisamos responder? Que gap de conhecimento existe?]

---

## 2. Vision

[Qual o estado ideal de conhecimento? Relatório completo? Apenas resposta?]

---

## 3. Out of Scope

- [ ] Não incluir opinião pessoal sem marcação clara
- [ ] Não citar fontes não verificáveis (blogs sem autor, fóruns)
- [ ] Não extrapolar além dos dados apresentados
- [ ] Não ignorar evidência contraditória

---

## 4. Principles

1. Evidence over opinion: dados > opinião sempre
2. Source hierarchy: peer-reviewed > institucional > jornalismo > blog
3. Uncertainty quantified: quando não há certeza, dizer "desconhecido"
4. Bias awareness: identificar potenciais conflitos de interesse nas fontes

---

## 5. Constraints

- **Tempo:** [X horas/dias]
- **Fontes:** [mínimo N fontes, tipos preferidos]
- **Idioma:** [PT / EN / ambos]
- **Profundidade:** [overview / intermediate / expert]

---

## 6. Goal

"[Responder a pergunta X] com [N fontes verificáveis], [formato Y], pronto em [tempo]."

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis). À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool (nexus-discipline — Inline Verification Mandate).
> Reflexo grounding (nexus-discipline): fundamenta-te na realidade primeiro — fetch a fonte real, não confies na memória do modelo.

### ISC-RES-01: Fontes
- [ ] ≥ [N] fontes primárias (estudos, papers, dados oficiais)
- [ ] ≥ [N] fontes secundárias (análises, reviews)
- [ ] Todas as fontes com URL ou referência completa
- [ ] Nenhuma fonte > [N] anos sem justificação (se aplicável)

### ISC-RES-02: Estrutura
- [ ] Pergunta de research claramente definida no início
- [ ] Sumário executivo < 300 palavras
- [ ] 3-7 secções com headers H2
- [ ] Conclusão que responde directamente à pergunta
- [ ] Secção "Limitações" que identifica gaps

### ISC-RES-03: Rigor
- [ ] Dados quantitativos com fonte citada
- [ ] Afirmações qualitativas com exemplo concreto
- [ ] Evidência contraditória mencionada (se existir)
- [ ] Nenhuma generalização além do que as fontes suportam

### ISC-RES-04: Actionability
- [ ] ≥ [N] recomendações baseadas em evidência
- [ ] Cada recomendação ligada a fonte(s) específica(s)
- [ ] "Next steps" ou "further research needed" no final

---

## 8. Test Strategy

| ISC | Método | Ferramenta | Responsável |
|-----|--------|------------|-------------|
| ISC-RES-01 | Source verification | Manual + archive.org | Brain |
| ISC-RES-02 | Structural review | Checklist | Brain |
| ISC-RES-03 | Fact-check amostral | perplexity.ai + manual | Brain |
| ISC-RES-04 | Actionability review | Manual | Revisor |

---

## 9. Verification

> Re-Read Check (nexus-discipline): relê a última mensagem do utilizador verbatim e confere cada pedido contra o que shipou.
> Flag UNVERIFIED (nexus-discipline): se uma fonte não pôde ser verificada, marca explicitamente — nunca disfarces de verificado.

- [ ] Todos os ISC verificados com evidência de tool
- [ ] Fontes verificáveis (URLs testados)
- [ ] Pergunta original respondida directamente
- [ ] Goal atingido

---

## 10. Learnings

> **Fase 7/7 (LEARN) — persistência. Preenche AQUI durante phase: learn antes de phase: complete.**
> Bloco estruturado: serve de fonte para extrair lições reutilizáveis (ver a skill `nexus-learner`).
> Ao entrar nesta fase: edita `phase:` no frontmatter para `learn`.

### 10.1 Did Differently
- (O que deveria ter sido feito de outra forma?)

### 10.2 Smarter Process
- (O que faria um processo mais inteligente?)

### 10.3 Preflight Gates Outcome
- (Quais gates dispararam? Foram úteis ou desperdício?)

### 10.4 Verification Doctrine Outcome
- (A doutrina de verificação nexus-discipline §1 apanhou alguma coisa?)

### 10.5 Reusable Insights (skill candidates)
> Cada bullet aqui é candidato a skill reutilizável. Marca com `[skill: <topic>]` para a skill `nexus-learner` o extrair.

- [skill: <topic-slug>] (princípio reusável — não código)

### 10.6 Anti-patterns Confirmed
- (Padrões que falharam — para evitar no futuro)

---

**Status:** [ ] Draft  [ ] Em Revisão  [ ] Concluído
**Autor:** [Nome]
**Revisor:** [Nome]
**Data:** [YYYY-MM-DD]
