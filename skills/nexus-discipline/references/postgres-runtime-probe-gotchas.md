# Postgres + PostgREST runtime probe gotchas (pitfall 2026-07-02 / 2026-07-04, executor)

> **Princípio:** estende `shell-probe-false-fails.md` para **probes que envolvem SQL real** (`psql`, PostgREST service-role, runtime `.mjs` via `node --input-type=module`). Cada padrão documenta **sintoma + causa + workaround canónico com probe alternativo**. Categorizar `psql` retornando 0 ou `""` quando o probe assume string.

---

## 17. `addIssueRelation` self-loop permitido pela API mas bloqueado por FK (M14, 2026-07-04)

**Sintoma:** `addIssueRelation(A, A, "related")` executa sem erro JS, mas DB error 23514 (`issue_relations_check`) aparece no **probe**, não na UI.

**Causa:** A `addIssueRelation` TS não tem `if (issueId === relatedIssueId) throw`. UI passa porque picker tem `excludeIds`, mas direct API calls from probe falham.

**Workaround no probe:**
```bash
# Test self-loop via direct PostgREST
SELF_ID=$(uuidgen | tr 'A-Z' 'a-z')
RESULT=$(curl -s -X POST "$URL/issue_relations?schema=app_schema" \
  -H "apikey: $ANON_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"issue_id\":\"$SELF_ID\",\"related_issue_id\":\"$SELF_ID\",\"type\":\"related\"}")
if echo "$RESULT" | grep -q '"23514"'; then ok "FK check blocks self-loop"; else bad; fi
```

**Lição:** a defesa da aplicação (UI excludeIds) é **fina** — DB-level CHECK é a única defesa **real**. Probe deve **testar a defesa DB**, não só a UI.

---

## 18. `PostgREST` service-role bypassa CHECK constraints em service-role, mas em anon (RLS) é REAL (M14 v2100p1, 2026-07-04)

**Sintoma:** probe com service-role `SUPABASE_SERVICE_ROLE_KEY` faz `update({ priority: 999 })` (que viola `issues_priority_check`) → **aceita silenciosamente**.

**Causa:** service-role bypassa CHECK constraints? **NÃO** — mas bypassa `updated_at` triggers que validam range. O `priority=999` é aceite porque **smallint em PG aceita 32767** como `priority` (que é `smallint`). O check constraint `priority >= 0 AND priority <= 4` é **só enforced se** o valor ultrapassar o range do tipo. Mas `999` cabe em `smallint` (max 32767) — então CHECK nem é tocado.

**Workaround no probe:**
```bash
# Use um valor que EXPLICITAMENTE viola o constraint, não que exede o range do tipo
RESULT=$(run update({ title: "x".repeat(600) }))   # CHECK title length 1..512
# Ou melhor: usar insert com FK inválido
RESULT=$(run insert({ ..., state_id: "00000000-dead-beef-cafe-deadbeef0000" }))
```

**Lição:** nem todo "invalid input" gera erro. Para forçar erro DB-level, **target constraints específicos**. CHECK constraints não enforced automaticamente para *over-range* smallint values (até smallint max).

---

## 19. `.single()` PostgREST call devolve null data + null error quando row missing (em vez de error)

**Sintoma:**
```js
const { data, error } = await sb.from("issues")
  .update({ priority: 3 }).eq("id", "nonexistent-id")
  .select("priority").single();
// data=null, error=null (silent miss)
```

vs.
```js
const { data, error } = await sb.from("issues")
  .select("*").eq("id", "nonexistent-id").single();
// data=null, error={ code: "PGRST116", message: "Cannot coerce..." }
```

**Causa:** UPDATE/INSERT **return affected rows count**, sem falha se a .eq().filter() não matched row (PostgREST trata como "0 rows updated, success"). SELECT **single() com 0 rows** falha com `PGRST116`.

**Workaround:**
```js
// Use `.maybeSingle()` em vez de `.single()` se a query pode legitimamente ter 0 rows
const { data, error } = await sb.from("issues")
  .update({ priority: 3 }).eq("id", "X").select("priority").maybeSingle();
// data=null mas error=null if missing — explicit null a representar "not found"
```

