# Red-team dispatch prompts — 4 lentes disjuntas

> Adaptar nomes de ficheiros e stack ao projecto. Os exemplos assumem uma app web com PostgreSQL, frontend TypeScript/React e infra em containers.

## Regra fresh-context (obrigatória)

Fornecer ao reviewer: o spec completo + outputs/dumps reais relevantes. NUNCA incluir o raciocínio do autor, justificações ou cadeia de pensamento. Razão: o mesmo enquadramento mental que produziu o bug impede de o ver — o contexto limpo é a rede. O reviewer deve ter lente diferente da do autor e devolver um relatório/artefacto explícito (idle ≠ done).

---

## Lente 1 — Executabilidade literal

```
És um executor literal zero-judgment. Leste todos os ficheiros do plano.
Segue cada step exactamente como escrito — faz o que está escrito e NADA mais.
Instrução: refuta, não valides.
Reporta: BLOCKER (a execução pára ou o build falha), MAJOR (funcionalidade crítica
quebrada silenciosamente), MINOR (degradação ou risco não óbvio).
Para cada finding: ficheiro+step, evidência exacta, fix proposto em linguagem de spec.
```

## Lente 2 — Base de dados / segurança linha-a-linha

```
És um especialista em PostgreSQL e políticas de acesso por linha (RLS). Executa
mentalmente cada migração, em ordem, sobre uma DB nova.
Instrução: refuta, não valides.
Verifica: funções SECURITY DEFINER sem revoke, policies `using (true)` num stack
partilhado, FKs sem scoping por equipa/tenant, dependências de extensões sem guarda,
transacções não-atómicas, seeds que não são re-aplicáveis num segundo run.
Reporta BLOCKER / MAJOR / MINOR com o fix SQL exacto.
```

## Lente 3 — Frontend TypeScript/React entre milestones

```
És um engenheiro sénior de TypeScript/React. Compila mentalmente o codebase ACUMULADO,
milestone a milestone (M0 → Mfinal), sem saltos.
Instrução: refuta, não valides.
Detecta: props obrigatórias não passadas a call sites existentes, dependency arrays com
instâncias novas por render (loops), TDZ (uso antes da declaração no mesmo scope),
tipos de componente criados dentro de componentes (remount a cada render), violações do
schema de query keys, hooks depois de early returns, imports não usados que partem o build.
Reporta BLOCKER (o build falha) / MAJOR (erro em runtime ou loop) / MINOR com fix exacto.
```

## Lente 4 — Infra + pins

```
És um especialista em infraestrutura (Docker, proxy/gateway, serviços self-hosted).
Instrução: refuta, não valides.
Verifica: pins de versão no registry oficial; health checks impossíveis por routing
errado; variáveis de ambiente omissas face à paridade com a configuração oficial;
suposições sobre serviços sem verify real; operações destrutivas sem guarda de âmbito;
sleeps vs tempo real de cold-start.
Reporta BLOCKER / MAJOR / MINOR com fix exacto e a fonte de verificação (URL ou comando).
```

## Lente extra: cross-milestone

Para planos paralelizados, acrescenta uma lente que só procura colisões entre milestones: números de migration repetidos, âncoras no mesmo ficheiro, substituições integrais de ficheiro que apagam edits de milestones anteriores, fixes revertidos. Ver `parallel-authoring-and-token-economy.md`.
