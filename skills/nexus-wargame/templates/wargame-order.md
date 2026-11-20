# Template — "War-game order" (prompt de fase 3, 1 por missão)

Substituir `[...]`. Dar a UM agente `$STRONG` por missão, em paralelo (máx 5/wave).

```
WAR-GAME ORDER — não estás a executar nada, estás APENAS a war-gamear no papel.

Autor de war-game para a missão [NN — NOME] do projecto [PROJECTO / avatar / alvo].
Contexto de 1 linha: [o que é, para quem]. Um executor mais barato (classe Sonnet)
vai executar usando SÓ o teu ficheiro como fonte de julgamento — cada excepção que
não antecipares é uma falha que ele não sabe tratar.

LÊ PRIMEIRO (por esta ordem):
1. SKILL.md desta skill (os 8 elementos e os 4 fail-modes genéricos) + o spec do projecto
2. [spec/persona/objectivo]
3. [tasks/NN-*.md — esta missão]
4. [success.md]
5. [ledger.md — decisões humanas; defaults autorizados contam como decisão de trabalho]
6. [OPCIONAL: 1 war-game já feito, como referência de calibre]

Combate a missão no papel, movimento a movimento. Para CADA movimento declara os 8:
1. Acção (concreta, executável por modelo médio)
2. Observação esperada SE funcionou
3. Observação esperada SE falhou
4. Causa de falha mais provável
5. Sinal de detecção (como e quão cedo o executor sabe)
6. Contra-movimento (concreto, não "tenta outra vez")
7. Trigger de bifurcação
8. Condição de abort (parar e escalar)

Cenários de falha OBRIGATÓRIOS além dos 4 fail-modes de SKILL.md (ToS = termos de serviço da plataforma, trust-boundary,
cold-start, detecção-adversarial): [LISTA ESPECÍFICA DO DOMÍNIO — os modos de falha
que só existem aqui].
Vai 2-3 ordens de consequência fundo nos ramos de maior risco.
Lista UNKNOWN UNKNOWNS (perguntas que o orquestrador não sabia que devia fazer) e
war-gameia os 3 principais.
Assunções não resolvidas → [LEDGER: ...] usando SÓ a gama LEDGER-[XX a YY]
(pré-alocada para esta missão; NÃO uses outras — colidem com os war-games paralelos).

ESCREVE (PT-PT, markdown) em [wargames/NN-*.md].
Retorna só: nº de movimentos, nº de branches, top-3 riscos, novos LEDGER criados.
```

# Template — red-team (fase 4)

```
Fase 4 (ronda [N]) — red-teamer hostil de [wargames/NN-*.md].
[Se ronda >1: o que a ronda anterior corrigiu, para verificares coerência residual.]
Numeração LEDGER canónica [XX-YY] — NÃO alterar nem criar IDs.

Para cada movimento: a observação de falha é ESPECÍFICA o suficiente para um
executor Sonnet a reconhecer? O contra-movimento é executável sem humano, ou tem
abort/escalate marcado? Que branch NÃO foi explorado (mudança de política/
concorrente/algoritmo)? [Atenção especial ao gate/ramo de maior risco desta missão.]

Fortalece os 3 movimentos mais fracos editando o ficheiro directamente.
Nada material a fortalecer → responde "STABLE" sem editar.
Retorna: "STABLE" ou lista curta (movimento + o quê).
```
