# sqlite3-python execution pitfalls 

Three concrete pitfalls encountered while writing a forward-only migration
runner + generated CHECK constraints against a migration runner and
a migration file. These are independent of the project —
they apply to any Python project using `sqlite3` to run DDL or generated
CHECK constraints.

---

## Pitfall 1 — `executescript()` auto-commits before running

**Symptom.** Code like this raises on the rollback:

```python
conn.execute("BEGIN")
conn.executescript(sql_body)   # SQL + DDL or multi-statement
conn.execute("INSERT INTO schema_migrations ...", (...))
conn.execute("COMMIT")
# ... later on error path:
conn.execute("ROLLBACK")       # ← sqlite3.OperationalError:
                               #   "cannot rollback - no transaction is active"
```

**Why.** Python's `sqlite3.Connection.executescript()` issues a
`COMMIT` *before* executing the script (this is documented but easy to
miss — see [DB-API 2.0 §sqlite3]). It also opens its own internal
transaction and does not respect an outer `BEGIN`. The `BEGIN` /
`COMMIT` pair outside the script appears to do nothing.

**Fix (the pattern).** Wrap the user's SQL inside your own
`BEGIN` / `COMMIT` at the *script* level — not as separate `conn.execute`
calls — and issue a defensive `ROLLBACK` on the error path that
suppresses "no active transaction":

```python
wrapped = "BEGIN;\n" + sql_body + "\nCOMMIT;\n"
try:
    conn.executescript(wrapped)
except sqlite3.Error as exc:
    try:
        conn.execute("ROLLBACK")
    except sqlite3.OperationalError:
        pass                       # already rolled back — silent OK
    raise MigrationApplyError(...) from exc

# Recording the apply itself is a SEPARATE single-statement commit —
# executescript above already committed, so this is its own implicit txn.
try:
    conn.execute(
        "INSERT INTO schema_migrations(version, checksum, applied_at) "
        "VALUES (?, ?, ?)",
        (version, checksum, applied_at_iso),
    )
except sqlite3.Error as exc:
    raise MigrationApplyError(
        f"applied but schema_migrations record failed: {exc}"
    ) from exc
conn.commit()
```

**Cost of skipping:** Migration partially applied (DDL persisted, but
schema_migrations row missing). Next start re-applies → checksum
mismatch → false-positive "live DB edit" error. Or worse: applied with
a recorded checksum from the empty-pre-state, drifts from reality
silently.

---

## Pitfall 2 — CHECK constraint is table-level, not column-level

**Symptom.** SQL like this raises `near "<col>": syntax error`:

```sql
CREATE TABLE fake_events (
    event_kind TEXT NOT NULL, CHECK(event_kind IN ('a','b','c')),  -- ← bad
    note TEXT
);
```

**Why.** In SQLite (and standard SQL), `CHECK` is a **table-level**
constraint that comes AFTER the column list. The above is invalid;
SQLite parses the comma before `CHECK` as expecting another column
definition.

**Fix.** Place `CHECK` after all column definitions, before the
closing `;`:

```sql
CREATE TABLE fake_events (
    event_kind TEXT NOT NULL,
    note TEXT,
    CHECK(event_kind IN ('a','b','c'))
);
```

**MySQL** accepts inline column CHECK; **PostgreSQL** does too.
**SQLite is strict.** When porting CHECK-bearing DDL between
dialects, this is the #1 silent break.

---

## Pitfall 3 — `tools/gen_checks.py` `-- CHECK:Name` marker is METADATA only

**Symptom.** First migration that uses the marker has no actual CHECK
constraint at runtime — inserts with bogus values pass silently.

**Why.** The `gen_checks.py` marker convention per spec 09 M0.3 is:

```
event_kind TEXT NOT NULL, -- CHECK:EventKind
```

This trailing comment is **metadata for the sync test** (it finds the
line, re-derives the CHECK from the registry, and string-compares).
It does NOT inject the SQL. The migration author must call
`generate_check_sql("EventKind")` and embed the actual clause:

```python
from tools.gen_checks import generate_check_sql
check_clause = generate_check_sql("EventKind")
sql_body = f"""
CREATE TABLE events (
    event_kind TEXT NOT NULL, -- CHECK:EventKind
    note TEXT,
    {check_clause}
);
"""
```

**The sync-test (M0.3 verify floor) will fire** if the embedded
CHECK and the registry drift — but only AFTER the migration has
been written, applied, and re-parsed. The negative control in
`tests/test_migrations.py::test_m03_negative_controls[5b]` (exemplo — teste do teu projecto) proves
this end-to-end at the DB level (sqlite3.IntegrityError on bogus
value).

---

## Working template — minimal SQLite forward-only migration runner

These three pitfalls compose into the canonical M0.3 shape. The
working code lives at `<project>/storage/migrate.py`
(commands below all from that path). Use as a reference, not a
copy-paste — every project has different metadata needs.

```bash
# Verify floor:
uv run python -m project.storage.migrate --db /tmp/t0.db && \
uv run python -m project.storage.migrate --db /tmp/t0.db
# Expect second line: "up-to-date (1 applied)"

# Negative control (corrupt a migration file then run):
echo " " >> migrations/001_meta.sql
uv run python -m project.storage.migrate --db /tmp/t0_neg.db
# Expect exit=2 with "CHECKSUM MISMATCH"
```

---

## Negatives controls worth keeping (pattern, not specific code)

| # | NC | What it pins down |
|---|---|---|
| 1 | Registry KeyError on unknown enum | `gen_checks` is the single source of truth, no silent fallback |
| 2 | sqlite3.IntegrityError on bogus value | CHECK actually fires at the DB layer, not just in tests |
| 3 | MigrationChecksumMismatch on tampered file | D27 forward-only enforced — no silent schema drift |
| 4 | MigrationApplyError on invalid SQL | Transactional rollback, no partial schema |
| 5 | Idempotent re-run prints `"up-to-date (1 applied)"` | Exact spec wording works in practice |

The combine-set of 1+2+3+4 is what proves the registry → CHECK → DB
chain is mechanical and falsifiable end-to-end. Anything less leaves
the enums drift-prone (which is exactly the bug pattern that motivates
in the spec).

---

## Provenance

- Date: 2026-07-12
- Session: schema-migration runner spike.
- Spec driving the design: 09-milestone-build-plan.md M0.3 section (D26/D27)

  the spec count discrepancies that gen_checks.py bakes in (EventKind=41,
  GateReasonCode=16, HealthCode=15).
