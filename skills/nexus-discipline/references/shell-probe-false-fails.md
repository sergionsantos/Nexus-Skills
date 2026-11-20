# Shell + DB + Cron Probe False-Fails — 16 padrões que parecem system failures mas são bugs do probe

> **Princípio (pitfall 2026-07-02, M0.9-14 + M4 + M5 + M6 executor):** um probe que reporta "fail" ou "pass wrong" pode estar errado, não o sistema. Antes de reportar "the planner is broken", diagnostica se o probe é válido. **16 padrões observados em 2026-07-02; custo total sem este diagnóstico: 5+ round-trips do user a pedir "verification status: unverified"**. Padrões 1-5 são shell-level (M0.9-14); padrões 6-11 são psql/PostgREST DB-level (M4-M5); padrões 12-16 são Postgres + cron motor SQL (M6).

---

## PARTE I — 5 padrões shell-level (pitfall 2026-07-02, M0.9-14)

### 1. `sha256sum` vs `shasum -a 256` (macOS)

**Sintoma:** o probe `sha256sum file1 file2 ...` devolve 0 linhas ou erro "command not found".

**Causa:** o GNU coreutils `sha256sum` **não vem por defeito em macOS** (que tem BSD userland). O macOS tem `shasum -a 256` (BSD).

**Detecção:**
```bash
which sha256sum    # vazio em macOS
which shasum       # presente
```

**Workaround em script portable:**
```bash
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum file1 file2 ...
else
  shasum -a 256 file1 file2 ...
fi
```

**Lição**: ao escrever scripts de verify cross-platform, testa o binário antes de assumir. Ou usa Python (`hashlib.sha256()`) que é portable.

---

### 2. `psql` query com enum reject devolve string vazia, não erro

**Sintoma:** `psql -tAc "select count(*) from foo where role='hacker'"` devolve string vazia `""` em vez de `0` ou um erro.

**Causa:** Postgres **aborta a query** quando o valor viola o CHECK constraint ou não é membro do enum. O `-tAc` suprime o erro visível no output mas **não propaga exit code** se `-q` não for passado.

**Workaround:** capturar stderr separadamente, ou tratar empty como 0/empty indistintamente:
```bash
NEG=$(psql -tAc "..." 2>/dev/null | tr -d ' \n')
[[ -z "$NEG" || "$NEG" == "0" ]] && ok "N: empty/0" || bad "N: $NEG"
```

**Lição**: `psql` em modo `-A -t -c` é silencioso. Probe que depende de valor exacto 0 precisa de tratar empty como "0 ou erro silencioso", não como 0 garantido.

---

### 3. CORS preflight com Origin errada: server omite ACAO header (correct, mas confunde probe)

**Sintoma:** probe `curl -X OPTIONS -H "Origin: http://localhost:3002" ...` devolve HTTP 200, mas **sem `Access-Control-Allow-Origin` header**.

**Causa:** Kong 2.8 CORS plugin **omite ACAO quando o Origin não está na allowlist** — em vez de pôr o Origin (que seria CORS misconfig) ou devolver 403.

**Lição**: CORS allowlist é a fonte de verdade, não o que tu **achas** que deve ser. Verifica `kong.yml` antes do probe.

---

### 4. `&` em `terminal()` em vez de `background=true` (executor backend)

**Sintoma:** comando tipo `bash script.sh &` é rejeitado com `"Foreground command uses '&' backgrounding. Use terminal(background=true) for long-lived processes"`.

**Workaround:** usa `background=true`:
```python
terminal(command="bash script.sh", timeout=60)
# background (long-lived)
terminal(command="bash script.sh", background=true, notify_on_complete=false, timeout=600)
```

---

### 5. CWD não persiste entre `terminal()` calls

**Sintoma:** primeiro `terminal(command="cd /abs/path/proj/app && pnpm dev")` corre ok; segundo recebe connection refused.

**Causa:** o harness **reseta o cwd entre chamadas**. `cd` dentro de um command line não persiste.

**Workaround 1** — prefixar o cwd em cada call.
**Workaround 2** — `workdir` parameter.
**Workaround 3** — paths absolutos em tudo.

**Lição (`nexus-discipline`):** **prefere paths absolutos a `cd`**.

