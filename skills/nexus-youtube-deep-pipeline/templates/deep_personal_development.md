# Deep Template: Personal Development

For interviews or monologues with a single guest sharing life advice, mindset, relationships, or personal growth content. Any length: the SIZING block appended to the prompt scales the output to the transcript. Designed for content types: `personal-development`.

## Output structure

```markdown
---
title: "[Guest] on [Central Theme]: [Hook]"
channel: "[[People/[Channel-Name]]]"
source: "[Channel Display Name]"
date: "[YYYY-MM-DD]"
url: "[video URL]"
language: "[EN/PT/ES]"
duration: "[HH:MM:SS]"
tema_principal: "[One-sentence distillation: who is the guest, what is the central claim, why does it matter]"
tags:
  - personal-development
  - [guest-name]
  - [primary-frameworks, e.g. decision-making, long-term-thinking]
  - [life-stage, e.g. fatherhood, marriage, mortality]
  - [guest-domain, e.g. business, philosophy, trading]
content_type: "personal-development"
topics:
  - [6-10 specific topics, e.g. "doors-metaphor", "doors-metaphor", "long-term-thinking", "fatherhood"]
has_quotes: true
---

# [Title] — Knowledge Document

## Sumário

[3 paragraphs: 1) who is the guest + their credibility; 2) the central question/tension; 3) what makes the conversation distinctive and what the listener should take away. No vague jargon. No "motivational" tone.]

## Conceitos e Princípios Centrais

### 1. [Framework Name]
- **O que é:** [clear definition, 1-2 sentences]
- **Como se manifesta na prática:** [concrete example from the transcript, with names/dates if relevant]
- **Por que importa:** [the leverage — what changes if you adopt this]
- **Aplicação paradoxal:** [the non-obvious implication or edge case]

### 2-15. [repeat above structure, 12-15 total]

## Armadilhas e Auto-sabotagem

### [Trap Name]
- **Trigger:** [what initiates the pattern]
- **Manifestação:** [how it shows up behaviourally]
- **Impacto:** [consequence — financial, psychological, relational]
- **Antídoto/Solução:** [what breaks the pattern]

### [10-13 traps total]

## Ferramentas & Técnicas Práticas

### [Tool Name]
- **Descrição:** [what it is, 1-2 sentences]
- **Como aplicar:** [concrete steps, ideally with the guest's own words]
- **Quando usar:** [specific situations]

### [10-11 tools total]

## Mudanças de Mindset

| De (Abordagem Comum / Reactiva) | Para (Abordagem Correcta / Intencional) |
|---|---|
| [25+ rows of De→Para transitions] |

## Sinais de Alarme

- ⚠️ [25+ warning signs the person is stuck in the wrong pattern]

## Aplicação Prática

### Esta Semana
- [ ] [5-8 concrete actions for the next 7 days]

### Prática Contínua
- [ ] [5-8 ongoing practices]

### [Optional: On Specific Topic]
- [ ] [3-5 practices for a specific life area like parenting, marriage, career]

## A Linha Pessoal (Contexto Biográfico)

[10+ sub-sections reconstructing the guest's life from dispersed fragments. Each sub-section is a specific event or era with verbatim quotes. Examples:]
- Family background (parents, upbringing)
- Career origin story
- Defining failure or setback
- Key relationships (partner, mentor, friend)
- Recent loss or transformation
- Current state

## Citações Relevantes

### [Theme Group 1]
> "[Verbatim quote 1]"
> "[Verbatim quote 2]"

### [Theme Group 2]
[repeat for 8-12 theme groups, 40+ total quotes]

## Timeline Emocional (Guest)

| Período | Evento | Resposta Operacional |
|---|---|---|
| [8+ entries: age/year, what happened, how they responded] |

## Estrutura por Capítulo (Timestamps Aproximados)

| Capítulo | Início | Conteúdo Central |
|---|---|---|
| [5-7 rows mapping the video structure] |

## Conceitos-Âncora (Para Linking Interno)

- [[Guest Name]]
- [[Concept 1]]
- [[Concept 2]]
[15-20 wikilinks]

## Metadados Internos

- **Qualidade da extracção:** [Excelente/Boa/Razoável]
- **Temas principais:** [5-8 themes]
- **Nível:** [Beginner/Intermediate/Advanced]
- **Sessão tipo:** [Interview/Monologue/Keynote]
- **Notas de extracção:** [extraction notes: dedup applied, ad reads excluded, fact-check coverage]
```

## Generation prompt (for LLM)

```
You are processing a personal-development interview transcript. Your task is to produce a knowledge document that captures **maximum density** of usable insight.

**Constraints:**
- Counts and sizes below are ceilings for a 90+ minute source. The SIZING block appended after this template gives the real numbers for this transcript and overrides them.
- 12-15 frameworks in "Conceitos Centrais", each with the 4-part structure (O que é / Como se manifesta / Por que importa / Aplicação paradoxal).
- 10-13 traps in "Armadilhas e Auto-sabotagem" with the 4-part structure (Trigger / Manifestação / Impacto / Antídoto).
- 10-11 tools in "Ferramentas & Técnicas" with the 3-part structure (Descrição / Como aplicar / Quando usar).
- 25+ De→Para rows in "Mudanças de Mindset" (as a markdown table).
- 25+ bullet points in "Sinais de Alarme".
- 10+ sub-sections in "A Linha Pessoal" reconstructing the guest's biography from dispersed fragments.
- 40+ verbatim quotes in "Citações Relevantes", grouped by theme (8-12 groups).
- 8+ entries in "Timeline Emocional" with date/age + event + operational response.
- 5-7 chapter rows in "Estrutura por Capítulo".
- 15-20 wikilinks in "Conceitos-Âncora".
- Ad reads / sponsor segments are EXCLUDED. Look for paragraphs with 2+ sponsor keywords and skip them.

**Verbatim quotes:** every quote in Citações Relevantes must be a DIRECT QUOTE from the transcript, not a paraphrase. Use the guest's own words. Include the surrounding context (1-2 sentences) so the quote is interpretable.

**Bio reconstruction:** fragments like "my dad", "when I was 26", "I met my wife" appear in different parts of the transcript. Reconstruct chronologically with date/age markers when available. If a date is not explicit, write "circa [year]" rather than invent.

**Numbers and names:** verify every dollar amount, year, person name, and book title against the transcript. Fabricated specifics are the #1 failure mode.

**Format:** start with the YAML frontmatter (closing `---`), then the H1 title, then sections in the order above. Output ONLY the markdown document, no preamble.
```

## Quality bar

- Clearly denser than surface processing; size set by the SIZING block
- 100% of numeric claims verifiable
- 0 ad reads in output
- Verbatim quotes preserved up to the SIZING count
- Bio timeline complete (or noted as "fragmentary" if insufficient data)
