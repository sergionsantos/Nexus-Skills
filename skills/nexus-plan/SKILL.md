---
name: nexus-plan
description: >
  Quick, economical planning AND execution of a medium/large improvement to an
  existing system (~140-300k tokens measured, vs 1M+ for the exhaustive
  nexus-plan-spec), keeping quality through a mandatory critic gate plus an
  independent verifier. Two regimes: PLAN-v2 (short complete plan, medium
  in-repo work) and Decision-Spec JIT (locked decisions + one milestone expanded
  at a time, for large/phased work or work with human gates). Model-agnostic:
  roles by TIER (strong/medium), not by named model. USE WHEN a human or
  orchestrator stays in the loop: "cheap plan", "plan this without burning 1M
  tokens", "decision-spec", executing improvements that come out of a
  nexus-analysis. DO NOT USE for: an exhaustive spec that a model must execute
  unattended with no judgment (-> nexus-plan-spec), a concrete bug (debug it
  directly), finding WHAT to improve (-> nexus-analysis), or a trivial task
  (just do it; the plan would cost more than the work).
version: "0.2.0"
status: active
---

# nexus-plan — planeamento económico com juízo no loop

## Quando usar esta vs `nexus-plan-spec`

| | `nexus-plan` (esta) | `nexus-plan-spec` |
|---|---|---|
| Custo | ~140-300k tokens | 1M+ tokens |
| Executor | tier médio, com orquestrador/humano a rever | modelo sem juízo, unattended |
| Onde está o juízo | no orquestrador (critic no plano, gates, verify no fim) | removido do executor à custa de especificar tudo |
| Escolhe quando | há alguém presente a supervisionar | ninguém supervisiona a execução |

## Contrato

O tier forte decide e revê; o tier médio escreve o volume e executa; um critic red-teama SEMPRE o plano antes de qualquer execução; um verificador independente (lente ≠ executor) fecha. Custo medido: **~140-300k tokens por melhoria** (50k é piso teórico para uma melhoria pequena, ainda não observado); 1-2 findings graves apanhados pelo critic por run (4/4 nos traços de origem). O que este skill NÃO garante: determinismo unattended — há um orquestrador com juízo no loop; se o executor vai correr sozinho sem supervisão, usa `nexus-plan-spec`.

## Papéis por TIER (model-agnostic — resolve com o que houver)

| Papel | Tier | Como instanciar |
|---|---|---|
| Arquitecto (decisões, plano/spec) | FORTE | sessão principal (o melhor modelo disponível) |
| Critic (red-team do plano, 1 passe) | FORTE | subagente/sessão DISTINTA do arquitecto; NUNCA o mesmo contexto que escreveu o plano |
| Expansor/Executor | MÉDIO | subagente de tier médio |
| Verificador independente | MÉDIO; FORTE se o milestone tem acção pública/irreversível | 3º contexto distinto — nunca o arquitecto nem o executor |
| Copy/criativo user-facing | FORTE em pessoa — nunca tier médio | sessão principal |
| Gates de acção pública/destrutiva | HUMANO — nunca automatizável | o dono do trabalho |

Regra de resolução: usa o modelo mais forte DISPONÍVEL para os papéis FORTE; se só houver um tier, o mesmo modelo faz tudo MAS os papéis mantêm-se separados (contextos/subagentes distintos — a lente independente é o que protege, não o modelo).

## Triagem — que regime?

1. Trabalho médio, in-repo, sem acções públicas, superfície conhecida → **PLAN-v2**: plano completo ~100-300 linhas, executor único sequencial.
2. Trabalho grande, multi-milestone, com gates humanos/acções públicas, ou terreno que muda ao executar → **Decision-Spec JIT**: spec de 1-2 páginas com decisões LOCKED + milestones em intenção; expande-se UM milestone de cada vez, só quando o anterior fecha. *(Validado n=1, só a 1ª expansão — cadeia multi-milestone por provar; a promessa de re-planeamento entre milestones é desenho, não traço.)*
3. Trivial ou spec exaustivo unattended → fora deste skill (ver description).

## Workflow (comum aos 2 regimes)

