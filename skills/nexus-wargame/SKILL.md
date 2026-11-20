---
name: nexus-wargame
description: >
  Transformar um objectivo em terreno adversarial (lead-gen, migração, campanha,
  lançamento, qualquer coisa que uma plataforma/concorrente/algoritmo pode fazer
  falhar) num conjunto de WAR-GAMES executáveis — planos acção→reacção→contra-acção
  com falhas antecipadas — usando o modelo mais forte disponível UMA vez, para que
  modelos baratos executem depois com o julgamento já embutido nos ficheiros.
  Usar quando o utilizador diz "faz um war-game de X", "planeia isto como war-game",
  "aplica o processo de wargames a Y", "/nexus-wargame", ou antes de gastar
  tokens de um modelo caro num projecto cujo caminho real é incerto e cheio de
  excepções. O modelo caro é PARÂMETRO (Opus, GPT-5-class — o mais forte à mão),
  não é um modelo fixo. NÃO usar para: plano linear/sequencial sem terreno adversarial
  (nexus-plan), spec de build de código (nexus-plan-spec), extrair lição desta
  sessão (nexus-learner), ou tarefa mecânica de output único.
version: 0.1.0
status: draft
---

# nexus-wargame — planos que herdam julgamento

> **Contrato:** um plano normal descreve o caminho optimista e cobre ~80% do trabalho; os 20% difíceis (excepções) ficam por resolver e exigem outra vez um modelo caro em tempo real. Um war-game descreve cada passo com o que se vê SE funciona, o que se vê SE falha, a causa provável, o sinal de detecção e o contra-movimento — de modo que um executor barato reconheça a falha e reaja sem improvisar. Este skill produz war-games red-teamed até convergirem, gastando o modelo caro uma vez para o transformar num artefacto reutilizável. Custo: disciplina de fan-out + N rondas de red-team. Ganho: o modelo caro deixa de ser necessário para executar.

## Princípio central

Não peças "um plano" ao modelo caro. Pede um **war-game**: combater a missão no papel, movimento a movimento. O ficheiro captura a experiência do modelo caro; um modelo barato executa depois porque as excepções já estão mapeadas. Origem e caso completo: `references/leadgen-avatars-case.md`.

## Os 8 elementos por movimento (não-negociável)

Cada movimento de um war-game declara os 8. Movimento sem os 8 = plano normal disfarçado, rejeitar.

1. Acção (concreta, executável por modelo médio)
2. Observação esperada SE funcionou (específica — o executor tem de a reconhecer)
3. Observação esperada SE falhou
4. Causa de falha mais provável
5. Sinal de detecção (como e quão cedo o executor sabe)
6. Contra-movimento (concreto — "faz X", nunca "tenta outra vez")
7. Trigger de bifurcação (condição que desvia para rota alternativa)
8. Condição de abort (quando parar e escalar para humano)

### Formato exacto (para ser verificável por `grep`)

Cada movimento é um cabeçalho `### M<k> — <título>` seguido de exactamente 8 linhas numeradas, com estes rótulos nesta ordem:

```
### M1 — <título>
1. **Acção:** …
2. **Se funcionou:** …
3. **Se falhou:** …
4. **Causa provável:** …
5. **Detecção:** …
6. **Contra-movimento:** …
7. **Bifurcação:** …
8. **Abort:** …
```

Templates de todas as fases em `templates/`: `spec.md` e `ledger.md` (fase 1), `task-NN.md` e `success.md` (fase 2), `wargame-order.md` (fase 3 e red-team, fase 4). No `wargame-order.md`, `[CAMINHO_SKILL]` é substituído pelo orquestrador pelo caminho absoluto desta skill antes de o entregar ao agente (o agente não conhece o contexto da conversa).

Glossário: **terreno adversarial** = objectivo em que uma plataforma, concorrente ou algoritmo pode fazer falhar o plano (ver `description`). **wave** = lote de agentes paralelos de uma fase, máx 5. **STABLE** = resposta do red-teamer que não encontrou nada material a fortalecer e não editou o ficheiro. **write-back** = escrever de volta, no war-game, a lição de uma falha fora da árvore (fase 7), tornando-o um ficheiro vivo.

