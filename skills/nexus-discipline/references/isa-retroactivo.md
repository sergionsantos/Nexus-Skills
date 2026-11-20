---
title: ISA Retroactivo — Procedure for Recovering Work Done Without an ISA
preserved_by: Phase 1 audit (2026-06-18) — value-bearing DROP, not re-inlined
---

# ISA Retroactivo — Recovery Procedure

> Use this when resuming work from a previous session that **should** have had an ISA but did not.
> The procedure exists because skipping it creates a baseline built on fiction (ghost docs) — which
> is worse than having no ISA at all.

---

## When This Applies

You are resuming a task that:
- produced or should have produced outputs in a prior session, AND
- has no `.isa/` artifact tracking those outputs

Do NOT skip straight into adding new outputs. Follow this procedure first.

---

## Procedure

### Step 1 — Stop immediately

Before adding any new outputs, pause. Do not continue building on top of an unverified baseline.

### Step 2 — Verify the filesystem FIRST

For each output the prior session supposedly produced, confirm real existence:

```bash
# For each claimed output file/directory:
search_files <path>        # or
read_file <path>
```

**Session summaries, assistant notes, and memory entries are leads — not ground truth.**
They may reflect the original plan, not what actually landed on disk.

### Step 3 — Create the retroactive ISA

Create `.isa/ISA-[name]-retroactivo.md` consolidating only what was verified:

```yaml
---
title: "[Task name] — Retroactive ISA"
date: <today>
status: retroactive
phase: verify          # advance to the current real phase
retroactive: true
note: "ISA created retroactively on <date>. Original session lacked ISA. Filesystem verified before filing."
---
```

Then populate the ISC section:

- **Each output verified on disk** → `- [x]` (fulfilled)
- **Each output expected but absent** → `- [ ]` (pending — list explicitly, do not omit)
- **Future work items** → `- [ ]` (open)
- **Divergences found** → record as a note under the ISC section (e.g., "the summary listed 5 docs; only 1 found on disk")
- **Process failure** → record the reason the ISA was missing (e.g., trigger phrase fired but ISA skipped)

### Step 4 — Continue with the new phase

Only after the retroactive ISA exists with a verified baseline do you proceed.

---

## Why This Matters

Without a retroactive ISA, the next phase inherits ambiguity — it cannot distinguish "done" from "planned". With a verified retroactive ISA, there is a real (not fictional) baseline against which future deliverables can be validated.

**An ISA citing ghost docs is worse than no ISA.** It creates false confidence that then propagates into subsequent phases, masking the gap until much later — usually at the worst possible moment.

---

## Quick Reference Card

| Situation | Action |
|---|---|
| Session summary lists outputs | Verify each on disk before citing in ISA |
| Output exists on disk | `- [x]` in ISC |
| Output expected but missing | `- [ ]` in ISC — do NOT mark fulfilled |
| Reason ISA was skipped | Record in retroactive note |
| Divergence summary vs disk | Record explicitly in ISC notes |

---

## Cross-Reference

- Ghost Docs anti-pattern: documentos citados num summary que não existem em disco (ver acima: verifica sempre no disco).
- ISA `phase:` field values: `observe → think → plan → build → execute → verify → learn → complete` (frozen invariant)
- Hook that enforces ISA gate at session stop: `a stop-time hook (if you have one)`
