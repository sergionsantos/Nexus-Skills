# GATE Calibration + Runtime Probe Patterns

Trio de patterns que emergiram da sessão projecto X M11–M13 (2026-07-04).

---

## R1 — GATE Calibration per Reversibility

### O anti-pattern original

Um plano executava "PÁRA → espera 'vai'" por defeito, incluindo para steps totalmente read-only. Resultado: o owner teve de dizer "vai" 3× consecutivas em M11.1 (detectar dups → analisar causa → rerank) sem nada de risco, apenas porque o plano assumia "default = PÁRA".

User explícito: *"pq tenho de dizer 3 vezes vai? executa até ao fim"*.

### Calibração correcta (3 níveis)

```ts
type StepRisk =
  | "read-only"          // psql SELECT, grep, cat — sem side-effects
  | "mut-reversible"     // UPDATE/INSERT com PK, dry-run, cache invalidate
  | "mut-irreversible"   // DROP, ALTER COLUMN, secrets, posts externos
```

**Aplicação por step do plano:**

```text
RULE FOR EACH STEP IN PLAN.MD:
  descobre risk class:
    sql/query → read-only            → executa, dump depois
    UPDATE/INSERT/DRY_RUN → mut-rev  → executa, dump depois
    DROP / ALTER / secrets → ir-rev  → PÁRA + mostra diff + GATE
  average: 1 PÁRA por step irreversible, 0 PÁRAs para o resto
```

### Decisão borderline: sandbox-first

Se não tens a certeza se Y é reversível, **executa em sandbox primeiro**:

```bash
DRY_RUN=true npx tsx scripts/migrate.ts   # só escreve plano JSON, não aplica
DRY_RUN=false npx tsx scripts/migrate.ts  # depois de Dump + GATE
```

Output da DRY_RUN é o teu "diff" para o gate humano. Custo: 1 extra run.

### Custo desta calibração

- **Calibrado bem**: ~0 round-trips para 90% dos steps.
- **Calibrado mal (PÁRA em tudo)**: N round-trips fricção; user perde confiança no executor.
- **Calibrado mal (nunca PÁRA)**: max 1 round-trip de diagnose/rollback (geralmente reversível).

Equívoco **"sempre PÁRA"** tão mau quanto **"nunca PÁRA"**.

### Marker no plano (template)

```markdown
### Step X.Y.Z — [ação]
- **Files:** [path]
- **Risk class:** [read-only | mut-reversible | mut-irreversible]
- **If verify fails:** ...
- **Done when:** ...
```

Calibração vira-se explícita no plano. Executor lê, aplica o nível certo.

---

## R2 — Runtime Probe CWD inside repo

### O anti-pattern original

```bash
# Em verify script (cwd=app/):
cat > /tmp/runtime-bulk.mjs <<'EOF'
import { createClient } from "@supabase/supabase-js";
EOF
node /tmp/runtime-bulk.mjs
# → Error [ERR_MODULE_NOT_FOUND]
#   Cannot find package '@supabase/supabase-js'
#   imported from /private/tmp/runtime-bulk.mjs
```

**Diagnóstico:** Node resolve módulos relativos ao ficheiro. `/tmp/` não tem `node_modules` vizinhos, então `@supabase/supabase-js` é invisível.

### Fix correcto

```bash
# Em verify script (cwd=app/):
APP="/abs/path/to/app"
cat > "$APP/.runtime-bulk.mjs" <<EOF
import { createClient } from "@supabase/supabase-js";
EOF
node "$APP/.runtime-bulk.mjs"
# → funciona — o ficheiro está em app/, node encontra node_modules/
# depois cleanup:
rm -f "$APP/.runtime-bulk.mjs"
```

### Variações

| Caso | Path | Notes |
|---|---|---|
| Probe one-shot em projeto pnpm | `$APP/.probe-XXX.mjs` (prefíxo `_` ou `.`) | `_*.mjs` é convenção lint-friendly |
| Probe puro (sem imports) | `/tmp/probe.mjs` | OK se `node:` só |
| tsx em vez de node | `npx tsx "$APP/.probe.tsx"` | Mesmo princípio — cwd em app/ |

