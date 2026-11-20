# Autoria paralela e economia de tokens — casos medidos

Duas observações de runs reais do pipeline exaustivo, generalizadas (sem nomes de projecto).

## 1. Autoria paralela cega gera colisões

**Caso:** 6 milestones autorados em paralelo por 6 agentes fortes, cada um cego aos outros. A qualidade DENTRO de cada milestone foi alta (4 lentes de red-team independentes confirmaram âncoras e grounding quase perfeitos). MAS todos os findings MAJOR/BLOCKER vieram da paralelização cega:

- (a) a **mesma migration (nº seguinte)** reclamada por 2 milestones (ambos leram "o mais alto é 0020, logo o próximo livre é 0021");
- (b) **3 colisões de âncora**: milestones a editar o mesmo ficheiro de navegação/layout, cada um a inserir a sua linha no mesmo ponto — a âncora de um deixa de bater depois de o outro correr;
- (c) **2 substituições integrais** de ficheiro por um milestone posterior que apagaram, sem herdar, o edit de um milestone anterior;
- (d) **1 milestone reverteu um fix** já feito por outro.

Custo de apanhar depois: 4 agentes de red-team + 2 de fix (~1M+ tokens). Custo do pre-flight que teria prevenido: uma tabela "ficheiro/recurso → milestone dono" antes de disparar (minutos, <5k tokens).

**Pre-flight (antes de disparar autores paralelos):**
1. Lista os ficheiros que mais de um milestone toca e o próximo número livre de cada sequência global (migrations, D#, F#).
2. Atribui cada recurso contestado a UM milestone.
3. Define quem emite a listagem final integral de cada ficheiro partilhado.
4. Põe no prompt comum as **invariantes transversais** (ex.: "todos os /api/* exigem `Authorization`", formato de arranque, chaves vivas).

Pre-flight e red-team são complementares: o primeiro mata colisões estruturais; o segundo apanha bugs de lógica que existem mesmo com um só autor (um import não usado que parte o build, um `React.memo` anulado por refs instáveis).

## 2. Custo do pipeline exaustivo (8 milestones, 43 steps, ~300 KB de plano, modelo forte em todas as fases)

| Fase | Tokens | Agentes |
|---|---|---|
| Autoria paralela (2 waves) | 1,15M | 8 |
| Red-team 5 lentes | 0,95M | 5 |
| Fix-pass | 0,88M | 8 |
| Verify-dos-fixes | 0,27M | 2 |
| **Total** | **~3,25M** | 23 |

Qualidade: 26 findings no 1.º passe (6 BLOCKER) → convergência em 2 ciclos. Compensou (apanhou uma chave de acesso inválida, um schema não exposto, um risco de segurança num container partilhado), mas o mesmo resultado era atingível com cerca de metade:

1. **Red-team: 2 lentes chegam para o grosso (~−30%).** Executabilidade literal + cross-milestone apanharam quase todos os findings únicos; as outras deram sobretudo duplicados do mesmo cluster. Lente de DB/infra extra só para milestones com DB/infra partilhada, apontada só a esses ficheiros.
2. **Modelo por fase (~−40% nas fases de volume).** Forte nos milestones de juízo denso (infra partilhada, auth, integração final); médio nos mecânicos. Fixers em modelo médio sempre que o finding traz file:line + fix sugerido (é colagem). Verify-dos-fixes em forte (detecção, barato).
3. **Digest de grounding partilhado (~−15% na autoria).** Em vez de cada agente re-ler spec + README + código (~30-50k de custo fixo × N agentes), o orquestrador produz UM digest (~10-15k) e injecta-o no prompt.
4. **O cluster de findings mais caro era prevenível no prompt.** Um BLOCKER transversal (cabeçalho de autenticação em falta em ~50 comandos de 6 ficheiros) nasceu de o prompt comum não incluir o facto "todos os endpoints exigem autenticação": 1 linha no pre-flight teria evitado ~40% dos findings.
5. **Falsos positivos conhecidos do validador custam um ciclo.** Inclui no prompt comum: cabeçalho `### Step M<N>.<M> — título`; "duplicate step IDs" pode ser falso positivo em cross-refs.

Estimativa com 1-5 aplicados: ~1,2-1,5M para o mesmo plano com a mesma qualidade final.
