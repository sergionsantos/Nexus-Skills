---
title: "ISA — Landing Page: Nexus Framework v2"
phase: observe
version: 1.0
owner: Sofia
created: 2026-05-15
migrated_to_isa: true
effort: E3
---

# ISA — Landing Page: Nexus Framework v2

## Problem
**Quem:** Developers que avaliam frameworks multi-agent
**O quê:** Página actual não transmite valor diferenciador em < 5s
**Impacto:** Bounce rate de 65%, tempo médio na página 45s
**Contexto:** Lançamento v2, concorrência com CrewAI, AutoGen

## Vision
Quando um developer chega à landing page, em 5 segundos percebe:
1. O que é o Nexus Framework
2. Porque é diferente dos outros
3. Como começar em < 10 minutos

**Estado ideal:**
- Developer não precisa de scroll para perceber o valor
- CTA "Get Started" é óbvio sem ser agressivo
- Mobile-first: 60% do tráfego é mobile

## Out of Scope
| # | Item | Porque |
|---|------|--------|
| 1 | Pricing page | Página separada, não landing |
| 2 | Blog integrado | Mantemos Ghost CMS |
| 3 | Dark mode toggle | v2.1, não v2 |

## Principles
1. **5-Segundo Rule** — Valor proposition claro em 5s
   *Exemplo:* Headline + subheadline acima da dobra
2. **Social Proof First** — GitHub stars, testimonials, logos
   *Exemplo:* Barra de logos abaixo do hero
3. **Friction Zero** — "Get Started" não pede email
   *Exemplo:* Link directo para docs / GitHub

## Constraints
- **Tempo:** 2 semanas
- **Tecnologia:** Next.js, Tailwind, Framer Motion
- **Performance:** Lighthouse > 95
- **Acessibilidade:** WCAG 2.1 AA
- **Dependências:** Copy aprovado por Sofia, assets por designer externo

## Goal
**Objectivo:** Reduzir bounce rate de 65% para < 40%
**Métrica de sucesso:** Bounce rate < 40%, tempo médio > 90s
**Prazo:** 2026-06-15
**Owner:** Sofia

## Criteria (ISC)

### ISC-QUAL-1: Valor em 5 Segundos
**Descrição:** Visitante percebe o que é e porque usar em 5s
**Teste:** Teste de 5s: mostrar página por 5s → perguntar "O que é?"
**Pass:** Resposta contém "framework" + "multi-agent" + 1 diferenciador
**Fail:** "Não sei" ou resposta genérica
**Prioridade:** Must
- [ ] Teste de 5s com 5 pessoas: resposta contém "framework" + "multi-agent" + 1 diferenciador

### ISC-PERF-1: Lighthouse > 95
**Descrição:** Performance score Lighthouse > 95
**Teste:** Correr Lighthouse CI em mobile e desktop
**Pass:** Score >= 95
**Fail:** Score < 90
**Prioridade:** Must
- [ ] Lighthouse CI em mobile e desktop devolve score >= 95

### ISC-FUNC-1: CTA Acima da Dobra
**Descrição:** Botão "Get Started" visível sem scroll
**Teste:** Abrir página em viewport 1366x768 → verificar CTA visível
**Pass:** CTA visível no primeiro viewport
**Fail:** CTA requer scroll
**Prioridade:** Must
- [ ] Playwright viewport check 1366x768: CTA visível sem scroll

### ISC-FUNC-2: Mobile-First
**Descrição:** Experiência mobile é igual ou melhor que desktop
**Teste:** Testar em iPhone 14 Pro e Android Pixel 7
**Pass:** Nenhum elemento quebrado, CTA facilmente clicável
**Fail:** Layout quebrado, CTA inacessível
**Prioridade:** Must
- [ ] Teste em iPhone 14 Pro e Android Pixel 7: zero elementos quebrados, CTA clicável

### ISC-SEC-1: WCAG 2.1 AA
**Descrição:** Passa em todas as checkpoints WCAG 2.1 AA
**Teste:** axe-core ou Lighthouse accessibility audit
**Pass:** 0 violações AA
**Fail:** Qualquer violação AA
**Prioridade:** Should
- [ ] axe-core: 0 violações WCAG 2.1 AA

### ISC-QUAL-2: Social Proof Visível
**Descrição:** GitHub stars + 2 testimonials visíveis no primeiro scroll
**Teste:** Verificar presença na página
**Pass:** Stars + 2 testimonials no hero ou imediatamente abaixo
**Fail:** Social proof ausente ou apenas numa secção inferior
**Prioridade:** Should
- [ ] GitHub stars e 2 testimonials visíveis no hero ou imediatamente abaixo da dobra

## Test Strategy
| ISC | Método | Ferramenta | Frequência |
|-----|--------|-----------|------------|
| ISC-QUAL-1 | Manual | Teste 5s com 5 pessoas | Antes de lançar |
| ISC-PERF-1 | Automático | Lighthouse CI | CI/CD |
| ISC-FUNC-1 | Automático | Playwright viewport check | CI/CD |
| ISC-FUNC-2 | Manual | Teste em devices reais | Antes de lançar |
| ISC-SEC-1 | Automático | axe-core | CI/CD |
| ISC-QUAL-2 | Manual | Revisão visual | Antes de lançar |

## Features
### F1 — Hero Section
**Descrição:** Headline, subheadline, CTA, visual abstracto
**ISC:** ISC-QUAL-1, ISC-FUNC-1
**Prioridade:** Must

### F2 — Features Grid
**Descrição:** 3 features principais com ícones e 1 frase cada
**ISC:** ISC-QUAL-1
**Prioridade:** Must

### F3 — Social Proof Bar
**Descrição:** GitHub stars, 2 testimonials, 3 logos de empresas
**ISC:** ISC-QUAL-2
**Prioridade:** Should

### F4 — Getting Started CTA
**Descrição:** Secção final com link para docs e GitHub
**ISC:** ISC-FUNC-1
**Prioridade:** Must

## Decisions
| Data | Decisão | Alternativas | Razão |
|------|---------|-------------|-------|
| 2026-05-15 | Single page (não multi-page) | Páginas separadas por feature | Foco, performance |
| 2026-05-15 | Framer Motion (não CSS puro) | CSS animations | Velocity, polish |

## Changelog
| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| 2026-05-15 | 1.0 | ISA inicial | Sofia |
| 2026-06-18 | 1.1 | Migração para nexus-discipline: frontmatter phase:, ISC-tag prefix, checkbox dialect | Revisor |

## Verification
- [ ] Todos os ISC Must passam
- [ ] Test Strategy executada
- [ ] Review por: Equipa (performance)
- [ ] Aprovado por: <nome>
- [ ] Data:
