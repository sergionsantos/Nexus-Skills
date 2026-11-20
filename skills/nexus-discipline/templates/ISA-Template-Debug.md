---
title: "ISA-Debug: [DESCRIÇÃO DO BUG]"
description: "Ideal State Artifact para investigação de bugs, debugging, e diagnóstico técnico"
date: [YYYY-MM-DD]
category: debug
tags: [isa, isa-lite, debug, bug, technical, nexus]
effort: [E2-E3]
phase: observe
mode: MINIMAL
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-Debug: [DESCRIÇÃO DO BUG]

> **Para:** Bugs intermitentes, falhas de parsing, edge cases de regex, problemas de provider
> **NÃO para:** Feature development (usar ISA-Template-Code.md) ou research (usar ISA-Template-Research.md)
> **Processo:** nexus-discipline condensado. Ao avançar de fase: edita `phase:` no frontmatter.
> **Nota Rule 0 (nexus-discipline §1):** fix de bug é código — revisão independente antes de `done` se não-trivial ou unattended.

---

## 1. Goal

[Descrever o bug em 1-2 frases. Incluir: o que falha, quando falha, e o output esperado vs actual.]

Exemplo: "Identificar root cause da falha intermitente onde blocos `<tool_use>{...}</tool_use>` chegam como TEXT em vez de serem executados, e propor fix + test."

---

## 2. Out of Scope

- [ ] Não alterar componentes não relacionados sem evidência
- [ ] Não implementar fix sem teste reproducer
- [ ] Não abrir PR/issue sem diagnóstico confirmado

---

## 3. Principles

1. Logs first — evidência antes de hipóteses
2. Reproducer obrigatório — sem reproducer, não há fix
3. Verificação independente — não confiar só em self-reports de subagentes

---

## 4. Criteria (ISC)

> Critérios binários (sim/não, testáveis). À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool (nexus-discipline — Inline Verification Mandate).
> Linguagem PROIBIDA ao marcar: "should work", "looks fixed", "done" (sem evidência de tool) — nexus-discipline

### ISC-DEBUG-01: Localização do código
- [ ] Ficheiro(s) suspeitos identificados com path + número de linha
- [ ] Função/método responsável pelo comportamento mapeado

### ISC-DEBUG-02: Diagnóstico técnico
- [ ] Root cause identificado (ex: regex edge case, race condition, provider quirk)
- [ ] Evidência de logs ou reproducer confirmando o diagnóstico

### ISC-DEBUG-03: Proposta de fix
- [ ] Fix proposto com diff ou linha de código alterada
- [ ] Justificação técnica do porquê resolve o root cause

### ISC-DEBUG-04: Teste reproducer
- [ ] Teste que reproduz o bug (ou explicação porquê é não-determinístico)
- [ ] Instruções para validar o fix

### ISC-DEBUG-05: Documentação
- [ ] Issue/PR preparada com diagnóstico completo (se confirmado)
- [ ] Nota técnica para futura referência

---

## 5. Verification

> Rule 0 (nexus-discipline §1): fix de código não-trivial ou unattended requer revisão independente antes de `done`.
> Loop de recuperação (nexus-discipline): se fix não resolve, diagnostica novamente — nunca re-emitir o mesmo comando que falhou.

- [ ] Todos os ISC verificados com evidência (paths, logs, diff, test output)
- [ ] Goal atingido: diagnóstico completo com fix proposto e testado
- [ ] Out of Scope respeitado
- [ ] Para código não-trivial/unattended: revisão independente corrida e limpa

---

## 6. Learnings

> **Fase 7/7 (LEARN) — persistência. Preenche AQUI durante phase: learn antes de phase: complete.**
> Bloco estruturado: serve de fonte para extrair lições reutilizáveis (ver a skill `nexus-learner`).
> Ao entrar nesta fase: edita `phase:` no frontmatter para `learn`.

### 6.1 Did Differently
- (O que deveria ter sido feito de outra forma?)

### 6.2 Smarter Process
- (O que faria um processo mais inteligente?)

### 6.3 Preflight Gates Outcome
- (Quais gates dispararam? Foram úteis ou desperdício?)

### 6.4 Verification Doctrine Outcome
- (A doutrina de verificação nexus-discipline §1 apanhou alguma coisa?)

### 6.5 Reusable Insights (skill candidates)
> Cada bullet aqui é candidato a skill reutilizável. Marca com `[skill: <topic>]` para a skill `nexus-learner` o extrair.

- [skill: <topic-slug>] (princípio reusável — não código)

### 6.6 Anti-patterns Confirmed
- (Padrões que falharam — para evitar no futuro)

---

**Status:** [ ] Draft  [ ] Aprovado  [ ] Concluído
**Autor:** [Nome do Agente]
**Data:** [YYYY-MM-DD]
