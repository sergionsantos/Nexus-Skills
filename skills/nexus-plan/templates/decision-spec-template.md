# Decision-Spec — <tema> (regime JIT)

> Autor: <tier forte>, <data>. Expansão em steps por <tier médio>, milestone a milestone,
> JUST-IN-TIME (só se expande M-n+1 quando M-n fecha). Grounding: <análise/relatório> —
> expansores CITAM, PROIBIDO re-explorar.

## Objectivo (1 frase)

## Decisões LOCKED (não re-decidir na expansão)

| # | Decisão | Racional |
|---|---|---|
| D1 | <tudo o que forçaria o expansor a improvisar: escolhas de alvo, mecanismos, canais, formatos, limites> | <porquê / que finding evita> |

<!-- Incluir SEMPRE que aplicável: gate humano por acção pública/irreversível (nunca automatizável);
constraint de runtime (portabilidade: markdown + python3 stdlib); regra de dados pessoais/legal. -->

## Milestones (intenção; expandir just-in-time)

**M0 — <nome> (<risco: sem exposição / com gate>; <esforço>)**
Intenção: <2-3 linhas>.
Critérios de aceitação (binários, ticados só com evidência): <binários, verificáveis, com negative control onde há checker novo>.

**M1..Mn — idem**

## Non-goals (expansor não toca)

## Riscos & mitigação

## Contrato de expansão (para o tier médio)

Paths pinados: <absolutos; desambiguar gémeos>.
1 milestone por vez. Formato por step: Goal · Files · Implementation (concreta) ·
Verify (predict-then-run, exit codes) · If-fails. Máx ~120 linhas/milestone.
Decisões locked invioláveis; ambiguidade fora delas → PÁRA. Gates humanos nunca automatizáveis.

## Estado
- [ ] Spec revisto pelo critic (1 passe)
- [ ] M0 · [ ] M1 · ...
