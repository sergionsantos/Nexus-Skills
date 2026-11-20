---
name: session-wrap
description: Wrap up the current work thread — write a durable, faithful topic note (state, decisions, pending items and limitations, files, lessons) so the session can be cleared and the theme re-entered later without starting from zero. Optionally also saves a short re-entry pointer in a persistent memory tool, if you have one. Use when finishing a theme, before /clear on a topic worth returning to, or when the user says "wrap this up", "fecha o tema", "/wrap".
version: 1.0.0
status: active
---

# session-wrap — end-of-thread wrap

Distill a finished work thread into one durable markdown note (the "wrap") that lets a future session re-enter the theme quickly. Optionally, also store a short pointer to it in a persistent memory tool.

## When
- End of a work thread the user will return to later.
- Before `/clear` on a theme worth re-entering.
- User says "fecha o tema", "wrap this up", "/wrap".

Most sessions need NO wrap (disposable). Only wrap themes you will re-enter.

## Phase 0 — Scope: workspace first, ALWAYS

The wrap is about **what THIS session worked on in THIS workspace** — never about what a memory/search tool happens to surface. Run this phase before writing anything:

1. **Identify the workspace.** `pwd` + git root. This is the anchor for everything below.
2. **Look for an active spec/plan:** a spec/plan file (e.g. `PLAN.md`, `SPEC.md`, an issue/ticket) or, if it exists, `.isa/ISA-*.md` (format of the nexus-discipline skill; check with `ls <workspace>/.isa/ISA-*.md`). If found, its title/scope IS the topic, and it becomes the authoritative source.
3. **No spec/plan → the session itself is the primary source.** Derive the topic from what was actually done in this conversation: files touched, decisions made, the user's opening request.
4. **Supplement with workspace signals** if the session context is thin (post-compaction, long session): `git log --oneline -10`, existing `Wraps/`/`LOG*.md` in the workspace, files modified today (`find <workspace> -name "*.md" -mtime -1`).
5. **Set the start of the theme** (session start if unsure). Anything before it is out of scope; this prevents mixing parallel work streams.

**Hard rule:** candidate topics come ONLY from steps 2-4. If unsure between candidates, ask the user to pick **among workspace/session-derived candidates** — never offer topics surfaced by a global memory search that don't match the workspace.

## Where the wrap file goes — one rule

The destination is configurable; ask the user once if there is no convention, and reuse it afterwards.

| Situation | Default path |
|---|---|
| Session inside a project directory | `<project-dir>/Wraps/wrap-<slug>-<YYYY-MM-DD>.md` |
| No identifiable project (loose theme) | `<notes-dir>/Wraps/wrap-<slug>-<YYYY-MM-DD>.md` (`<notes-dir>` = a notes folder the user names) |

- **Naming:** always `wrap-<slug>-<YYYY-MM-DD>.md` — lowercase `wrap-` prefix, greppable. Not `WRAP-*`, not `LOG-*`, not bare `<slug>-<date>`.
- **Never:** inside `.isa/` (spec ≠ state), loose in the project root, in `.audit/`, or as `LOG-*.md`. `LOG.md`-style files are running project journals — a wrap may LINK to them, not replace or impersonate them.
- If the project is a code repo, never commit wrap files into it (keep `Wraps/` untracked or ignored; to ignore it locally without touching `.gitignore`: `echo Wraps/ >> .git/info/exclude`).
- Existing wraps in old locations: leave them. Migration is a separate task, never a side effect of a new wrap.

## Procedure

1. Run Phase 0.
2. Collect sources, in this hierarchy: **spec/plan (curated) > session context (Phase 0) > raw records** (git history, memory search results, logs).
3. Write the wrap file at the path above. Mark it **DRAFT** at the top, with topic, date and start-of-theme. Sections:
   - **Estado** — what is actually done, and where things stand now.
   - **Decisões** — decisions taken and why.
   - **Pendente + limitações** — open items, known limitations, risks. This is the most important section: never promote planned → done, never omit limitations.
   - **Ficheiros** — files/artifacts touched or produced (paths).
   - **Lições** — non-obvious things learned that a future session should not rediscover (optional, only if real).
   Cite each claim's source: `[A#]` for a curated artifact (spec/plan/doc), `[R#]` for a raw record (commit, log, search hit); list the sources at the end (e.g. `[A1] PLAN.md`, `[R1] commit abc1234`). Be faithful. Full example: [references/example-wrap.md](references/example-wrap.md).
4. Review: diff the draft against the specific new content written this round (spec, LOG, commits). A draft can silently omit or misattribute the round's central finding; fix by hand. The spec/plan remains the source of truth; the wrap is the re-entry index.
5. **Optional — persistent memory pointer.** Only if the user has a persistent memory tool: save ONE short record with topic, date and the wrap file path (and 2-3 lines of state). Then verify by searching for the topic — only report the wrap complete if the search returns the record. If you have no such tool, skip this step; the file path is the re-entry pointer.
6. Report to the user: the wrap path, a 3-5 line summary, and anything marked PENDING.

## Re-entry later
New session → read the wrap file (or search your memory tool for the topic and follow the pointer to the file). Then check the "Pendente" section against the current workspace state before continuing.

## Fallback when automatic retrieval is unavailable
If a memory/search tool you wanted to use is offline or returns nothing useful, that is an infrastructure problem, NOT a licence to skip the wrap or fake sources:
- State explicitly what failed.
- Write the wrap by hand from the Phase 0 sources (session + workspace — you have them without retrieval), at the canonical path.
- If the optional memory pointer could not be written, either omit any "re-entry: search memory for ..." line or mark it `PENDING pointer write — not yet in memory`, and tell the user.
- NEVER leave a re-entry line pointing at a record that was never written.

## Anti-patterns

| Anti-pattern | Correction |
|---|---|
| Asking "wrap X or Y?" where X/Y came from a global memory search, unrelated to the workspace | Phase 0 hard rule — candidates only from spec/session/workspace |
| Writing the wrap before scoping | Phase 0 first, always |
| Letting a tool default decide the path | Use the location rule: `Wraps/wrap-<slug>-<date>.md` |
| Writing the wrap as `WRAP-*.md` in the project root, inside `.isa/`, or as `LOG-*.md` | `Wraps/` subdir, `wrap-` prefix; LOG.md is a different artifact |
| Moving old wraps to the new location "while at it" | Migration is a separate, deliberate task |
| Reporting done without verifying the memory pointer (when one was written) | Search must return the pointer record |
| Trusting an automatically assembled summary because it looks coherent | Retrieval can return records from an adjacent project, not this session. Treat it as an INDEX; add a `FIDELITY NOTE` (a line in the wrap saying that the summary was assembled automatically and is only an index, followed by the path of the authoritative artifact) pointing at the session's authoritative artifact and report both paths |
| A parallel stream's spec/plan file never made it into the repo (worktree cleaned up before commit) | Before wrapping a multi-stream round, check every stream's spec landed (`git ls-files .isa/ \| grep <topic>`); if one is missing, write its section from commit messages + session, and say explicitly what was lost |
| Spec passed as a source but the draft still omits the round's central finding | Always compare the draft to what was newly written this round, every time |

## Caveat
A wrap is a set of HIGHLIGHTS, not an exhaustive record. It can miss a decision — it is append-friendly and correctable by hand. Don't trust it blindly.
