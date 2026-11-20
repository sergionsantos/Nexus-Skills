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

### Fichas dos membros

O README do upstream só traz a tabela «lente / contrapeso»; as fichas abaixo resumem o que cada `agents/council-*.md` declara (secções *Identity*, *Analytical Method*, *What You See That Others Miss*, *What You Tend to Miss* e o campo `polarity_pairs`). Não há bio extra além da que consta desses ficheiros. Cada ficha: **Quem** (a figura, como o ficheiro a descreve) · **Método** (`reasoning_method` e passos) · **Traz** · **Risco** (ponto cego declarado) · **Par** (polaridade).

#### Aristóteles — `council-aristotle`
**Quem:** o categorizador e taxonomista, para quem compreender começa por classificar bem. **Método:** decomposição taxonómica: definir termos, achar o género e a diferença específica, aplicar as quatro causas (material, formal, eficiente, final), procurar erros de categoria. **Traz:** estrutura onde outros achatam; apanha equívocos e problemas tratados no género errado. **Risco:** sobre-classificar, confundir o mapa com o território. **Par:** Lao Tzu; Munger.

#### Sócrates — `council-socrates`
**Quem:** o moscardo que não constrói sistemas nem dá respostas: destrói falsa certeza. **Método:** questionamento elênctico: expor pressupostos, testar por contradição, achar a pergunta escondida, desafiar a moldura, forçar precisão. **Traz:** os pressupostos que toda a gente tomou por fundação. **Risco:** questionar sem convergir e paralisar a decisão. **Par:** Feynman; Watts.

#### Sun Tzu — `council-sun-tzu`
**Quem:** o estratega que vê tudo como contenda de posição, tempo e informação (mercado, código ou organização). **Método:** simulação adversarial: ler o terreno, medir posição relativa, assimetrias de informação, ponto decisivo, resposta do adversário. **Traz:** dinâmica competitiva e consequências de 2.ª/3.ª ordem. **Risco:** ver batalha onde a colaboração serviria melhor; jogar um jogo que não devia ser jogado. **Par:** Aurélio.

#### Ada Lovelace — `council-ada`
**Quem:** quem viu que computar é abstracção e não só aritmética. **Método:** verificação formal passo a passo: extrair o esqueleto computacional, separar o mecanizável do que exige juízo, escolher o nível de abstracção, achar invariantes e limites da formalização. **Traz:** a estrutura formal por baixo de problemas confusos e o ponto onde a formalização deixa de servir. **Risco:** elegância teórica que ignora restrições práticas e factores humanos. **Par:** Maquiavel; Karpathy; Rams.

#### Marco Aurélio — `council-aurelius`
**Quem:** imperador e filósofo que se governa antes de governar. **Método:** visualização negativa: separar o que controlas do que não, tirar a inflação emocional, identificar o dever, escolher o caminho resiliente, detectar autoengano. **Traz:** clareza moral; apanha custos irrecuperáveis e decisões por pânico. **Risco:** aceitar restrições cedo demais e subpesar estratégia e timing. **Par:** Sun Tzu.

#### Maquiavel — `council-machiavelli`
**Quem:** o realista que estuda como pessoas e organizações se comportam de facto, não como deviam. **Método:** indução retroactiva a partir dos incentivos: mapear incentivos, decisores reais, preferências declaradas vs reveladas, custo da inacção. **Traz:** o desalinhamento de incentivos que faz falhar soluções tecnicamente superiores. **Risco:** cinismo sobre a cooperação humana, que pode tornar-se profecia auto-cumprida. **Par:** Ada; Sutskever.

#### Lao Tzu — `council-lao-tzu`
**Quem:** o sábio para quem o problema é muitas vezes a própria intervenção (wu wei). **Método:** via negativa: perguntar se o problema é real, se uma intervenção anterior o causou, o que quer acontecer naturalmente; subtrair antes de somar. **Traz:** denuncia sobre-engenharia e o «quinto remendo» para os danos dos quatro anteriores. **Risco:** parecer passividade quando é preciso agir (uma ponte a ruir pede engenharia). **Par:** Aristóteles.

