# Cold-Eyes Review — Findings Patterns from Independent Lens Sessions (2026-07-04)

> When Rule 0 (independent review) is satisfied via **cold-eyes fallback** (subagente unavailable, per `nexus-discipline` Rule 0 fallback mode), the agent executes the review with their own model under a lens of "I didn't write this". This file catalogues **11+ cold-eyes findings discovered in 2026-07-04 projecto X M11-M15 review sessions** — concrete patterns future cold-eyes sessions should look for.

## 1. The cold-eyes method recap

- Read each function touched, *as if you hadn't written it* (do NOT re-read your own execution reasoning — that contaminates the lens).
- Classify every finding FROZEN tier (BLOCKER / MAJOR / MINOR / NIT — see `references/independent-code-review-calls.md` §3).
- Cite ID (e.g. F-MR1, F-MR8.2) — keeps audit trail.
- A MEDIUM finding is NOT a fix — backlog unless cheap.
- Final verdict **without hedging**. Cold-eyes is fallback, not substitute.

## 2. Findings patterns observed (M11-M15 projecto X)

Each row: finding → fix shape (if applied).

### 2.1 — Stale / lying JSDoc comments

| Finding | Fix |
|---|---|
| **F-MR1 (M11):** trigger file comment claimed "Uses `_fi_key()` PL/pgSQL helper" — code uses `max ‖ 'a'`. Comment drifted from implementation. | Rewrite: "Strategy `max ‖ 'a'` works for ≤100 issues/team; v2 port `generateKeyBetween` to PL/pgSQL." |

**Pattern:** Any time a comment claims X, verify X is still true after refactor.

### 2.2 — Dead / shadow variables

| Finding | Fix |
|---|---|
| **F-MR2 (M11):** declared `v_max_len` and `v_last_char`, never used — leftover from half-refactor. | grep declared variables that have no consumer; remove unused. |

**Pattern:** After refactor, scan declarations for orphan ones.

### 2.3 — Self-loop guards on TS API only

| Finding | Fix |
|---|---|
| **F-MR6.2 (M12):** `setParent()` throws if childId === parentId but DB has no constraint. Any future API caller bypassing UI can self-loop. | Minimum: BEFORE INSERT trigger on DB; Acceptable MVP: documentation note. |

**Pattern:** JS-only guards are bypassable. DB-level is source of truth.

### 2.4 — Partial-failure handling in `Promise.all`

| Finding | Fix |
|---|---|
| **F-MR8.2 (M13):** `Promise.all(ids.map(update))` rejects on FIRST failure; 49/50 applied but rollback apparent. | Replace with `Promise.allSettled` + collect `succeeded` / `failed`. `onSuccess` merges per row, `onError` reports partial but still merges what succeeded. |

**Pattern:** "All or nothing" is almost never what bulk callers want. Per-row merge = server-is-source-of-truth.

### 2.5 — PostgREST FK name guessing

| Finding | Fix |
|---|---|
| **F-MR9.1 (M14):** `select "issues:issues!fk_issue_relations_issue_id(...)"` returns 400 — real name is `issue_relations_issue_id_fkey`. | Never guess FK name in PostgREST embed. Use `pg_constraint.conname` (see `references/shell-probe-false-fails.md` #14). |

**Pattern:** Auto-generated FKs follow `<table>_<col>_fkey`, migrations often use custom — always query the constraint catalog.

### 2.6 — Keyboard shortcut browser conflicts

| Finding | Fix |
|---|---|
| **F-MR9.3 (M14):** `Cmd+B/X/R` mapped to relation picker conflicts with native `Cmd+B` (sidebar) / `Cmd+X` (cut) / `Cmd+R` (refresh). | Require `!e.shiftKey` + `!e.altKey`. Test in actual browser, not unit-test. |

**Pattern:** Cmd+single-key is dangerous; require modifier-key combinations.

### 2.6a — Workspace-wide queries leak across teams

| Finding | Fix |
|---|---|
| **F-MR8.4 (M17.1):** `useLabels()` returned workspace-wide labels (all teams' labels), then `labels-manager.tsx` showed them per-team. Multi-team workspace = user sees labels they shouldn't see. | Add `teamId?: string` param to hook + filter `fetchLabels({teamId})` to `team_id.eq.<id> OR team_id.is.null` (preserves global labels). Add cache key discriminator `qk.teamLabels(teamId)`. |

**Pattern:** ANY query that fetches "all labels" / "all projects" / "all users" / "all cycles" is **workspace-wide by default** — multi-team workspaces leak across tenants. Hook API must require `teamId` (or `workspaceId`) for tenant-scoped queries. M17 polish root cause lesson.

### 2.7 — Cache invalidation gaps in React Query

| Finding | Fix |
|---|---|
| **F-MR6.1 (M12):** `useSetParent` had no `onSuccess` invalidation; UI only updated when realtime reconciliation fired (D112) — visible delay. | Trace `qc.invalidateQueries` calls per mutation: invalidate target, source, AND detail-page caches. Plus optimistic cache update per row. |

**Pattern:** Mutations without explicit client cache invalidation appear broken until realtime round-trip arrives.

### 2.8 — `Promise.allSettled` double-error pattern

| Finding | Fix |
|---|---|
| **F-MR8.2 detail:** mutationFn throws `partialErr` with `succeeded` + `failed` arrays. `onError` must merge succeeded BEFORE reporting error (otherwise dropped promises look lost). | Test with partial-failure (1 valid + 1 fake); `onError` must: 1) merge `succeeded` from error payload, 2) invalidate lists, 3) toast descriptive message ("Updated 2/3; 1 failed: ..."). |

