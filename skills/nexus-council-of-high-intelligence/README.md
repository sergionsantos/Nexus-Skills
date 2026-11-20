# nexus-council-of-high-intelligence

Conselho de **18 pensadores fixos** (Aristóteles, Sócrates, Feynman, Sun Tzu, Ada Lovelace, Taleb, Kahneman, Munger, Meadows, Torvalds, Rams, …) que debate uma decisão real em rondas e devolve um veredicto estruturado. Cada membro corre como **subagente independente**, definido em `agents/`.

O conselho atribui a pergunta difícil a personas analiticamente diferentes, mantém as primeiras posições independentes, força o desacordo directo e devolve um veredicto que preserva as questões por resolver, a dissidência, os critérios de falha e o próximo passo concreto.

## Quando usar

Convoca o conselho quando a decisão tem **risco material, valores em conflito, evidência incompleta ou irreversibilidade**. Frases que activam a skill: «convoca o conselho», «council this», «stress-test / pressure-test / war room desta decisão», «o que diria o conselho sobre…».

### Quando NÃO usar
- Factos ou consultas de documentação: responde-se directamente.
- Escolhas baratas e reversíveis: faz-se a experiência (ou usa `--quick` / `--duo`).
- Criação pura (escrever, desenhar algo de raiz) sem decisão em jogo.
- Para fabricar apoio a uma resposta que já escolheste.
- Se queres a opinião de **uma pessoa concreta** à tua escolha, usa antes `nexus-persona-council` (ver abaixo).

## Como invocar

Pede em linguagem natural ou com flags (o `SKILL.md` define o modo; ver «Modos»):

```text
Convoca o conselho: devemos tornar open-source o nosso framework de agentes?
Council --quick: devemos lançar hoje ou esperar pela revisão de segurança?
Council --duo --members torvalds,ada: esta abstracção compensa o custo?
Council --triad risk: o que pode tornar este lançamento irreversível?
Council --full: qual é o modelo de preços certo para o produto?
```

Antes de convocar, escreve a decisão, as restrições, a evidência, a reversibilidade e o prazo: o veredicto é tão bom quanto o caso que lhe dás.

## Modos

| Modo | Forma | Quando |
|---|---|---|
| **Triad** (por omissão, ou `--triad <domínio>`) | 3 membros; análise cega, contra-interrogatório anónimo, posição final, síntese | Decisão com risco; o protocolo escolhe o triad e justifica |
| `--full` | Os 18 membros | Apostas altas, várias molduras concorrentes |
| `--members a,b,c` | Selecção explícita de 2–11 membros | Controlas tu o painel |
| `--profile <nome>` | Perfil de painel: `classic` (18), `exploration-orthogonal` (12), `execution-lean` (5) | Descoberta de «incógnitas desconhecidas» ou ciclo rápido decisão→acção |
| `--quick` | Restatement + análise rápida (≤200 palavras) + posição final (≤75), **sem contra-interrogatório** | Precisas de amplitude, não de adversarial completo |
| `--duo` (ou dois membros nomeados) | Par de polaridade: posições, resposta directa, declarações finais | Uma só tensão define a decisão |

Triads disponíveis (`references/protocol.md`): `architecture`, `strategy`, `ethics`, `debugging`, `innovation`, `conflict`, `complexity`, `risk`, `shipping`, `product`, `founder`, `ai`, `ai-product`, `ai-safety`, `decision`, `systems`, `uncertainty`, `design`, `economics`, `bias`. Os perfis acrescentam triads próprios (`unknowns`, `market-entry`, `system-design`, `reframing`, `ai-frontier`, `blind-spots`; `ship-now`, `launch-strategy`, `stability`). O modo, o painel e o lugar de peso 1,5× do domínio ficam fixados **antes** da Ronda 1.

## Os 18 membros

Tabela construída a partir do bloco `council:` de cada `agents/council-*.md`. «Polaridade» é o rótulo do próprio ficheiro; «Contrapesos» são os pares de polaridade definidos no protocolo (usados em `--duo`).

