---
title: "ISA-Content: [NOME DO CONTEÚDO]"
description: "Ideal State Artifact para criação de conteúdo — blog, email, newsletter, social"
date: [YYYY-MM-DD]
category: content
tags: [isa, content, blog, email, newsletter, nexus]
effort: [E2-E4]
phase: observe
mode: NATIVE
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-Content: [NOME DO CONTEÚDO]

> **Versão:** Content
> **Para:** Blog posts, emails, newsletters, threads sociais, copywriting
> **Output:** Conteúdo pronto para publicação
> **Processo:** nexus-discipline (7 fases). Ao avançar de fase: edita `phase:` no frontmatter.

---

## 1. Problem

[Que mensagem precisa ser comunicada? Que problema o conteúdo resolve?]

---

## 2. Vision

[Como seria o conteúdo perfeito? Tom, formato, reacção do leitor.]

---

## 3. Out of Scope

- [ ] Não incluir jargão sem explicação
- [ ] Não fazer claims não verificáveis
- [ ] Não exceder [N] palavras (se aplicável)
- [ ] Não desviar do tópico principal

---

## 4. Principles

1. Reader-first: o que o leitor ganha lendo isto?
2. Specific over generic: exemplos concretos > generalizações
3. One idea: um conteúdo = uma ideia principal
4. CTA clarity: leitor sabe o que fazer a seguir

---

## 5. Constraints

- **Tempo:** [X horas]
- **Formato:** [Blog / Email / Newsletter / Thread / Landing copy]
- **Tom:** [Profissional / Conversacional / Técnico / Persuasivo]
- **SEO:** [Keyword principal e volume, se aplicável]
- **Plataforma:** [Ghost / LinkedIn / X / Email tool]

---

## 6. Goal

"[Conteúdo de X palavras] sobre [tópico], com [Y características], pronto para [plataforma] até [data]."

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis). À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool (nexus-discipline — Inline Verification Mandate).

### ISC-CONT-01: Estrutura
- [ ] Título < 60 chars (blog) ou < 100 chars (email subject)
- [ ] Hook nos primeiros 2-3 frases
- [ ] 3-5 secções com headers H2 (blog) ou 2-3 blocos (email)
- [ ] Conclusão com CTA claro

### ISC-CONT-02: Conteúdo
- [ ] ≥ [N] exemplos concretos ou case studies
- [ ] ≥ [N] dados/estatísticas com fonte
- [ ] ≥ [N] insights acionáveis
- [ ] Zero fluff — cada parágrafo acrescenta valor

### ISC-CONT-03: Tom e Estilo
- [ ] Flesch Reading Ease > [N] (ou nível técnico adequado)
- [ ] Voz activa > 70% das frases
- [ ] Frases < 25 palavras (média)
- [ ] Zero erros gramaticais (Grammarly/LanguageTool)

### ISC-SEO-01: SEO (se aplicável)
- [ ] Keyword principal no título
- [ ] Keyword no primeiro parágrafo
- [ ] Meta description 150-160 chars
- [ ] Alt text em imagens (se houver)

### ISC-CONV-01: Conversão (se aplicável)
- [ ] CTA único e específico
- [ ] CTA posicionado no final (e opcionalmente no meio)
- [ ] Urgência ou escassez apenas se verdadeiras

---

## 8. Test Strategy

| ISC | Método | Ferramenta | Responsável |
|-----|--------|------------|-------------|
| ISC-CONT-01 | Structural review | Manual | Sofia |
| ISC-CONT-02 | Fact-check | perplexity.ai | Brain |
| ISC-CONT-03 | Automated | readable.com / Grammarly | Sofia |
| ISC-SEO-01 | Automated | Yoast / Lighthouse | Sofia |
| ISC-CONV-01 | Manual review | — | Sofia |

---

## 9. Verification

> Re-Read Check (nexus-discipline): relê a última mensagem do utilizador verbatim e confere cada pedido contra o que shipou.

- [ ] Todos os ISC verificados com evidência de tool
- [ ] Revisado por 2º par (se blog/newsletter)
- [ ] Formatado para plataforma de destino
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

**Status:** [ ] Draft  [ ] Em Revisão  [ ] Pronto para Publicar  [ ] Publicado
**Autor:** [Nome]
**Revisor:** [Nome]
**Data:** [YYYY-MM-DD]