## Workflow (7 fases)

O modelo caro (parâmetro `$STRONG`, o mais forte disponível) faz as fases 1-4; modelos baratos (`$CHEAP`, Sonnet/Haiku-class) fazem 5-7.

1. **INTENT + spec** (`$STRONG`) — definir o objectivo, o ICP/alvo (perfil de cliente ideal), os limites duros. Decisões subjectivas do humano vão para um `ledger.md` com **default declarado** por item (executor usa o default ou bloqueia; nunca assume em silêncio).
2. **Decomposição** (`$STRONG`) — partir em 4-6 missões independentes (`tasks/NN-*.md`) + `success.md` com métricas testáveis. Uma missão por ficheiro.
3. **War-game em batch** (`$STRONG`) — 1 agente por missão, em paralelo (**máx 5 por wave**; acima disso, waves sequenciais). Cada um escreve `wargames/NN-*.md` com os 8 elementos por movimento + os fail-modes obrigatórios do domínio. **Pré-alocar gamas de LEDGER-id por missão** (ex. m01→13-18, m02→19-24) — agentes paralelos colidem na numeração senão.
   **Consolidação (após a fase 3, antes da fase 4)** — o orquestrador integra no `ledger.md` canónico os `[LEDGER: ...]` criados dentro de cada war-game (cada um na sua gama pré-alocada), um a um, com default declarado. Se dois war-games decidirem a mesma questão com granularidade diferente (um item largo vs. dois estreitos), o orquestrador decide qual fica e regista a decisão no próprio `ledger.md`; o red-team usa a numeração canónica resultante.
4. **Loop de red-team até convergir** (`$STRONG`) — 1 red-teamer hostil por war-game, em paralelo. Fortalece os 3 movimentos mais fracos OU responde "STABLE" sem editar. Repetir em rondas: ronda N+1 só re-examina os que a ronda N editou (+ coerência cruzada das edições). **Convergência = uma ronda devolve STABLE em todos.** Tipicamente 2-3 rondas; findings encolhem cada ronda (defeito grande → coerência entre edições → zero). Ver tabela de rondas abaixo.
5. **Materialização** (`$CHEAP`) — executor transforma war-games em assets concretos, seguindo-os como única fonte de julgamento. Situação não coberta → PÁRA e sinaliza, não inventa.
6. **Execução** (`$CHEAP`) — operar dentro dos guardrails. Cada acção mapeia a um movimento; observação = falha → contra-movimento; observação = nada → escala.
7. **Review + write-back** (`$CHEAP`, `$STRONG` pontual) — comparar realidade vs success.md e vs failure-tree. Falha DENTRO da árvore → contra-movimento previsto. Falha FORA da árvore → escala a `$STRONG` + humano, e escreve a lição de volta no war-game (ficheiro vivo).

## Fail-modes obrigatórios (o red-team verifica que estão cobertos)

Genéricos (adaptar ao domínio): (a) política/ToS da plataforma ou sistema-alvo; (b) trust boundaries — segurança, legal/RGPD, dano a terceiros — como **abort duro, nunca contornar**; (c) cold start / arranque sem tracção; (d) detecção adversarial (shadowban, rate-limit, ban). Domínio específico acrescenta os seus (ex. info que magoa o utilizador, crise no destino) — declara-os no prompt de cada war-game.

## Convergência do red-team

| Ronda | Foco | Sinal de saída |
|---|---|---|
| 1 | Fortalecer 3 movimentos mais fracos por ficheiro | Todos passam 1x |
| 2 | Coerência das edições da ronda 1 (pointers, contradições, dependências implícitas entre ficheiros) | Só re-examina editados |
| 3+ | Verificar residuais das correcções da ronda 2 | **STABLE em todos = fechado** |

Entre rondas, o orquestrador regista `sha256sum wargames/*.md > rondas/rN.sha256` no fim de cada ronda. Convergência = `sha256sum -c rondas/r(N-1).sha256` passa sem diferenças (zero edições, ficheiros byte-idênticos) **e** todos os red-teamers devolveram STABLE. Não é regresso infinito — o ponto fixo é "uma ronda devolve zero edições".

