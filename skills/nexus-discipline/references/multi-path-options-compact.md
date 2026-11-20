# Multi-path options → compact output, not narrative sections

> **Pitfall:** when offering 2-3 paths (e.g. "Opção A / B / C") the natural instinct is to write 4-5 sections per option (Acção / Quando escolher / Custo / Risco). The owner finds this **opaque** and asks for "forma simples". Compact bullets win.
>
> **Captured:** 2026-07-08, M0.4 `plan/feature-x/` session. User said: *"Não está claro quais são as opções A, B e C. Podes, por favor, apresentá-las de forma simples?"* **Skill:** `nexus-discipline` (reflexos extra).

## The wrong way (verbose)

```markdown
### Opção A — Aceitar como está

**Acção:** arquivar esta re-run em `review/grade-loop-2026-07-08/` como evidência
de que o gate continua a passar. Não correr grader [R], não despachar Opus.

**Custo:** 0 wall-clock adicional, 0 tokens adicionais.

**Output adicional:** nada.

**Quando escolher:** o teu pedido foi "aplica o loop" e o resultado é que ele
já estava aplicado (Opus, há 18h). Não inventar trabalho para justificar o loop.

**Risco:** zero (estamos a confirmar algo já confirmado).
```

4 sections × ~3 lines each = ~15 lines for one option. For 3 options = **45+ lines of prose** that the owner has to scan to find the actual decision.

## The right way (compact)

```markdown
**A — Aceitar como está. Custo: 0.** O loop já correu há 18h (Opus) e passou. Esta
re-run confirma o mesmo. Arquivamos e seguimos.

**B — 1 ronda do Sonnet. Custo: ~10 min + alguns tokens.** Um agente diferente
do autor lê os ficheiros e dá uma vista de olhos fresca. Pode confirmar ou
encontrar coisas novas.

**C — Auditoria completa nova com Opus. Custo: ~30-60 min + tokens caros.** Re-faz
a auditoria pesada do zero. Só vale a pena se houver suspeita de erro ou se algo
mudou entretanto.

**A minha recomendação é A** — porque o plano já foi auditado e não mudou.
```

3 lines per option + 1 line for the recommendation. **3-4× more dense**, same information, faster to scan, easier to reply to.

## The 5-line rule

When offering ≤3 options:

- **1 line per option** = action + cost (1 phrase)
- **1 line per option** = when it makes sense (optional, fold into the same line)
- **1 line total** = recommendation with reasoning ("recomendo X porque Y")

Total: **3-5 lines** for 3 options. Hard cap.

When offering 4+ options, you're probably in the wrong format — you should be deciding, not offering 4+ paths.

## When the verbose format is correct (exception)

- **Tables** of trade-offs with columns (option | cost | risk | reversible?) are still OK — they're scannable.
- **Decision matrices** for complex multi-axis choices (option × constraint) are still OK.
- **Documentation of why each was rejected** is OK AFTER the decision, not before.

The anti-pattern is **prose sections for ≤3 mutually-exclusive paths**.

## Cross-ref to the user's preference

- This is consistent with the owner preference for terse cadence: "1 marco/milestone, não narração contínua; açucar (listas de bullets verbose) reduz utilidade".
- A style skill (if you have one) explicitly forbids "verbose narrative for routine reports".

## What about the `clarify` tool?

`clarify` with `choices` array is the **structural** way to offer options compactly — the UI renders them as clickable rows. Use it when:

- Options are mutually exclusive AND
- The owner needs to pick exactly one AND
- You're OK waiting for an answer (clarify is blocking)

Use prose-bullets (the pattern above) when:

- You want to offer options + your recommendation in the same turn AND
- The owner might pick, propose their own, or counter ("neither, here's another")

## Diagnostic

If the user says any of:

- "podes explicar de forma simples"
- "não está claro"
- "sumariza em 1 linha"
- "TL;DR please"
- "dá-me só a recomendação"

You're in the verbose camp. Strip to the 5-line rule.