---

## Resumo (Parte I — shell-level)

| # | Padrão | Antes do probe |
|---|---|---|
| 1 | sha256sum vs shasum | `which sha256sum shasum` |
| 2 | psql enum reject | Capturar stderr; empty = 0/erro |
| 3 | CORS preflight com Origin errada | Verificar kong.yml allowlist |
| 4 | `&` em terminal() | Usar `background=true` |
| 5 | CWD não persiste | Paths absolutos |

---

## PARTE II — 6 padrões psql/PostgREST (pitfall 2026-07-02, M4-M5 projecto X)

> **Princípio:** os 5 padrões acima são shell-level. M4-M5 descobriu uma classe diferente — DB-level — onde `psql` ou PostgREST devolvem valores que o probe interpreta incorrectamente. Todos se manifestaram como "FAIL" quando na verdade o sistema estava correcto.

### 6. `psql -tAc` strippa espaços do valor (UUIDs, strings, titles)

**Sintoma:** comparar `uuidgen` (UPPERCASE: `CC0C2460-...`) com `psql -tAc "select id from ..."` (lowercase: `cc0c2460-...`) → comparação falha mesmo quando IDs batem.

**Workaround — normalize antes de comparar:**
```bash
PROJ_ID_LC=$(echo "$PROJ_ID" | tr 'A-Z' 'a-z')
[[ "$PROJ_ID_LC" == "$DB_PROJ_LC" ]] && ok
```

**Alternativa — forçar lowercase no `uuidgen`:**
```bash
PROJ_ID=$(uuidgen | tr 'A-Z' 'a-z')
```

---

### 7. `psql -tAc "begin; set; select; commit;"` devolve multi-linha

**Sintoma:**
```bash
N=$(psql ... -tAc "begin; set local request.jwt.claim.sub='...'; select count(*) from projects; commit;")
# BEGIN\nSET\n0\nCOMMIT
```

**Workaround — extrair só linhas numéricas:**
```bash
N=$(psql ... -tAc "..." 2>&1 | grep -E '^[0-9]+$' | head -1)
[[ "$N" == "0" ]] && ok
```

---

### 8. `tr -d ' '` apaga `t`/`f` boolean output

**Sintoma:** `tr -d ' '` apaga **todos** os espaços **e** os chars `t`/`f` que estiverem no meio.

**Workaround — preservar newlines, trimar com awk:**
```bash
T=$(psql ... -tAc "select trashed_at is not null from ..." | grep -E '^[tf]$' | head -1)
[[ "$T" == "t" ]] && ok
```

---

### 9. `psql` como superuser bypass RLS

**Sintoma:**
```bash
psql ... -c "set local request.jwt.claim.sub = '00000000-...-0ff'; select count(*) from projects;"
# devolve 1 — RLS parece não funcionar!
```

**Causa:** o user `postgres` (superuser) bypass RLS. `set role authenticated` é necessário para testar o filtro RLS real.

**Workaround:**
```bash
psql ... -c "set role authenticated; begin; set local request.jwt.claim.sub = '00000000-...-0ff'; select count(*) from projects; rollback;"
```

---

### 10. `psql -t -c` adiciona leading space

**Sintoma:** `psql -t -c "select name from foo where id=1"` devolve `" ActualName"` (com space à esquerda).

**Workaround — trim com awk:**
```bash
T=$(psql -t -c "select name from foo where id=1" | head -3 | grep -v '^$' | head -1 | awk '{$1=$1};1')
```

---

### 11. `set -u` + var name quebrado por zero-width char

**Sintoma:**
```
/tmp/script.sh: line 99: BEFORE_TOTAL​: unbound variable
```

**Causa:** o var name tem **zero-width character** (`U+200B`) colado no fim.

**Workaround:** re-escrever a linha do var assignment sem copy-paste.

---

## Resumo combinado (11 padrões)

