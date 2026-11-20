# Tier Guide — E1 a E5

> Tabela de referência para classificação de effort e requisitos mínimos por tier.
> Âncora doutrinária: `references/effort-and-process.md` §1 (calibração).
> Template: `nexus-discipline/templates/Tier-Guide.md`

---

## Tabela Principal

| Tier | Budget | ISC Floor (soft) | Revisão independente | ISA | Processo 7-fases | Quando Usar |
|------|--------|------------------|----------------------|-----|------------------|-------------|
| **E1** trivial/mecânico | <90s | nenhum | ❌ (só se unattended) | ❌ | ❌ | rename, 1 comando, facto binário |
| **E2** pequeno | <3min | 5-8 (ISA-Lite) | ⚠️ código não-trivial/unattended → Rule 0; resto → opcional | ⚠️ ISA-Lite opcional | ❌ | edit 1 ficheiro, fix óbvio |
| **E3** substancial | <10min | 8-12 | ✅ obrigatória p/ código | ✅ ISA-Lite/Full | ✅ condensado | multi-ficheiro, análise, design |
| **E4** complexo | <30min | 12-15 | ✅ + critic do plano | ✅ ISA-Full | ✅ completo | arquitectura, refactor grande |
| **E5** multi-fase | <120min+ | 15 (cascata de ISAs) | ✅ + cross-vendor audit | ✅ cascata (1/fase) | ✅ completo + tracking | migração, build multi-fase |

**Regra mecânica:** tarefa **mecânica E não-criativa** → E1, independentemente de outros sinais. Não monta artefacto para um typo.

**Precedência Rule 0:** para deliverables de **código**, a coluna *Revisão independente* é sempre regida pela Rule 0 (SKILL.md §1) — dispara para código não-trivial OU unattended em qualquer tier.

---

## Notas do Tier Guide

### Time Budget
O time budget é a constraint principal do tier. O ISC floor é um mínimo orientador na dimensão contagem — não uma barreira dura que bloqueia tiers mais baixos de ter ISCs úteis.

### Sobre "thinking floors"
nexus-discipline **não usa** floors numéricos de thinking capabilities nem a closed enumeration PAI (IterativeDepth, ApertureOscillation, etc.). A profundidade de raciocínio é calibrada pelo effort level do modelo (configuração `effortLevel: xhigh|max` do agente para E4/E5) — não por contar nomes proprietários. Seleccionar capabilities a partir de uma lista fechada era uma abstracção de uma versão anterior, abandonada; remover previne phantom capabilities por copy-paste.

### Delegation
A delegação (subagentes, ferramentas especializadas) é encorajada em E3+ mas não tem floor numérico fixo. A pergunta operacional é: *"Consigo fazer isto com Glob+Grep em <30s?"* Se não → considera delegar ou pedir aprovação do plano.

### Tier Intent
O utilizador deve sentir uma amplitude de velocidade dramática entre tiers. E1 é a via rápida — <90s, doutrina leve. E2 é estruturado-mas-ágil. E3 é o tier médio substancial. E4/E5 são onde a doutrina completa — critic do plano, advisor calls, cross-vendor audit, verificação aprofundada — justifica o custo. Nunca deixar que a cerimónia consuma o budget; o único motivo aceitável para gastar o tempo de um tier é o trabalho em si.

---

## Tier Completeness Gate — Secções ISA Requeridas

| Tier | Secções requeridas |
|------|--------------------|
| **E1** | Goal, Criteria |
| **E2** | Problem, Goal, Criteria, Test Strategy |
| **E3** | Problem, Vision, Out of Scope, Constraints, Goal, Criteria, Features, Test Strategy |
| **E4** | Todas as 12 |
| **E5** | Todas as 12 + workflow de entrevista antes de BUILD |

### As 12 Secções do ISA (ordem fixa)

1. `## Problem` — O que está partido ou em falta agora
2. `## Vision` — Como é o estado ideal atingido
3. `## Out of Scope` — Anti-visão — o que não está incluído
4. `## Principles` — Verdades substrate-independentes
5. `## Constraints` — Mandatos arquitecturais imóveis
6. `## Goal` — Espinha hard-to-vary — 1-3 frases que nomeiam done verificável
7. `## Criteria` — ISCs atómicos (um binary tool probe cada)
8. `## Test Strategy` — Abordagem de verificação por ISC
9. `## Features` — Work breakdown
10. `## Decisions` — Log de decisões com timestamp
11. `## Changelog` — Conjecture / refuted-by / learned
12. `## Verification` — Evidência por ISC

> ISA-Lite (E2-E3 simples): Problem · Goal · Criteria (5-8) · Out-of-Scope · Verification — 30s de setup.
> ISA-Full (E3 complexo, E4, E5): todas as 12 secções.
> E5 multi-fase: um ISA por fase, cross-linked ("Pré-requisito de" / "Sucessor de"). Nunca um monolítico para N fases.

---

## Frontmatter `phase:` — OBRIGATÓRIO em todos os ISAs

Todos os ISAs produzidos neste tier devem ter `phase:` no YAML frontmatter, avançando por:

```
observe → think → plan → build → execute → verify → learn → complete
```

Mantém `phase:` actualizado. (Opcional: só se tiveres hooks/gates que leiam `phase:` — nesse caso, omiti-lo faz esses gates ignorarem o ISA; esses gates não vêm com esta skill.)

---

## Quick Reference Card

```
E1: <90s,   ISC nenhum,  sem revisão obrigatória, Goal+Criteria
E2: <3min,  ISC 5-8,     Rule 0 se código,         +Problem+Test Strategy
E3: <10min, ISC 8-12,    revisão obrigatória p/ código, +Vision+OoS+Constraints+Features
E4: <30min, ISC 12-15,   revisão + critic do plano, todas as 12 secções
E5: <120min+, ISC 15,    revisão + cross-vendor,    todas as 12 + entrevista + cascata ISAs
```

---

**Fonte doutrinária:** `references/effort-and-process.md` §1 (Calibração), §3 (Artefacto ISA); SKILL.md §1 (Doutrina de Verificação)  
**Reconciliado de:** Algorithm v6.3.0 (Daniel Miessler / PAI) — dropped: closed capability enumeration, PAI numeric thinking-floors  
**Data:** 2026-06-18
