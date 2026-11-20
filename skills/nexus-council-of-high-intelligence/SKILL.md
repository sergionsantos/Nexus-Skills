---
name: nexus-council-of-high-intelligence
description: "Convenes a fixed council of 18 historical thinkers (Socrates, Feynman, Sun Tzu, Ada Lovelace, Taleb, Kahneman, Munger, Meadows, Torvalds, Rams, ...) to pressure-test a real, material decision: a blind first round, an anonymized cross-examination, a final stance round, a confidence-weighted tally and a structured verdict (kill criteria, next step, minority report). Each member runs as an independent subagent defined in agents/. Modes: --quick, --duo, --triad <domain>, --members a,b,c, --full. Use when the user asks to 'convene the council', 'council this', 'stress-test / war-room this decision' and the decision has material downside, competing values, incomplete evidence or irreversibility. Do NOT use for factual lookups, cheap reversible choices or pure creation. For user-defined personas instead of this fixed roster use nexus-persona-council."
---

# Council of High Intelligence

Structured multi-perspective deliberation with 18 fixed members, run through parallel subagents. Based on the open-source project `0xNyk/council-of-high-intelligence` (MIT; see `LICENSE`). Everything needed is inside this folder:

- `references/protocol.md` — the authoritative protocol: member/domain/polarity/profile/mode tables, round prompts, enforcement steps, tie-breaking and the **Output Templates** heading. Read it before running; never reconstruct tables or templates from memory.
- `agents/council-{name}.md` — one definition per member (identity, method, output formats).
- `configs/`, `scripts/` — optional multi-provider routing (not used by this skill's default path).

## Trigger phrases
"convene the council", "council this", "pressure-test this", "stress-test this", "war room this", "what would the council say about...", or an explicit request for several expert perspectives on a real decision.

## Scope gate
Convene only for material downside, competing values, incomplete evidence or irreversibility. For factual lookups, cheap reversible choices or pure creation, answer directly (or use `--quick`/`--duo`).

## Mode selection
- `--quick`: two rounds, no cross-examination.
- `--duo` or two named members: Duo mode (polarity pair).
- `--full`: all 18 members.
- `--triad <domain>` or a bare question: pick a triad from the protocol tables and state the reason. Default.
- `--members name1,name2,...`: explicit selection of 2–11 members. `--profile <name>` selects a panel profile.

State and lock the mode, the panel and the 1.5× domain-weight seat before Round 1, before any position exists.

## Execution — subagents of a single provider
Use the protocol's single-provider path. Skip the protocol's provider detection, model routing and external-provider dispatch (STEP 1 paths A/B, `codex_exec`, `gemini_cli`, `ollama_run`, `cursor_cli`, `openai_compatible_api`); they are optional extras. Report `single provider (subagents)`. The `--models`, `--dry-route`, `--no-auto-route` flags and `.council.yaml` routing keys do not apply.

Dispatch all members of each round together, in one call to your subagent tool (the Task/Agent tool of your host, e.g. in Claude Code):
- Council members are NOT registered agents in a clean install: run each member as a generic subagent and give it the absolute path of `agents/council-{name}.md` to read (never use `subagent_type`).
- Each member reads its complete `agents/council-{name}.md` (path inside this skill's folder; give subagents the absolute path) and receives the protocol's round-specific prompt verbatim plus the case context.
- Keep all rounds and word limits: problem-restate gate, blind-first Round 1, anonymized Round 2, Round 3 crystallization ending with the exact `STANCE: | CONFIDENCE: | DEALBREAKER:` line — or the Quick/Duo equivalents.
- Assign stable Member A/B/C labels before Round 2; strip self-attribution from blind outputs; never disclose the mapping to members. Restore names only in the Chairman synthesis.
- After Round 2 run STEP 4: `supported_objection_review`, `novelty_gate`, optional `assumption_challenge`, evidence labels, anti-recursion. An objection needs a relevant case/source fact with locator, a causal mechanism and an observable falsifier; label assumptions, never invent facts or sources.
- At most one repair request per unsupported objection per session. Unresolved unsupported objections are excluded from verdict reasoning but recorded in the Minority Report as exclusions, not evidence. Keep supported minority objections and every actual vote.
- Agreement never triggers enforcement. The assumption challenge needs a named material assumption and evidence gap; one relevant member, once per session.
- Pass the review record to Round 3 and the synthesis. Re-dispatch only the member that needs a bounded follow-up.

## Tally and Chairman
Apply STEP 6 exactly: base weight 1.0, domain seat 1.5×, confidence high/med/low = 1.0/0.75/0.5, consensus = two-thirds of total base weight. Below the threshold, present the split; do not force consensus.

The main session acts as Chairman (do not spawn another agent; this takes precedence over protocol STEP 1.7/STEP 7, which describe dispatching the synthesis to a separate call) and writes the verdict with the exact Council/Quick/Duo Verdict template from the protocol, leading with Unresolved Questions and ending with Session Metadata. Set `provider_count: 1` and `fallbacks_triggered: none` unless a real failure occurred.

## Do not
- Skip or merge rounds, or rename/reorder/drop template sections.
- Invent stances, objections or dissent.
- Convene for trivial or cheaply reversible questions.