## Variante mínima (sem fan-out)

Para quem não tem subagentes ou quer gastar pouco: **1 war-game** (uma só missão, a de maior risco), **1 red-teamer**, tudo sequencial, no mesmo `$STRONG`; ledger e `success.md` curtos. Perde-se: o paralelismo (e o custo de ~12 invocações do fluxo completo cai para ~3-4), a cobertura das restantes missões (ficam sem war-game; o executor barato PÁRA nelas em vez de improvisar) e a coerência cruzada entre war-games (a ronda 2 só tem um ficheiro para examinar). Convergência mantém-se: repetir o red-team até STABLE. Usar quando o terreno adversarial está concentrado numa missão, ou como primeira passagem antes de decidir se compensa o fluxo completo. Se houver >1 missão com risco real de falha, usar o fluxo completo.

## Quando NÃO usar

- Plano linear/sequencial sem terreno adversarial → `nexus-plan` (plano curto) ou `nexus-plan-spec` (build spec).
- Spec de build de software para outro modelo executar → `nexus-plan-spec`.
- Lição/gotcha desta sessão → `nexus-learner`.
- Tarefa mecânica de output único, sem excepções que valha a pena mapear → executa directo.
- Automação que o harness deve FORÇAR → hook, não skill.

## Verificação (o utilizador confirma assim)

1. Cada war-game tem movimentos com os **8 elementos** no formato fixo (ver «Formato exacto»). Verifica (a partir da raiz do projecto; `F` = ficheiro do war-game):
   ```bash
   F=wargames/01-exemplo.md; M=$(grep -cE '^### M[0-9]+ ' "$F"); echo "movimentos=$M"
   for p in '1. \*\*Acção' '2. \*\*Se funcionou' '3. \*\*Se falhou' '4. \*\*Causa provável' '5. \*\*Detecção' '6. \*\*Contra-movimento' '7. \*\*Bifurcação' '8. \*\*Abort'; do
     n=$(grep -cE "^$p:\*\*" "$F"); [ "$n" -eq "$M" ] && echo "OK  $p ($n)" || echo "FALTA $p: $n de $M"; done
   ```
   Tudo `OK` (e `M` ≥ 1) = os 8 elementos presentes em todos os movimentos.
2. Red-team convergiu: última ronda = STABLE em todos, tamanhos byte-estáveis vs ronda anterior.
3. Os 4 fail-modes obrigatórios estão cobertos em cada war-game (o red-team reporta-o).
4. **Teste real da tese:** um executor `$CHEAP` produz a fase 5 respeitando os gates dos war-games **sem improvisar** — e uma revisão independente encontra só findings do tipo já previsto. Se o executor barato improvisa fora da árvore, o war-game não estava completo → volta à fase 4.

## Anti-padrões

| Anti-padrão | Correcção |
|---|---|
| Pedir "plano" ao modelo caro | Pede war-game — os 8 elementos por movimento |
| Modelo caro a EXECUTAR o projecto | Modelo caro só war-gameia (fases 1-4); barato executa (5-7) |
| Agentes paralelos colidem em LEDGER-id | Pré-alocar gamas por missão antes do fan-out |
| >5 agentes numa wave | Partir em waves sequenciais de 5 |
| Red-team infinito / 1 ronda só | Convergência = ronda devolve STABLE em todos (tipic. 2-3) |
| Executor barato inventa fora da árvore | War-game incompleto — volta à fase 4, fortalece esse ramo |
| Ledger sem default → executor assume | Todo o item tem default declarado OU marca-se BLOQUEIA |
| Trust boundary com contorno "esperto" | Abort duro — segurança/legal/dano nunca se contornam |

## Changelog
- v0.1.0 (2026-07-07): criação — extracção do processo executado num projecto de lead-gen (2 personas, 11 war-games, 3 rondas de red-team até STABLE). Modelo caro generalizado para parâmetro `$STRONG`.
- v0.1.1: formato exacto dos 8 elementos + comando de verificação; templates de fase 1-2 (`spec`, `ledger`, `task-NN`, `success`); variante mínima; consolidação de LEDGER; sha256sum entre rondas; glossário.
