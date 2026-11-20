# Prompts parametrizados (validados nos traços — adaptar `<...>`, manter as cláusulas a negrito)

## §critic (tier FORTE, 1 passe)

```
Passe ÚNICO e cirúrgico (economia de tokens é objectivo explícito — sem re-exploração).
Revisão adversarial do plano <path> (melhoria <X> do relatório <path-análise>, consultável).

**Contexto dado como verificado** (não re-verificar): <factos ground já pagos>.

Procura falhas em:
a) Verifies que não podem devolver "não" ou com predicts errados (<suspeitas concretas>)
b) Steps que partem comportamento existente (<invariantes: demos, symlinks, trabalho fechado>)
c) Decisões locked D1-DN — alguma errada/em falta que force o executor a improvisar?
d) **Ownership: quem corre o quê? Algum caminho em que o executor faz trabalho
   do orquestrador/humano (gates, juízo, escrita pós-revisão)?**
e) <risco técnico específico deste plano>
f) CLIs: erros de `argparse` são `SystemExit` (código 2), não valor de retorno — o spec tem de dizer qual dos dois o verify espera.

**NÃO procures falhas em:** mérito da melhoria (aprovado pelo dono), <decisões já tomadas>, estilo.
Output: findings BLOCKER/HIGH/MEDIUM com fix 1-2 linhas; verdict ACCEPT/REVISE. Máx 400 palavras.
```

## §executor (tier MÉDIO)

```
Executa o plano <path> (v pós-critic — fixes já incorporados), steps <S1→SN> <APENAS —
S<X> é do orquestrador, não teu; no fim de S<N> PÁRAS e devolves>.

Disciplina:
- Decisões locked D1-DN invioláveis; ambiguidade fora delas → PÁRA e pergunta.
  (Typo interno óbvio do plano: corrige e REPORTA — não é ambiguidade.)
- Verify same-turn por step, predict-then-run (escreve o esperado ANTES), exit codes visíveis.
- CLIs: erros de `argparse` são `SystemExit` (código 2), não valor de retorno — especifica isso no spec/verify (ex.: `pytest.raises(SystemExit)` ou exit code 2 no shell).
- If-fails não cobre o sintoma real → PÁRA com dump (Expected · Actual), não improvises.
- <paths read-only> READ-ONLY. Zero acções públicas. <ficheiros live> — edits atómicos.
- **REGRA ABSOLUTA:** <o gate específico deste plano — ex.: nunca escrever X sem revisão>.
- Grounding pago: cita <análise+plano>; lê APENAS os ficheiros que os steps tocam
  (+ inputs explicitamente mandados ler: <lista>).

Report final: tabela step→estado→comando+resultado+exit, **incluindo <verifies críticos
nomeados UM A UM — especialmente negative controls>**, desvios se houver.
```

## §verify (tier MÉDIO; FORTE se houve acção pública/irreversível)

```
Verify independente de <run> (lente ≠ executor<, ≠ revisor-de-juízo se aplicável>;
re-corre tu, não confies no report).

Re-corre contra a realidade:
1..N. <cada verify crítico, com o esperado; incluir: negative controls RE-CRIADOS por ti,
regressões de comportamento fechado hoje, cruzamentos entre artefactos (draft↔final),
spot-checks de claims contra fonte primária, leitura do código novo (bugs/edge cases)>.

Output: por item CONFIRMADO/FALHOU com exit codes; findings com severidade; ou "limpo"
explícito. Curto.
```

## §ping-recuperação (quando o executor fica idle sem report — orçamentar 1 por subagente)

1. Spot-check em disco primeiro (1 comando composto: ls dos artefactos + greps chave).
2. Ping:
```
Spot-check em disco: <o que está aplicado>. FALTA: <steps/report>. Envia o report
completo: tabela step→estado→evidência com exit codes, incluindo <verifies em falta
nomeados um a um>.
```

## §fix-loop (finding do verificador)

Fix vai ao EXECUTOR original (tem contexto; manda mensagem de seguimento ao mesmo agente) com: problema verbatim do
verificador + fix sugerido + verifies a re-correr (com predict). Depois: re-verify do
MESMO verificador sobre o diff apenas. Zero findings → done.
```
