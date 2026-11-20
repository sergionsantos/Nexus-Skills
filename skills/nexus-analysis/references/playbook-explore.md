# Playbook EXPLORE — multi-lens paralelo

> Objectivo da fase: 4-5 reports de factos com evidência ficheiro:linha, um por lente, ZERO recomendações. As recomendações nascem na síntese (tua), não nos agentes — agente que recomenda contamina a síntese com conclusões não cruzadas.

## Prompt template por agente (copy-paste e preenche)

```
És um agente de exploração READ-ONLY. Lente: <LENTE>.
Superfície: <dirs/ficheiros — ex.: app/src (TS/TSX), app/db/migrations, docker-compose do stack>.
Standard de comparação (se aplicável): <ex.: documento de features do produto de referência>.

REGRAS:
- Só FACTOS com evidência: cada finding termina com `ficheiro:linha` ou comando+resultado.
- Grep com 0 hits é um facto citável ("0 hits de X em Y") — reporta-o.
- ZERO recomendações, zero "dever-se-ia". Se vires algo alarmante, reporta o facto, não a solução.
- Cobre a checklist abaixo; acrescenta o que a lente te mostrar além dela.

CHECKLIST DA LENTE:
<colar a checklist da lente, abaixo>

OUTPUT: lista numerada de findings, agrupados por tema, cada um com evidência.
```

## Checklists por lente (o que cada agente DEVE procurar)

### Lente 1 — Arquitectura/código
- Camadas críticas vs cobertura de testes: lista ficheiros de teste (`find . -name "*.test.*"`) e cruza com os módulos mais críticos (sync, mutations, auth) — o gap é o finding
- Trilhas de fixes em comentários (`grep -rn "FIX\|HACK\|TODO\|D[0-9]\{2\}"`) — densidade de remendos numa zona = fragilidade
- Invalidação/caching: keys usadas ao escrever vs keys usadas ao ler (classe de bug real do exemplo trabalhado: invalidava `search("")` mas as queries activas eram `search(termo)`)
- Operações read-then-write não-atómicas; estado derivado reconstruído por render; last-write-wins não documentado
- Padrões N+1, round-trips múltiplos onde 1 query/RPC resolvia

### Lente 2 — Infra/deploy/segurança
- Secrets em plaintext, keys demo/públicas, tokens em `.env*` (`grep -rn "secret\|key\|password" --include=".env*"` + descodificar JWTs)
- Persistência: o que acontece num reboot? (launchd/systemd/cron presente? processo manual?)
- Divergência config-app vs config-infra (as DUAS pontas do mesmo contrato — auth, CORS, portas)
- Permissões largas (service_role onde anon chegava; bypass de RLS)
- O que parte se o backend reiniciar

### Lente 3 — Gap funcional vs standard
- **A query de ouro:** para cada tabela/coluna do schema, existe UI que a use? (`grep` do nome do campo nos componentes; 0 hits = valor latente). No exemplo trabalhado: `due_date` filtrável+mutável com 0 hits nos forms = melhoria #2
- **⚠️ Cross-check obrigatório do 0-hit (calibração numa app CRM):** quando o frontend fala com uma API própria, os nomes snake_case das tabelas NUNCA aparecem no web (endpoints/tipos camelCase) — a query naive deu 13/14 falsos-positivos. Por cada tabela 0-hit, confirma contra as PÁGINAS reais (nav/rotas) se a feature tem UI via API antes de a declarar latente; e exclui tabelas internas por design (sessões, filas, push_subscriptions). No caso real, de 14 candidatas sobrou 1 gap genuíno (audit_logs)
- Features do standard de comparação em falta (percorre o reference doc item a item)
- Capacidades enterradas: rotas sem link, flags desligadas, tabelas completas com RLS e zero componentes

### Lente 4 — UX/robustez
- Error handling visível: `error.tsx`/`loading.tsx`/boundaries (find), uso de `isError` (grep), retry, offline (`navigator.onLine`)
- "O utilizador distingue 'vazio' de 'partido'?" — procura renders de lista que engolem erro (`data ?? []`)
- Mobile/responsivo: contagem de breakpoints, drawer/sidebar
- Consistência de design: tokens do design system aplicados onde? (grep das cores/fontes novas vs componentes que ainda usam default)
- Operações de dono que exigem SQL/consola em vez de UI

