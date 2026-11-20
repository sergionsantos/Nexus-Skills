---
name: nexus-plan-spec
description: Escreve um spec/plano de build EXAUSTIVO e determinístico (10-20k linhas, 10+ milestones), reality-checked contra o ambiente real e executável por um modelo médio ou por um executor literal sem decisões próprias. É a versão pesada do planeamento; para um plano rápido/médio usa `nexus-plan`. Usar quando pedem "faz um plano completo para X", "spec para outro modelo executar", "build plan de um clone/produto", "plano exaustivo", ou quando o output vai ser executado por um agente sem juízo crítico. Impõe um modo de operação (verificar primeiro, simular antes de escrever, prever antes de correr, desconfiar da própria lente). Alimenta a execução disciplinada de `nexus-discipline` (contrato VERIFY-PREFLIGHT-GATE + MILESTONE-CADENCE).
---

# nexus-plan-spec — spec determinístico para executor literal

> **Escolher a skill certa.** `nexus-plan-spec` (esta) = plano exaustivo, paste-ready, com red-team e validador mecânico; custa muitos tokens (um run real de 8 milestones/43 steps gastou ~3M tokens de subagentes). `nexus-plan` = plano económico para melhorias médias/grandes. Se o trabalho cabe em ≤10 steps e o executor tem juízo, usa `nexus-plan`.

## O contrato

O leitor do spec é um **executor literal sem juízo**: faz exactamente o que está escrito e NADA que não esteja. O spec só é bom se: zero decisões abertas, zero âncoras ambíguas, zero valores por confirmar, cada step verificável com output real. Métrica única: *"um modelo médio chega ao fim sem nunca ter de adivinhar?"*

## §0 — OPERATING MODE (obrigatório, seja qual for o modelo que invoca esta skill)

Isto não é estilo — é o método. Um modelo que salte estas regras produz "mais um plano", não um plano-spec.

1. **Comando > suposição.** Qualquer facto verificável por um comando verifica-se AGORA (`docker inspect`, `ls`, `psql`, ler o compose real, decodificar o token). Nunca escrever "assumindo que..." num spec — ou verificaste, ou é uma Open Question para o dono, ou é `[ASSUMED]` marcado. Num caso real, 5 minutos de inspecção mudaram portas, revelaram que um serviço previsto nem existia, e evitaram um milestone inteiro escrito contra um stack imaginário.

2. **Ler a fonte INTEIRA antes de sintetizar.** Ground truth lê-se completo (em chunks se preciso), não por amostragem. Planeia o orçamento de contexto: chunks dimensionados, leituras independentes em paralelo, nunca duas passagens pelo mesmo material por desorganização. *Coverage ledger* (artefacto obrigatório): checklist das secções da fonte (via `grep "^#"` ou índice gerado), tick por chunk lido + 1 linha de notas; "li tudo" só com ledger completo em disco.

3. **Simular a execução mentalmente ANTES de escrever cada step.** Pergunta permanente: *"neste ponto da sequência, que ficheiros existem, com que conteúdo exacto? que estado tem a base de dados? este edit por âncora ainda encontra a âncora?"* Escrever o step contra o estado ACUMULADO, não contra o estado imaginado. Externalizar como `state-snapshot.md` por milestone (`references/state-snapshot-template.md`).

4. **Predict-then-run nos verifies.** Escrever o output esperado EXACTO antes do comando — se não consegues prever o valor, o step está subespecificado: fixa o estado dos dados de teste ("cria um item NOVO com estado Backlog", nunca "usa um item") ou torna o expected relativo. Cada verify ganha um "If verify fails" com diagnóstico diferencial real (sintoma→causa→acção), não wishful thinking. Falha sem entrada correspondente = o executor PÁRA (VERIFY-PREFLIGHT-GATE da skill `nexus-discipline`).

5. **Decidir no momento, registar imediatamente.** Todo "depende" converte-se em D## numerado com o porquê, ANTES de aparecer num step. Decisão nova a meio = D## novo no cabeçalho do milestone. Nunca reutilizar um D#/F# para coisa diferente. O Register é estrutura de dados, não prosa.

6. **A tua lente é suspeita — por construção.** Author-pass ≠ done. Pede red-team sem esperar que o dono peça; aceita findings sem defender o texto; re-verifica os próprios fixes (num caso real 4 de 28 fixes ficaram parciais); pára quando os findings viram cosméticos (assímptota — não persegue zero absoluto).