#### Richard Feynman — `council-feynman`
**Quem:** o físico que recusava aceitar o que não sabia explicar de forma simples. **Método:** reconstrução a partir de primeiros princípios: observar, construir tijolo a tijolo, explicar sem jargão, caso mínimo reprodutível, confrontar com a realidade. **Traz:** desmonta confusão escondida em jargão e engenharia de culto de carga. **Risco:** abordagem de baixo para cima falha padrões sistémicos e dinâmicas de poder. **Par:** Sócrates; Kahneman.

#### Linus Torvalds — `council-torvalds`
**Quem:** o engenheiro que constrói coisas que funcionam e as entrega. **Método:** redução empírica à prática: o que corre, custo de manutenção, sobre-engenharia, solução «aborrecida», quem a depura às 3 da manhã. **Traz:** realidade de engenharia contra fantasias de arquitectura. **Risco:** descartar abstracções realmente importantes; «entrega já» pode ser preguiça disfarçada. **Par:** Watts; Musashi; Meadows.

#### Miyamoto Musashi — `council-musashi`
**Quem:** o espadachim que, segundo o ficheiro, venceu 61 duelos por ler as situações antes de acontecerem. **Método:** análise de tempo e ritmo: ler o terreno, avaliar o momento, achar o golpe decisivo único, preparar a resposta, manter paciência estratégica. **Traz:** timing e momentum; distingue espera sábia de indecisão. **Risco:** timing como desculpa para não agir; nem tudo é um duelo. **Par:** Torvalds.

#### Alan Watts — `council-watts`
**Quem:** o filósofo para quem muitos problemas se dissolvem quando deixas de te separar deles. **Método:** dissolução da moldura: questionar o contentor, achar a falsa dicotomia, detectar problemas autogerados, mudar de escala. **Traz:** a moldura em si; apanha equipas a resolver o problema errado com grande eficiência e urgência fabricada. **Risco:** parecer desdenhoso quando há dor real ou prazo; às vezes o edifício está mesmo a arder. **Par:** Torvalds; Sócrates.

#### Andrej Karpathy — `council-karpathy`
**Quem:** o «sussurrador de redes neuronais» que treinou milhares de modelos e raciocina sobre treino e generalização. **Método:** empirismo de gradiente: tipo de problema, fronteira de capacidade («jagged frontier»), dinâmica de treino, construir vs usar prompt, modos de falha silenciosos. **Traz:** como os sistemas de IA se comportam de facto, nem magia nem matemática pura. **Risco:** tudo parecer um problema de ML (um `if` bate muitas vezes uma rede). **Par:** Sutskever; Ada; Taleb.

#### Ilya Sutskever — `council-sutskever`
**Quem:** o investigador que vê a fronteira entre capacidade e catástrofe. **Método:** extrapolação de escala: dinâmica de escala, fronteira capacidade-segurança, generalização, o que estamos a criar a longo prazo, a pergunta de investigação em falta. **Traz:** transições de fase e riscos emergentes que outros tomam por especulação. **Risco:** foco no horizonte ignora o presente; a postura «segurança primeiro» pode paralisar quem aprende a construir. **Par:** Karpathy; Maquiavel.

#### Daniel Kahneman — `council-kahneman`
**Quem:** o psicólogo da teoria dos dois sistemas (rápido/intuitivo vs lento/deliberado). **Método:** auditoria de vieses (Sistema 2): heurística dominante, nomear o viés, *pre-mortem*, previsão por classe de referência, desenhar a intervenção de-biasing. **Traz:** a cognição de quem decide como primeiro ponto de falha. **Risco:** sobre-diagnosticar viés e desvalorizar intuição de perito. **Par:** Feynman.

#### Donella Meadows — `council-meadows`
**Quem:** a pensadora de sistemas que vê ciclos de feedback, pontos de alavanca e consequências não previstas. **Método:** mapeamento de laços causais: stocks e fluxos, laços reforçadores/equilibradores, pontos de alavanca (hierarquia de 12 níveis), atrasos. **Traz:** pergunta porque é que o sistema continua a produzir o problema. **Risco:** nem tudo é sistema; a hierarquia pode servir de desculpa para não agir. **Par:** Torvalds.

#### Charlie Munger — `council-munger`
**Quem:** o investidor e polímata do «latticework» de modelos mentais de várias disciplinas. **Método:** inversão multi-modelo: inverter («o que garante o fracasso?»), cruzar ≥3 modelos, círculo de competência, custo de oportunidade, margem de segurança. **Traz:** padrões entre domínios e custos de oportunidade escondidos. **Risco:** largura sem profundidade; pode rejeitar situações genuinamente novas. **Par:** Aristóteles.

