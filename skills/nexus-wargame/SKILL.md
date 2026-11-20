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

Não peças "um plano" ao modelo caro. Pede um **war-game**: combater a missão no papel, movimento a movimento. O ficheiro captura a experiência do modelo caro; um Sonnet-class executa depois porque as excepções já estão mapeadas. Origem e caso completo: `references/leadgen-avatars-case.md`.

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

## Workflow (7 fases)

O modelo caro (parâmetro `$STRONG`, o mais forte disponível) faz as fases 1-4; modelos baratos (`$CHEAP`, Sonnet/Haiku-class) fazem 5-7.

1. **INTENT + spec** (`$STRONG`) — definir o objectivo, o ICP/alvo (perfil de cliente ideal), os limites duros. Decisões subjectivas do humano vão para um `ledger.md` com **default declarado** por item (executor usa o default ou bloqueia; nunca assume em silêncio).
2. **Decomposição** (`$STRONG`) — partir em 4-6 missões independentes (`tasks/NN-*.md`) + `success.md` com métricas testáveis. Uma missão por ficheiro.
3. **War-game em batch** (`$STRONG`) — 1 agente por missão, em paralelo (**máx 5 por wave**; acima disso, waves sequenciais). Cada um escreve `wargames/NN-*.md` com os 8 elementos por movimento + os fail-modes obrigatórios do domínio. **Pré-alocar gamas de LEDGER-id por missão** (ex. m01→13-18, m02→19-24) — agentes paralelos colidem na numeração senão.
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

Byte-idêntico entre rondas + zero edições reportadas = convergido. Não é regresso infinito — o ponto fixo é "uma ronda devolve zero edições".

## Quando NÃO usar

- Plano linear/sequencial sem terreno adversarial → `nexus-plan` (plano curto) ou `nexus-plan-spec` (build spec).
- Spec de build de software para outro modelo executar → `nexus-plan-spec`.
- Lição/gotcha desta sessão → `nexus-learner`.
- Tarefa mecânica de output único, sem excepções que valha a pena mapear → executa directo.
- Automação que o harness deve FORÇAR → hook, não skill.

## Verificação (o utilizador confirma assim)

1. Cada war-game tem movimentos com os **8 elementos** — `grep -c` a marcadores dos 8 num ficheiro deve bater com nº de movimentos × 8, ou inspecção visual de 1 movimento.
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