### Lente 5 (opcional) — Integração/ecossistema
- Quem mais (pessoas, agentes, sistemas do dono) beneficiaria de acesso programático? Existe API/MCP/CLI?
- Lógica de escrita presa a client-side (hooks browser) = irreutilizável por automação
- Dados duplicados/desconexos entre este sistema e os outros do dono

## Disciplina de execução

- **Paralelo, máx 5 por wave.** 2ª wave só se a 1ª abrir perguntas novas (o plano do exemplo trabalhado previa 2 waves; dirigida, não repetição de lentes).
- Agentes read-only (Explore) — nunca executor.
- **Spot-check à chegada:** por report, verifica tu mesmo 2-3 claims (1 grep, 1 ficheiro:linha). Agente que falha 1 claim em 3 → re-verifica TODOS os claims dele antes de usar (subagentes alucinam paths e linhas).

## Contar padrões estruturais — bloco balanceado, não regex de linha

Padrões multi-linha (catch vazio, if/else aninhado, componente JSX) **não** se contam com grep de linha — subcontam. Caso interno do autor (app CRM, análise de UX; não incluído): regex ingénuo de `catch` deu **11**; um scan Python de blocos balanceados (conta `{`/`}` para achar o corpo real de cada `catch`) deu **44** (33 vazios/só-comentário + 8 `.catch(() => {})` + 3 `.catch(() => null)`) — o grep de linha tinha subcontado 4× (deu 11), e a review fresh apanhou a subcontagem como MINOR. Regra: se o padrão que procuras tem corpo com chavetas (`catch {...}`, `if {...}`, componente `<X>...</X>`), escreve um script curto (Python/node) que parseia blocos, não um `grep -c`. Grep de linha só é seguro para padrões de 1 linha (import, chamada de função, atributo JSX).

## Modo EXPLORE-SOLO (sem subagentes, ou delegação disponível mas a falhar)

Calibrações internas do autor, não incluídas (2 execuções solo e uma com serviço de delegação saturado — 5 delegações timeout 180s/0 bytes):

- **Pre-flight de delegação** (se o runtime TEM delegação): 1 chamada-sonda barata com timeout curto ANTES do fan-out. Falha/timeout → não insistas nas 5 lentes: cai para solo JÁ. 5 timeouts de 180s = 15 min queimados sem um facto. **Canal alternativo:** se o canal principal de delegação está saturado, tenta lançar o subagente por um canal directo (ex.: invocação directa da CLI do agente, sem passar pelo gateway); testa-o no pre-flight antes de desistir da delegação.
- **Solo = mesmas lentes, SEQUENCIAIS**, uma de cada vez, mesmo contrato só-factos. Prova processual obrigatória: **tabela lente → comandos corridos → findings → spot-checks** no método do relatório (senão "cobri 5 lentes" é claim sem evidência).
- No checklist, marca `EXPLORE-SOLO` (vs `EXPLORE-MULTIAGENT`) — o contrato "reports + spot-check por report" não se aplica literalmente a solo; a tabela substitui-o.
- Solo NÃO muda a regra da review: continua a precisar de agente fresh na fase VERIFY; sem ele, relatório fica "por rever" (ver playbook-verify).

## Erros típicos

| Erro | Correcção |
|---|---|
| 4 agentes com o prompt genérico "encontra problemas" | Lentes distintas com checklist cada — redundância encontra o mesmo 4× |
| Aceitar recomendações dos agentes | Contrato só-factos; recomendação é trabalho da síntese |
| Usar report sem spot-check | 2-3 claims verificados por report, sempre |
| Parar na 1ª wave com perguntas abertas | Perguntas novas → wave 2 dirigida (não repetir lentes) |
| Contar padrão multi-linha (catch/if/componente) com `grep -c` | Script de blocos balanceados — grep de linha subconta 4× (caso real) |