1. **Grounding pago uma vez.** Se existe análise prévia (nexus-analysis, relatório com evidência ficheiro:linha), o plano CITA-A e proíbe re-exploração aos subagentes. Nunca pagar o grounding duas vezes.
2. **Arquitecto escreve** (tier forte, em pessoa): decisões LOCKED numeradas (D1-DN — tudo o que forçaria o executor a improvisar), steps/milestones com Verify predict-then-run + If-fails, ownership por step (executor vs orquestrador vs humano), non-goals, paths pinados absolutos, recovery. Templates: `templates/decision-spec-template.md` · `templates/plan-v2-template.md`.
3. **Critic-gate (obrigatório, 1 passe).** Prompt em `templates/prompts.md` §critic — inclui "contexto dado como verificado" (corta re-exploração), "NÃO ataques X" (mérito já decidido), e a pergunta de ownership ("quem corre o quê? algum caminho em que o executor faz trabalho do orquestrador/humano?"). REVISE com fixes mecânicos → o ARQUITECTO aplica os fixes e segue — sem 2º passe de critic (4/4 traços convergiram assim). BLOCKER estrutural → re-desenha.
4. **Executor** (tier médio): steps sequenciais quando há ficheiros partilhados; verify same-turn por step com exit codes; ambiguidade fora das decisões locked → PÁRA e pergunta; steps do orquestrador/humano NUNCA na sequência do executor. Prompt: `templates/prompts.md` §executor.
5. **Juízo não se delega:** colunas/decisões que dependem de contexto do dono (prioridades, fit, copy pública) ficam explicitamente para o orquestrador ou humano — o executor deixa-as vazias/"orq.".
6. **Verify independente** (lente ≠ executor ≠ revisor): re-corre contra a realidade, não contra o report; negative controls re-criados; findings → fix pelo executor → re-verify do MESMO verificador sobre o diff. Zero findings = done. Prompt: `templates/prompts.md` §verify.
7. **Registo do traço:** PROMPTS-<run>.md (prompts verbatim + desvios) + TOKEN-LEDGER-<run>.md (tokens por fase, medidos onde a ferramenta os expõe). É o que permite calibrar o método — sem ledger não há economia provada.

## Operacional (o que os traços ensinaram — detalhe em `references/patterns.md`)

- **Idle-sem-report é o modo de falha nº1 do executor** (3/3 runs): spot-check em disco ANTES de pingar; ping nomeia os verifies em falta um a um. Orçamenta 1 ping por subagente.
- **Verifies críticos nomeados um a um** no pedido de report — senão o executor omite os negative controls.
- **Reutiliza o contexto do subagente**: expansão e execução do mesmo milestone no MESMO agente (mensagem de seguimento) poupa a releitura do spec.
- **Typo interno do plano ≠ ambiguidade**: executor bem instruído corrige typos óbvios REPORTANDO-os; só pára em ambiguidade de decisão.

## Portabilidade

Artefactos = markdown + python3 stdlib. Nada no plano pode assumir tooling específico de um só agente fora de secções marcadas como tal. Self-report do executor nunca é aceite sem verify independente.

## Verificação (confirmar que o skill funcionou)

No fim de um run: verify independente limpo registado · TOKEN-LEDGER com total dentro de ~50-300k (fora disso, explicar porquê) · critic-gate registado com verdict e findings · zero trabalho declarado done sem lente independente.

## Quando NÃO usar

- Spec exaustivo para executor unattended sem orquestrador → `nexus-plan-spec`.
- Descobrir O QUE melhorar → `nexus-analysis` (este skill executa o output dela).
- Bug com repro → depura directamente. · Tarefa trivial → executa directo.

## Anti-padrões

| Anti-padrão | Correcção |
|---|---|
| Plano de 10k linhas para trabalho supervisionado | Triagem — regime certo; volume não é qualidade |
| Saltar o critic ("o plano é meu, está bom") | Passo 3 — 4/4 traços tiveram findings graves (1 BLOCKER de gate, 2 HIGH de content-loss, canal⟂público-alvo) |
| Executor com steps do orquestrador na sequência | Passo 4 — ownership por step; critic pergunta "quem corre o quê" |
| Re-explorar o que a análise já pagou | Passo 1 — citar, proibir re-exploração |
| Aceitar self-report do executor | Passo 6 — verify independente re-corre tudo |
| Declarar economia sem medir | Passo 7 — TOKEN-LEDGER obrigatório |
| Papéis colapsados num só contexto quando só há 1 modelo | Tabela de tiers — separar por contexto/subagente, a lente é o que conta |

## Changelog
- v0.2.0: draft→active — 1º uso real com sucesso (regime JIT: spec→critic BLOCKER real apanhado→1º milestone executado→verify independente 8/8 limpo, ~110-140k tokens). Lições incorporadas: (a) valores de fixture pinados pelo AUTOR do spec — o executor nunca escolhe os esperados; (b) colapso arquitecto=executor tolerável SE o verify independente ficar noutra lente (wording neutro nos prompts: evitar "red-team"/"ataca"/CAPS agressivos, que alguns classificadores bloqueiam); (c) mudanças a contratos de outros skills = diff proposto para aprovação, nunca edit unilateral.
- v0.1.1: fixes pós-review do critic: lentes DISTINTAS por papel (critic/verify nunca no contexto do arquitecto); banda de custo honesta 140-300k medido; JIT marcado n=1/cadeia-por-provar.
- v0.1.0: criação — destilado de 4 traços reais (~800k tokens total para 4 melhorias executadas e verificadas vs 1M+ de um único plano exaustivo). 10 padrões em `references/patterns.md`.
