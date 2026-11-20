---
title: "ISA — Curso em Vídeo: Multi-Agent Systems do Zero"
phase: observe
version: 1.0
owner: <nome>
created: 2026-05-20
migrated_to_isa: true
effort: E4
---

# ISA — Curso em Vídeo: "Multi-Agent Systems do Zero"

## Problem
**Quem:** Developers que querem aprender a construir sistemas multi-agent mas não sabem por onde começar
**O quê:** Cursos existentes são ou teóricos demais ou usam frameworks proprietários
**Impacto:** 80% dos alunos abandonam cursos de AI antes do módulo 3
**Contexto:** Lançamento da Nexus Academy, queremos diferenciação prática

## Vision
Quando um developer completa este curso, consegue construir um sistema multi-agent funcional
com 3 agentes comunicantes, deployado, em produção, em 1 dia.

**Estado ideal:**
- Aluno termina todos os módulos (completion rate > 80%)
- Aluno deploya projeto próprio em < 24h após conclusão
- Reviews mencionam "finalmente um curso prático"

## Out of Scope
| # | Item | Porque |
|---|------|--------|
| 1 | Teoria de LLMs | Foco em arquitetura, não fundamentos |
| 2 | Fine-tuning de modelos | Fora de scope técnico |
| 3 | Certificação formal | MVP sem burocracia |
| 4 | Comunidade/forum | Discord já existe |

## Principles
1. **Mão na Massa** — Cada módulo tem exercício prático deployável
   *Exemplo:* Módulo 2 → aluno tem 2 agentes a conversar via API
2. **Stack Open Source** — Nada proprietário, tudo replicável
   *Exemplo:* Usar uma framework open-source de agentes, não plataformas pagas
3. **Progressão Rápida** — Primeiro agente em < 30 minutos
   *Exemplo:* Módulo 1 = "Hello World" de agente em 15 min

## Constraints
- **Tempo:** 6 semanas (produção), 4 horas totais de conteúdo
- **Formato:** 8 módulos, 20-30 min cada, + exercícios
- **Tecnologia:** framework open-source de agentes, Node.js, Python
- **Orçamento:** 0€ software, 500€ edição de vídeo
- **Plataforma:** YouTube (gratuito) + Gumroad (pago com extras)

## Goal
**Objectivo:** Curso torna-se referência prática para multi-agent systems
**Métrica de sucesso:** > 1000 alunos em 90 dias, completion rate > 80%, NPS > 50
**Prazo:** 2026-07-31
**Owner:** <nome>

## Criteria (ISC)

### ISC-FUNC-1: Primeiro Agente em 30 Min
**Descrição:** Aluno tem primeiro agente funcional em < 30 min do início
**Teste:** Testar com 3 developers juniores: tempo até "agente responde"
**Pass:** < 30 minutos
**Fail:** > 45 minutos
**Prioridade:** Must
- [ ] Teste com 3 developers juniores: todos atingem "agente responde" em < 30 minutos

### ISC-FUNC-2: Deploy Funcional
**Descrição:** Aluno consegue deployar sistema multi-agent em produção
**Teste:** Último módulo inclui deploy real (Render/Railway/self-hosted)
**Pass:** Aluno consegue aceder ao sistema via URL pública
**Fail:** Deploy falha ou requer conhecimento não ensinado
**Prioridade:** Must
- [ ] Aluno acede ao sistema via URL pública após seguir o módulo de deploy

### ISC-PERF-1: Completion Rate > 80%
**Descrição:** > 80% dos alunos que começam terminam todos os módulos
**Teste:** Analytics da plataforma → completion rate
**Pass:** > 80%
**Fail:** < 60%
**Prioridade:** Must
- [ ] Analytics da plataforma: completion rate >= 80% (verificar semana 4 após lançamento)

### ISC-QUAL-1: NPS > 50
**Descrição:** Net Promoter Score > 50 (promoters - detractors)
**Teste:** Survey no final do curso
**Pass:** NPS >= 50
**Fail:** NPS < 30
**Prioridade:** Should
- [ ] Survey final: NPS >= 50 (verificar mensalmente)

### ISC-SEC-1: Zero Dependências Pagas
**Descrição:** Todo o stack é open source ou free tier
**Teste:** Listar todas as ferramentas usadas → verificar custo
**Pass:** 100% free / open source
**Fail:** Qualquer ferramenta paga obrigatória
**Prioridade:** Must
- [ ] Auditoria de dependências: 100% das ferramentas são free / open source

### ISC-FUNC-3: Exercícios Auto-Graduados
**Descrição:** Exercícios têm verificação automática (pass/fail)
**Teste:** Cada exercício tem script de validação
**Pass:** Aluno corre script → sabe se passou
**Fail:** Correção manual ou subjectiva
**Prioridade:** Should
- [ ] Cada exercício tem script de validação que devolve pass/fail sem intervenção humana

## Test Strategy
| ISC | Método | Ferramenta | Frequência |
|-----|--------|-----------|------------|
| ISC-FUNC-1 | Manual | Teste com 3 juniors | Antes de lançar |
| ISC-FUNC-2 | Manual | Testar deploy pipeline | Antes de lançar |
| ISC-PERF-1 | Automático | Plataforma analytics | Semanalmente |
| ISC-QUAL-1 | Automático | Typeform / SurveyMonkey | Mensalmente |
| ISC-SEC-1 | Manual | Auditoria de dependências | Antes de lançar |
| ISC-FUNC-3 | Automático | Scripts de validação | CI/CD |

## Features
### F1 — Módulo 1: Hello Agent
**Descrição:** Primeiro agente com a framework escolhida em 15 min
**ISC:** ISC-FUNC-1
**Prioridade:** Must

### F2 — Módulo 4: Multi-Agent Chat
**Descrição:** 3 agentes a comunicar via gateway
**ISC:** ISC-FUNC-1, ISC-FUNC-2
**Prioridade:** Must

### F3 — Módulo 8: Deploy em Produção
**Descrição:** Deploy completo com Docker + health checks
**ISC:** ISC-FUNC-2
**Prioridade:** Must

### F4 — Sistema de Exercícios
**Descrição:** Repo com exercícios + scripts de validação
**ISC:** ISC-FUNC-3
**Prioridade:** Should

## Decisions
| Data | Decisão | Alternativas | Razão |
|------|---------|-------------|-------|
| 2026-05-20 | YouTube + Gumroad | Udemy, Teachable | Alcance + controlo |
| 2026-05-20 | 8 módulos (não 12) | Curso completo | MVP, velocidade |
| 2026-05-20 | uma framework open-source de agentes | LangChain, CrewAI | Stack escolhida |

## Changelog
| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| 2026-05-20 | 1.0 | ISA inicial | Autor |
| 2026-06-18 | 1.1 | Migração para nexus-discipline: frontmatter phase:, ISC-tag prefix, checkbox dialect | Revisor |

## Verification
- [ ] Todos os ISC Must passam
- [ ] Test Strategy executada
- [ ] Review por: Equipa (técnico)
- [ ] Aprovado por: <nome>
- [ ] Data:
