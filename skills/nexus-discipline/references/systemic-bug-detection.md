# Schema-level systemic-bug detection (for execution)

> **Audience:** executor (no `nexus-discipline` operating mode) que suspeita de bug systemic
> **Origem:** pitfall 2026-07-04, projecto X M11.1.0b (cleanup board_order duplicates).
> **Lição central:** "investigar a causa antes do fix" apanhou systemic bug (DEFAULT literal `'a0'::text` em `board_order` e `sort_order`); o fix sintomático (rerank 2 issues) deixava a porta aberta para 100% de reincidência em qualquer team novo.

## Quando usar

**Sinal:** o spec / verify-fresh detecta um **problema pequeno** (e.g.: 1-2 dups, 1-3 rows com formato errado, 1-2 inconsistências). Antes de o fixar:

1. **PÁRA e re-avalia.** Pergunta: *"é 1 caso isolado ou é systemic?"*
2. **Se for 1 caso isolado:** fix sintomático é OK (rerank those 2, move on).
3. **Se for systemic** (column default, missing constraint, missing trigger): fix só o sintoma vai voltar. **Investiga root cause** + **fixa default/constraint/trigger no mesmo migration**.

## O probe (4 queries-chave, ~30s)

```sql
-- 1. Schema-level defaults (literal vs generated)
select column_name, data_type, column_default
from information_schema.columns
where table_schema='<schema>' and table_name='<table>'
  and column_name in ('<col1>', '<col2>', ...)
order by column_name;

-- Expected pattern: column_default is NULL (caller provides value)
-- OR column_default references a function (e.g., 'gen_random_uuid()', 'now()')
-- SUSPICIOUS: column_default is a literal value (e.g., ''a0'::text', '0'::int)
--   → all inserts without explicit value get the literal → systemic

-- 2. Constraints que protegem integridade
select conname, contype, pg_get_constraintdef(oid)
from pg_constraint
where conrelid = '<schema>.<table>'::regclass
order by conname, contype;

-- Expected: PK, FKs, NOT NULL, CHECK constraints
-- SUSPICIOUS: table has no UNIQUE constraint on a column that "should be unique"
--   e.g.: "board_order" is unique per team, but no UNIQUE(board_order, team_id) constraint

-- 3. Triggers que defendem invariantes
select tgname, tgenabled
from pg_trigger
where tgrelid = '<schema>.<table>'::regclass
  and NOT tgisinternal
order by tgname;

-- Expected: triggers for updated_at, validations, fan-out
-- SUSPICIOUS: no trigger for "should auto-generate" (e.g., board_order, created_at)

-- 4. Application-level fallbacks (where caller relies on DB default)
-- Run from app/ source:
grep -nE "board_order\?:|sort_order\?:" src/lib/api/<entity>.ts

-- Expected: optional field with explicit comment "defaults server-side"
-- SUSPICIOUS: optional field with NO comment → caller may not realize
--   that the default is hard-coded, not generated
```

## Decision tree pós-probe

```
1. Schema default is a literal value (suspect)?
   YES → confirmar: `select pg_get_function_def('default_expr'::regproc)`.
   Se a função existe e é razoável (gen_random_uuid, etc.) → NOT suspect.
   Se é literal hard-coded → **systemic root cause**. Ir para step 2.

2. Caller no app é optional (?:string)?
   YES → **schema default + app optional = 100% dup risk** (qualquer insert sem valor explícito → dup).
   Fix: migration que muda default para NULL + trigger BEFORE INSERT que gera valor, OU força caller a definir.
   NO (caller sempre define) → **app-side bug**, not systemic.

3. CHECK/UNIQUE constraint que protegeria?
   YES (existe) → **caller** tem bug, não schema.
   NO (falta) → adicionar constraint + NOT VALID para não bloquear dupes existentes, depois VALIDATE.

4. Decide: fix sintomático (rerank) ou systemic (migration + constraint)?
   Systemic sempre que a query 1 ou 3 diz "yes, the schema assumes" e a query 4 diz "no, the app doesn't compensate".
```

## Caso real: M11.1.0b (2026-07-04)

**Cenário:** cleanup de 1 cluster de `board_order` dup `a0` entre 2 issues de NEX.

**Sintoma:** `count(distinct board_order) = 16` mas `count(*) = 17`.

**Investiguei (não fixei ainda) com a query 1:**
```sql
select column_name, data_type, column_default
from information_schema.columns
where table_schema='app_schema' and table_name='issues'
  and column_name in ('board_order','sort_order');
```

**Resultado:** `board_order text NOT NULL DEFAULT 'a0'::text` e `sort_order text NOT NULL DEFAULT 'a0'::text`. **LITERAL hard-coded em `0003_issues.sql:22`.**

**Confirmar com query 4 (app caller):** `grep -nE "board_order\?:|sort_order\?:" src/lib/api/issues.ts` → `board_order?: string; // column rank; defaults to 'a0' server-side`. **Caller é optional, schema default é literal = 100% risk**.

**Decisão:** fix sintomático (rerank 2 issues) + fix systemic (migration 0016b que muda default para gerar via trigger + remove literal `'a0'::text`). Custo: +20min poupa-te o problema de vires cá daqui a 1 semana com 5 dups.

**Lição:** o sintoma "1 dup" não te diz que não há 5 dups latentes. A query 1 disse: "todos os issues de NEX que foram criados sem `board_order` explícito no app **vão** colidir com a 1ª do team". Era inevitável.

## Quando NÃO usar

- Sintoma "1 row com formato errado" **e** schema default é função (não literal) → app bug, não systemic.
- "X rows duplicadas" mas X ≥ 5 + caller sempre define value → constraint missing, não schema default. Different fix (add UNIQUE + backfill).
- Quando o problema é 1 row (não pattern): `select * from <table> where id = <that row>` → ver se é mesmo 1 caso isolado. Sem necessidade desta técnica.

## Forma concreta (script copy-paste)

```bash
#!/bin/bash
# Usage: ./detect-systemic-bug.sh <schema> <table> <col1> [col2 ...]
SCHEMA="$1"
TABLE="$2"
shift 2
COLS="$@"

export PATH="/usr/local/opt/libpq/bin:/usr/local/opt/node@22/bin:$HOME/.local/bin:$PATH"
DB_URL=$(grep "^SUPABASE_DB_URL=" .env.local | cut -d= -f2- | tr -d '"\r')

echo "=== 1. column defaults (schema) ==="
psql "$DB_URL" -P pager=off -tAc "
select column_name, column_default
from information_schema.columns
where table_schema='$SCHEMA' and table_name='$TABLE' and column_name in ($(printf "'%s'," $COLS | sed 's/,$//'))"
echo ""
echo "=== 2. constraints ==="
psql "$DB_URL" -P pager=off -tAc "
select conname, contype, pg_get_constraintdef(oid)
from pg_constraint
where conrelid = '$SCHEMA.$TABLE'::regclass"
echo ""
echo "=== 3. triggers ==="
psql "$DB_URL" -P pager=off -tAc "
select tgname, tgenabled
from pg_trigger
where tgrelid = '$SCHEMA.$TABLE'::regclass and NOT tgisinternal"
echo ""
echo "=== 4. app caller ==="
grep -nE "$(echo $COLS | tr ' ' '|')" src/lib/api/*.ts | head -20
```

**Uso típico:** `./detect-systemic-bug.sh app_schema issues board_order sort_order`

## Lição meta

A maioria dos bugs em sistemas maduros **não são "1 caso"**, são **"1 caso visível"**. O sintoma é a ponta do iceberg. Se passares 5min a investigar a causa antes do fix, **poupas 5 dias de reincidência** (carry-over M9 testing foi exactamente isso: 1 dup "isolado" de M3 que ninguém investigou, e o estado acumulou).

**Versus a alternativa "just fix the symptom":** 1 dia de fix + risco de "fix Tomorrow again". Pior trade-off.
