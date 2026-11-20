---
title: "ISA — API de Autenticação v2"
phase: observe
version: 1.0
owner: Equipa
created: 2026-05-01
migrated_to_isa: true
effort: E4
---

# ISA — API de Autenticação v2

## Problem
**Quem:** Developers que integram com a nossa plataforma
**O quê:** Auth v1 usa tokens opacos sem refresh — apps quebram a cada 24h
**Impacto:** 30% dos tickets de suporte são "token expirado"
**Contexto:** 200+ integrações activas, crescendo 20/mês

## Vision
Quando um developer integra a nossa API, a autenticação funciona
invisivelmente durante meses sem intervenção manual.

**Estado ideal:**
- Nenhum ticket "token expirado" em 90 dias
- Developer configura uma vez, esquece
- Refresh automático sem código adicional do cliente

## Out of Scope
| # | Item | Porque |
|---|------|--------|
| 1 | OAuth2 social (Google, GitHub) | Foco em API keys primeiro |
| 2 | MFA para API calls | Roadmap Q3, não v2 |
| 3 | Rate limiting por endpoint | Já existe em gateway |

## Principles
1. **Backward Compatible** — v1 tokens continuam a funcionar
   *Exemplo:* v1 tokens válidos por 30 dias adicionais
2. **Zero Config** — refresh automático, sem headers especiais
   *Exemplo:* Cliente envia token velho, recebe novo no response

## Constraints
- **Tempo:** 4 semanas
- **Tecnologia:** Node.js, Redis para blacklist
- **Compliance:** Tokens não podem conter PII
- **Dependências:** Equipa de infra precisa de Redis cluster

## Goal
**Objectivo:** Reduzir tickets "token expirado" de 30% para < 5% em 90 dias
**Métrica de sucesso:** < 5% tickets auth-related
**Prazo:** 2026-06-30
**Owner:** Equipa

## Criteria (ISC)

### ISC-FUNC-1: Refresh Automático
**Descrição:** Cliente recebe novo access token sem pedir explicitamente
**Teste:** Enviar request com token a expirar em < 5 min → response inclui novo token
**Pass:** Novo token presente no header `X-New-Token`
**Fail:** Token expira, cliente recebe 401
**Prioridade:** Must
- [ ] Novo token presente no header `X-New-Token` quando token expira em < 5 min

### ISC-FUNC-2: Backward Compatibility
**Descrição:** Tokens v1 continuam válidos
**Teste:** Enviar request com token v1 → deve passar
**Pass:** 200 OK
**Fail:** 401 Unauthorized
**Prioridade:** Must
- [ ] Request com token v1 devolve 200 OK

### ISC-SEC-1: Blacklist Funcional
**Descrição:** Tokens revogados são rejeitados imediatamente
**Teste:** Revogar token → enviar request em < 1s → deve falhar
**Pass:** 401 Unauthorized
**Fail:** 200 OK (token ainda válido)
**Prioridade:** Must
- [ ] Token revogado rejeitado com 401 em < 1s após revogação

### ISC-PERF-1: Latência de Refresh
**Descrição:** Refresh não adiciona latência perceptível
**Teste:** Medir tempo de request com refresh vs sem refresh
**Pass:** Delta < 50ms
**Fail:** Delta > 100ms
**Prioridade:** Should
- [ ] Delta de latência com refresh < 50ms medido em k6

## Test Strategy
| ISC | Método | Ferramenta | Frequência |
|-----|--------|-----------|------------|
| ISC-FUNC-1 | Automático | Postman + Newman | CI/CD |
| ISC-FUNC-2 | Automático | Jest | CI/CD |
| ISC-SEC-1 | Automático | Jest + Redis mock | CI/CD |
| ISC-PERF-1 | Automático | k6 | Nightly |

## Features
### F1 — Refresh Middleware
**Descrição:** Intercepta tokens a expirar, gera novo, inclui no response
**ISC:** ISC-FUNC-1, ISC-PERF-1
**Prioridade:** Must

### F2 — Blacklist Service
**Descrição:** Redis SET com TTL, check O(1)
**ISC:** ISC-SEC-1
**Prioridade:** Must

## Decisions
| Data | Decisão | Alternativas | Razão |
|------|---------|-------------|-------|
| 2026-05-01 | Refresh no response header | Body JSON | Menos breaking change |
| 2026-05-02 | Redis em vez de DB | PostgreSQL | Latência < 1ms necessária |

## Changelog
| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| 2026-05-01 | 1.0 | ISA inicial | Autor |
| 2026-06-18 | 1.1 | Migração para nexus-discipline: frontmatter phase:, ISC-tag prefix, checkbox dialect | Revisor |

## Verification
- [ ] Todos os ISC Must passam
- [ ] Test Strategy executada
- [ ] Review por: Raquel (segurança)
- [ ] Aprovado por: <nome>
- [ ] Data:
