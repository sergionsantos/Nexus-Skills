# Explain-Then-Recommend (detailed support doc)

> **Companion to the `nexus-discipline` doctrine (explain-then-recommend rule).** Anti-pattern + protocol for the moment when the user says *"explica palavras simples e dá a recomendação"* (or its variants).
>
> Source session: **projecto X M11.1.0 root-cause, 2026-07-04.** User said: *"nao percebo a opcao a ou b. explica palavras simples e da recomendacao"*. Triggered after I gave a structured A/B option menu for a 5%-threshold gate decision.

---

## 1. The pattern (when to apply)

The user has just received a **menu** of options (typically A/B/C or A/B) and asked you to:
- **Translate** it into plain language ("explica palavras simples"), OR
- **Recommend** one with reasoning ("dá a recomendação", "tu decides?" as a question), OR
- Both.

This is **different** from:
- "Tell me A/B/C" (wants the menu, neutral framing OK).
- "What's the trade-off?" (wants trade-off explanation, may or may not want recommendation).
- "What would you do in my place?" (wants recommendation, no menu needed).

**Detector rules** (trigger this protocol if ANY):
1. Last user message contains: "não percebo", "não entendo", "não sei", "explica X", "em palavras simples", "dá a tua recomendação", "what would you do", "tu decides??" with **?** or query intonation.
2. User has been in this session for >1 turn and just rejected a structured menu before (signal: they want explanation).
3. Decision involves trade-off terminology they're unlikely to know (e.g. sysadmin language for end-user, technical debt vs feature velocity for product owner, type punning vs runtime API for backend dev).

## 2. The protocol (3 steps, ORDER MATTERS)

### Step 1 — Analogy-first framing (200-400 words max)

**Goal:** translate the trade-off into a metaphor the user already has. The metaphor captures the **structural shape** of the choice, not just a feeling.

**Test for a good analogy:** if you remove the technical words and keep the analogy, does the user immediately understand the trade-off structure?

| Trade-off type | Bad analogy | Good analogy |
|---|---|---|
| Cause vs symptom (M11.1.0) | "It's complex" | "Paracetamol vs análise de enxaqueca" |
| Optimize vs fix underlying | "Two ways to do this" | "Patch the leak vs replace the pipe" |
| Speed vs correctness | "Pick one" | "Travel fast alone, travel far together" (African proverb) |
| Manual vs automated | "Different effort profiles" | "Do it by hand this time vs build a sewing machine" |
| Reversible vs irreversible | "Be careful" | "Closing a browser tab vs deleting production data" |

**Critical:** the analogy captures **the axis of the trade-off**, not the domain. "Painting the wall" vs "fixing the leak" — paint is just decoration, won't tell the user why we'd choose between "fix now" and "patch now". If your analogy sounds like decoration, redo it.

### Step 2 — Re-state options A/B/C with 1-line trade-offs (max 50 words per option)

After the analogy, **re-list the options** but compact:
- Each = 1 sentence
- Trade-off named explicitly (cost / time / risk / reversibility)
- Do NOT add new options that weren't in your original menu (defeats the protocol's purpose)

**Example (M11.1.0):**
> "**Opções:**
> - **A** — tratar só hoje: corrige os 2 duplicates existentes. Se voltar a aparecer, temos de voltar aqui.
> - **B** — investigar a causa (5 min) + tratar: custa 5 min mais, mas pode impedir que o problema volte.
> - **C** — só investigar: cobarde, não corriges o problema actual."

### Step 3 — **Explicit recommendation** with justification (no hedging)

After the options, **your opinion**. First-person, definitive.

> "**Recomendo B.** Tratar causa > tratar sintoma quando custa pouco mais. C só faz sentido se tens um deadline imediato. A é OK se estás confortável com voltar cá se aparecer de novo."

**Anti-patterns to avoid:**
- "Eu acho que B, mas depende" — hedging destroys the value
- "Tu é que percebes" — user explicitamente NÃO quer isto
- "Qualquer opção é válida" — if so, why offer?
- "Posso prosseguir com X se quiseres" — puts decision back on user

**When you genuinely don't have a strong opinion:** say so, but propose a tiebreaker (e.g. "I lean A weakly; pick whichever makes you feel safer — A is fully reversible, B is partially irreversible").

## 3. Examples (real cases from session)

### Example 1 — Cause vs symptom (M11.1.0)
**Original A/B/C (technical):** "rerank via PostgREST | rerank + investigate root cause | investigate only"

