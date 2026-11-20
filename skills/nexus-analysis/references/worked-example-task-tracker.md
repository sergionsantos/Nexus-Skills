# Worked example end-to-end — análise de um gestor de tarefas web (7 melhorias)

> O caso completo, fase a fase, anonimizado: a aplicação analisada era um gestor de tarefas web (clone de um tracker de issues maduro) com frontend Next.js/TypeScript e backend Supabase em Docker. Marcação de proveniência: **[TRAÇO]** = estava nos artefactos reais da análise (relatório, checklist, verificação); **[RECONSTRUÍDO]** = intermédio não persistido, reconstruído para ensino — fiel ao método, não citável como facto histórico. Nomes de ficheiros, contagens e portas são os do caso original, só sem o nome do projecto.

## SCOPE [TRAÇO]
Pedido: "7 melhorias substanciais para a app (clone de um tracker de issues, a correr numa porta local)". N=7 dado pelo dono. Superfície: `app/src` (≈9,4 mil linhas TS/TSX, 138 ficheiros), `app/db/migrations`, stack docker (gateway/rest/realtime/db), LOGs do projecto. Standard de comparação: um documento de features do produto de referência. Checklist de controlo aberta com critérios de conclusão binários.

## GROUND [TRAÇO]
Claims do LOG → checks vivos:

| Claim do LOG | Check | Resultado | Classe |
|---|---|---|---|
| "app live na porta local" | `lsof -i :<porta>` | nada — app PARADA | doc stale, realidade pior |
| "config do gateway revertida no disco" (armadilha conhecida) | diff config vs versão preparada | já endurecida, armadilha resolvida | doc stale, realidade melhor |
| "backlog: bulk-toolbar por fazer" | grep do componente | feito | doc stale, realidade melhor |
| — (não documentado) | descodificar JWTs do `.env.local` vs `JWT_SECRET` do compose | `iss: supabase-demo` vs secret rotacionado — a app vai falhar auth ao arrancar | **divergência crítica nova** |

A divergência nova (cruzamento config-app × config-infra que nenhuma lente isolada apanha) tornou-se a melhoria #1.

## EXPLORE [TRAÇO — método e findings; prompts exactos não persistidos]
4 agentes read-only paralelos: arquitectura/código · infra/deploy/segurança · gap vs documento de features do produto de referência · UX/robustez. Amostra de factos devolvidos (todos no relatório final com evidência):
- `due_date` filtrável+mutável mas **0 hits** em `issue-detail.tsx`/`issue-create-dialog.tsx` (lente gap; grep-zero como prova)
- invalidação usa `qk.search("")` mas queries activas usam `qk.search(termo)` → pesquisa stale (lente código; bug real)
- zero `error.tsx`/`isError` em toda a árvore (lente UX)
- 3 ficheiros de teste, todos lógica pura; sync layer 0 testes; trilha de remendos F3/F14/F21/F28 em comentários (lente código)
- listas sem virtualização; `fetchAllIssues` cap 1000; bulk = N requests (lente código)

## SYNTHESIZE [RECONSTRUÍDO — pool e etiquetas não foram persistidos; clusters e selecção final são [TRAÇO]]
Pool ~20+ findings → etiquetas P/L/T → clusters:

| Cluster (→ melhoria final) | Findings agrupados | Fonte |
|---|---|---|
| #1 env + serviço persistente + secrets | app down · JWT mismatch · service_role demo · sem persistência | P |
| #2 metadados schema→UI | due_date · estimate · templates · initiatives · cycle/snooze (5+ findings, 1 slot) | **L** |
| #3 camada de erro | zero error.tsx · zero isError · sem offline · sem retry mutations | P |
| #4 testes sync + fixes | 0 testes sync · bug search-invalidation · keys inline · toggle não-atómico | P |
| #5 API para agentes | lógica presa a hooks de browser · tarefas geridas em markdown fora da app | **T** |
| #6 performance de escala | sem virtualização · cap 1000 · bulk N-requests · joins client-side | P/L |
| #7 admin + editorial + mobile | allowlist via SQL · design a meio · 14 breakpoints | P |

Quotas cumpridas: L=#2, T=#5, restantes P. A transformação (#5) nasceu na síntese — pergunta-guia "que utilizador este sistema não serve?" → agentes automáticos do dono; evidência de desconexão: tarefas geridas em markdown fora da app.

## STRUCTURE [TRAÇO]
Anatomia anotada do item #2 no `playbook-structure.md`. Ordem aplicando as heurísticas por ordem: #1 pré-condição → #2 maior ganho/diff → #3 ambiente instável → #4 seguro de vida → #5 transformação → #6 escala → #7 coerência. Trade-off explícito registado: #4 depois de #2/#3 por pragmatismo (diffs pequenos aditivos primeiro), com a alternativa rigorosa oferecida.

## VERIFY [TRAÇO]
- Mecânico: secs=7 probs=7 accs=7 imps=7 exit=0 (registado na checklist).
- Review passe 1 (13 claims): 1 MAJOR (complexidade de um join mal calculada + fix atribuído ao sítio errado) + 1 MINOR (linha errada) → corrigidos.
- Passe 2 (sessão fresh, 2 agentes Explore + spot-checks vivos): todos os claims CONFIRMADOS + facto novo (o projecto não era um repo git próprio) → **zero findings → análise adoptada como final**.
- Fecho: resumo ordenado no chat; commit/push só se a política do workspace o permitir.

## Lições transferíveis deste caso
1. O finding mais crítico (#1) veio do GROUND, não dos agentes — nunca saltar a fase.
2. O melhor rácio ganho/diff (#2) veio de grep-zero sobre schema pronto — a "query de ouro" da lente 3.
3. A transformação (#5) não estava em nenhum relatório de agente — nasceu do cruzamento com o ecossistema do dono na síntese.
4. A review independente pagou-se: 2 erros reais corrigidos + 1 facto novo, em claims que o autor tinha por certos.
