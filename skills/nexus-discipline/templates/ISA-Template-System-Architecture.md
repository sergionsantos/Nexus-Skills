---
title: "ISA-System-Architecture: [NOME DO SISTEMA / INTEGRAÇÃO]"
description: "Ideal State Artifact para arquitectura de sistemas — integrações, bridges, migrations, infra"
date: [YYYY-MM-DD]
category: nexus
tags: [isa, isa-lite, system-architecture, integration, nexus]
effort: [E3-E5]
phase: observe
mode: FULL
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-System-Architecture: [NOME DO SISTEMA / INTEGRAÇÃO]

> **Para:** Arquitectura de sistemas, bridges KB-Project, migrations, integrações de vault, infra
> **Output:** Estrutura de directórios + scripts + documentação + plano de validação
> **Processo:** nexus-discipline (7 fases). Para E5 multi-fase: um ISA por fase (nexus-discipline — cascata de ISAs).
> **Ao avançar de fase:** edita `phase:` no frontmatter (`observe→think→plan→build→execute→verify→learn→complete`).
>
> **Nota:**
> Esta template captura padrões fixos de sistemas de integração e generaliza-os para outros contextos de arquitectura de sistema. Usa como ponto de partida e adapta para o sistema em causa.

---

## 1. Goal

"[Implementar/migrar/integrar X] para [N] verticais/componentes de teste, com [artefactos Y], validado e funcional até [DATA]."

---

## 2. Problem

[O que está mal ou em falta na arquitectura actual? Que fricção cria? 2-3 frases.]

---

## 3. Vision

[Qual o estado ideal? Como seria o sistema perfeito — para agentes, para o utilizador, para manutenção futura?]

---

## 4. Out of Scope

- [ ] [O que NÃO move/altera nesta fase — específico]
- [ ] [Limitação de automatização — ex: syncs manuais com aprovação]
- [ ] [Componente que fica fora — ex: código de produto]
- [ ] [O que não se cria — ex: base de dados; filesystem + markdown + scripts]

---

## 5. Principles

1. **[Padrão de naming fixo]** — ex: README.md é o padrão, nunca MANIFEST.md ou outros nomes
2. **[Source of truth]** — ex: KB é a fonte de verdade; projecto é staging area
3. **[Preservação de histórico]** — ex: `git mv` preserva history; nunca `cp + rm`
4. **[Temporalidade]** — ex: staging é temporário; dados novos vivem em staging até validação

---

## 6. Constraints

- **Tempo:** [X horas/dias]
- **Stack:** [filesystem + markdown + scripts / ou outra]
- **Dependências:** [git, bash, outros]
- **Backward compat:** [sim/não — impacto em links internos, agentes, outros]

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis). À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool (nexus-discipline — Inline Verification Mandate).

### ISC-ARCH-01: Estrutura do Sistema
- [ ] [Componente principal criado/movido com path correcto]
- [ ] [Documento raiz no lugar correcto — ex: README.md na raiz do projecto]
- [ ] [Pasta de staging criada — ex: `staging/` para novos dados]
- [ ] [Scripts de integração criados — ex: `scripts/sync-to-X.sh`, `scripts/sync-from-X.sh`]

### ISC-DOC-01: Documentação de Arquitectura
- [ ] [Documento raiz define path canónico do componente]
- [ ] [Documento raiz define workflow de uso (passos 1-2-3-4)]
- [ ] [Secção "PARA AGENTES" com ponto de entrada explícito]
- [ ] [Secção de limitações/out-of-scope documentada]

### ISC-SCRIPT-01: Scripts Funcionais
- [ ] [Script de sync A→B: copia com backup + log]
- [ ] [Script de sync B→A: actualiza estado]
- [ ] [Scripts verificam paths antes de executar]
- [ ] [Scripts têm modo `--dry-run` para preview]

### ISC-INT-01: Integração com Sistema Maior
- [ ] [MOC / índice central actualizado com nova localização]
- [ ] [Links internos não quebram após move/criação]
- [ ] [Acessível via referência canónica a partir de qualquer ponto]

### ISC-TEST-01: Validação End-to-End
- [ ] [Vertical/componente de teste funcional (agente ou utilizador consegue usar sem explicação adicional)]
- [ ] [Zero ficheiros perdidos durante migração (se aplicável)]
- [ ] [Utilizador consegue usar o sistema sem explicação adicional]

---

## 8. Test Strategy

| ISC | Método | Ferramenta | Responsável |
|-----|--------|------------|-------------|
| ISC-ARCH-01 | Structural review + ls | bash | Autor |
| ISC-DOC-01 | Read + checklist | Manual | Autor |
| ISC-SCRIPT-01 | Dry-run execution | bash | Autor |
| ISC-INT-01 | Link check + grep | grep | Autor |
| ISC-TEST-01 | End-to-end walkthrough | Manual | Revisor |

---

## 9. Decisions

| Data | Decisão | Rationale | Alternativas Consideradas |
|------|---------|-----------|---------------------------|
| [Data] | [Decisão] | [Porquê] | [Alternativas] |

---

## 10. Verification

> Rule 0 (nexus-discipline §1): scripts e código de infra são "unattended" por natureza — revisão independente obrigatória antes de `done`.
> Re-Read Check (nexus-discipline): relê a última mensagem do utilizador verbatim e confere cada pedido contra o que shipou.

- [ ] Todos os ISC verificados com evidência de tool
- [ ] Goal atingido
- [ ] Out of Scope respeitado
- [ ] [Padrões de naming fixos seguidos — ex: README.md, não MANIFEST.md]
- [ ] Scripts revistos independentemente (code-reviewer/verifier), zero findings no diff

---

## 11. Learnings

> **Fase 7/7 (LEARN) — persistência. Preenche AQUI durante phase: learn antes de phase: complete.**
> Bloco estruturado: serve de fonte para extrair lições reutilizáveis (ver a skill `nexus-learner`).
> Ao entrar nesta fase: edita `phase:` no frontmatter para `learn`.

### 11.1 Did Differently
- (O que deveria ter sido feito de outra forma?)

### 11.2 Smarter Process
- (O que faria um processo mais inteligente?)

### 11.3 Preflight Gates Outcome
- (Quais gates dispararam? Foram úteis ou desperdício?)

### 11.4 Verification Doctrine Outcome
- (A doutrina de verificação nexus-discipline §1 apanhou alguma coisa?)

### 11.5 Reusable Insights (skill candidates)
> Cada bullet aqui é candidato a skill reutilizável. Marca com `[skill: <topic>]` para a skill `nexus-learner` o extrair.

- [skill: <topic-slug>] (princípio reusável — não código)

### 11.6 Anti-patterns Confirmed
- (Padrões que falharam — para evitar no futuro)

---

**Status:** [ ] Draft  [ ] Aprovado  [ ] Concluído
**Autor:** [Nome do Agente]
**Data:** [YYYY-MM-DD]
