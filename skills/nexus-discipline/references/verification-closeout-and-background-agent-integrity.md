# Verification closeout and background-agent integrity

Class-level lessons for long, delegated builds and spec/code mutations.

## 1. Process exit is not task completion

An HTTP wrapper or background shell can exit `0` while the agent payload says `completed=false`, lists missing artefacts, or admits the canonical validator was not run.

Gate on all three:

1. transport/process exit;
2. agent semantic status and unresolved items;
3. fresh canonical verification against the final filesystem.

Never promote a successful wrapper exit into DONE language.

## 2. DONE evidence must be fresh after the final mutation

After any edit, repair, reviewer patch, negative-control restoration, or housekeeping commit, rerun the canonical check in the same reporting turn. Show the literal command output and exit code. Earlier green output is stale after later mutations.

If no canonical suite exists, label the check `ad-hoc verification`, state what it covers and does not cover, execute a negative control, restore the state, and rerun the happy path.

## 3. Verify exact documented interfaces

Before declaring a tool failure, read its actual CLI or the canonical plan and run the exact supported command. An invented flag can create a verifier-caused false FAIL. When this happens:

- identify the verifier error explicitly;
- rerun with the exact interface;
- do not attribute the failure to the implementation;
- retain both outputs in the audit trail.

## 4. Green tests do not prove transaction boundaries

Review transaction semantics independently of the happy path. In particular, schema DDL and its migration-ledger INSERT must commit atomically. A runner that commits DDL and records the migration afterwards can leave applied-but-unrecorded schema.

Required negative control:

1. make the migration body valid;
2. force failure specifically at the migration-record INSERT;
3. assert the new tables/indexes do not persist;
4. assert the ledger has no new version;
5. restore and rerun idempotency.

For Python sqlite3, remember that `Connection.executescript()` may issue an implicit COMMIT. If atomicity with a subsequent parameterized INSERT is required, execute complete SQL statements within an explicit transaction using SQLite-aware statement boundary detection (for example `sqlite3.complete_statement`), not naive `split(';')`.

## 5. Reviewer sequence for high-risk delegated work

1. Author/lead writes and self-verifies.
2. Orchestrator inspects real files and runs canonical checks.
3. Fresh-context strong reviewer checks semantic consistency.
4. Author repairs directed findings.
5. Orchestrator reruns canonical checks after the last mutation.
6. Only then use DONE language.

## 6. Negative-control restoration gate

A negative control that mutates source or schema is incomplete until:

- the original state is restored in a `finally`-equivalent path;
- the happy-path suite passes again;
- `git status --short` is clean;
- temporary files are removed.
