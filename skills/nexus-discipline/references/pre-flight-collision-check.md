# Pre-Flight Collision Check — "Cria X em path Y" tasks

> Origem: sessão CRM 2026-07-01 (CALL 3 — `projectActivitiesToRows.ts`). Spec dizia "cria o ficheiro"; ficheiro já existia com API divergente e 4 consumidores activos. Documenta o protocolo para tasks estruturalmente "cria X".

## 1. O padrão

Quando a task é do tipo:

- *"Cria o ficheiro `path/to/X.ts`"*
- *"Cria a função `foo` em `path/to/Y.ts`"*
- *"Cria o módulo de projection"*
- *"Adiciona o helper `Z` em `path/W`"*
- *"Implementa `class Foo` no path `P`"*

…o instinto é ir directo a `write_file` ou `patch`. **Anti-pattern.** O ficheiro pode já existir (tracked, untracked, ou em working tree de uma sessão anterior que fechou sem commit), com API divergente do spec, e ser importado por N consumidores que partem silenciosamente se fizeres overwrite cego.

## 2. O anti-pattern

```bash
# ❌ INGÉNUO
task: "cria packages/db/src/utils/projectActivitiesToRows.ts"
→ write_file(path, "...")  # overwrite cego
→ backfill e ingest partem com ImportError ou regressão silenciosa
```

Custo: 1-2h de reversão + risco de regressão silenciosa em prod (ex.: `source_ref` re-key = todos os dedups existentes quebram).

## 3. O protocolo correcto — 4 tool calls paralelos ANTES do write_file

Quando a task é estruturalmente "cria X em path Y", o **primeiro bundle de tool calls nunca inclui write_file**. É sempre este bundle paralelo (mesma call, mesma response):

### Check 1 — Existe no git?

```bash
git -C <repo> status <path>
git -C <repo> log --oneline -n 5 -- <path>
```

**Detector de perigo:**
- `Untracked files: <path>` → ficheiro existe no working tree mas nunca foi commitado. **STOP** — provavelmente de uma sessão anterior que fechou em standby.
- Log mostra commits anteriores → ficheiro foi commitado e pode ter sido modificado depois.

### Check 2 — Quem o importa/consome?

```bash
grep -rln "<expected-export-name>" <repo> \
  --include=*.ts --include=*.tsx \
  --exclude-dir=node_modules --exclude-dir=dist
```

**Detector de perigo:**
- N>0 match → existem consumidores reais. Mudar a API quebra-os.
- Se a task é "cria pela primeira vez" mas `grep` encontra consumidores → **STOP**, há um "X" que o spec não vê.

### Check 3 — Qual o conteúdo actual?

```bash
read_file <path>     # se existir
```

Comparar 4 dimensões API:
1. **Type aliases** (nome + shape): spec diz `VendorLead`, código tem `LeadForProjection`?
2. **Return shape**: spec diz `{rows, skippedNoContact, ...}`, código retorna `ActivityRow[] + stats by ref`?
3. **Parameter signatures**: spec diz `sql: any`, código tem `sql: postgres.Sql`?
4. **Fórmulas determinísticas** (dedup, hashing, encoding): spec diz `md5(a+b+c+d[:120])`, código usa `md5(a+":"+b+":"+c+":"+d[:120])`?

**Qualquer divergência >cosmética dispara STOP.**

### Check 4 — Onde corre (consumidores)?

```bash
grep -n "from.*<expected-path>" <repo> -r --include=*.ts \
  --exclude-dir=node_modules --exclude-dir=dist
```

Confirmar que os matches do Check 2 **são realmente consumidores** (não docs ou comentários), e listar o impacto de overwrite.

## 4. STOP — matriz de opções (apresentar ao user)

Quando os 4 checks revelam divergência >cosmética, **NÃO** avançar. Emitir relatório estruturado:

```markdown
## Divergência spec ↔ implementação

| Aspecto | Spec (CALL 3) | Realidade (working tree) |
|---|---|---|
| Type alias | VendorLead | LeadForProjection |
| Return do projector | inline object | ActivityRow[] + stats by ref |
| Param signature | sql: any | sql: postgres.Sql |
| Dedup formula | md5(c+t+d+desc[:120]) | md5(c+":"+t+":"+d+":"+desc[:120]) |

**Consumidores activos:** 4 (1 backfill + 3 ingest)

## 3 opções, preciso de decisão:

(A) **Aceitar existente como DONE** — divergências são cosméticas ou load-bearing.
    Custo: 0. Risco: zero.

(B) **Cosmético só** — rename `LeadForProjection` → `VendorLead`, manténs resto.
    Custo: 5min. Risco: zero (todos os call sites actualizados em batch).

(C) **Spec estrito** — refactor projector para return inline + sql: any.
    Custo: 30min + 4 call sites a actualizar. Risco: médio (regressão visual na próxima vez que alguém usa `ActivityRow[]`).
```

## 5. Quando é que o pre-flight check NÃO se aplica?

- **Greenfield em repo recém-inicializado** (sem consumidores, sem sessões anteriores). Mas se tens dúvida → corre na mesma; custo é 3-4 tool calls.
- **Migration com ficheiro confirmado-órfão** (spec explicitamente diz "reescreve do zero, ignora o que está lá"). Mas nesse caso o user deve usar frase explícita do tipo *"overwrite intencional"* — não inferir.
- **Tasks puramente textuais/docs** (não-código): o bundle paralelo ainda ajuda (existe o ficheiro? está em conformidade com o template?), mas raramente dispara STOP porque docs não têm consumidores compilados.

## 6. Forma rápida de detectar o pattern