| # | Domínio | Padrão | Antes do probe |
|---|---|---|---|
| 1 | shell | sha256sum vs shasum | `which sha256sum shasum` |
| 2 | psql | enum reject devolve "" | Capturar stderr |
| 3 | shell | CORS preflight com Origin errada | Verificar kong.yml allowlist |
| 4 | shell | `&` em terminal() | Usar `background=true` |
| 5 | shell | CWD não persiste | Paths absolutos |
| 6 | psql | UUID case mismatch | Normalizar lowercase |
| 7 | psql | `begin;set;select;commit;` multi-linha | `grep -E '^[0-9]+$'` |
| 8 | psql | `tr -d ' \\t'` apaga `t`/`f` boolean | Filtrar `^[tf]$` |
| 9 | psql | postgres bypass RLS | `set role authenticated` |
| 10 | psql | `psql -t -c` adiciona leading space | `awk '{$1=$1};1'` |
| 11 | shell | zero-width char em var name | `cat -A`, re-type |

---

## PARTE III — 5 padrões Postgres + cron motor SQL (pitfall 2026-07-02, M6 projecto X)

> **Princípio:** M6 partilhou o DB com M4 (ambos usam `pg_cron`). Os padrões abaixo são **Postgres-specific + cron-infra-related**, distintos dos 5 shell + 6 psql da PARTE I/II. Característica comum: o probe reporta "FAIL" mas o sistema — incluindo o controlo de concorrência partilhado — está correcto. A armadilha é **interpretar** valores correctos como errados porque não se conhece o invariante do domínio.

### 12. `string_agg(..., ORDER BY ...)` falha em `psql -tAc` (unaligned mode)

**Sintoma:**
```bash
ARR=$(psql ... -tAc "select string_agg(jobname, ',' order by jobname) from cron.job")
ERROR:  column "job.jobname" must appear in the GROUP BY clause or be used in an aggregate function
```

**Causa:** `string_agg` aceita `ORDER BY` directamente, **mas** dentro de um aggregate em modo `-A` (unaligned), o parser pode interpretar mal.

**Workaround — usar `array_agg` em vez de `string_agg`:**
```bash
ARR=$(psql ... -P pager=off -tAc "select array_agg(jobname order by jobname)::text from cron.job")
# {"app_schema_cycles","app_schema_purge_trash"}
```

**Lição:** `array_agg(... ORDER BY ...)::-text` é a versão **canónica e estável** em psql `-tAc`. Prefere-a a `string_agg(... ORDER BY ...)`.

---

### 13. `psql -tAc` strippa espaços em saídas de `array_agg`/`string_agg` (cron schedules, strings com espaço)

**Sintoma:**
```bash
SCHED=$(psql ... -tAc "select array_agg(schedule order by jobname)::text from cron.job")
# {"15****","0 3 * * *"}     ← sem espaços nos elementos!
echo "$SCHED" | grep -q "15 * * * *"   # FALHA
```

**Causa:** o mode `-A` (unaligned) do psql strippa whitespace **de cada elemento do array**. O **array delimiters** (`{`, `}`, `,`) sobrevivem; **só o whitespace dentro dos elementos** desaparece.

**Workaround — `psql -t -c` em vez de `-tAc`:**
```bash
SCHED=$(psql ... -t -c "select array_agg(schedule order by jobname)::text from cron.job")
# {"15 * * * *","0 3 * * *"}
```

