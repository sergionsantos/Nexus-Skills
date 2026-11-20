# Deep Template: Biography

For trader-biography or person-centred interviews where the **guest's life journey** is the central thread. The output is structured around the timeline rather than thematic frameworks.

## Output structure

```markdown
---
title: "[Guest Name] on [Their Defining Lesson]: [Hook]"
channel: "[[People/[Channel-Name]]]"
source: "[Channel Display Name]"
date: "[YYYY-MM-DD]"
url: "[video URL]"
language: "[EN]"
duration: "[HH:MM:SS]"
tema_principal: "[One-sentence: who is the guest, what did they do, what did they learn]"
tags:
  - trader-biography
  - [guest-name]
  - [asset-class if relevant: futures/forex/stocks/crypto]
  - [their-approach: scalping/swing/position]
  - [psychology themes if relevant]
content_type: "trader-biography"
trader: "[Guest Name]"
instrument: "[forex|futures|stocks|crypto|options|general]"
topics:
  - [6-10 specific topics: their origin, defining trade, lessons, market view]
has_quotes: true
---

# [Title] — Knowledge Document

## Sumário

[3 paragraphs: 1) who is the guest, their track record; 2) the journey arc from start to now; 3) the central lesson from their story.]

## Percurso e Contexto (Bio Completo)

- **Origem:** [where they come from, family, education, pre-trading life]
- **Background profissional:** [jobs, education, failures before trading]
- **Estilo de trading:** [scalping, swing, position; instruments; timeframes]
- **Marcos relevantes:** [notable results, payouts, year, year]
- **Setup actual:** [current capital, current approach, current business]

## Timeline Detalhada (Idade/Ano + Evento)

[15-20 entries with the chronological life path. Each entry: age/year + what happened + impact.]

## Principais Lições do Percurso

### [Lesson 1 — short title]
- **Contexto:** [at what stage this lesson emerged]
- **O que aprendeu:** [concrete insight]
- **Como aplica:** [how it manifests in current trading]
- **Citação verbatim:** [direct quote from the guest]

### [5-8 lessons, each with the 4-part structure above]

## Erros e Obstáculos

### [Error/Obstacle]
- **O que aconteceu:** [concrete description with numbers if available]
- **Impacto:** [consequence — financial, psychological, career]
- **Como superou:** [what changed or how resolved]
- **Citação verbatim:** [their words on the mistake]

### [5-8 errors total]

## Psicologia e Mentalidade

### [Psychological theme 1]
- **Como este trader experiencia o problema:** [concrete, in their voice]
- **O que descobriu:** [insight or practice]
- **Aplicação prática:** [how it translates to daily trading]
- **Citação verbatim:** [their words on the psychology]

### [3-5 themes]

## Estratégia e Abordagem ao Mercado

### [Strategy element 1]
- **O que é:** [description of setup or concept]
- **Como identifica:** [entry conditions/context]
- **Gestão da trade:** [stops, targets, position management]

### [3-5 strategy elements]

## Filosofia de Trading

[Paragraph describing the trader's market vision — what works, what doesn't, what most traders get wrong. 3-4 paragraphs.]

## Citações Mais Fortes

> "[Quote 1 — most impactful line of the interview]"
> "[Quote 2]"
[15-20 quotes, in chronological order or grouped by theme]

## Aplicação Prática (Para Traders em Desenvolvimento)

- [Specific advice 1]
- [Specific advice 2]
- [5-8 pieces of advice, all with concrete actions]

## Metadados Internos

- **Qualidade da extracção:** [Excelente/Boa]
- **Temas principais:** [list]
- **Nível do trader:** [Retail/Professional/Institutional]
- **Sessão tipo:** Interview
```

## Generation prompt

```
You are processing a trader-biography or person-centred interview. The output is structured around the guest's LIFE JOURNEY, not abstract frameworks.

**Constraints:**
- Counts and sizes below are ceilings for a 90+ minute source. The SIZING block appended after this template gives the real numbers for this transcript and overrides them.
- The Percurso e Contexto section is the centrepiece — reconstruct from dispersed fragments.
- Timeline Detalhada: 15-20 entries chronologically. Use age markers ("at 26", "before 25") and explicit years when stated. If not stated, write "circa [year]" not invented specifics.
- Principais Lições: 5-8 lessons, each with 4-part structure + verbatim quote.
- Erros e Obstáculos: 5-8 with 4-part structure + quote.
- Citações Mais Fortes: 15-20 quotes, not paraphrased.
- Ad reads / sponsor segments EXCLUDED.

**Verification:** every dollar amount, year, payout, person name, and book title must match the transcript. Fabricated specifics are unacceptable.

**Format:** YAML frontmatter, H1, then sections in the order above.
```