**Lição:** `single()` é apropriado só quando **0 rows = erro** (e.g., `fetchIssueByIdentifier`). `maybeSingle()` para queries nullable. Probe precisa esperar `data=null` como resultado válido para UPDATE non-matched, não erro.

---

## 20. Trigger BEFORE INSERT precisa de `when (new.X is null)` ou só dispara para ALL rows

**Sintoma:** trigger `set_issue_board_order` cria novo rank para **todos** os issues (mesmo quando caller passou `board_order` explícito). Resultado: `priority` field com valor `a0` literal sobrescreve um valor intencional.

**Causa:** trigger BEFORE INSERT que não testa `when (new.column is distinct from old.column)` ou `when (new.board_order is null)`. PostgREST + supabase-js atualiza sem old record (INSERT only). O trigger fires para **todos** os rows.

**Workaround no probe:** **wrap trigger em `if new.board_order is null then ...` ou `if tg_op = 'INSERT' and new.board_order = 'a0' then`** — permite bypass se caller já deu um valor intencional.

**Lição:** triggers BEFORE INSERT aplicam-se a **todos** os rows. Se só queremos um subconjunto, **filtrar com `when`** clause ou **conditional dentro do trigger**.

---

## 21. `service_role` bypassa CHECK constraints mas NÃO bypassa FK constraints (M14 v2155p2 vs v2100p1)

**Sintoma:**
```bash
# Service-role UPDATE:
update issues set priority = 999 where id = X
# → SUCCESS (smallint max 32767; CHECK for <= 4 not checked because value fits in smallint)

# Service-role UPDATE:
update issue_relations set related_issue_id = 'not-a-uuid' where id = Y
# → SUCCESS (PostgREST validates UUID format BEFORE sending to DB)

# Service-role INSERT com FK violation:
insert into issue_relations (issue_id, related_issue_id, type) values (A, B, 'related')
# where A exists but B doesn't
# → FK violation error 23503 (FK IS enforced even for service_role)
```

**Causa:** service-role bypassa **RLS** (Row-Level Security) mas NÃO bypassa **CHECK constraints** (todos) nem **FK constraints** (todos). **Confusão comum** entre o que bypassa e o que não bypassa.

**Tabela canónica (probe-relevant):**
| Constraint | service-role bypassa? |
|---|---|
| RLS policies | ✅ YES |
| CHECK constraints | ❌ NO |
| FK constraints | ❌ NO |
| NOT NULL | ❌ NO |
| UNIQUE | ❌ NO |
| PRIMARY KEY | ❌ NO |
| Custom triggers (BEFORE/AFTER) | ❌ NO (executam sempre) |

**Lição:** quando probe quer testar "constraint X dispara" → use FK violation, type overflow (varchar overflow not smallint), ou `not null` violation. **Não** espera CHECK constraint sobre smallint overflow para disparar.

---

## Resumo de novos padrões (17-21)

| # | Domínio | Padrão | Probe workaround |
|---|---|---|---|
| 17 | TS+DB | self-loop permitido por API mas DB bloqueia | Test self-loop via direct PostgREST |
| 18 | service-role | smallint overflow bypassa CHECK | Use varchar overflow ou FK violation |
| 19 | supabase-js | UPDATE `.single()` missing row devolve null silencioso | Use `.maybeSingle()` para nullable |
| 20 | Trigger | BEFORE INSERT fires para ALL rows sem WHEN | Wrap trigger em `if new.x is null then` |
| 21 | service-role | bypassa RLS mas NÃO CHECK/FK/NOT NULL/UNIQUE | Testar contra FK violation directamente |

---

## Lição meta: o que difere este doc de `shell-probe-false-fails.md`

- **shell-probe-false-fails.md (16 padrões)** são sobre como o **probe shell/psql** reporta incorrectamente o **estado verdadeiro** (false-fail positivo, false-pass negativo).
- **postgres-runtime-probe-gotchas.md (5 padrões)** são sobre como o **sistema subjacente** não testa a defesa completa. Mostra **o que o probe precisa de saber** para validar a defesa.

São ortogonais: o shell pode estar OK e ainda assim o probe ser incorrecto (shell-probe), ou o shell pode estar incorrecto e o sistema ser defensivo (este doc).