| Membro | Ficheiro | Domínio / lente | Polaridade | Contrapesos principais |
|---|---|---|---|---|
| Aristóteles | `council-aristotle` | Categorização e estrutura | Classifica tudo | Lao Tzu; Munger |
| Sócrates | `council-socrates` | Destruição de pressupostos | Questiona tudo | Feynman; Watts |
| Sun Tzu | `council-sun-tzu` | Estratégia adversarial | Lê terreno e concorrência | Aurélio |
| Ada Lovelace | `council-ada` | Sistemas formais e abstracção | O que pode / não pode ser mecanizado | Maquiavel; Karpathy; Rams |
| Marco Aurélio | `council-aurelius` | Resiliência e clareza moral | Controlo vs aceitação | Sun Tzu |
| Maquiavel | `council-machiavelli` | Dinâmicas de poder, realpolitik | Como os actores realmente se comportam | Ada; Sutskever |
| Lao Tzu | `council-lao-tzu` | Não-acção e emergência | Quando menos é mais | Aristóteles |
| Richard Feynman | `council-feynman` | Debugging de primeiros princípios | Recusa complexidade inexplicada | Sócrates; Kahneman |
| Linus Torvalds | `council-torvalds` | Engenharia pragmática | Entrega ou cala-te | Watts; Musashi; Meadows |
| Miyamoto Musashi | `council-musashi` | Timing estratégico | O golpe decisivo | Torvalds |
| Alan Watts | `council-watts` | Perspectiva e reenquadramento | Dissolve falsos problemas | Torvalds; Sócrates |
| Andrej Karpathy | `council-karpathy` | Intuição de redes neuronais e ML empírico | Como os modelos realmente aprendem e falham | Sutskever; Ada; Taleb |
| Ilya Sutskever | `council-sutskever` | Fronteira de escala e segurança de IA | Quando a capacidade se torna risco | Karpathy; Maquiavel |
| Daniel Kahneman | `council-kahneman` | Viés cognitivo e ciência da decisão | O teu próprio pensamento é o primeiro erro | Feynman |
| Donella Meadows | `council-meadows` | Pensamento sistémico, ciclos de feedback | Redesenha o sistema, não o sintoma | Torvalds |
| Charlie Munger | `council-munger` | Raciocínio multi-modelo e economia | Inverte: o que garante o fracasso? | Aristóteles |
| Nassim Taleb | `council-taleb` | Antifragilidade e risco de cauda | Desenha para a cauda, não para a média | Karpathy |
| Dieter Rams | `council-rams` | Design centrado no utilizador | Menos, mas melhor: decide o utilizador | Ada |

Os membros são instrumentos analíticos, não pretensões de personificação. Cada `agents/council-*.md` define identidade, método e formato de resposta (inclui os formatos por ronda).

## Como corre (protocolo)

Fonte autoritativa: `references/protocol.md` (o `SKILL.md` diz quais as partes que se aplicam com subagentes de um só fornecedor).

1. **Restatement** — cada membro reformula o problema e propõe um enquadramento alternativo (≤50 palavras); divergências grandes são sinalizadas.
2. **Ronda 1, análise cega** (≤400 palavras) — em paralelo, cada membro só vê o problema.
3. **Ronda 2, contra-interrogatório anónimo** (≤300 palavras) — membros rotulados A/B/C, sem auto-atribuição; cada um avalia afirmações concretas de pares.
4. **Verificação pós-ronda** (STEP 4) — revisão de objecções suportadas, *novelty gate*, desafio de pressuposto opcional, etiquetas de evidência, anti-recursão. Uma objecção só conta com facto/fonte relevante (com localização), mecanismo causal e falsificador observável; no máximo um pedido de reparação por objecção. Concordância nunca dispara reforço.
5. **Ronda 3, cristalização** (≤100 palavras) — termina com a linha exacta `STANCE: … | CONFIDENCE: high|med|low | DEALBREAKER: yes|no`.
6. **Contagem** — peso base 1,0 (1,5× no lugar do domínio); confiança high/med/low = 1,0/0,75/0,5; consenso se o peso da opção ≥ 2/3 do peso base total. Abaixo disso **não se força consenso**: apresenta-se o impasse.
7. **Veredicto** — escrito pela sessão principal (Chairman); não se lança outro agente.

### Formato do veredicto
Modelo exacto em `references/protocol.md` (secção *Output Templates*): Problema, Composição do conselho, Chairman, Roteamento, Compromissos aceitáveis, **Critérios de falha**, **Próximo passo concreto** (um só), **Questões por resolver** (lidera), Consenso, Contagem de votos, Insights por membro, Pontos de desacordo, **Relatório de minoria**, Scorecard de diversidade epistémica, Follow-up e Metadados da sessão. Existem variantes Quick e Duo. Etiquetas de evidência: `FACT`, `INFERENCE`, `ASSUMPTION`, `UNKNOWN`.

## Custo