**After the rule:**
> "Rerank dos 2 duplicates que vejo hoje, vs investigar primeiro a coluna default 'a0' no schema. O primeiro corrige o sintoma (5 min), o segundo trata a causa (5 min extra) e pode impedir que isto volte.
>
> Analogia: enxaqueca que volta toda a semana — paracetamol para a dor de hoje, ou análise para perceber o que dispara? Tratar causa > sintoma quando o custo extra é baixo.
>
> Recomendo **B** — investigar + fixar no mesmo ciclo. A é aceitável se tens deadline imediato."

**What user did:** picked B (and didn't push back).

### Example 2 — When NOT to recommend (counter-example)
If the trade-off is **genuinely symmetric** and you don't have more info than the user, don't fake a recommendation.

**Example:** "pick a postgres UUID library" when both nanoid and uuid-pkg work fine. **Right answer:** "either works; no testable difference in our case. Pick whichever you know better."

## 4. Why this protocol exists (rationale)

The default menu + "tu decides" is **lazy**: it transfers the cognitive load to the user, but the user delegated because they don't have the context to decide. **Information asymmetry**: you know the trade-off better than they do (you've seen hundreds of times before). Withholding your recommendation **wastes the asymmetry**.

The "neutral pros/cons" frame assumes the user can weight pros and cons. They can't — that's why they asked. Your job is **to model the weighting function for them**, given the user's earlier signals in this session (risk tolerance, time pressure, etc.).

The user explicitly asked. This is the user trusting you with a small amount of decision authority. Don't waste it by being "neutral".

## 5. Variant: user says "pick one" but doesn't ask for reasoning

If user just says *"pick one"* without the explain + recommendation prefix:

- **Plausible interpretation 1:** trust me, just pick. → *pick + brief one-liner why ("B because it's reversible")*
- **Plausible interpretation 2:** they want what you'd pick, but want the explanation later. → *still explain + recommend* (cheap, satisfies both)

**Default: explain + recommend.** Cost of over-explaining: 200 extra words. Cost of under-explaining: 1 round-trip to clarify. Over-explaining wins.

## 6. Diagnostic: am I falling back to neutral framing reflexively?

Symptoms you've defaulted to menu + tu decides:
- Menu has 3+ options and no obvious recommendation
- Your "Recommendation" section is absent OR uses hedging ("poderia", "talvez", "depende")
- You listed trade-offs without weights
- You closed with a question back to user ("qual achas?")

If you spot this on **re-read** of your draft: rewrite Step 3 with a definitive recommendation. **Cost:** 30s. **Benefit:** 1 round-trip saved.

## 7. Edge case: user disagrees with recommendation

User picks **A** when you recommended **B**. **Do not**:
- Push back ("mas B é melhor...")
- Apologize ("ah desculpa, eu tinha sugerido...")
- Defend your analysis at length

**Do:**
- Confirm the choice "A, registado"
- Note the trade-off you're accepting (one line: "A: se voltar a aparecer, voltamos cá. OK")
- Move on

**Why:** user knows they can change the recommendation next time. Pushing back destroys the trust you've built by being willing to recommend in the first place.

## 8. Anti-self-warnings (when this rule bites back)

| Situation | Use the rule? | Why |
|---|---|---|
| User asks "A ou B?" with **?** for two technical options both within their expertise | NO | They have the context; recommend OK, full protocol overkill |
| User says "explica" but on a topic *they* specified previously | NO | They're asking for a refresher on their own problem; just rephrase their own question |
| Decision has ethical/legal/risk impact beyond your modeling | NO | Defer to human ("isto tem impacto X que tu conheces; não tomo esta decisão") |
| User explicitly says "só quero opções, sem recomendação" | NO | Override Step 3 → list only, no recommendation |
| Decision is **high-stakes** (production deploy, migration, financial) | YES but with caveat | Recommend + require explicit ack ("para avançar preciso que confirmes A ou B com a tua justificação") |

## 9. Cross-references in SKILL.md

- Recovery: when user disagrees, just confirm and move on
- Honest report: user explicitly asking for a recommendation is a signal of trust; reciprocate

---

**Lição meta (sessão M11.1.0):** nunca deixes um menu A/B sem recomendação explícita quando o user pediu explicação. É o anti-pattern "neutrality theatre" — performar neutralidade quando a confiança do user em ti é o que está a ser pedida.
