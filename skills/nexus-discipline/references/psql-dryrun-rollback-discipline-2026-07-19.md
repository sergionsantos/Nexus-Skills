# psql-dryrun-rollback-discipline-2026-07-19.md

> **Source:** real incident (migration applied during a "dry-run").
> **Severity:** Real production migration applied unintentionally during verify dry-run; rollback successful but avoidable.

## The trap

`psql --single-transaction -f migration.sql` does **NOT** auto-rollback. It wraps all statements in a transaction that **commits at the end if no error** (exit 0 → commit, exit non-zero → rollback).

Common wrong assumption: "single-transaction means dry-run / atomic". **Wrong.** Single-transaction = atomic boundary, but commits on success.

## Reproduction (the actual incident)

```bash
# Goal: verify migration 021 syntactically valid + check what tables it would create
psql -h 127.0.0.1 -p 54322 -U app_user -d app_db \
  -v ON_ERROR_STOP=1 \
  --single-transaction \
  -f migrations/021_settings.sql
# → exit 0, output: BEGIN / CREATE TABLE / CREATE INDEX / COMMIT
# → MIGRATION WAS APPLIED. settings now exists in prod.
```

Detection (post-mortem): subsequent `SELECT EXISTS (...)` returned `t` instead of expected `f`.

## Three safe dry-run variants

### Variant A: `-1` flag (auto-rollback on disconnect)

```bash
psql -h ... -d ... -U ... -1 -f migration.sql
```

`-1` (alias for `--single-transaction`) PLUS connection-close-trigger rollback. This is the **safest for quick verification** because it rolls back even if you Ctrl-C.

### Variant B: explicit BEGIN + ROLLBACK wrapper

```bash
psql -h ... -d ... -U ... -v ON_ERROR_STOP=1 <<EOF
BEGIN;
$(cat migrations/021_settings.sql)
ROLLBACK;
EOF
```

Explicit transaction with explicit rollback. Works for SQL files that don't already have BEGIN/COMMIT inside (will fail with "already in transaction" if they do).

### Variant C: temp table verification (most rigorous)

```bash
# 1. Apply migration to ephemeral DB
docker exec -i some_pg psql -U postgres -d app_db_test \
  -f migrations/021_settings.sql
# 2. Verify schema
psql -h ... -U ... -d app_db_test -c "\d app.settings"
# 3. Verify business logic against fresh DB
# 4. Drop test DB
docker exec -i some_pg psql -U postgres -c "DROP DATABASE app_db_test"
```

For thorough verification including FK constraints, triggers, and runtime behavior. Slower but catches more bugs.

## Detection pattern (post-dryrun safety net)

After ANY migration dry-run, ALWAYS run:

```sql
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'memory' AND table_name = '<expected_new_table>'
) AS exists_in_prod;
-- Expected: f (false). If t (true), migration applied — rollback immediately.
```

If `t` after a "dry-run", rollback:
```sql
DROP INDEX IF EXISTS memory.idx_<table>_<col>;
DROP TABLE IF EXISTS memory.<table>;
```

## When NOT to use `-1` (Variant A)

- Migrations that include `CREATE INDEX CONCURRENTLY` (cannot run inside transaction).
- Migrations that need to commit mid-stream (rare; usually wrong design).
- DDL like `VACUUM`, `REINDEX`, `CLUSTER` that can't run in transaction.

For simple migrations (CREATE TABLE IF NOT EXISTS + CREATE INDEX plain btree), `-1` works fine.

## When to USE direct apply (no dry-run)

- Migration already validated by separate ephemeral test (Variant C).
- Owner gave explicit "vai" for that specific migration.
- Migration is idempotent (CREATE TABLE IF NOT EXISTS) AND has been reviewed by Rule 0 subagente.

For pgauto M1 (migration 021 + 022), owner gave "vai" so we applied directly. The dry-run incident happened DURING verify-script construction, before owner gave "vai".

## Checklist before any psql -f migration

- [ ] Did I use `-1` OR explicit BEGIN/ROLLBACK wrapper? If not → STOP, fix command.
- [ ] Did I post-verify with `SELECT EXISTS ...`? If not → run it NOW.
- [ ] If `EXISTS = t` after "dry-run", did I rollback? (DROP INDEX + DROP TABLE).
- [ ] Is the target DB prod or ephemeral? For prod, ensure owner gate cleared first.

## Related

- `nexus-discipline` "psql dry-run trap" bullet (one-liner).
- `postgres-runtime-probe-gotchas.md` (runtime gotchas).
- Postgres docs: https://www.postgresql.org/docs/current/sql-set-transaction.html (single-transaction = atomic, NOT dry-run).
