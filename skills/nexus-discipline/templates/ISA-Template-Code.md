---
title: "ISA-Code: [NOME DA FEATURE/API]"
description: "Ideal State Artifact para tarefas técnicas — APIs, features, scripts, infra"
date: [YYYY-MM-DD]
category: code
tags: [isa, code, api, feature, technical, nexus]
effort: [E2-E5]
phase: observe
mode: FULL
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-Code: [NOME DA FEATURE/API]

> **Versão:** Code
> **Para:** APIs, features, scripts, refactors, configuração, DevOps
> **Output:** Código + documentação + testes
> **Processo:** nexus-discipline (7 fases). Ao avançar de fase: edita `phase:` no frontmatter.
> **Nota Rule 0 (nexus-discipline §1):** todo o deliverable de código não-trivial ou que corre sozinho (hooks, crons, serviços, prod) requer revisão independente antes de `done` — não esperar que seja pedida.

---

## 1. Problem

[O que está quebrado ou missing? Qual dor técnica?]

---

## 2. Vision

[Como seria o sistema perfeito? Performance, UX dev, manutenibilidade.]

---

## 3. Out of Scope

- [ ] Não alterar [componente X] (separado)
- [ ] Não adicionar features não solicitadas
- [ ] Não quebrar backward compatibility (se aplicável)
- [ ] Não introduzir novas dependências sem justificação

---

## 4. Principles

1. Test-first: testes antes ou junto com código
2. Simplicity: solução mais simples que funciona
3. Observability: logs, métricas, tracing por omissão
4. Security: never trust input, validate everything

---

## 5. Constraints

- **Tempo:** [X horas/dias]
- **Stack:** [linguagem/framework obrigatório]
- **Infra:** [onde corre — local/VPS/cloud]
- **Dependências:** [libs/frameworks já disponíveis]
- **Backward compat:** [sim/não — se sim, como]

---

## 6. Goal

"[Feature X] implementada com [Y critérios], [testes Z%], documentada, deployed até [data]."

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis, granulares, independentes).
> À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool no mesmo bloco (nexus-discipline — Inline Verification Mandate).
> Linguagem PROIBIDA ao marcar: "should work", "looks fine", "done" (sem evidência de tool) — nexus-discipline

### ISC-FUNC-01: Funcionalidade Core
- [ ] [Feature 1 — critério binário]
- [ ] [Feature 2 — critério binário]
- [ ] [Feature 3 — critério binário]

### ISC-FUNC-02: Edge Cases
- [ ] [Edge case 1 — comportamento definido]
- [ ] [Edge case 2 — comportamento definido]

### ISC-PERF-01: Performance
- [ ] [Métrica binária — ex: p95 < 200ms]
- [ ] [Métrica binária — ex: memória < 512MB]

### ISC-QUAL-01: Qualidade de Código
- [ ] Cobertura de testes > [N]%
- [ ] Linting zero warnings ([ferramenta])
- [ ] Type hints / static analysis pass
- [ ] Complexidade ciclomática < [N] por função

### ISC-SEC-01: Segurança
- [ ] Input validation em todos os endpoints/inputs
- [ ] Secrets em env vars (nunca hardcoded)
- [ ] SQL injection / XSS / CSRF mitigados
- [ ] Rate limiting implementado

### ISC-DOC-01: Documentação
- [ ] README com setup, env vars, exemplos
- [ ] API docs (OpenAPI / docstrings)
- [ ] CHANGELOG.md entry

### ISC-DEP-01: Deploy
- [ ] Funciona em ambiente de staging
- [ ] CI/CD passa (se aplicável)
- [ ] Rollback plan definido

---

## 8. Test Strategy

| ISC | Método | Ferramenta | Responsável |
|-----|--------|------------|-------------|
| ISC-FUNC-01 | Unit + integration tests | pytest / jest | Autor |
| ISC-PERF-01 | Benchmark / load test | k6 / locust | Autor |
| ISC-QUAL-01 | Static analysis | ruff / mypy / eslint | Autor |
| ISC-SEC-01 | Security scan | bandit / semgrep | Autor |
| ISC-DEP-01 | Deploy test | CI/CD pipeline | Autor |

---

## 9. Features

- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] [Feature 3]
- [ ] [Feature 4]
- [ ] [Feature 5]

---

## 10. Decisions

| Data | Decisão | Rationale | Alternativas |
|------|---------|-----------|--------------|
| [Data] | [Decisão] | [Porquê] | [Alternativas] |

---

## 11. Verification

> Rule 0 (nexus-discipline §1): revisão independente (code-reviewer/verifier) obrigatória para código não-trivial ou unattended. Dá ao revisor spec+output, não o teu raciocínio. Itera até zero findings no diff.
> Linguagem de estado honesta: "implementado, happy-path testado, por rever" (intermédio) vs "revisto independente + limpo, done" (só este é done).

- [ ] Todos os ISC verificados com evidência de tool
- [ ] Testes passam (CI green)
- [ ] Revisão de código independente corrida (code-reviewer/verifier), zero findings no diff
- [ ] Deploy em staging validado
- [ ] Goal atingido
- [ ] Re-Read Check: cada pedido explícito conferido contra o que shipou

---

## 12. Learnings

> **Fase 7/7 (LEARN) — persistência. Preenche AQUI durante phase: learn antes de phase: complete.**
> Bloco estruturado: serve de fonte para extrair lições reutilizáveis (ver a skill `nexus-learner`).
> Ao entrar nesta fase: edita `phase:` no frontmatter para `learn`.

### 12.1 Did Differently
- (O que deveria ter sido feito de outra forma?)

### 12.2 Smarter Process
- (O que faria um processo mais inteligente?)

### 12.3 Preflight Gates Outcome
- (Quais gates dispararam? Foram úteis ou desperdício?)

### 12.4 Verification Doctrine Outcome
- (A doutrina de verificação nexus-discipline §1 apanhou alguma coisa?)

### 12.5 Reusable Insights (skill candidates)
> Cada bullet aqui é candidato a skill reutilizável. Marca com `[skill: <topic>]` para a skill `nexus-learner` o extrair.

- [skill: <topic-slug>] (princípio reusável — não código)

### 12.6 Anti-patterns Confirmed
- (Padrões que falharam — para evitar no futuro)

---

**Status:** [ ] Draft  [ ] Em Desenvolvimento  [ ] Code Review  [ ] Aprovado  [ ] Deployed
**Autor:** [Nome]
**Revisor:** [Nome]
**Data:** [YYYY-MM-DD]
