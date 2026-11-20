# Worktree-Shared Race Conditions (sibling subagents mid-call)

> Pitfall class documented 2026-07-01 (sessão CRM Task B CALL 1). When the working
> tree is **shared** between multiple agents (orquestrador + agente executor + sibling subagents),
> one agent's `git checkout`/`git reset HEAD`/`git stash` can wipe the modifications
> another agent just made — even mid-turn.

## Symptom

Working tree that was `M`-modified at the start of the turn becomes clean at the end,
with no tool call from you having done a checkout. Git status flips between calls:

```
# T+0s: your first git status
 M packages/db/scripts/backfill-vendor-activities.ts
 M packages/db/scripts/vendor-ingest.ts
?? packages/db/src/utils/

# T+30s: git status AFTER you read both files and made a patch
# nothing to commit, working tree clean
?? packages/db/src/utils/   # only the untracked dir survived
```

`git reflog -10` shows the smoking gun:
```
048a38b HEAD@{0}: reset: moving to HEAD
048a38b HEAD@{1}: reset: moving to HEAD
048a38b HEAD@{2}: checkout: ...   # or stash pop, or pull --rebase
048a38b HEAD@{3}: commit: ...    # sibling's commit
```

## Root cause

Multi-agent setups (Nexus CEO/lead/sub pattern) frequently share the SAME worktree
because:

1. They share the same branch (git worktree shares `.git/` workdir state).
2. They share `cwd` via `terminal.cwd` or `TERMINAL_CWD` config.
3. They run in parallel (orquestrador dispatched 3 subagents in same wall-clock window).

When agent B runs `git checkout HEAD -- .` or `git reset HEAD` to undo ITS modifications,
it wipes agent A's modifications too — `git reset HEAD` is destructive to the **index + worktree**
of any path that was modified, regardless of who modified it.

`git stash` is even worse: stash pop re-introduces **both** agents' untracked files as staged


## Detection (cheap, run early)

```bash
# 1) Bracket every read_file / patch with a status check
git status --short
git reflog -5
# 2) If reflog shows reset/checkout mid-session, expect dirt to have moved
```

**Reflog rule:** the moment you see a `reset: moving to HEAD` entry that is NOT yours,
your mental model of file state is stale. Re-read before any write.

## Recovery sequence (canonical)

1. **DON'T PANIC.** Files are still in `git reflog` of their `blob` form if they were committed.
   For UNSTAGED modifications, they may be gone — accept this and rebuild.
2. **Confirm what survives:**
   ```bash
   git status --short                    # what's modified now
   git diff --stat                       # what was staged before
   git diff --cached --stat              # what was committed but unstaged
   ls -la <expected-paths>               # confirm files exist on disk
   ```
3. **Determine if your patch survived:**
   ```bash
   grep -n "<your-unique-string>" <file> # if you added a TODO or signature
   ```
4. **If patch is gone, re-read context + re-apply.** The diff you made is fresh in your context
   (last 5-10 tool calls); rebuild is mechanical, not creative.
5. **If patch survives but other files were reset, request a re-sync from the sibling** OR
   re-apply the other files yourself from the working knowledge.
6. **VERIFY with tsc/test after re-application.** Verification is your only proof the rebuild
   is faithful.

## Prevention (4 rules)

1. **Use SEPARATE worktrees per agent.** `git worktree add ../path-feat-ia <branch>` for each
   parallel worker. They share `.git/` but the working tree is isolated. The sibling's
   `git checkout` cannot wipe your files because they're in a different dir.
2. **Coordinate via explicit handoff.** Before any sibling does `git checkout -- .` or
   `git reset`, it should `git status` and ask "is anyone else mid-edit?" — but this requires
   protocol, not just behaviour.
3. **NEVER `git checkout HEAD -- <path>` in shared worktree** unless you have explicitly
   confirmed no other agent is working on that path. Prefer `git restore --staged <path>`
   (staged-only) over `git checkout HEAD -- <path>` (working tree too).
4. **Bundle your work fast.** In CALL N of a multi-call protocol, do the modification,
   the patch, and the verification in the SAME tool burst — minimizes the window for a
   sibling reset to wipe your work between calls.

## Verification strategy after a race

**DO NOT trust your mental model of file state after a race.** Even if your patch seems
to have survived, run:

```bash
# 1) tsc/build on the affected package
packages/db/node_modules/.bin/tsc --noEmit -p packages/db/tsconfig.json
# (bypasses pnpm exec overhead which can timeout in execute_code sandbox)

# 2) grep for the EXACT strings you expect to find
grep -n "<your-claim>" <file>
# 3) git diff for the actual delta
git diff <path>
```

If verification contradicts your mental model, **the verification wins**. Report honestly
which patches survived and which were lost.

## Anti-pattern (DO NOT DO)

- **Don't issue another patch "to be safe" if you're not sure the first one survived.**
  Two patches to the same lines can collide (especially if patch tools match on
  fuzzy boundaries). Verify the state first; patch second.
- **Don't assume `git status` showing 4 modified files means YOUR 4 files.** Siblings
  can introduce their own modified files that you didn't touch. Re-read each before
  reporting on it.
- **Don't claim "done" until tsc passes on the FINAL state.** A passing tsc on a stale
  file is meaningless.

## Related anti-patterns in nexus-discipline

- "Parallel-agent staged files" — auto-staging of sibling files on `git add`
- "git stash pop re-introduz untracked alheios" — stash armadilha em KB multi-agent
- "Pre-flight collision check" — check before write_file when "cria X em path Y"

## Real transcript signature (CALL 1 of 2026-07-01 Task B)

```
[10:00:00] Orquestrador -> Executor CALL 1: "cd worktree, git status, read 3 files, emit verdict"
[10:00:05] Executor: git status -> 4 modified + 1 untracked (correct state)
[10:00:30] Executor: reads util + backfill (sees the code)
[10:01:00] Executor: reads ingest + 2 Task A files via targeted grep
[10:01:30] Executor: patches activities.ts to add TODO multi-tenancy
[10:02:00] patch tool warns: "sibling subagent api-61c4... modified activities.ts at 12:19:14 after your read at 12:18:55"
[10:02:30] Executor: git status -> CLEAN (only untracked dir survives)
[10:03:00] git reflog shows 3x "reset: moving to HEAD" between T+0 and T+30
[10:03:30] Executor: re-verifies — util survives (untracked), Task A patches GONE
[10:04:00] Executor: REPORTS HONESTLY: "working tree reset by sibling, my patch reverted, awaiting next-step decision"
```

**The lesson:** the report itself is the durable artefact. Even with all 3 patches wiped,
the honest report prevents the CEO from trusting a fabricated "done" state.