Re-lê a última mensagem do user. Procura por:
- "cria o ficheiro X" / "create file X"
- "cria a função Y em path Z"
- "implementa o módulo W"
- "adiciona o helper V"
- "extrai X para util partilhado" (especialmente — extraction implies existing source)

Se encontrares, o teu **próximo tool call é o bundle paralelo de 4 checks**, não `write_file`. Pula a tentação de fazer ambos em simultâneo.

## 7. Relação com DIV-GUARD

| Aspecto | DIV-GUARD | PRE-FLIGHT COLLISION |
|---|---|---|
| Origem | Gate explícito do user ("se X, PARA") | Estrutura da task ("cria X") |
| Detector | Trigger phrase no input do user | Trigger phrase no spec da task |
| Custo de perguntar | 30s | 30s (com bundle de 4 checks) |
| Custo de falhar | 1-2h reversão + regressão | 1-2h reversão + regressão |
| STOP output | Paths verificados + N leituras possíveis | Tabela spec-vs-realidade + 3 opções |
| Caso 2026-07-01 | Task A tenant_id scoping | CALL 3 projectActivitiesToRows |

São **complementares, não sobrepostos**. Uma task pode ter ambos os gates (ex.: *"cria X em path Y, MAS se já existir com API diferente, PARA"*). Se ambos disparam, ambos os outputs devem aparecer no relatório.

## 8. Caso de estudo #2 — CALL 2 (success path: pre-flight evitou trabalho fantasma)

**Sessão:** CALL 2, 2026-07-01, ~11:30Z (branch de feature).

**Spec do CEO:** *"Implementa contra a ISC-B"* — 4 tarefas: criar util, refactor backfill, patch ingest, 2 TODOs Task A.

**Tentação:** assumir que a CALL 1 tinha parado em standby (lema de um wrap-up anterior: *"agente ficou em standby"*) e implementar tudo de raiz.

**Bundle de pre-flight (4 tool calls paralelos):**
1. `git status` + `ls -la packages/db/src/utils/` → **ficheiro JÁ EXISTIA** (`projectActivitiesToRows.ts`, 7583 bytes, untracked), criado pela CALL 1.
2. `grep -rln "projectActivitiesToRows"` → **4 consumidores reais** (1 backfill + 3 ingest).
3. `read_file <util>` → **API completa e elegante**, dedup formula `md5(c+\":\"+t+\":\"+d+\":\"+desc[:120])` matched o backfill em prod.
4. `read_file packages/db/scripts/vendor-ingest.ts` → **já importa o util** nas linhas 60-64, já chama `projectActivitiesToRows` no dry-run (linha 430) e no COMMIT (linhas 688-738).

**Resultado:** zero linhas escritas por mim. CALL 1 já tinha implementado 100% da spec. A única coisa que CALL 2 teve de fazer foi **verificar** (tsc verde rc=0; smoke-test puro rc=0 confirmando idempotência + DST + bad-data defense) e adicionar os 2 TODOs da Task A.

**Custo poupado:** ~45min de implementação + risco de divergência com `source_ref` em prod (quebraria dedup de 29.113 rows).

**Lição dupla:**
- **Confirmar antes de escrever** — pre-flight não é só "STOP quando diverge", também é "SKIP quando já está feito".
- A tentação oposta (escrever por cima do que já existe) é igualmente dispendiosa — e acrescenta a vergonha de duplicar.

## 9. Smoke-test pattern para confirmar lógica após pre-flight (quando tsc não basta)

Quando o pre-flight descobre que a implementação JÁ EXISTE e está bem escrita, precisas **provar que funciona** sem os custos de:
- dry-run contra prod DB (`DATABASE_URL` remoto, latência de VPN)
- full NDJSON parse (15+ MB, timeout 120s+)
- commit em batch (reversão difícil)

**Pattern (≤ 30s, smoke-test puro):**

```bash
cat > /tmp/_validate_<util>.ts <<EOF
import { projectActivitiesToRows, parseVendorDate } from "<abs-path-to-util>";
const leads = [ /* 3-4 rows: bom, sem contact, null, com dados estranhos */ ];
const stats = { leadsProcessed:0, leadsSkippedNoContact:0, totalEntriesScanned:0, ... };
const rows = projectActivitiesToRows(leads as any, stats);
console.log(rows.length, stats);
// idempotência: 2ª run → mesmos source_refs
const refs1 = new Set(rows.map(r => r.source_ref));
const rows2 = projectActivitiesToRows(leads as any);
const refs2 = new Set(rows2.map(r => r.source_ref));
console.log("idempotent:", refs1.size === refs2.size);
// DST: parseVendorDate("29/06/2026, 16:41") → UTC 15:41 (WEST em Jun = -1h)
EOF
cd <repo>/packages/db && ./node_modules/.bin/tsx /tmp/_validate_<util>.ts
```

**Porquê isto satisfaz Rule 1 (live-probe, SKILL.md §1):**
- Check é **falível** — pode devolver "no" (counts errados).
- Exercita o caminho real (imports, runtime types, dedup formula).
- É **determinista** — mesmos inputs → mesmos source_refs.
- É **rápido** — 11s de runtime vs 4min+ de dry-run real.

**Quando NÃO usar:** quando o código tem side-effects inevitáveis (abre connections, escreve em disco) ou quando o input válido é impossível de sintetizar. Nestes casos, dry-run real é o único caminho.

## 10. Changelog

- 2026-07-01 — v2 (v2). +Caso de estudo #2 CALL 2 success path (pre-flight evitou trabalho fantasma). +Smoke-test pattern §9 para confirmar lógica sem dry-run prod.
- 2026-07-01 — v1 (v2). Caso de estudo: CALL 3 `projectActivitiesToRows.ts` (199 linhas já escritas, 4 consumidores activos, dedup formula em prod com 10.635 leads · 0 dup verificados).