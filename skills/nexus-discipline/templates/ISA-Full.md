---
title: "ISA-Full: [NOME DA TAREFA]"
description: "Ideal State Artifact Full — 12 campos completos para tarefas E4-E5"
date: [YYYY-MM-DD]
category: [categoria]
tags: [isa, isa-full, nexus]
effort: [E4-E5]
phase: observe
mode: FULL
path: ".isa/ISA-[nome-da-tarefa].md"
---

> **Proveniência:** Estrutura derivada de PAI v5.0.0 (Daniel Miessler) — 12 secções fixas, ordem canónica.
> Processo de execução: nexus-discipline (7 fases completas). Calibração: nexus-discipline E4-E5.
> Ao avançar de fase: edita `phase:` no frontmatter (`observe→think→plan→build→execute→verify→learn→complete`).

# ISA-Full: [NOME DA TAREFA]

> **Versão:** Full (12 campos)
> **Para:** Tarefas complexas (E4-E5), multi-fase, ou com alto risco de ambiguidade
> **Tempo de criação:** 5-10 minutos

---

## 1. Problem

[Descrever o problema actual. O que está errado? O que falta? 2-3 frases.]

---

## 2. Vision

[Descrever o estado ideal. Como seria se fosse perfeito? Não mencionar solução técnica.]

---

## 3. Out of Scope

- [ ] [O que NÃO fazer 1 — específico]
- [ ] [O que NÃO fazer 2 — específico]
- [ ] [O que NÃO fazer 3 — específico]
- [ ] [O que NÃO fazer 4 — específico]
- [ ] [O que NÃO fazer 5 — específico]

---

## 4. Principles

1. [Princípio 1 — formato "Noun over Noun"]
2. [Princípio 2 — ordenado por prioridade]
3. [Princípio 3]
4. [Princípio 4 — opcional]

---

## 5. Constraints

- **Tempo:** [X horas/dias/semanas]
- **Budget:** [X euros ou "não aplicável"]
- **Tecnologia:** [stack obrigatória ou "não aplicável"]
- **Dependências:** [bloqueios externos ou "nenhum"]
- **Infra:** [limitações de infraestrutura ou "não aplicável"]

---

## 6. Goal

[Mensurável, específico, com deadline — formato SMART]

Exemplo: "Criar API REST para gestão de tarefas com autenticação JWT, documentação OpenAPI, testes >80% coverage, deploy em Docker até 2026-05-20."

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis, granulares, independentes). Mínimo 5, ideal 10-15, máximo ~15.
> À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool no mesmo bloco (nexus-discipline EXECUTE — Inline Verification Mandate).
> Linguagem PROIBIDA ao marcar: "should work", "looks fine", "done" (sem evidência de tool) — nexus-discipline

### ISC-FUNC-01: [Categoria Funcional]
- [ ] [Critério binário 1 — subject + verbo + condição]
- [ ] [Critério binário 2]
- [ ] [Critério binário 3]

### ISC-FUNC-02: [Categoria Funcional 2]
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

### ISC-PERF-01: [Categoria Performance]
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

### ISC-QUAL-01: [Categoria Qualidade]
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

### ISC-SEC-01: [Categoria Segurança]
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

### ISC-DOC-01: [Categoria Documentação]
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

---

## 8. Test Strategy

| ISC | Método de Teste | Ferramenta | Responsável |
|-----|-----------------|------------|-------------|
| ISC-FUNC-01 | [Método] | [Ferramenta] | [Agente] |
| ISC-PERF-01 | [Método] | [Ferramenta] | [Agente] |
| ISC-QUAL-01 | [Método] | [Ferramenta] | [Agente] |

---

## 9. Features

- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] [Feature 3]
- [ ] [Feature 4]
- [ ] [Feature 5]

---

## 10. Decisions

| Data | Decisão | Rationale | Alternativas Consideradas |
|------|---------|-----------|---------------------------|
| [Data] | [Decisão] | [Porquê] | [Alternativas] |

---

## 11. Changelog

| Versão | Data | Alterações |
|--------|------|------------|
| 0.1 | [Data] | [Alterações] |

---

## 12. Verification

> Rule 0 (nexus-discipline §1): para deliverables de código não-trivial ou unattended, revisão independente (code-reviewer/verifier) obrigatória antes de `done`. Dá ao revisor spec+output, não o teu raciocínio.
> Advisor (opcional): para E4+, Advisor antes de te comprometeres com abordagem e após deliverable durável.
> Cross-vendor audit (opcional): após advisor e antes de `complete`.
> Re-Read Check: relê a última mensagem do utilizador verbatim e confere cada pedido contra o que shipou.

- [ ] Todos os ISC verificados com evidência (screenshots/logs/tool output)
- [ ] Test strategy foi executada
- [ ] Out of Scope foi respeitado
- [ ] Principles foram seguidos
- [ ] Goal foi atingido
- [ ] Decisions documentadas
- [ ] Para código não-trivial/unattended: revisão independente corrida, zero findings no diff
- [ ] Re-Read Check: cada pedido explícito conferido (nenhum `✗` pendente)

---

## 13. Learnings

> **Fase 7/7 (LEARN) — persistência. Preenche AQUI durante phase: learn antes de phase: complete.**
> Bloco estruturado: serve de fonte para extrair lições reutilizáveis (ver a skill `nexus-learner`).
> Ao entrar nesta fase: edita `phase:` no frontmatter para `learn`.

### 13.1 Did Differently
- (O que deveria ter sido feito de outra forma?)

### 13.2 Smarter Process
- (O que faria um processo mais inteligente?)

### 13.3 Preflight Gates Outcome
- (Quais gates dispararam? Foram úteis ou desperdício?)

### 13.4 Verification Doctrine Outcome
- (A doutrina de verificação nexus-discipline §1 apanhou alguma coisa?)

### 13.5 Reusable Insights (skill candidates)
> Cada bullet aqui é candidato a skill reutilizável. Marca com `[skill: <topic>]` para a skill `nexus-learner` o extrair.

- [skill: <topic-slug>] (princípio reusável — não código)

### 13.6 Anti-patterns Confirmed
- (Padrões que falharam — para evitar no futuro)

---

**Status:** [ ] Draft  [ ] Em Revisão  [ ] Aprovado  [ ] Concluído
**Autor:** [Nome]
**Revisor:** [Nome]
**Data:** [YYYY-MM-DD]