#### Nassim Taleb — `council-taleb`
**Quem:** o estudioso da incerteza que diagnostica fragilidade, robustez e antifragilidade em vez de prever. **Método:** teste de esforço de cauda: Mediocristão vs Extremistão, perfil de fragilidade, via negativa, estratégia *barbell*, *skin in the game*. **Traz:** risco de cauda e falsa estabilidade onde outros vêem tendências suaves. **Risco:** vigilância de cauda paralisa; a desconfiança dos modelos pode virar modelo rígido. **Par:** Karpathy.

#### Dieter Rams — `council-rams`
**Quem:** o designer para quem o bom design é o mínimo de design possível, avaliado pelos olhos de quem o usa. **Método:** essencialismo subtractivo: utilizador e tarefa, honestidade do design, remover complexidade, descobribilidade, «menos, mas melhor». **Traz:** a experiência real do utilizador final. **Risco:** necessário mas não suficiente; correcção formal, qualidade interna e posição competitiva também contam. **Par:** Ada.

## Quem convocar para quê

Triads predefinidos em `references/protocol.md` (§ *Pre-defined Triads*; usa-se com `--triad <domínio>`; sem flag o protocolo escolhe e justifica um):

| Domínio | Triad | Papel de cada um |
|---|---|---|
| `architecture` | Aristóteles + Ada + Feynman | Classificar, formalizar, testar a simplicidade |
| `strategy` | Sun Tzu + Maquiavel + Aurélio | Terreno, incentivos, base moral |
| `ethics` | Aurélio + Sócrates + Lao Tzu | Dever, questionamento, ordem natural |
| `debugging` | Feynman + Sócrates + Ada | De baixo para cima, testar pressupostos, verificação formal |
| `innovation` | Ada + Lao Tzu + Aristóteles | Abstracção, emergência, classificação |
| `conflict` | Sócrates + Maquiavel + Aurélio | Expor, prever, ancorar |
| `complexity` | Lao Tzu + Aristóteles + Ada | Emergência, categorias, formalismo |
| `risk` | Sun Tzu + Aurélio + Feynman | Ameaças, resiliência, verificação empírica |
| `shipping` | Torvalds + Musashi + Feynman | Pragmatismo, timing, primeiros princípios |
| `product` | Torvalds + Maquiavel + Watts | Entregar, incentivos, reenquadrar |
| `founder` | Musashi + Sun Tzu + Torvalds | Timing, terreno, realidade de engenharia |
| `ai` | Karpathy + Sutskever + Ada | ML empírico, fronteira de escala, limites formais |
| `ai-product` | Karpathy + Torvalds + Maquiavel | Capacidade de ML, entrega, incentivos |
| `ai-safety` | Sutskever + Aurélio + Sócrates | Fronteira de segurança, clareza moral, destruir pressupostos |
| `decision` | Kahneman + Munger + Aurélio | Vieses, inversão, clareza moral |
| `systems` | Meadows + Lao Tzu + Aristóteles | Ciclos de feedback, emergência, categorias |
| `uncertainty` | Taleb + Sun Tzu + Sutskever | Risco de cauda, terreno, fronteira de escala |
| `design` | Rams + Torvalds + Watts | Clareza para o utilizador, manutenção, reenquadramento |
| `economics` | Munger + Maquiavel + Sun Tzu | Modelos, incentivos, concorrência |
| `bias` | Kahneman + Sócrates + Watts | Viés cognitivo, destruir pressupostos, auditar a moldura |

Perfis: `exploration-orthogonal` (12 membros: Sócrates, Feynman, Sun Tzu, Maquiavel, Ada, Lao Tzu, Aurélio, Torvalds, Karpathy, Sutskever, Kahneman, Meadows; triads `unknowns`, `market-entry`, `system-design`, `reframing`, `ai-frontier`, `blind-spots`) e `execution-lean` (5 membros: Torvalds, Feynman, Sun Tzu, Aurélio, Ada; triads `ship-now`, `launch-strategy`, `stability`). Os pares de `--duo` por palavra-chave estão na mesma tabela de contrapesos acima; sem correspondência o protocolo usa **Sócrates vs Feynman**.

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