### Caveat para tsx

`tsx` herda o cwd, mas resolve via `tsconfig.json` paths no project root. Probe `.tsx` em `$APP/` funciona se `tsconfig.json` tiver o probe coberto em `include` (default: `src/**/*.tsx`). Em `scripts/` separado, `tsconfig.scripts.json` é necessário (M0.10 pitfall já documentado).

---

## R3 — Cold-Eyes Review Fallback (Rule 0 modo fallback)

### Quando usar

`delegate_task` não está configurado (`.claude/` empty, sem ACP CLI instalado, sem modelo alternativo). Rule 0 manda revisão independente, mas não há lente externa disponível.

### Procedimento cold-eyes (10 passos, ~10 min)

```
1. NÃO relembres o teu próprio raciocínio de execução.
   Lê só: spec original + diff final + estado disco.

2. Cold-read TODAS as funções tocadas (read_file beginning-to-end).
   Ato de "ver sem saber porque foi escrito" apanha dead vars,
   comments stale, edge cases quebrados.

3. Para cada finding, classifica ANTES de fixar:
   BLOCKER  → aplica fix + re-verify
   HIGH     → aplica fix
   MEDIUM   → registar em backlog
   FALSE-POSITIVE → descarta com justificação

4. Cite ID (F-NN ou nome da lens que descobriu).

5. Cold-eyes não vê 100% do que subagente vê. Marque findings com
   "cold-eyes" para distinguir de review real quando passar a
   existir subagente.

6. Caveat honesto: mesmo modelo, mesmos blind spots. Fallback,
   não substituto de subagente real.

7. Exemplo real (M11 cold-eyes, 2026-07-04):
   - F-MR1 (HIGH): comment claiming `_fi_key` usage — code does NOT use _fi_key
   - F-MR2 (MEDIUM): unused vars `v_max_len`, `v_last_char`
   - F-MR4 (FALSE-POSITIVE): "trigger devolve 'a0' literal" — query exclui 'a0', gera 'aGa'
   Apanhou 2 reais, falsificou 1. Tempo: 8 min.

8. Resumo final: Blockers+HIGH fixed + veredito sem hedging.
   Ex: "M11 cold-eyes review applied: 1 BLOCKER (F-MR8.2 Promise.all→allSettled),
       5 MEDIUM backlogs. Done."

9. Se o spec existe (nexus-plan-spec), mantém a estrutura D#
   numbering + cita spec no review.

10. Após cold-eyes com fixes aplicados, re-corre verify fresh
    (não réutilises o nome do script — sistema detecta como no-fresh).
```

### Cold-eyes vs review real

| Aspecto | Cold-eyes | Subagente `verifier` |
|---|---|---|
| Mesmo modelo? | Sim (mesmo) | Possivelmente diferente |
| Custo? | ~10 min inline | ~5-15 min delegação |
| Cobre? | Padrões do próprio treino | Padrões + lente ortogonal |
| Quando? | Default se não há subagente | Quando há subagente + spec claro |

---

## Sinais cruzados (quando esta skill combina com outras)

- **falsificável verify + R3 cold-eyes**: negativos control devem ser derivados de findings cold-eyes que imagina. Se não consegue imaginar um input mau para um check, o check é hollow (Rule 0, `SKILL.md` §1).

- **env sanity + R2 CWD**: o `export PATH=...` backstop ajuda scripts em qualquer cwd. R2 complementa para `node_modules` resolution.

- **threshold percentuais + R1 reversibilidade**: gate 5% em N=17 é trivial noise. Use **combinado** — read-only queries executam sempre (R1); queries de threshold PÁRAM-SE E interpretam-se (Rule 1, `SKILL.md` §1); só mutações irreversíveis PÁRAM COM HARD gate (R1).