Cada ronda lança todos os membros em paralelo como subagentes: um painel de 3 gasta 3 subagentes por ronda e `--full` gasta 18 por ronda, mais eventuais repetições pontuais (reparação de objecção, linha `STANCE` em falta). [Dedução do protocolo, o `SKILL.md` não indica um número.] Usa `--quick`, `--duo` ou um triad quando a decisão não justifica o painel completo.

## Instalação

Copia (ou faz symlink de) esta pasta inteira — mantém `agents/`, `references/` e `LICENSE` ao lado do `SKILL.md`:

```bash
# Claude Code (macOS / Linux)
cp -r nexus-council-of-high-intelligence ~/.claude/skills/
# Codex
cp -r nexus-council-of-high-intelligence ~/.codex/skills/
```

```powershell
# Windows (PowerShell)
Copy-Item -Recurse nexus-council-of-high-intelligence "$HOME\.claude\skills\"
Copy-Item -Recurse nexus-council-of-high-intelligence "$HOME\.codex\skills\"
```

Abre uma sessão nova. Requisito único: capacidade de lançar subagentes em paralelo (por exemplo a ferramenta Task/Agent do Claude Code). Não precisa de serviços externos.

> Esta skill não inclui o `install.sh` nem o plugin de marketplace do upstream; a instalação é por cópia da pasta.

## Origem, créditos e diferenças face ao upstream

Fork (MIT) de [`0xNyk/council-of-high-intelligence`](https://github.com/0xNyk/council-of-high-intelligence) (© 2026 nyk). O `LICENSE` é o original, sem alterações.

Comparado ficheiro a ficheiro com o upstream:

- **Idênticos ao original:** os 18 `agents/*.md`, `scripts/detect-providers.sh`, `configs/auto-route-defaults.yaml` e `LICENSE`.
- **`SKILL.md`:** novo. Em vez do `SKILL.md` do upstream (que serve de protocolo), este é um invólucro que fixa a execução com **subagentes de um só fornecedor**, ignora a detecção de fornecedores/roteamento externo (`codex_exec`, `gemini_cli`, `ollama_run`, `cursor_cli`, `openai_compatible_api`, `--models`, `--dry-route`, `--no-auto-route`, `.council.yaml`) e declara `provider_count: 1`.
- **`references/protocol.md`:** é o `SKILL.md` do upstream, com (a) caminhos adaptados a esta pasta (`<skill>/agents/…` em vez de `~/.claude/agents/…` / plugin) e (b) duas alterações de conteúdo: o antigo «dissent quota» (mínimo de 2 dissidentes) foi substituído por **revisão de objecções suportadas**, e o *novelty gate* e o prompt da Ronda 2 passaram a exigir objecções com facto, mecanismo e falsificador, sem obrigar a discordar.
- **`configs/provider-model-slots*.example.yaml` (3 ficheiros):** diferem do upstream só nas chaves de enforcement, que reflectem a alteração acima (`supported_objection_review`, `assumption_challenge` em vez de `force_counterfactual_if_consensus_gt` / `require_dissenting_members`).
- **Não incluído do upstream:** `SKILL.codex.md`/`SKILL.gemini.md`/`SKILL.opencode.md`, `install.sh`, plugin Claude (`.claude-plugin/`), `demos/`, `assets/`, scripts de validação, `CHANGELOG`, `CONTRIBUTING`, `SECURITY`.

Referência do projecto original: README e árvore em <https://github.com/0xNyk/council-of-high-intelligence>.

## Relação com `nexus-persona-council`

Skill irmã neste repositório (`../nexus-persona-council/`), com propósito diferente:

- **Esta skill:** 18 membros **fixos** já incluídos, sem preparação, com protocolo único e rígido.
- **`nexus-persona-council`:** personas **à tua escolha** (modos `solo`, `counsel`, `battle`, `lens`; 1.º argumento obrigatório).
- Pensadores históricos genéricos → esta. «O que diria a pessoa X» → a outra.

## Estrutura de pastas

```text
SKILL.md                      ponto de entrada (execução com subagentes)
README.md                     este ficheiro
LICENSE                       MIT, © 2026 nyk (original)
agents/                       18 contratos de membro (council-*.md)
references/protocol.md        protocolo canónico: tabelas, prompts, enforcement, templates
configs/                      exemplos de roteamento multi-fornecedor (opcionais, não usados por omissão)
scripts/detect-providers.sh   detecção de fornecedores (opcional; bash + perl; não usado por omissão)
```

## Licença

MIT. Copyright (c) 2026 nyk. Ver [`LICENSE`](LICENSE). Mantém o aviso de copyright e a licença em qualquer redistribuição.