**Pattern:** Errors aren't "transaction abort". Partial success is still success; cache updates must reflect reality.

### 2.9 — PostgREST service-role bypasses CHECK constraints (informational)

| Finding | Fix |
|---|---|
| **F-MR8.12 (M13):** Service-role key bypasses `priority BETWEEN 0 AND 4` constraint. Out-of-range probes silently accepted invalid data. | Not client-fixable. Test with ANON key for user-facing constraint validation. Document as informational. |

**Pattern:** Service-role = admin. RLS + CHECK only enforceable with non-admin keys.

**Workaround for runtime probe with CHECK constraints:** use a query that PostgREST WILL reject despite service-role. E.g. `priority` is a `smallint` (range -32768..32767) — sending `priority: 999999` violates the type cast, returns 400. Use **type-cast violations**, not constraint violations, when probing with service-role. M15.3 lesson.

### 2.10 — `'use server'` vs `'use client'` mishap

| Finding | Fix |
|---|---|
| **M15.2:** Generated `lib/api/teams.ts` with `"use server" if false else "use client"` — invalid syntax (no conditional). Build broke. | Use **only** one of `'use client'` / `'use server'` as a single string literal. No conditionals. No string concat. |

**Pattern:** Both are file-level string directives, not values.

### 2.11 — Document fidelity drift vs DB state

| Finding | Fix |
|---|---|
| **M15 closeout:** doc claimed "3 cron jobs (purge, cycles, auto_archive)" but exact text was "Cron jobs: 3 (purge, cycles, auto_archive)". Probe expected `"purge + cycles + auto_archive"` — false-fail. | When closing a milestone, run a verify that greps the doc for state claims — make claims match probe patterns. |

**Pattern:** When verifying docs-as-source-of-truth, ensure the doc text and probe text share *literal phrasing*. Drift = false-fails.

## 3. The cold-eyes sequencing

Cold-eyes works best as a **discrete phase** between fixes, not before any fixes:

1. **State**: "I'm doing cold-eyes, fresh lens"
2. **Read**: each function/hook file, schemas, recent migrations
3. **Hunt**: patterns 2.1-2.11 above — explicit checklist
4. **Classify**: BLOCKER / MAJOR / MINOR / NIT (frozen taxonomy)
5. **Cite ID**: F-MR[N] or M-MR[N] per finding
6. **Apply** (with care): only BLOCKER + MAJOR fixes in scope; MEDIUM → backlog
7. **Verify**: re-run verify script — assert each finding gone
8. **Verdict**: clean (or N1/N2 still applies) — without hedging

## 4. Cold-eyes anti-patterns

- **Re-read your own execution reasoning**. Contaminates lens.
- **"Is this what I would have done?"**. If X works + consistent with neighbouring code, doesn't matter.
- **Treat MEDIUM as fix-worthy**. Distinguish "5min fix while I'm here" from "refactor". M- = backlog.
- **Skip prod-side concerns** (RLS, FK, service-role). Most findings happen at DB boundary, not TS layer.
- **Report zero findings** when there are several. Cold-eyes is biased toward real problems if you look.

## 5. Cold-eyes vs subagente trade-off (transparent)

`nexus-discipline` documents cold-eyes as **fallback** when subagentes are not configured. Honest trade-off:

| | subagente (Rule 0 proper) | cold-eyes (fallback) |
|---|---|---|
| Lens purity | Same model, fresh context | Same model, **same blind spots** |
| Speed | One turn dispatch + result | Same executor, manual lens |
| Coverage | Subagente reads what you ask | You read what you can grep |
| Trust | External | Self-rated (citation is proxy) |

**Cold-eyes is NOT Rule 0** — never claim it as. But it's better than no review. Catches the **comment-vs-code drift** class which is genuinely hard to spot during implementation.

End.
