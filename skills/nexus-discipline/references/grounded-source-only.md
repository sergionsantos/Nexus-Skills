# grounded-source-only — verbatim citation discipline for identity/memory blocks

> **Companion to**: `nexus-discipline`. Use whenever constructing an identity block,
> memory dump, candidate claim, persona prompt, or any artefact that **asserts facts
> about a user/person/system** — especially when the source is an external KB or
> interview and the temptation is to "fill in" details that feel right.
>
> **Origin (case pattern)**: an agent wrote an 8-claim core identity block for a person
> from a knowledge-base document and mixed in 3 plausible-but-fabricated details: a
> relative's city of residence that appears nowhere in the source, a business
> affiliation copied from a *different* profile, and a past project presented as a
> current company. The owner rejected it hard: *"A truth-first memory system cannot
> inject invented identity, not even in a spike."* Three rounds of correction followed.

---

## Procedure (apply before any identity-block write)

1. **Read the entire source document first.** Don't skim; the context around a fact
   matters. "Lives in City X since 2018" might be inferred from a tangential paragraph —
   but if it's not literal, it doesn't go in.
2. **For each candidate claim, write the line number + verbatim excerpt:**
   ```
   claim: "Full name: Jane Q. Example"
   source: profile.md L22
   verbatim: "- **Full name:** Jane Q. Example"
   ```
3. **If you can't cite a line, drop the claim.** "Doesn't appear in source" is a valid
   reason to omit. Don't substitute from memory or pattern-match from similar profiles.
4. **Watch for adjacent-context contamination.** A line saying a relative is a biologist
   doesn't license a claim about her residence. Copy the line, not the gist of the section.
5. **For complex concatenations** (e.g. "married to X, dating since date A, wedding date B),
   cite ALL source lines. Don't present a concatenation as a single fact — it's 3 facts glued.
6. **Before the user sees it, run a self-check**: for each claim, can the user
   `grep -nF "verbatim phrase" <source-file>` and find it? If not, fix.

---

## Why it matters

If a fabricated claim reaches a prompt or memory store and the user later asks about it,
the agent will either (a) confidently repeat the fabrication — worst case, a memory system
that "works" but corrupts over time — or (b) contradict itself when challenged (detectable
immediately; user loses trust). The cleanest fix is to never let fabricated claims in.

---

## Anti-patterns

| Anti-pattern | Concrete instance | Correction |
|---|---|---|
| **Plausible-sounding detail from a neighbouring paragraph** | "Sister lives in City X since 2018" — City X appeared nowhere in the KB; the year was invented because "country + sister + some year" felt right. | Procedure §1-2 — read full source, cite line, drop if no cite. |
| **Pattern-matching from similar profiles** | "Works at Company A" — another profile has Company A; the agent assumed this one did too. | Procedure §3 — drop if not in source. Cross-profile inference is forbidden for memory blocks. |
| **Conflating past and present entity** | "Runs Foo Ltd" — the KB mentions "Foo Marketing" as a 5-year project that ended. Not a current entity, not "Ltd". | Procedure §4 — copy the line, not the gist. Everything else is invented. |
| **Citing a record that doesn't exist yet** | "per M2 anchor record" — M2 hadn't run; the record wasn't in the memory store; the citation was aspirational. | A cited record must already exist. Otherwise write a TODO line in the proposal, not a citation. |
| **Owner permission as cover for invention** | "Owner approved M1 → I have license to fill in" — approval was for the *task* to run, not to invent facts about the user's family. | Permission to *act* is not permission to *fabricate*. Verify scope. |

---

## Format the proposal so the user can verify cheaply

Structure the block for review so the user can confirm 1 claim per line against the source:

```
### Claim N — <human label>
- Source: :<line_number>
- Verbatim excerpt (L<N>):
  <exact source content>
- What goes into the block:
  <the actual claim text, ideally == verbatim>
- Topic: <lens.facet.entity.aspect>
- Volatility: <permanent|situational|ephemeral>
```

The user does `grep -nF "<excerpt>" <source>` to verify each one. Cheap, fast, falsifiable.
If a single claim fails the grep, the whole block is rejected — no "the others are right,
keep them" fallback.

---

## When this does NOT apply

- **Generic/operational knowledge** ("the service listens on port 8700") — system facts
  inferable from code reading, not identity.
- **Code/config artefacts** — JSON, YAML, SQL are not "memory claims" about a person.
- **The agent's own self-description** — the agent is the source.
- **Repetition of facts the user has just stated** — quoting the current turn back is not fabrication.

The rule is specifically about **claims about a third party** that the agent constructs
from external documents: highest fabrication risk, highest cost of undetected fabrication.

## Related

- `nexus-discipline` §1-§2 — same-turn evidence and done-language discipline, complementary.
