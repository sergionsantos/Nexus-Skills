---
name: nexus-discipline
version: 1.0.0
description: "Execution & verification discipline for AI coding agents: verify before claiming (predict-then-run, negative controls, independent review), honest done-language, per-phase triad (ISA + status file + ad-hoc verify), milestone cadence and action gates. Core doctrine in this file (§1-§6); trigger playbooks P1-P15 in `references/playbooks.md`; problem-class routing in §7; full reference index in `references/INDEX.md`. Pairs with nexus-plan-spec (consumes the VERIFY-PREFLIGHT-GATE and MILESTONE-CADENCE contracts defined here). Disciplina de execução e verificação para agentes de código."
tags: ["execution", "discipline", "isa", "verification", "done-language", "milestones", "multi-agent"]
category: engineering-discipline
source:
  - "Daniel Miessler — Personal AI Infrastructure (ISA v5.0.0 + Algorithm v6.3.0)"
  - "Calibração contra sessões reais de agentes (verificação, linguagem de conclusão, gates)"
---
# nexus-discipline — doutrina de execução

> **ISA** = Ideal State Artifact: ficheiro de spec/estado de uma tarefa por fases (`.isa/ISA-<nome>.md`, ver `templates/ISA.md`). **ISC** = critério de aceitação binário `- [ ]` dentro dele.

> **Estrutura deste skill:** §1-§6 = doutrina estável (muda por calibração, não por sessão). §7 = routing por classe de problema. §8 = regra anti-drift. Factos detalhados, war-stories e recipes vivem em `references/` (índice completo em `references/INDEX.md`).

## §1 — Verificação (o ponto fraco medido; puxa aqui mais que em tudo)

- **Um edit é uma hipótese; um check que passa é a prova.** Check válido = um que **pode devolver "não"**. "Revi e parece certo" NÃO é check.
- **Predict-then-run:** escreve o resultado esperado com valores concretos (contagem, exit code, string exacta) ANTES de correr o check. Sem predição, o check só confirma; com predição, falsifica o modelo mental. Predição escrita depois de ver o resultado não conta (hindsight fit).
- **Negative control:** se nunca viste este check falhar, inverte UMA expectativa (assert flipado, input mau de propósito) e confirma que **rebenta**. Harness que não sabe falhar reporta verde para sempre — "9/9 PASS" só é evidência depois de teres visto um FAIL possível.
- **Exit code visível** (`cmd; echo "exit=$?"`) + **dump de valores reais** por-campo — nunca "PASS" nu (um gate já foi rejeitado por isto).
- **Rule 0 — revisão independente (código não-trivial, NÃO-NEGOCIÁVEL):** author-pass ≠ done; lente ≠ autor; dá-lhe spec+output, não o teu raciocínio; itera até zero findings no diff; re-verifica os próprios fixes.
- **Rule 1 — live-probe** para artefactos user-facing; "should work" sem output real não é evidência.
- **Same-turn verify:** DONE-language exige verify fresh NESTE turno — cached-verify de turno anterior não é verify. **Escopo por custo:** o verify do turno cobre o subconjunto afectado (script ad-hoc focado); a suite canónica completa corre no fecho de milestone, não a cada turno.
- **Schema-first em porting/DB:** SQL de port/migração exige introspecção do schema real ANTES de escrever a query (citar tabela/coluna não verificada = inventar schema = BLOCKER); dry-runs destrutivos exigem rollback explícito comprovado. Casos e recipes: §7 (psql dry-run · gotchas Postgres).
- **Prova de step irreversível vive no MESMO artefacto que reporta o step.** Uma condição escrita para autorizar um irreversível (`count(*)=0` antes de um `DROP COLUMN`, dump de confinamento antes de um DDL) **exige o dump colado no próprio status-file/relatório desse step** — não "corri e passou". Caso real: a condição foi cumprida na prática mas **a prova evaporou-se com o turno**; procurou-se em 4 commits, no state-snapshot e no SQL, e não existia. Resultado honesto: o ISC ficou **NÃO-PROVADO** para sempre, porque um irreversível não é re-executável. O executor recusou-se a inferir "0 linhas" sem evidência em disco — comportamento certo. Mitigação possível depois do facto é só **confinar** o blast radius (sonda read-only a mostrar tabela vazia hoje), nunca provar o estado anterior. Corolário: se o dump não cabe no status-file, escreve-o num ficheiro versionado e cita o path.

