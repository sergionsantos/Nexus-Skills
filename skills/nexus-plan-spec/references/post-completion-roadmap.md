# Roadmap pós-conclusão (closeout)

Template para emitir um plano de evolução **depois** de um roadmap principal estar concluído (ex.: milestones M0-M10 feitos → M11+). Exemplo real: 5 milestones, 38 steps atómicos, emitidos sobre uma app já feature-complete.

## Quando usar

- Fecho de uma fase após o último milestone do roadmap principal.
- Roadmap pós-MVP quando o sistema está feature-complete mas a UX/performance/E2E ainda não foram trabalhadas.
- **Não usar** para planeamento pré-execução (modo normal da skill), nem para refactor de um único componente (isso é uma tarefa simples).

## Os 3 artefactos (todos em disco ANTES do relatório verbal)

1. **`closeout.md`** (ficheiro de estado/decisões do projecto)
   - §1 Estado real (ground truth verificado) · §2 Gap analysis (reportado vs real) · §3 Decisão de âmbito (o que avança / o que adia, com D## numeradas) · §4 Cadência (1 milestone por vez) · §5 Fora de âmbito · §6 Protocolo de verificação · §7 Critérios de done globais · §8 Estado por milestone anterior · Registo de decisões.
2. **`plan/ROADMAP.md`** — milestones com steps atómicos no formato §6 do SKILL.md.
3. **`plan/AMENDMENTS-PENDING.md`** — itens adiados, cada um com **gatilho para retomar** ("quando o utilizador pedir 'vista por responsável'").

## Ground truth em dump real

```bash
psql "$DB_URL" -tAc "select name from _migrations order by applied_at desc limit 5"
psql "$DB_URL" -tAc "select count(*), count(distinct board_order) from issues where trashed_at is null"
psql "$DB_URL" -P pager=off -tAc "select board_order, count(*) from issues where trashed_at is null group by board_order having count(*) > 1"
psql "$DB_URL" -tAc "select jobname, schedule from cron.job"
psql "$DB_URL" -tAc "select table_name from information_schema.tables where table_schema='app' order by 1"
```

## Gap analysis (estrutura de tabela)

| Item do closeout original | Reportado | Estado real | Gap |
|---|---|---|---|
| Latência percebida de mutação < 50 ms | Optimistic-first (D47) | Não medido | Nunca medido em runtime |
| LCP < 1,5 s local | Alvo "cold first load" | Build verde | Não medido com Lighthouse |
| Top-3 da v1 | bulk + sub-issues + relations | Nenhum feito | A fazer |

Cada item do template de closeout ganha uma linha de gap analysis real. O template sozinho é prospectivo; o gap analysis mostra o que realmente falta.

## Decisões (D-numbered) no closeout, não no README da Parte A

Exemplo: `D107` T1-T2 avançam, T3-T5 adiam · `D108` cadência em 5 milestones · `D109` limpeza de duplicados é pré-requisito bloqueante (higiene de dados antes de polish visual). São decisões estruturais pós-conclusão; mantêm a Parte A congelada.

## Tiering justificado

- **Tier 1 (quick wins, ~1 dia):** coerência visual, limpeza de dados, empty states.
- **Tier 2 (top-3 pedidos, 1-2 dias):** funcionalidades principais.
- **Tier 3 (produção, v1.5):** E2E, orçamento de performance, tracking de erros.
- **Tier 4/5 (schema-ready/polish, v1.5-v2):** opções avançadas, mobile, pesquisa full-text, rotação de segredos.

Tier 1 antes de Tier 2 (o polish é o que o utilizador mais vê e o Tier 2 herda a inconsistência). Tier 3+ adia-se: sem adopção real, optimizar é prematuro.

## Step atómico real (com gate)

```markdown
### Step M11.1.1 — GATE PRÉ-APLICAÇÃO (limpar duplicados)
**Goal:** corrigir o valor duplicado sem perder a ordem das restantes linhas
**Files touched:** `app/db/migrations/0016_fix_dup.sql` (criar)
**Behavior spec:** para cada `board_order` duplicado, gerar rank único mantendo a ordem por `created_at`
**Commands:** pre-dump do estado real (select das linhas duplicadas)
**⛔ GATE PRÉ-APLICAÇÃO:** o dump mostra 2 linhas; mostrar o diff proposto, PARAR, esperar aprovação.
**Verify (predict-then-run):** duplicados → 0 · distintos → 17 · total → 17 (intacto)
**If verify fails:** distintos=17 mas total=18 → outra linha duplicada; repetir com rank iterativo · total≠17 → reverter a partir do backup
**Done when:** distintos = 17 E total = 17 E 0 duplicados
```

## Cadência (MILESTONE-CADENCE, da skill `nexus-discipline`)

1 marco por milestone; steps intermédios só "verify-OK". Cada milestone termina com: (1) script de verify fresh com nome único; (2) review independente com contexto limpo e lente diferente da do autor; (3) linguagem intermédia honesta: *"M<N> implementado (…), aguarda review independente"*.

## Erros mecânicos típicos do check final (e como evitá-los)

1. Grep de `**Verify**` sem o formato real do marcador (lista com `- ` ou parágrafo) → 0 resultados, quando havia 37. Usa substring simples (`grep -c "Verify"`).
2. Regex "inteligente" com grupos escapados em vez de padrão literal.
3. Verify sem `If verify fails` correspondente (37 Verify, 8 If-verify-fails): o autor salta-o quando o verify parece trivial. O validador desta skill trata-o como FAIL.

## Done (closeout completo)

Todos os milestones em `implementado, aguarda review` → review independente sem BLOCKER/HIGH → closeout actualizado com notas de review reais (não o template) → `AMENDMENTS-PENDING.md` criado → resumo de sessão → closeout arquivado.
