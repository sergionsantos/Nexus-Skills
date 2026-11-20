# Dump Real Values on Smoke Tests

> **Pitfall class:** verification scope. **Lesson class:** reporting contract.

## The complaint (paraphrased from a real owner rejection)

> *"GATE NAO aceite — verifiquei os valores reais dos 5 samples e varios campos NAO aterram (o '5/5 PASS' e enganador: compila e corre, mas os dados estao vazios)."*

A report said `5/5 PASS` on 5 smoke-test samples for a new enrichment script. The numbers all looked right (5 refs scraped, 5 mappings printed, all fields with non-null values in the JSON). But when the owner inspected the actual values, three out of five samples had **garbage data** in fields the agent claimed were populated:

- `built_area` showed `1102` for a 110 m² apartment (regex bug concatenating "110" + "2" from the "m2" suffix).
- `parking_type` showed `"Elevator:"` for a warehouse (regex was grabbing the **next label** instead of the value).
- `parking_spaces` was `null` for all 5 because the test samples all happened to have "no parking" — and the agent didn't notice the regex was failing because there was no sample with a real parking value to validate against.

The agent had run the script. The TSC was green. The dump had printed all 5 mappings with no errors. **Every "verification" signal was green, and the data was still wrong.**

## Why "PASS" without values is a category error

`nexus-discipline` §1 Rule 1 (live-probe for user-facing artefacts) says: *marca passou SÓ com evidência de probe via tool*. That rule was technically followed — `pnpm exec tsx --env-file ...` ran and produced output. But the rule conflates "the script ran" with "the data is right". They're not the same.

The honesty rule (report only what you verified) says: *diz o que estás a fazer e porquê, e nunca reportes sucesso que não verificaste*. Also technically followed — the report said "5/5 PASS" and listed counts. But the report **omitted the actual values**, so the owner couldn't see the problem without re-running the script himself. The verification existed; the **visibility** of the verification didn't.

## The fix (preference, not patch)

When reporting on a smoke test / dry-run / fixture validation, the report contract is:

**For every field the user named (or that the ISC said should be populated), show the actual value, not just "non-null" or "passing".**

Concrete format for smoke-test reports (replace the existing "5/5 PASS" with this):

```
=== ref=125201034-83 (Apartamento, RENTAL) — 21/24 fields filled ===
  typology              = 'T3'             (✓ matches description)
  property_type         = 'Apartamento'    (✓ from Tipo do imóvel)
  rooms                 = 3
  total_divisoes        = 4
  bathrooms             = 2
  wcs                   = null            (legitimate — owner didn't fill)
  parking_spaces        = null            (legitimate — this ref has "Sem estacionamento")
  parking_type          = 'Sem estacionamento'
  area_m2               = 122              (✓ expected ~110m² from description)
  area_construida_bruta = 110              (✓ parsed from "110 m²" not "1102")
  agency_name           = 'Acme Realty'
  agent_name            = 'Jane Doe'
  agent_email           = 'jane@example.com'
  agent_phone           = '+000****0000'
  agent_mls             = 'MLS-0000'
  listing_status        = 'Proposta Aceite'
  transaction_type      = 'RENTAL'
  price                 = 1400
  concelho              = 'Sintra'
  freguesia             = 'Massamá e Monte Abraão'  (multi-word "e" handled)
  distrito              = 'Lisboa'
  build_year            = 1988
  energy_certificate    = 'C'
  description           = 'Apartamento T3 para arrendamento...'
  tenant_id             = null            (legitimate — Org A ≠ Org B)
  agent_cross_check     = 'no-mls'
```

Three rules for the dump:
1. **Show the value**, even if it's null. Don't say "PASS" or "—" — say `null` (and tag as `legitimate` if you verified why).
2. **Tag expected vs observed.** If you can cross-check against another source (e.g. the description text in this case, or a second source), do it inline: `(✓ matches description)`. The ✓ mark is a quick visual signal that the data was sanity-checked, not just non-null.
3. **Distinguish bugs from missing data.** A `null` for a field the page didn't render is different from a `null` because the regex failed. The dump above says `legitimate — owner didn't fill` for `wcs` and `legitimate — this ref has "Sem estacionamento"` for `parking_spaces`. Without that annotation, the owner can't tell whether the scraper is broken or the data isn't there.

## Where to apply (anywhere live-probe and honest reporting apply)

- **Smoke tests** (N samples, varied inputs) — always show the dump. PASS/FAIL is a header; values are the substance.
- **Dry-run output** (ingest previews, migration previews) — show the first 3-5 mapped rows verbatim, then counts. The user wants to read the data, not trust "ok 1167 rows".
- **Code review findings** — when reporting "this field is broken", paste the **actual** value that came out, not the regex/test that "should" work. "The regex returns null" without showing the input is half a finding.
- **Bug reports** — always pair the claim with the observed value. "parking_type is wrong" → "parking_type is 'Elevador:' for a listing whose value should be empty (Armazém 124151233-1). The regex lookahead was matching the next label."

## Anti-patterns to delete from muscle memory

| Anti-pattern | Replacement |
|---|---|
| "5/5 PASS" | "5/5 scraped. Dump: [full field values per sample]" |
| "All fields populated" | "[field-by-field dump with nulls flagged as legitimate]" |
| "Verified with `pnpm exec tsx`" | "Verified: `pnpm exec tsx` → rc=0, output=[paste first 5-10 lines of stdout]" |
| "Looks correct" (no evidence) | "Cross-check: [field X] = [value], matches [external source]" |
| "Happy-path test" (only the success case) | Include at least 1-2 samples with **expected non-happy values** (null fields, edge cases) so the regex failure modes get exercised |

## Connection to existing rules

- **Rule 1 (live-probe, SKILL.md §1)** — strengthens: the "evidência de tool" requirement is met by **showing the tool's output in the report**, not by saying "I ran the tool".
- **Honest reporting (SKILL.md §2)** — adds: the "Taxonomia de claims em 4 estados" must include a **fifth dimension**: is the value visible to the user, or just known to the agent? A claim is only as good as the user's ability to verify it.
- **Self-check before ending the turn (`effort-and-process.md` §6)** — adds to the self-check: *"Did I show actual values for the fields the user cared about, or did I summarize as 'ok'?"*

## Origin

Seen in a smoke test before a `--commit` gate on a data-ingest script. The agent reported `5/5 PASS` on 5 varied samples; the owner inspected the actual values and rejected the gate because three of the five had hidden bugs. The fix was to add a dump-real-values step to the smoke-test report contract, and to add **edge-case samples** to the smoke set (a record in an unusual state, one with the optional field populated, one of a different type) so the regex failure modes got exercised by the smoke test rather than surfacing in the gate review.

## Cross-references

- `nexus-discipline` §1 (verification doctrine) — the parent rule.
- `nexus-discipline` §2 (done-language) — the reporting rule.
