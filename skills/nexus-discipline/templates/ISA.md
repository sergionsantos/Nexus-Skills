---
title: "ISA: [Nome do Projecto]"
description: "Ideal State Artifact base — 12 secções canónicas para tarefas E3+"
date: [YYYY-MM-DD]
category: [categoria]
tags: [isa, nexus]
effort: [E3-E5]
phase: observe
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA: [Nome do Projecto]

**Versão:** 1.0  
**Data:** YYYY-MM-DD  
**Autor:** [nome]  
**Status:** Draft  
**Path:** `.isa/ISA-[nome-da-tarefa].md`

> **Proveniência:** Estrutura derivada de PAI v5.0.0 (Daniel Miessler) — 12 secções fixas, ordem canónica.
> Processo de execução: nexus-discipline (7 fases). Critérios: ISC binários (nexus-discipline).

---

## Problem

**Quem:** [persona]  
**O quê:** [problema]  
**Impacto:** [custo]  
**Contexto:** [onde/quando]

---

## Vision

Quando [persona] usa [artefacto], consegue [resultado]
sem [fricção].

**Estado ideal:**
- [descrição vívida]
- [o que desapareceu]
- [o que apareceu]

---

## Out of Scope

| # | Item | Porque |
|---|------|--------|
| 1 | | |
| 2 | | |

---

## Principles

1. **[Nome]** — [descrição]
   *Exemplo:*

2. **[Nome]** — [descrição]
   *Exemplo:*

---

## Constraints

- **Tempo:**
- **Orçamento:**
- **Tecnologia:**
- **Compliance:**
- **Dependências:**

---

## Goal

**Objectivo:**  
**Métrica de sucesso:**  
**Prazo:**  
**Owner:**

---

## Criteria (ISC)

> Critérios binários (sim/não, testáveis, granulares, independentes). Formato: `### ISC-[CATEGORIA]-[N]: [descrição]`.
> Categorias típicas: FUNC, PERF, QUAL, SEC, DOC. Mínimo 5, ideal 10-15.
> À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool no mesmo bloco (nexus-discipline EXECUTE).

### ISC-FUNC-01: [Categoria Funcional]
- [ ] [Critério binário 1 — subject + verbo + condição]
- [ ] [Critério binário 2]

### ISC-FUNC-02: [Categoria Funcional 2]
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

### ISC-PERF-01: [Categoria Performance]
- [ ] [Critério binário — ex: p95 < 200ms]

### ISC-QUAL-01: [Categoria Qualidade]
- [ ] [Critério binário]

### ISC-SEC-01: [Categoria Segurança]
- [ ] [Critério binário]

### ISC-DOC-01: [Categoria Documentação]
- [ ] [Critério binário]

---

## Test Strategy

| ISC | Método | Ferramenta | Frequência |
|-----|--------|-----------|------------|
| ISC-FUNC-01 | | | |
| ISC-PERF-01 | | | |
| ISC-QUAL-01 | | | |

---

## Features

### F1 — [Nome]
**Descrição:**  
**ISC relacionados:**  
**Prioridade:**  
**Notas:**

---

## Decisions

| Data | Decisão | Alternativas | Razão |
|------|---------|-------------|-------|
| | | | |

---

## Changelog

| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| | | | |

---

## Verification

> Rule 0 (nexus-discipline §1): para deliverables de código não-trivial ou unattended, revisão independente obrigatória antes de `done`.
> Inline Verification Mandate: nenhum ISC transita para `[x]` sem evidência de tool capturada no bloco que o reivindica.

- [ ] Todos os ISC Must passam (com evidência de tool)
- [ ] Test Strategy executada
- [ ] Para código não-trivial/unattended: revisão independente (code-reviewer/verifier) corrida e limpa
- [ ] Re-Read Check: última mensagem do utilizador relida verbatim, cada pedido conferido contra o que shipou
- [ ] Review por:
- [ ] Aprovado por:
- [ ] Data:

---

## Learnings

> **Fase 7/7 (LEARN) — persistência. Preenche AQUI durante phase: learn antes de phase: complete.**
> Bloco estruturado: serve de fonte para extrair lições reutilizáveis (ver a skill `nexus-learner`).
> Ao entrar nesta fase: edita `phase:` no frontmatter para `learn`.

### 1. Did Differently
- (O que deveria ter sido feito de outra forma?)

### 2. Smarter Process
- (O que faria um processo mais inteligente?)

### 3. Preflight Gates Outcome
- (Quais gates dispararam? Foram úteis ou desperdício?)

### 4. Verification Doctrine Outcome
- (A doutrina de verificação nexus-discipline §1 apanhou alguma coisa?)

### 5. Reusable Insights (skill candidates)
> Cada bullet aqui é candidato a skill reutilizável. Marca com `[skill: <topic>]` para a skill `nexus-learner` o extrair.

- [skill: <topic-slug>] (princípio reusável — não código)

### 6. Anti-patterns Confirmed
- (Padrões que falharam — para evitar no futuro)

---

**Status:** [ ] Draft  [ ] Em Revisão  [ ] Aprovado  [ ] Concluído  
**Autor:** [Nome]  
**Revisor:** [Nome]  
**Data:** [YYYY-MM-DD]