## §2 — DONE-LANGUAGE (escada de evidência)

Escada: **verificado-agora** > verificado-antes (<48h) > inferido > assumido. Só verificado-agora autoriza afirmação nua; o rung <48h serve claims intermédios, **nunca** "done". Taxonomia de claims (nunca arredondar para cima): Completo (+pointer ficheiro:linha) · Falhou (verbatim) · Saltado (+razão) · Não-verificado (etiquetado). Linguagem canónica: "implementado, happy-path testado, **por rever**" (intermédio) vs "**revisto independente + limpo**, done". Vocabulário STATUS + miss-patterns: `references/done-language-and-status-vocabulary.md`.

## §3 — Triad per-phase (unidade mínima que satisfaz um gate multi-turno)

> **Escopo:** a triad completa aplica-se a execução multi-agente com gate (coordenador a ler status files). Trabalho single-agent sem coordenador: ISA + verify por turno chegam — o status-file não tem leitor.

1. **ISA** (`{project}/.isa/ISA-<Lite|Full>-<slug>.md`) — frontmatter `phase:` (observe→…→complete), `status:`, ISCs como `- [ ]` binários; tick só com evidência no mesmo bloco.
2. **Status file** (`/tmp/<project>-status/<agent>.status`) — `STATUS=working|done|blocked|need` + sentinela `@@DONE`/`@@BLOCKED`/`@@NEED`.
3. **Ad-hoc verify script** por turno (nome novo, scope deste turno, exit 0/1, limpo após correr).

Verificar só 1 de 3 é insuficiente. Cada turno produz trabalho novo OU re-verify com script+evidência diferentes — re-correr o mesmo verify não é progresso (re-emendar só metadata para provocar um novo turno é um loop). **Quando o dono pede novidades ou exige resolução:** recupera o último entregável e a primeira dependência por satisfazer; executa a próxima acção autorizada que reduza essa dependência antes de responder. Não substituas aquisição, revisão ou entrega pendente por reexecução de testes sintéticos inalterados, nova ISA ou outro relatório de estado. Reporta o delta verificável, o bloqueio específico e a sequência de resolução; se só o dono puder desbloquear, pede a intervenção mínima concreta. Não sugiras trabalho entre turnos sem processo efectivamente lançado.

## §4 — VERIFY-PREFLIGHT-GATE (contrato com nexus-plan-spec)

**Escopo:** aplica-se a steps de planos emitidos por nexus-plan-spec (expected + failure-tree garantidos por construção). Em planos legacy/ad-hoc sem esse formato: best-effort — ausência de expected não é PÁRA automático; deriva o expected antes de correr e marca `UNVERIFIED` o que não for derivável.

1. Antes do verify: confirma que o step tem expected concreto + failure-tree ("If verify fails"). Num plano nexus-plan-spec, não ter → step subespecificado; **PÁRA** e reporta (não improvises um expected).
2. Corre o verify. Resultado ≠ expected E o sintoma **não bate com nenhuma entrada** do failure-tree → **PÁRA**: dump tabular (Expected · Actual · entrada mais próxima do failure-tree · porquê não bate). Zero improviso de fixes fora da árvore. Escreve `STATUS=need` — o diagnóstico exige modelo forte e **a escalada é decisão do orquestrador/owner, não tua**. **Excepção única: se a divergência for demonstravelmente da FORMA da sonda** — substring que apanha mais do que devia (`grep -c "fetch("` a contar `refetch()`), docstring que o próprio step manda colar, eco do runner (code-frame do vitest a repetir a linha-fonte) — **corriges a sonda e segues**, com dump antes/depois: o failure-tree governa o comportamento do código, não a ergonomia do `grep`. Âncoras que valem mais que substrings: `await fetch(`, `^Error:`, nome exacto com parêntesis, e `grep -vE '^\s*(\*|//|/\*)'` antes de contar. Dois `@@NEED` seguidos por esta causa custaram 2 paragens de um worker que estava certo.
3. Sintoma coberto pelo failure-tree → aplica a acção prescrita, re-corre o verify, regista.