7. **Paragens limpas, o disco é a verdade.** Nunca partir uma unidade de trabalho a meio de um output; marcadores exactos de fim de pass; cada pass auto-contido e retomável. A conversa pode morrer a qualquer momento — plano só na conversa = plano morto; exporta para ficheiros antes de o considerar entregue.

8. **Escalar, não improvisar.** O que é do dono (segurança, acessos, hosting, âmbito, dados) vai em pergunta estruturada (opções concretas + recomendação marcada), não em suposição nem pergunta vaga. As respostas entram como camada de amendment sem reescrever o plano.

9. **Blast radius primeiro.** Classificar cada acção: reversível → avança sem fricção; irreversível/partilhada → gate explícito no próprio step (`⛔ GATE PRÉ-APLICAÇÃO`: preparar, PARAR, review forte + aprovação humana, só depois aplicar). Paralelizar tudo o que é independente (reviewers, leituras, edits em batch). Gate sem humano presente (cron/headless): PÁRA no step, regista PENDING, continua steps independentes do gate se existirem, senão termina o run com relatório.

10. **Estado honesto.** "implementado, verifies com dumps, por rever" ≠ "done". Dumps reais colados, nunca "PASS" nu. **Verifica literal fresh a cada turno** quando o contexto exige "verify real"; verify em cache não é verify. Sem especulação quando o estado DONE já está provado: prova real + exit code visível é a única aceitação.

## Pipeline (10 fases, ordem obrigatória)

### 1. Ground truth antes de inventar
Feature reference verificado (fonte primária citada por claim; incertezas `⚠️ UNVERIFIED`; adições próprias `[ASSUMED]`). Se não existe, produzi-lo primeiro (research pass separado). O plano nunca inventa comportamento do produto-alvo — resolve os `⚠️` com decisão explícita registada.

### 2. Reality-check do ambiente antes de fechar valores
Aplicar §0.1 ao stack inteiro: inspeccionar containers, compose/proxy/env reais, portas ocupadas, serviços em falta, roles/passwords da DB. **Timing: ANTES de emitir o primeiro step de execução** — num caso real o reality-check só aconteceu depois de 12 passes e obrigou a reescrever o M0. Valores de env no plano = valores REAIS verificados. O que faltar no ambiente vira STEP novo, não nota de rodapé.

### 3. Locked Decisions Register = espinha dorsal
Toda decisão numerada (D01…) numa tabela única emitida ANTES de qualquer step. Versões pinadas exactas e verificadas no registry (o red-team apanha pins inventados). Precedência explícita: amendments > decisões de milestone > Register > texto dos steps.

### 4. Perguntas mínimas ao dono → amendments
Só o que genuinamente não se decide sozinho. Respostas = camada de amendment; a precedência resolve — o plano não se reescreve. Amendments = tabela única no `00-README` (fonte canónica). `D###-R` = revisão de D### (mesma raiz numérica); decisão nova = número novo. **Tie-break amendment-vs-amendment:** o mais recente vence; se o conflito for real (não substituição), resolve-se com D novo que os reconcilia — nunca deixar os dois de pé para o executor escolher.

**Citation hygiene:** cada `Source: <doc>:linha N` no Register deve bater com `sed -n 'Np' <doc>`. Cite-mismatch é BLOCKER; correcção: re-traçar cada D## e adicionar um D##-R.

### 5. Emissão por passes com protocolo anti-truncação
1 milestone por pass; NUNCA partir um step a meio de um output; marcador exacto de fim; cada pass auto-contido (restate das dependências no topo). **Write-as-you-go: cada pass vai para ficheiro NO MOMENTO da emissão.** Excepção: um único artefacto coeso (1 ficheiro sem milestones numerados) → "write final pass", sem marcadores intermédios; com >1 milestones ou artefactos de closeout separados, mantém a cadência.

