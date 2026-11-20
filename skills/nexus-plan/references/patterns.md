# 10 padrões dos traços (evidência por padrão)

1. **"Contexto dado como verificado" no brief do critic** — lista de factos ground já pagos; o critic re-verifica só o que ataca. Evidência: um critic re-contou dois pools de IDs (147+36) e mesmo assim ficou em ~80k tokens; apanhou 2 HIGH.
2. **"NÃO ataques X" explícito** (mérito já decidido pelo dono, estilo) — zero findings desperdiçados em 3/3 critics.
3. **Fixes de critic aplicados pelo arquitecto, sem 2º passe** — REVISE com fixes mecânicos convergiu em 1 ronda 4/4 vezes; re-ronda só se BLOCKER estrutural.
4. **Verifies críticos nomeados um a um no pedido de report** — o executor omite negative controls se não forem pedidos explicitamente.
5. **Idle-sem-report = modo de falha nº1** (3/3 runs com subagente): protocolo = spot-check em disco (1 comando composto) → ping dirigido com o que falta. Nunca assumir done nem falha pelo idle.
6. **Predict-then-run pedido explicitamente produz desvios honestos** — o executor auto-corrigiu 2 textos de verify imprecisos DECLARANDO-os; noutro run reportou um typo do plano em vez de improvisar.
7. **Steps do orquestrador/humano fora da sequência do executor** — BLOCKER real: um step de revisão na sequência levaria o executor a preencher scores não-revistos para desbloquear o próprio verify. Ownership por step + pergunta de ownership no critic.
8. **Colunas de juízo não se delegam** — dados citáveis (dossier, resumo) são do tier médio; contexto do dono (fit estratégico, prioridades, copy pública) é do tier forte/humano. Uma coluna "Fit" foi revista 2× pelo orquestrador com contexto que nenhum artefacto continha.
9. **Typo interno de plano ≠ ambiguidade de decisão** — executor corrige typos óbvios reportando; pára só em ambiguidade de decisão real (ex.: verify "0.2c" vs instrução "0.2a").
10. **Reutilizar contexto do subagente entre fases do mesmo milestone** (expansão → execução no mesmo agente via mensagem de seguimento) — poupa releitura integral do spec.

## Meta-padrão (porquê isto funciona)

O plano exaustivo (`nexus-plan-spec`) paga tokens para REMOVER juízo do executor. Este método paga MUITO menos porque mantém o juízo no orquestrador — o custo desloca-se de "especificar tudo" para "rever nos pontos certos" (critic no plano, orquestrador nos gates, verificador no fim). A condição de validade é exactamente essa: há um orquestrador presente. Sem ele, usa `nexus-plan-spec`.

## Traços de origem (resumo)

4 runs reais (refactor de um skill em 6 milestones, 2 × PLAN-v2, 1 × Decision-Spec JIT), todos com critic-gate; custo medido dos 3 runs com ledger: ~725-905k tokens para TRÊS melhorias planeadas + executadas + verificadas limpas, vs 1M+ só para o PLANO de um único run exaustivo anterior. O critic encontrou findings graves em 4/4 (1 BLOCKER de gate, 2 HIGH de perda de conteúdo, 1 BLOCKER de canal⟂público-alvo). Os artefactos originais eram específicos de um projecto privado e não foram incluídos.
