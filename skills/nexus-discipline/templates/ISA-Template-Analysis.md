---
title: "ISA-Analysis: [NOME DO CONTEÚDO]"
description: "Ideal State Artifact para análise de vídeos, podcasts, ou conteúdo multimédia"
date: [YYYY-MM-DD]
category: analysis
tags: [isa, analysis, video, podcast, nexus]
effort: [E2-E4]
phase: observe
mode: NATIVE
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-Analysis: [NOME DO CONTEÚDO]

> **Versão:** Analysis
> **Para:** Análise de vídeos, podcasts, webinars, entrevistas, cursos em vídeo
> **Input:** URL do vídeo / ficheiro / transcrição
> **Processo:** nexus-discipline (7 fases). Ao avançar de fase: edita `phase:` no frontmatter.

---

## 1. Problem

[O que precisamos extrair deste conteúdo? Porquê?]

---

## 2. Vision

[Qual o output ideal? Resumo? Notas? Action items? Quotes?]

---

## 3. Out of Scope

- [ ] Não transcrever manualmente (usar Whisper/transcrição automática)
- [ ] Não incluir timestamps a menos que solicitado
- [ ] Não adicionar opinião pessoal — apenas factos do conteúdo
- [ ] Não reproduzir conteúdo protegido por copyright na íntegra

---

## 4. Principles

1. Source-first: toda afirmação ligada a timestamp ou secção
2. Actionable: output deve ser utilizável sem rever o vídeo
3. Structured: formato consistente para comparação entre análises

---

## 5. Constraints

- **Tempo:** [X minutos/horas]
- **Formato:** [Markdown / Notion / Obsidian]
- **Idioma:** [PT / EN / outro]
- **Ferramenta:** [Whisper / yt-dlp / manual]

---

## 6. Goal

"[Análise estruturada de X minutos de conteúdo] com [Y elementos] extraídos, pronta em [tempo]."

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis). À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool (nexus-discipline — Inline Verification Mandate).

### ISC-ANAL-01: Estrutura da Análise
- [ ] Sumário executivo < 200 palavras no topo
- [ ] 3-7 secções principais identificadas com headers H2
- [ ] Cada secção tem 2-5 bullet points de conteúdo chave
- [ ] Conclusão ou "key takeaway" no final

### ISC-ANAL-02: Conteúdo Extraído
- [ ] ≥ [N] insights acionáveis identificados
- [ ] ≥ [N] quotes relevantes com contexto
- [ ] ≥ [N] referências a recursos/ferramentas mencionados
- [ ] ≥ [N] conceitos-chave definidos (se técnico)

### ISC-ANAL-03: Precisão
- [ ] Zero afirmações não presentes no conteúdo original
- [ ] Termos técnicos mantidos no idioma original (se aplicável)
- [ ] Nomes próprios e entidades verificados

### ISC-FORM-01: Formatação
- [ ] Markdown válido com hierarquia clara
- [ ] Links para recursos mencionados (se disponíveis online)
- [ ] Tags/categorias no frontmatter para descoberta futura

---

## 8. Test Strategy

| ISC | Método | Ferramenta | Responsável |
|-----|--------|------------|-------------|
| ISC-ANAL-01 | Review estrutural | Manual | Brain |
| ISC-ANAL-02 | Cross-check com transcrição | grep + manual | Brain |
| ISC-ANAL-03 | Fact-check amostral | perplexity.ai | Brain |
| ISC-FORM-01 | Lint markdown | markdownlint | Autor |

---

## 9. Verification

> Re-Read Check (nexus-discipline): relê a última mensagem do utilizador verbatim e confere cada pedido contra o que shipou.

- [ ] Todos os ISC verificados com evidência de tool
- [ ] Análise revisada contra conteúdo original (amostra)
- [ ] Formato consistente com análises anteriores
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

**Status:** [ ] Draft  [ ] Concluído
**Autor:** [Nome]
**Data:** [YYYY-MM-DD]
