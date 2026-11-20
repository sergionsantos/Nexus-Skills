# Critic protocol — 4 lentes adversariais sobre planos

> **Quando invocar:** imediatamente antes de declarar um plano/spec "done" (pré-execução) ou um closeout/roadmap "done" (pós-conclusão). Não esperar que o dono peça — fazê-lo sempre (§0.6).
>
> **Classificação:** BLOCKER (impede a execução) · HIGH (afecta qualidade/ambiguidade) · MEDIUM (nice-to-have). Ciclo: fix → re-verify com as 4 lentes → itera até BLOCKER=0 (assímptota).

## Princípio

O autor vê o plano com lente de validação ("isto vai funcionar"). O critic vê-o com lente de falsificação ("onde é que isto vai falhar?"). Por construção, a lente do critic apanha melhor bugs de estado acumulado, âmbito escondido e inconsistências entre steps. **É complementar ao autor, não redundante**: num caso real, um plano de 38 steps com gap analysis e verificação mecânica já feitas ainda escapou com 3 BLOCKER e 4 HIGH.

**Regra de iterações:** 1 iteração com 4 lentes apanha ~60-70% dos bugs; 2 iterações (após fixes) ~85-90%; 3+ é regresso. A assímptota é BLOCKER=0, não zero findings.

## Lente 1 — Executabilidade literal

**Pergunta:** *neste ponto da sequência, que ficheiros existem com que conteúdo exacto? que estado tem a DB? este edit por âncora encontra a âncora?*

1. Para cada step que toca código, abre o ficheiro real e confirma: símbolos importados existem; funções referenciadas estão definidas no sítio certo (cliente vs servidor vs DB); tipos existem.
2. Para cada step que toca a DB, confirma que funções, tabelas e colunas referenciadas existem (`pg_proc`, `information_schema.columns`) e que as permissões são consistentes com a identidade que o step assume.
3. Para cada step de infra partilhada, confirma o blast radius (outros projectos na mesma DB, gateways partilhados).

**Exemplo típico:** um step chamava uma função SQL `rankAfter(...)` que só existia como função TypeScript no cliente. Um `grep "rankAfter" db/migrations/ src/lib/` de 30 segundos apanhou-o. Saída: lista de steps in-executáveis, cada um com "o que existe vs o que o step assume".

## Lente 2 — Consistência do estado acumulado

**Pergunta:** *depois do step N-1, qual é o estado real? O step N assume esse estado?*

1. Cada milestone tem um `state-snapshot.md` emitido ANTES do primeiro step (ficheiros existentes, schema, rotas).
2. Cada step escreve contra o snapshot, não contra a memória.
3. Procura handoffs entre steps (um step que toca, por acidente, num ficheiro que outro assume intacto).
4. Forward-refs: confirma que a referência é canónica ("MODIFICA `issue-card.tsx` (JÁ EXISTE, criado em M3.7)") com `find` antes de emitir. Exemplo típico: o plano dizia "cria `board-card.tsx` OU usa a vista de board se os cards forem inline" — ambíguo; o ficheiro real era outro. Saída: ambiguidades classificadas (forward-ref incorrecta · em falta · ficheiro-alvo errado).

## Lente 3 — Completude / âmbito escondido

**Pergunta:** *o que está subespecificado?*