## §5 — MILESTONE-CADENCE (contrato com nexus-plan-spec)

No fecho de cada milestone de um plano em execução:
1. Todos os steps do milestone com verify PASS registado (dumps, não veredictos).
2. `state-snapshot.md` do milestone escrito/actualizado (template: `nexus-plan-spec/references/state-snapshot-template.md`).
3. Checks mecânicos do batch **quando o milestone gerou/editou artefactos-plano** (paridade de fences, contagem de steps, numeração D#/migrações) — em milestones só-execução, N/A.
4. Milestone correctness-oculta (sync/realtime, RLS/permissões, concorrência, crypto/auth) → review independente com modelo forte OBRIGATÓRIA antes de avançar. Se não podes despachar essa review, escreve `STATUS=need` e pára no gate — a escalada de modelo é do orquestrador.
4b. Step destrutivo aplicado a meio do milestone (migração, delete) + step seguinte falha → NÃO continues nem revertas por improviso: PÁRA (§4.2) — o failure-tree ou o owner decidem o caminho de recuperação.
5. ISA da fase actualizado (ISCs ticked com evidência) + marco em disco, nunca só no chat.
6. **Fecho de milestone COMMITA e ANUNCIA sem esperar pergunta:** commit granular do trabalho do milestone (mensagem descritiva) + actualização do `LOG.md` do projecto (se existir) fazem parte da checklist de fecho — não dependem de memória conversacional nem de pedido do owner. Push NÃO: continua decisão do owner. Anúncio = 1 linha no chat com hash + o que fechou.

## §6 — Gates de acção e disposição

- **Blast radius primeiro:** reversível → avança; partilhado/irreversível/unattended → sobe a disciplina inteira independente do tamanho do diff. `⛔ GATE PRÉ-APLICAÇÃO` (config partilhada, prod, secrets, configuração do próprio agente): diff preparado, PARAR, esperar "vai" do owner.
- **Div-guard:** instrução condicional ("replica MAS se X, pára") é a decision tree completa — cumprir a letra violando o espírito é o erro mais comum.
- **Escalar, não improvisar:** o que é do dono (segurança, acesso, scope, dados) vai em pergunta estruturada com recomendação marcada. Ordem de execução dentro de spec aceite é decisão de engenharia — não perguntes ao owner o que o spec já cobre.
- **Turn-ending check:** último parágrafo é resultado, não plano/promessa. Re-prompt idêntico do sistema com objectivo já completo+verificado → STOP de 1 parágrafo, não fabricar trabalho (protocolo 3-gates: `references/alg-enforcement-3-gates.md`).
- **Effort calibration E1-E5** + processo 7-fases (E3+): `references/effort-and-process.md` §1/§3.

## §7 — Routing por classe de problema

**Gatilho comportamental → playbook P1-P15:** `references/playbooks.md` (verify/comando→P1 · valor token-like→P2 · resultado de tool→P3 · finding de review→P4 · correcção do dono→P5 · delegação/subagente idle→P6 · fontes em conflito→P7 · declarar done→P8 · retomar/ambiente mudou→P9 · tool partida→P10 · iterar ou parar→P11 · scans repetidos→P12 · config partilhada/unattended→P13 · fechar marco/ISA→P14 · patch alheio/doc engordou→P15).

**Classe de problema → reference primária** (selecção curada; índice COMPLETO em `references/INDEX.md`):

> Nota de scope: os anti-patterns AP1-AP4 (`alg-enforcement-3-gates.md`) e os 3 failure modes de done-language aplicam-se a **qualquer trabalho multi-fase** (pivots, migrações, orquestração multi-agente).

| Classe de problema | Reference |
|---|---|
| DONE-LANGUAGE, vocabulário STATUS, miss-patterns | `references/done-language-and-status-vocabulary.md` |
| Count-based proof (read-path ≠ write-path) | `references/count-based-proof.md` |
| ALG enforcement / re-prompts idênticos / stop-audit | `references/alg-enforcement-3-gates.md` |
| Verify probe false-fails | `references/verify-probe-anti-patterns.md` + `references/shell-probe-false-fails.md` |
| Verificação pós-mutação stale / pointer truth | `references/final-mutation-and-pointer-truth-gates.md` |
| Reprodutibilidade de artefactos gerados (run-twice/hash) | `references/generated-artifact-reproducibility-gate.md` |
| Review independente sem contaminação | `references/fresh-context-verifier-protocol.md` + `references/independent-code-review-calls.md` |
| Negative controls (scope) | `references/source-aware-negative-controls.md` |
| Calibração de gates + probes runtime (cwd) | `references/gate-calibration-and-runtime-probes.md` |
| Ground-truth drift entre sessões | `references/ground-truth-drift-between-sessions.md` |
| Pre-flight collision ("cria X" quando X já existe) | `references/pre-flight-collision-check.md` |
| Multi-agent sibling edits / worktree races | `references/multi-agent-sibling-edits-detector.md` + `references/worktree-shared-race-conditions.md` |
| Loops em probes/execuções interrompidas | `references/loop-detection-case-studies.md` |
| Spike read-only antes de write em prod | `references/spike-read-only-dry-run-pattern.md` |
| Auth-blocked → pivot para subtask sem auth | `references/auth-blocked-redirect-first.md` + `references/pivot-to-auth-free-hardened.md` |
| Bug sistémico vs isolado | `references/systemic-bug-detection.md` |
| Decisão de produto em falta no spec | `references/product-decision-gap-protocol.md` |
| Claims sobre pessoas/sistemas (grounded-source-only) | `references/grounded-source-only.md` |
| Explain-then-recommend (UX de resposta ao dono) | `references/rule-0-11-explain-then-recommend.md` |
| Schema-first / psql dry-run / gotchas Postgres | `references/psql-dryrun-rollback-discipline-2026-07-19.md` + `references/postgres-runtime-probe-gotchas.md` |
| Ferramenta que sanitiza segredos no disco | `references/write-file-api-key-sanitization-corrupts-disk.md` + `references/read-file-display-vs-disk-sanitization.md` |
| Owner tem o segredo, o agente não chega — pergunta estruturada | `references/structured-ask-owner-for-secret.md` |
| Comandos com gate de aprovação em canais remotos | `references/approval-gated-commands-remote-channels.md` |
| Esforço E1-E5 e processo de 7 fases | `references/effort-and-process.md` |

## §8 — Regra anti-drift (como este ficheiro se mantém)

1. **Sessão nova NUNCA acrescenta prosa a este ficheiro.** Lição de sessão → ficheiro novo (ou append) em `references/` + 1 linha em `references/INDEX.md` (+ linha na tabela §7 só se abre classe de problema nova).
2. §1-§6 só mudam por **decisão explícita do dono** ou por calibração com evidência de sessões reais — com bump de `version:`.
3. Orçamento deste ficheiro: **≤150 linhas** — check mecânico obrigatório no fecho de QUALQUER edição: `wc -l SKILL.md` (>150 = corta antes de fechar; P15). Nota de nível: exit-code checks são gate mecânico; predict-then-run é disciplina auto-relatada — vale como hábito, não como prova.
4. Caso datado (`*-2026-*`) neste ficheiro é sempre bug — move para references.