**Caveat do workaround:** `psql -t` adiciona leading space nos elements (ver #10). Combine com `awk '{$1=$1};1'`.

**Lição:** sempre que o output de `psql` for uma string **com espaços** (cron schedules, names com primeiro/nome, message bodies), **não** uses `-tAc`. A combinação `(psql -t -c) + awk '{$1=$1};1'` preserva espaços e trima leading/trailing. `-tAc` é só para **valores atómicos** (UUID, integer, boolean `t`/`f`).

---

### 14. `FK name no DB ≠ FK name esperado pelo probe` (constraint naming)

**Sintoma:** probe procura `issues_cycle_id_fkey`, DB tem `fk_issues_cycle`:
```bash
FK=$(psql ... -tAc "select conname from pg_constraint where conname='issues_cycle_id_fkey'")
# vazio
```

**Causa:** o nome do FK constraint **não segue convenção fixa** — depende do autor da migration. Postgres auto-gera nomes `<table>_<column>_fkey`, mas migrations customizadas usam prefixos (`fk_<table>_<column>`). O probe que assume uma convenção falha quando a migration usa outra.

**Workaround — procurar por definição, não por nome:**
```bash
FK=$(psql ... -tAc "select conname from pg_constraint where contype='f' and conrelid='app_schema.issues'::regclass and pg_get_constraintdef(oid) like '%cycle_id%'")
```

**Lição:** **`pg_constraint.conname` é variável**. Probes devem procurar pela **definição** (`pg_get_constraintdef()`) ou pelo **column** (`conkey`), nunca pelo nome. O `_migrations` ledger dá-nos o nome canónico da migration — mas o nome do constraint **dentro** da migration é determinado na altura da criação, não do plano.

---

### 15. `pg_extension` vs `pg_available_extensions` (red-team: extension REAL vs AVAILABLE) — pitfall confirmado

**Sintoma:** probe usa `pg_available_extensions` para "verificar se pg_cron está disponível":
```bash
psql ... -tAc "select extname from pg_available_extensions where extname='pg_cron'"
# 'pg_cron' (sim, disponível)
```
Mas:
```bash
psql ... -tAc "select extname from pg_extension where extname='pg_cron'"
# (vazio — não está LOADED)
```

**Causa:** `pg_available_extensions` lista **todas as extensions** que o Postgres supporta carregar. `pg_extension` lista **as que foram CREATE EXTENSION** — i.e. estão loaded neste DB. Para verificar se um **job de cron** pode correr, precisas de **`pg_extension`** (loaded), não `pg_available_extensions` (capability).

**Workaround canónico (lição red-team M6 — usar SEMPRE `pg_extension` em guards):**
```bash
# Verificar REAL loading (correcção)
psql ... -tAc "select extname, extversion from pg_extension where extname='pg_cron'"
# → 'pg_cron|1.6.4' (loaded) ou vazio (not loaded → guard degrada sem abortar)

# Só usar pg_available_extensions para "vale a pena tentar CREATE?"
psql ... -tAc "select name from pg_available_extensions where name='pg_cron'"
```

**Lição (red-team):** Em migrations com guards de **infra partilhada** (qualquer extension, qualquer cron, qualquer role com BYPASSRLS), usar `pg_extension` para detectar estado actual. `pg_available_extensions` **não** diz se está loaded — só se está built-in. **Não confundir** — uma extension pode aparecer em `pg_available_extensions` e nunca ter sido loaded (e.g. shared_preload_libraries vazio).

---

### 16. `cron.schedule` invariant: count FUTURE cycles, não total

**Sintoma:**
```bash
# D72: ensure_cycles mantém upcoming_cycle_count+1 cycles with ends_at > now()
FUTURE=$(psql ... -tAc "select count(*) from app_schema.cycles where team_id='X' and ends_at > now()")
# 3 (correct: upcoming=2 + active=1)
[[ "$FUTURE" == "3" ]] && ok   # OK

# Mas probe com filtro total:
TOTAL=$(psql ... -tAc "select count(*) from app_schema.cycles where team_id='X'")
# 4 (3 future + 1 ended deixado por rollover)
[[ "$TOTAL" == "3" ]] && ok   # FALHA — D72 não apaga ended cycles!
```

**Causa:** D72 `run_cycle_maintenance()` move **issues** de cycle ended → next cycle, mas **não apaga cycles ended** (comportamento intencional: cycles antigos ficam como audit trail). Logo, `count(*) from cycles where team_id=X` pode ser `<= upcoming+1+ended_count`.

**Workaround — invariante explícito:**
```bash
FUTURE=$(psql ... -tAc "select count(*) from cycles where team_id='X' and ends_at > now() at time zone 'UTC'")
[[ "$FUTURE" == "$EXPECTED" ]] && ok "F: invariant holds ($FUTURE future cycles)"
# NÃO falla se ended_count != 0 — esse é expected behaviour
```

**Lição:** Ao verificar invariantes de geração de cron (`ensure_cycles`, `cron.schedule` no M6, etc.), **sempre** filtra por **estado actual** (`ends_at > now()`), não por **count total** (`count(*)`). Cycles rolled-over ainda existem fisicamente — é feature, não bug.

---

## Resumo combinado (16 padrões: 5 shell + 6 psql/PostgREST + 5 Postgres+cron)

| # | Domínio | Padrão | Antes do probe |
|---|---|---|---|
| 1 | shell | sha256sum vs shasum | `which sha256sum shasum` |
| 2 | psql | enum reject devolve "" (não erro) | Capturar stderr; tratar empty como 0/erro |
| 3 | shell | CORS preflight com Origin errada | Verificar kong.yml allowlist |
| 4 | shell | `&` em terminal() | Usar `background=true` |
| 5 | shell | CWD não persiste | Paths absolutos em tudo |
| 6 | psql | UUID case mismatch | Normalizar ambos para lowercase antes de comparar |
| 7 | psql | `begin;set;select;commit;` multi-linha | `grep -E '^[0-9]+$'` antes de comparar |
| 8 | psql | `tr -d ' \\t'` apaga `t`/`f` boolean | Filtrar `^[tf]$` ou extrair última coluna |
| 9 | psql | postgres bypass RLS | `set role authenticated` antes de test |
| 10 | psql | `psql -t -c` adiciona leading space em strings | `awk '{$1=$1};1'` no final |
| 11 | shell | zero-width char em var name | `cat -A` antes de correr, re-type var name |
| **12** | **psql** | **`string_agg(... ORDER BY ...)` falha em `-tAc`** | **Usar `array_agg(... ORDER BY ...)::text`** |
| **13** | **psql** | **`-tAc` strippa espaços em `array_agg`/`string_agg` outputs** | **Usar `-t -c` + `awk '{$1=$1};1'`** |
| **14** | **psql** | **FK name no DB ≠ FK name esperado pelo probe** | **Procurar por `pg_get_constraintdef()` ou `conkey`, nunca `conname`** |
| **15** | **psql** | **`pg_extension` vs `pg_available_extensions`** | **`pg_extension` para runtime (loaded); `pg_available_extensions` só para "try CREATE?"** |
| **16** | **psql** | **Invariant `count FUTURE not total`** | **Filtrar por `ends_at > now()`, nunca `count(*)` para invariant checks de generators** |

**Lição meta (4ª, extensão da 3ª):** quando o probe reporta "FAIL" no DB, **categorizar em 4 buckets**:

1. **Probe-level false-fail** (1-16 acima) → corrigir o probe. Validar com negative control que o probe é capaz de falhar (P1 playbook).
2. **Schema/cache shared infra** → restart ou `NOTIFY pgrst, 'reload schema'` (PostgREST). Documentar como workaround conhecido (M4 + M6 lições).
3. **RLS/auth real** → `set role authenticated` + reverificar. Se ainda falha, é real (P4 playbook).
4. **Invariant mismatch** → o probe assume um invariant errado. Filtrar pela propriedade actual (não pelo count total).

Para diagnosticar qual: **roda o probe com `bash -x script.sh`** para ver exactamente onde o output desvia. Se `count(*) = 4` mas esperava 3 → invariante errado (#16). Se `count(*) = 0` mas query foi `where team_id='X'` → RLS bypass (#9) ou cache (#2 da PARTE II).

**Lição meta (5ª, sobre cron motor SQL partilhado):**

Em DB partilhado (M4 + M6 ambos com pg_cron), **4 armadilhas coexistem** que probes single-purpose não apanham:

a. **Naming collisions** entre jobs — usar prefixo escopado (`app_schema_*`, não `nexus_*` ou `other_*`).
b. **`cron.unschedule(jobid)` antes de `cron.schedule`** em migrations para **idempotência** — se a migration corre 2× (dev ou CI), não duplica jobs.
c. **Schedule string preservation** — `cron.schedule('name', '15 * * * *', ...)` aceita formato standard; o output display pode strippar espaços (padrão #13).
d. **Timezone-awareness** — `now()` no server pode diferir de `now() at time zone 'UTC'`; o D72 invariant compara **UTC** consistency. Sempre filtra com timezone explícito.

---

## Caso de estudo (sessão 2026-07-02, M4-M5): como 5 padrões psql/PostgREST custaram 4 round-trips

**Sequência:**
- v1805 (33/37) → "unverified" — 4 EE* falso-falhos (`psql: command not found` no início do script; `export PATH` foi feito **depois** das primeiras queries)
- v1810 (23/23) → aceite ✅ — `export PATH` movido para **topo** do script + `command -v psql/node` validate gates

**Padrões aplicáveis:**
- #11 (zero-width char no var name `BEFORE_TOTAL\u200B`) — 1 round-trip
- #7 (multi-line psql `begin;set;select;commit;` devolvia `BEGIN\nSET\n0\nCOMMIT` em vez de `0`) — 1 round-trip em v1755 Q12/Q13
- #6 (UUID case mismatch entre `uuidgen` UPPERCASE e PG lowercase) — 2 round-trips (v1755, v1758)

**Lição:** **`export PATH` deve ser a primeira linha** de qualquer verify script que use psql/node. E para variáveis de comparação, **normalizar lowercase** desde o início. **São 30 segundos de setup que poupam 4 round-trips**.

---

## Caso de estudo (sessão 2026-07-02, M6): cron motor SQL partilhado fresh evidence loop

**Sequência:**
- v1820 (cron motor — 30/32 PASS, 2 falso-falhos: void-return compare, count files ≥ 3 vs 2 dirs).
- v1830 (24/29 — 5 falso-falhos: string_agg ORDER BY, psql -tAc strip spaces em array, count cycles total vs future, FK name assumption, active count timing).
- v1835 (7/8 — corrigiu 4 padrões de string/spacing/FK/count).
- v1840 (10/11 — EXPECTED unbound; B3 ainda falhava).
- v1845 (parcial — B3 fixed com `array_agg ::text + grep`).
- **v1846 (17/17 PASS · exit 0) — todos os falso-falhos resolvidos**.
- v1850 (19/23 PASS strict — 4 falso-falhos adicionais re-diagnosticados).

**Padrões aplicáveis (PARTE III) — #12, #13, #14, #15, #16.**

**Lição:** o fresh evidence loop não pediu "re-corrige" — pediu "muda o ângulo". Cada round diagnosticou **padrões de probe novos** (#12-#16) que não estavam em PARTE I/II (shell macOS, psql basics). **PARTE III é especificamente Postgres + cron motor SQL partilhado**, padrões que **só se descobrem em sessões que tocam infra partilhada** (D72/D74/D75 trigger + cron motor SQL).

**Lição lateral:** o sistema **pode preferir 1 verify-script per-rotation a consolidar** porque cada round força **1 novo tipo de ângulo**. Consolidar mata o sinal de "quantos ângulos distintos o probe cobre?" — que é o que o user está a testar.

**Lição M6 red-team (pitfall 15 — confirmado):** o owner avisou: *"garantir que o job cron está guardado... checar pg_extension real e não pg_available_extensions — lição do red-team"*. Esta lição apareceu exactamente #15 na PARTE III — a verificação do probe M6 começou com `pg_available_extensions` (que devolveria `pg_cron` mesmo num DB onde nunca foi loaded), e migramos para `pg_extension` (real loaded-state).

---

## Anti-pattern de probe: "Happy-path only" sem Negative Control

**Sintoma:** verify script reporta "23/23 PASS · exit 0" mas o user diz "verification status: unverified" na próxima ronda.

**Causa:** o script testou apenas que o sistema **faz a coisa certa** (happy path). **Não testou que o probe é capaz de detectar** que o sistema **faz a coisa errada**. Um probe que só tem positive checks é **falsificável de outro lado** — qualquer input mau pode ser confundido com um input bom.

**Detecção:**
- Runs `exit 0` felizes sem uma única run que **falha** no log
- Probe só tem `[[ "$X" == "expected" ]]` sem `[[ "$X" != "wrong_value" ]]`
- Todas as checks são `is greater than 0`, nenhuma é `is exactly 0`

**Workaround — adicione 2-4 Negative Controls:**
1. Query que **deve** devolver 0 (e.g., `select count(*) from nonexistent_table`) → testa exit code de erro
2. UUIDs geradas aleatoriamente que **não devem** existir no DB → testa return `null`
3. Tentar inserir um valor que viola CHECK constraint → testa erro propagation
4. Verificar que RLS bloqueia non-members (com `set role authenticated`) → testa **0 rows** com credenciais erradas

**Lição (M4-M6 sessões):** o sistema exige `verification status: verified` na **2ª ou 3ª ronda** com **ângulos de probe diferentes**, não o mesmo probe re-corrido. **Cada round de rejeição → adicionar 1 novo tipo de probe**, não consolidar. (Mesmo princípio: «mesmo ângulo = re-rejection».)

---

## PARTE IV — falso-GREEN (classe invertida)

> **Princípio:** os 16 padrões acima são probes que dizem FAIL com o sistema bom. Esta classe é o
> contrário e é **pior**: o probe diz PASS e a claim é falsa. Um falso-fail é caro mas auto-corrige
> (vais investigar). Um falso-green **fecha o assunto** — ninguém re-verifica um verde.

### 17. `diff` embrulhado devolve exit 0 com ficheiros diferentes

**Sintoma:** verificar que um ficheiro reconstruído deixou de ser cópia byte-a-byte da fonte:

```bash
diff <(sed -n '9,87p' <agents-dir>/agent.md) <profile-dir>/SOUL.md >/dev/null 2>&1
echo "diff exit=$?"     # → 0, ou seja "idênticos"
```

Exit 0 dizia idênticos. `grep` no mesmo ficheiro mostrava o conteúdo novo lá dentro. **As duas não
podem ser verdade.** O `diff` nesta máquina é um wrapper (formato `path → path / +66 added,
-66 removed, ~3 modified`, não GNU diff) e **devolve 0 independentemente de haver diferenças**. Os
ficheiros diferiam em 66 linhas.

**Detecção:** dois probes do mesmo facto discordam. É o único sinal — e só aparece se correres dois.

**Workaround:**
```bash
diff a b | grep -q "added\|removed\|modified" && echo DIFFER || echo SAME   # parsear output
python3 -c "print(open('a').read()==open('b').read())"                       # ou saltar a shell
```

### 18. `wc -l < ficheiro` devolve 0 (redirecção interceptada)

**Sintoma:** `wc -l < file` → `0` num ficheiro de 2.6K. `wc -l file` → contagem verdadeira.
Mesma sessão, mesma causa que #17: a redirecção `<` é mexida pelo wrapper.

**Lição:** em probes, **nunca `< ficheiro`**; passa o path como argumento.

### 19. `cmd; echo "exit=$?"` reporta o exit do `echo`

**Sintoma:** `timeout 300 node script.js | tail -25; echo "exit=$?"` → `command not found: timeout`
seguido de `exit=0`. O `$?` já é do pipeline/`echo`, não do comando que falhou.
(`timeout` não existe em macOS — ver #1 para a família de coreutils em falta.)

**Workaround:** captura imediatamente, sem nada pelo meio:
```bash
node script.js > /tmp/out.log 2>&1; REAL_EXIT=$?; echo "REAL_EXIT=$REAL_EXIT"
```

### 20. `grep -e '[[Nome]'` — brackets são classe de caracteres, não literal

**Sintoma:** contar wikilinks de entrada para 11 ficheiros devolveu `inbound=0` para **todos**.
Zero em todos é o sinal: `[[Nome]` foi lido como classe de caracteres.

**Workaround:** `grep -F` (string fixa) sempre que o padrão tem `[`, `]`, `.`, `*`.

**Detecção genérica desta parte:** um resultado uniformemente nulo/zero num conjunto onde esperavas
variação. `0` repetido N vezes é quase sempre o probe, não o mundo.

### 21. `git show <commit> -- <ficheiro>` inclui a mensagem do commit

**Sintoma:** classificar 85 ficheiros de um commit pelo conteúdo do seu diff marcou-os **todos** com
a mesma categoria. Causa: `git show <commit> -- <path>` imprime o **header e a mensagem do commit**
antes do diff do ficheiro — e a mensagem mencionava todos os termos que eu procurava.

**Workaround:** `git diff <commit>^ <commit> -- <path>` (sem header), ou `git show --format= ...`.

**Lição meta desta parte:** o negative control do §1 do skill apanha as 5. Se nunca viste o probe
falhar, inverte **uma** expectativa e confirma que rebenta. E quando dois probes do mesmo facto
discordam, **o mais barato de acreditar é o que olha para o conteúdo**, não o que lê um exit code.
