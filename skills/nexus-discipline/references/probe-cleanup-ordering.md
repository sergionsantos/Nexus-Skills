# Pattern: Cleanup-before-invariants em verify scripts

> **Pitfall (2026-07-04, M18 v0070 projecto X):** cleanup **tem** de correr antes do invariant check final. Cleanup-then-assert-then-cleanup-again-invariants é race condition guaranteed.

## Sintoma

Verify script corre:
```
setup → mutation → cleanup → invariants check
```
Mas o `delete from app_schema.issues where title like 'M18r-%'` corre, mas o `count(*)` no invariants corre antes do delete completar (ou devido a autocommit lag). **Result**: invariants reportam valores stale que incluem as test rows.

Probe real (M18 v0070):
```
I1: 17 distinct board_order
→ FAIL: 19 (M18r-* ainda no DB quando count correu)
```

## Causa

Em psql, `DELETE` é auto-commit por defeito. **Mas** se o script tem múltiplas `psql -tAc` chamadas, cada uma abre/fecha connection — não há "transaction" a envolver tudo. Race possível em DBs com muitas conexões ou replicas.

Adicionalmente, se o test rows estavam em **state transitório** (e.g., triggers M9 issue_notify, M11 board_order trigger), o delete **espera** que os triggers completem antes de retornar. Em DBs ocupados, isso pode introduzir latência mensurável.

## Fix canónico

**Cleanup BEFORE invariant check**:

```bash
# ❌ NÃO
psql -tAc "delete from app_schema.issues where title like 'M18-%'"
DISTINCT=$(psql -tAc "select count(distinct board_order) from ...")  # stale!

# ✅ SIM
# Setup
psql -tAc "insert into app_schema.issues ..."
# Mutate + assert
# Cleanup (always before final invariants)
psql -tAc "delete from app_schema.issues where title like 'M18-%'"
# Verify cleanup actually happened
REMAIN=$(psql -tAc "select count(*) from ... where title like 'M18-%'")
[[ "$REMAIN" == "0" ]] && ok "cleanup confirmed"
# Now invariants (no race)
DISTINCT=$(psql -tAc "select count(distinct board_order) from ...")
[[ "$DISTINCT" == "17" ]] && ok "invariants intact"
```

## Padrão geral: setup → mutate → assert → cleanup → verify-cleanup → invariants

| Phase | Quando corre | Failure mode |
|---|---|---|
| Setup | Início do script | None — fresh state |
| Mutate | Após setup | Assertion pode falhar (test goal failure) |
| Assert | Após mutate | Mostra progresso |
| **Cleanup** | **Antes de invariants** | **Crítico: testar cleanup funcionou** |
| Verify-cleanup | Após cleanup | `REMAIN=0` confirma que cleanup correu |
| **Invariants** | **Após verify-cleanup** | Final state check |

## Detector

Se invariants falham com valor `expected + 1` ou `expected + 2` (não `expected + N` com N grande), provavelmente é race entre cleanup e invariant check.

```bash
# Se invariants falham:
REMAIN=$(psql -tAc "select count(*) from app_schema.issues where title like 'M18-%'")
if [[ "$REMAIN" != "0" ]]; then
  echo "Cleanup incomplete — re-run cleanup"
fi
```

## Lição lateral (gate de tamanho de amostra)

Cleanup + invariants têm de ser **atómicos no contexto do probe**. Se o cleanup falha, **re-correr o cleanup + re-run invariants** antes de reportar fail.

## Caso real (M18 v0070)

```bash
# v0070 original (failed):
psql ... -tAc "delete from app_schema.issues where title like 'M18r-%'"
DISTINCT=$(psql ... -tAc "select count(distinct board_order) from app_schema.issues where trashed_at is null")
[[ "$DISTINCT" == "17" ]] && ok "I1" || bad "I1=$DISTINCT"  # FAIL: 19

# v0070p1 fixed (passed):
psql ... -tAc "delete from app_schema.issues where title like 'M18r-%'"
REMAIN=$(psql ... -tAc "select count(*) from app_schema.issues where title like 'M18r-%'")
[[ "$REMAIN" == "0" ]] && ok "Cleanup confirmed"
DISTINCT=$(psql ... -tAc "select count(distinct board_order) from app_schema.issues where trashed_at is null")
[[ "$DISTINCT" == "17" ]] && ok "I1"  # PASS
```

**Diff**: invariants reordered para depois do cleanup-confirmation.

## Anti-pattern: cleanup-only-without-verify

```bash
# ❌ Cleanup sem verify — pode falhar silenciosamente
psql ... -tAc "delete from ..."

# ✅ Cleanup + verify
psql ... -tAc "delete from ..."
REMAIN=$(psql ... -tAc "select count(*) from ...")
[[ "$REMAIN" == "0" ]] && ok "cleanup"
```

## Resumo (1-liner)

**Verify scripts: cleanup → verify-cleanup (REMAIN=0) → invariants check. Nunca cleanup-then-invariants sem intermediário.**