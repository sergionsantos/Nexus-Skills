---
title: "ISA-Design: [NOME DO DESIGN]"
description: "Ideal State Artifact para design visual — UI, UX, branding, presentations"
date: [YYYY-MM-DD]
category: design
tags: [isa, design, ui, ux, visual, nexus]
effort: [E2-E4]
phase: observe
mode: NATIVE
path: ".isa/ISA-[nome-da-tarefa].md"
---

# ISA-Design: [NOME DO DESIGN]

> **Versão:** Design
> **Para:** UI design, UX flows, branding, presentations, landing pages, mockups
> **Output:** Figma / HTML / PPTX / assets visuais
> **Processo:** nexus-discipline (7 fases). Ao avançar de fase: edita `phase:` no frontmatter.

---

## 1. Problem

[Que problema de design resolvemos? Usability? Brand? Conversão?]

---

## 2. Vision

[Como seria o design perfeito? Sensação, estética, funcionalidade.]

---

## 3. Out of Scope

- [ ] Não redesignar [componente X] (fora do scope)
- [ ] Não criar novas ilustrações do zero (usar stock/existentes)
- [ ] Não animações complexas (apenas transitions simples)
- [ ] Não multi-language nesta fase

---

## 4. Principles

1. Function over form: design serve o objectivo
2. Consistency: seguir design system existente
3. Accessibility: WCAG AA mínimo
4. Mobile-first: 60%+ tráfego é mobile

---

## 5. Constraints

- **Tempo:** [X horas/dias]
- **Formato:** [Figma / HTML+CSS / PPTX / Canva]
- **Brand:** [guidelines a seguir]
- **Assets:** [disponíveis / a criar / stock]
- **Plataformas:** [desktop / mobile / ambos]

---

## 6. Goal

"[Design X] para [propósito], com [Y características], entregue em [formato] até [data]."

---

## 7. Criteria (ISC)

> Critérios binários (sim/não, testáveis). À medida que cada ISC passa: `- [ ]` → `- [x]` com evidência de tool (nexus-discipline — Inline Verification Mandate).

### ISC-DES-01: Layout e Composição
- [ ] Grid consistente (8px ou design system)
- [ ] Hierarquia visual clara (tamanho, cor, espaçamento)
- [ ] White space adequado (não cluttered)
- [ ] Alinhamento consistente (esquerda/central)

### ISC-DES-02: Tipografia
- [ ] Máximo 2 font families
- [ ] Escala tipográfica definida (H1, H2, body, caption)
- [ ] Legibilidade: line-height ≥ 1.5 para body text
- [ ] Contraste suficiente (WCAG AA)

### ISC-DES-03: Cores
- [ ] Paleta limitada a 3-5 cores principais
- [ ] Cores seguem brand guidelines (ou justificação)
- [ ] Estado de hover/focus/active definido para interactivos
- [ ] Dark mode considerado (se aplicável)

### ISC-DES-04: Componentes
- [ ] Botões: 3 estados (default, hover, disabled)
- [ ] Form inputs: label, placeholder, error state
- [ ] Cards/containers: padding consistente, shadow/border
- [ ] Icons: estilo consistente (filled/outline), tamanho padronizado

### ISC-UX-01: Usabilidade
- [ ] Flow principal completável em < [N] passos
- [ ] Feedback visual para acções (loading, success, error)
- [ ] Empty states considerados
- [ ] Error states com mensagem acionável

### ISC-ACC-01: Acessibilidade
- [ ] Contraste WCAG AA (4.5:1 texto normal, 3:1 UI components)
- [ ] Focus indicators visíveis
- [ ] Alt text para todas as imagens
- [ ] Navegação por teclado possível (se aplicável)

### ISC-PERF-01: Performance Visual
- [ ] Assets optimizados (< 200KB cada imagem)
- [ ] SVG para icons (quando possível)
- [ ] Web fonts com fallback system fonts

---

## 8. Test Strategy

| ISC | Método | Ferramenta | Responsável |
|-----|--------|------------|-------------|
| ISC-DES-01 | Visual review | Figma / Browser | Sofia |
| ISC-DES-02 | Automated | Stark plugin / Lighthouse | Sofia |
| ISC-DES-03 | Brand review | Manual | Sofia |
| ISC-UX-01 | User flow test | Manual / Maze | Sofia |
| ISC-ACC-01 | Automated | axe-core / Lighthouse | Autor |
| ISC-PERF-01 | Asset audit | Manual + squoosh | Autor |

---

## 9. Features

- [ ] [Screen/Component 1]
- [ ] [Screen/Component 2]
- [ ] [Screen/Component 3]
- [ ] [Screen/Component 4]
- [ ] [Screen/Component 5]

---

## 10. Verification

> Re-Read Check (nexus-discipline): relê a última mensagem do utilizador verbatim e confere cada pedido contra o que shipou.

- [ ] Todos os ISC verificados com evidência de tool
- [ ] Review com stakeholder (o dono do projecto ou lead)
- [ ] Testado em múltiplos dispositivos/tamanhos
- [ ] Assets exportados no formato correcto
- [ ] Goal atingido

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

**Status:** [ ] Draft  [ ] Em Revisão  [ ] Aprovado  [ ] Entregue
**Autor:** [Nome]
**Revisor:** [Nome]
**Data:** [YYYY-MM-DD]