**Paralelizar autoria de milestones (pre-flight obrigatório):** o modo por defeito é SEQUENCIAL de propósito — cada pass vê o estado acumulado do anterior, o que evita de graça a classe de erro abaixo. Se paralelizares (agentes independentes, um por milestone, para ganhar tempo — legítimo), corre PRIMEIRO um **registo de recursos partilhados**: lista os ficheiros que mais de um milestone vai tocar e o PRÓXIMO número livre de cada sequência global (migrations, D#, F#), e ATRIBUI cada recurso contestado a um milestone específico ANTES de disparar os autores — nunca deixes dois agentes cegos decidirem cada um "o próximo livre é X". Inclui também as **invariantes transversais de verificação** (ex.: "todos os endpoints exigem autenticação") no prompt comum. É barato (uma tabela + grep) e mata a colisão na origem. O red-team continua obrigatório (§8): apanha bugs de lógica que nada têm a ver com paralelismo. Casos medidos em `references/parallel-authoring-and-token-economy.md`.

### 6. Formato de step atómico (invariável)
`Goal / Depends on / Files touched / Behavior spec / Implementation (código COMPLETO paste-ready, zero "...") / Commands / Verify / If verify fails / Done when`. O Behavior spec descreve o comportamento do produto-alvo DENTRO do step. O Verify segue §0.4 (predict-then-run, dumps reais, estado fixado). Cabeçalho de step: `### Step M<N>.<M> — <título>`.

### 7. Consistência a 15k linhas — mecanismos onde há tooling, disciplina assistida no resto

> Honestidade sobre enforcement: só fences/contagens/placeholders têm check mecânico (validador). Forward-refs, contiguidade de D## e não-re-derivação de constantes NÃO são verificados por ferramenta — são passos manuais que o red-team (fase 8) deve atacar especificamente.
- Constantes partilhadas num módulo único definido cedo (query keys, enums, rotas), referido por D## — nunca re-derivar.
- Ficheiro editado ≥4 vezes → o último step que o toca emite a **listagem final integral**; ficheiros críticos ganham apêndice de referência com checkpoints por milestone.
- **Composição vira colagem**: merges (ex.: políticas de acesso + amendments) pré-compostos como `appendix-*-final.*` + step `cp`. Erros de merge em segurança são silenciosos — a classe mais perigosa.
- Forward-refs explícitos nos dois sentidos ("editado em M7.5" ↔ "criado em M2.4").
- Checks mecânicos **após cada batch de edits** (não só no fecho): paridade de fences, contagem de steps, grep de marcadores, numeração D#/migrations contígua.
- **Constraint registada ≠ constraint aplicada**: propriedades globais do Register (ex.: "a autenticação é PARTILHADA") viram pergunta-checklist por classe de step.
- `state-snapshot.md` por milestone: estado acumulado pós-milestone.

### 8. Red-team obrigatório (§0.6 operacionalizado)
4 lentes disjuntas em paralelo, instrução adversarial ("refuta, não valides"): executabilidade literal · base de dados/segurança linha-a-linha · frontend · infra+pins (prompts em `references/redteam-dispatch-prompts.md`; protocolo e armadilhas em `references/critic-protocol.md`). Ciclo: findings → fix → **verify-dos-fixes** → confirm → parar na assímptota. Multi-agente: **idle ≠ done** — pede sempre o relatório/artefacto explicitamente. Num plano grande, o 1.º red-team encontra sempre 3-6 findings (esperado): corrige e re-despacha, nunca auto-aprova.

### 9. Kit de execução (o plano não basta)
- `00-README-EXECUTOR.md`: precedência, factos do ambiente, índice D##, **routing de modelos** (passos com modelo forte exigem gate humano; o resto é colar ficheiros).
- Steps de infra partilhada com `⛔ GATE PRÉ-APLICAÇÃO`.
- **Compatibilidade com `nexus-discipline`:** MILESTONE-CADENCE (1 marco por milestone, steps intermédios só "verify-OK") + VERIFY-PREFLIGHT-GATE (desvio não coberto pela failure-tree → PÁRA + dump tabular). O gate assume failure-tree por step **garantida por construção** — por isso o validador trata "If verify fails" em falta como FAIL, não warning.
- Validador mecânico: `scripts/validate-plan-spec.sh <ficheiro.md>` — IDs de step únicos · fences balanceadas · Verify e If-verify-fails (**contagem total ≥ nº de steps**, FAIL se menor; não verifica step a step) · placeholders proibidos (FAIL) · Done-when/Files/Commands/D## (contagens). **NÃO valida** (disciplina manual): grafo de dependências entre steps (ciclos passam), forward-refs bidireccionais, contiguidade D##, re-derivação de constantes.
- Notas sobre o validador: precisa de cabeçalhos `### Step M<N>.<M> — …` (travessão); aceita `**Files touched:**` e `**Files touched**:`; "duplicate step IDs" pode ser falso positivo quando há cross-refs em cabeçalhos.

### 10. Persistência e re-entrada
Guarda as decisões num ficheiro de estado/âncora (D## + estado de cada milestone) e, se tiveres memória persistente, um ponteiro para ele. Fecha a sessão com um resumo de passagem (ver `session-wrap`, se instalada).

## Sub-rotinas de execução

Corpo em `references/execution-subroutines.md`: (1) verify literal fresh com exit code visível; (2) tocar no schema da DB (forward-only, dry-run, ⛔ GATE); (3) seleção de worktree; (4) probes persistidas em disco. Padrões de evidência em `references/verify-evidence-patterns.md`; roadmap pós-conclusão em `references/post-completion-roadmap.md`.

## Calibração por dimensão do plano

**§0 aplica-se SEMPRE**; a tabela calibra só as fases 1-10. Um plano de 6 steps não dispensa §0.1 (verificar), §0.3 (simular) nem §0.6 (lente suspeita).

| Plano | Fases obrigatórias |
|---|---|
| ≤10 steps | 2, 3, 6 + validador |
| 10–40 steps | + fases 1, 5, 8 (1 reviewer) |
| >40 steps | pipeline completo |
| **Qualquer step irreversível/partilhado/produção** | + gates §0.9 e fase 8 OBRIGATÓRIOS, seja qual for o nº de steps — o blast radius sobe a disciplina, não o tamanho |

## Anti-padrões (proibidos no spec)

- "escolhe / decide / podes querer / adaptar conforme" — o autor decide, sempre.
- Sketches, `// add logic here`, "..." em código.
- Versões sem pin ou pins não verificados no registry.
- Verify sem expected concreto; "PASS" aceite sem dump.
- Edit por âncora de prosa num ficheiro já editado 3+ vezes.
- Step que compõe/merge quando podia colar um artefacto pré-composto.
- Assumir o ambiente (portas, serviços, env, roles) sem inspecção.
- Escrever um step sem simular o estado acumulado em que corre (§0.3).
- Autocorrecção em prosa dentro do step ("… NÃO — usar X"): o executor literal lê as duas instruções. Apaga a versão errada.

## Anti-padrões de processo

- ❌ Verify corrido uma vez e nunca repetido = verify em cache. Re-corre por turno quando o estado pode ter mudado.
- ❌ Reportar "done" antes de verify literal fresh (sem exit code visível nem dump colado é especulação).
- ❌ Passar uma linha de OWNER-BLOCKED a done sem o dono intervir: exige aprovação explícita, não auto-aprovação do agente.
- ❌ Escrever o plano em >1 ficheiro de uma vez sem write-as-you-go por milestone (o ficheiro único coeso é a excepção).
- ❌ Auto-aprovar após um 1.º red-team com vários BLOCKER, mesmo que pareçam cosméticos: corrige com file:line e re-despacha.
- ❌ Citar tabelas/funções/colunas que não existem. Antes de escrever SQL, confirma-as no schema real (migrations + `information_schema`); em joins confirma o nome real da coluna-chave.
- ❌ Reimplementar uma função existente "à tua maneira" ao portar: lê a fonte (não a docstring) e preserva a semântica, incl. o comportamento fail-closed.
- ❌ Fixar o intervalo esperado de um script novo a partir de estimativas: corre-o primeiro em cópia read-only e escreve o número medido ("medido a <data> em cópia").
- ❌ Regex de normalização que também casa o alvo já canónico e conta `k>0` como mudança: prova a idempotência com `if novo != antigo`.
- ❌ `rg -i` num verify cujo objectivo é detectar variantes de capitalização (anula o verify): é sempre case-sensitive.
- ❌ Disparar N autores paralelos sem registo de recursos partilhados (§5), ou achar que o red-team substitui o pre-flight (ou vice-versa): são complementares.
- ✅ Funcionou: hardcodar no plano os valores de um motor/ferramenta externa em vez de "recalcula"; o executor médio nunca tem de interpretar output técnico.

## Referências

- `references/critic-protocol.md` — 4 lentes adversariais + armadilhas do próprio critic.
- `references/redteam-dispatch-prompts.md` — prompts de despacho por lente.
- `references/state-snapshot-template.md` — snapshot por milestone.
- `references/verify-evidence-patterns.md` — evidência canónica e verify ad-hoc.
- `references/post-completion-roadmap.md` — plano pós-conclusão (closeout).
- `references/parallel-authoring-and-token-economy.md` — autoria paralela e custos medidos.
- `references/execution-subroutines.md` — sub-rotinas de execução.
- Skills relacionadas: `nexus-plan` (versão rápida), `nexus-discipline` (execução e gates), `nexus-analysis` (onde o plano nasce de uma análise).
