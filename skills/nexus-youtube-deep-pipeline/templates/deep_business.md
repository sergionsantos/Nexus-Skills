# Deep Template: Business / AI / Health

For business, ai-tech, health, and real-estate content where the focus is on operational frameworks, technical depth, or system design rather than personal journey.

## Output structure

```markdown
---
title: "[Topic]: [Hook from the talk]"
channel: "[[People/[Channel-Name]]]"
source: "[Channel Display Name]"
date: "[YYYY-MM-DD]"
url: "[video URL]"
language: "[EN]"
duration: "[HH:MM:SS]"
tema_principal: "[One-sentence: what is the central technical/operational claim]"
tags:
  - [primary domain: business/ai-tech/health/real-estate]
  - [guest-name]
  - [key frameworks, e.g. pricing, growth, agents]
  - [specific tools, e.g. RAG, MCP, hiring]
content_type: "[business|ai-tech|health|real-estate]"
topics:
  - [6-10 specific topics]
has_quotes: true
---

# [Title] — Knowledge Document

## Sumário

[3 paragraphs: 1) what the guest is building / has built; 2) the central technical or operational challenge; 3) the framework or approach the guest advocates.]

## Conceitos e Princípios Centrais

### 1. [Concept Name]
- **O que é:** [definition, 1-2 sentences]
- **Como se manifesta na prática:** [concrete example from the guest's work, with metrics if available]
- **Por que importa:** [the leverage / consequence]
- **Aplicação paradoxal:** [edge case or non-obvious implication]

### [12-15 concepts]

## Frameworks e Modelos

### [Framework Name]
- **Inputs:** [what goes in]
- **Process:** [what happens]
- **Outputs:** [what comes out]
- **Failure modes:** [what breaks the framework]

### [3-5 frameworks]

## Armadilhas e Erros Comuns

### [Trap Name]
- **Trigger:** [what initiates the pattern]
- **Manifestação:** [how it shows up]
- **Impacto:** [consequence]
- **Antídoto/Solução:** [what breaks the pattern]

### [10-13 traps]

## Ferramentas e Técnicas Práticas

### [Tool/Technique Name]
- **Descrição:** [what it is]
- **Como aplicar:** [concrete steps]
- **Quando usar:** [specific situations]
- **Custo / recursos:** [what it takes to deploy]

### [10-11 tools]

## Citações Mais Fortes

> "[Quote 1]"
> "[Quote 2]"
[15-20 quotes, grouped by theme]

## Aplicação Prática

### Esta Semana
- [ ] [5-8 actions]

### Prática Contínua
- [ ] [5-8 ongoing practices]

## Linha Pessoal (Breve)

[3-5 sub-sections if guest shared biographical content. Skip entirely if no bio.]

## Metadados Internos

- **Qualidade da extracção:** [Excelente/Boa]
- **Temas principais:** [list]
- **Sessão tipo:** [Interview/Talk/Keynote]
```

## Generation prompt

```
You are processing a business, AI, or health interview. The focus is OPERATIONAL FRAMEWORKS and TECHNICAL DEPTH, not personal biography (unless guest shares significant personal content).

**Constraints:**
- Counts and sizes below are ceilings for a 90+ minute source. The SIZING block appended after this template gives the real numbers for this transcript and overrides them.
- 12-15 concepts with the 4-part structure.
- 3-5 explicit frameworks with Inputs/Process/Outputs/Failure modes.
- 10-13 traps with 4-part structure.
- 10-11 tools with Descrição/Como aplicar/Quando usar/Custo.
- 15-20 verbatim quotes, grouped by theme.
- Ad reads / sponsor segments EXCLUDED.

**Bio section:** only include if guest shared substantial personal content (e.g., founder story, illness recovery). If interview is purely technical, skip entirely.

**Verification:** all numbers, names, tool versions, book titles must match transcript.

**Format:** YAML frontmatter, H1, then sections in the order above.
```