- [ ] **TDD-first** nos steps de feature (escrever o teste que falha antes de implementar)? Polish puramente visual pode dispensá-lo, mas precisa de smoke test visual.
- [ ] **Steps pequenos** (2-5 min)? >50 linhas, >1 ficheiro ou >1 conceito = dividir.
- [ ] **"..." em código?** `grep "\.\.\." plan/`.
- [ ] **Tarefas vagas?** "implementar X" → "criar `path/X.ts` com [interface] que devolve [tipo]".
- [ ] **5 porquês em fixes?** Corrigir o sintoma (ex.: reordenar duplicados) sem perguntar a causa (condição de corrida?) deixa-a a produzir mais. Adiciona uma query de causa-raiz e um limiar de paragem.
- [ ] **Casos além do conhecido?** Um fix que só trata "as 2 linhas duplicadas que vi" falha com 3+ — detectar primeiro, corrigir depois.
- [ ] **Dependências implícitas** usadas sem declarar em Files (props em falta, hooks que exigem um id).
- [ ] **Ordem ambígua entre milestones** que inserem no mesmo ponto.
- [ ] **Componentes partilhados com nomes diferentes** em milestones diferentes: define o nome canónico no primeiro.

## Lente 4 — Predict-then-run

1. Cada `**Verify**` tem output esperado concreto ("0 linhas", "17 distintos", "exit 0")? Estado fixado ("usa o item X, que existe antes deste milestone", não "um item qualquer")? Dump real esperado?
2. Cada `**If verify fails**` tem diagnóstico diferencial (sintoma→causa→acção)? "Corre outra vez" é 1 de N modos de falha; cobre os plausíveis.
3. Cada `**Done when**` é binário ("X passou E Y dump OK", não "X está OK").

## Classificação e acção

| Tier | Definição | Acção |
|---|---|---|
| **BLOCKER** | Impede a execução do step | Fix obrigatório antes de declarar done |
| **HIGH** | Ambiguidade, vagueza, dependências em falta | Fix recomendado (1 iteração) |
| **MEDIUM** | TDD, causa-raiz, qualidade, nomes | Opcional; regista num ficheiro de pendentes se for nice-to-have |

Reporta `CRITIC REPORT — N findings, X BLOCKER, Y HIGH, Z MEDIUM`. Mesmo com zero findings, reporta (não é desculpa para saltar o passo).

## Armadilha: o próprio critic produz falsos positivos por regex frágil

Um critic que parte o plano por `## Step ` e conta `**Verify**` / `**Files touched**` por regex exacta falha com variações legítimas de formato: `**Files touched:**` (com dois-pontos), `**Verify (smoke):**` (com subtítulo). Num caso real reportou "25/25 steps sem Files touched" — todos tinham.

- **Sinal de alarme: findings uniformes demais** (o mesmo finding em todos os N steps). É mais provável um bug de regex do que uma falha sistémica: PÁRA e re-verifica com um método independente antes de reportar.
- **Método robusto:** contar com substring (`grep -c "Files touched"`), nunca com regex de variantes exactas; em Python, `"Files touched" in bloco`. Regex à medida só quando a variação é conhecida e controlada.
- Para dividir por cabeçalhos que podem aparecer dentro de code fences (exemplos citados), usa um split ancorado ao início de linha (`^### Step `) e ignora o conteúdo dentro de fences.
- Re-verifica cada fix do critic com um método independente, incl. o regex que produziu o falso positivo.

## Template de despacho (critic de agente único)

```markdown
És um critic a rever um spec de plano para o projecto X. Aplica 4 lentes de forma adversarial (refuta, não valides). Não produzas elogios — só findings.

L1 executabilidade: para cada step, abre o ficheiro/função/tabela referenciada e confirma que existe. Lista "isto falharia porque X não existe".
L2 estado acumulado: por milestone, lista o que o step seguinte assume do anterior; reporta "ficheiro-alvo errado" e "forward-ref em falta".
L3 completude: procura "..." em código, tarefas vagas, TDD em falta, causa-raiz em falta, ordem ambígua, componentes sem nome canónico.
L4 predict-then-run: cada Verify tem expected concreto? cada If-verify-fails tem diagnóstico diferencial?

Classifica BLOCKER · HIGH · MEDIUM. Formato: tabela markdown, um finding por linha, com ficheiro+step, evidência exacta e fix em linguagem de spec.
```

Despacho com contexto limpo (fresh-context): ver `redteam-dispatch-prompts.md`.
