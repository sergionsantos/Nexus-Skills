# Ledger — decisões subjectivas do humano (fase 1; consolidado após a fase 3)

Todo o item tem **default declarado** OU estado BLOQUEIA. O executor usa o default ou pára; nunca assume em silêncio.

## Gamas de ID pré-alocadas (por war-game — evita colisões em paralelo)
| Missão | Gama |
|---|---|
| ledger base (fase 1) | LEDGER-01 a 12 |
| m01 | LEDGER-13 a 18 |
| m02 | LEDGER-19 a 24 |
| m[NN] | LEDGER-[XX] a [YY] |

## Itens
| ID | Pergunta / decisão | Default declarado | Estado (DEFAULT / DECIDIDO / BLOQUEIA) | Origem (spec / mNN) |
|---|---|---|---|---|
| LEDGER-01 | [decisão] | [default] | DEFAULT | spec |

## Consolidação (após a fase 3 — o orquestrador)
Os `[LEDGER: ...]` criados dentro de cada war-game são integrados aqui, um a um, na sua gama. Conflito de granularidade (item largo vs. vários estreitos): o orquestrador decide e regista abaixo.

| Decisão de granularidade | Itens afectados | Resultado |
|---|---|---|
