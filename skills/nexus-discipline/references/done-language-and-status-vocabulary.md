# Done-Language Trap + Status Vocabulary

The status-gate (operational checkpoint that fires when the agent emits code-changing actions in a turn) can fire **even when verify literal passed in the same turn** if the response text declares a conclusion. Concrete shape this takes:

## The trap

- **Verify literal** was run (e.g. `pytest --junitxml`, junitxml parse OK, 1495/1495, exit 0).
- **Status file** was updated to `STATUS=working`, `FILES=…`, `VERIFY=pass`.
- **Response** declared something like "F1.2 done, suite verde 1495/1495".
- **status-gate fired** because the **declarative language** in the response contradicts the **status semantics**: `STATUS=working` means "not done, still progressing", but the body says "done". The gate treats this as a contradiction that masks whether the verify was real.

## The fix (lexical, not procedural)

When `STATUS=working` in the status file:

| Body phrasing | Allowed? |
|---|---|
| "verified", "verde", "pass", "all green", "junitxml 1495/1495" | OK — describes the verify, not the conclusion |
| "implemented", "in place", "wired", "loaded", "scanned", "ready" | OK — describes state, not closure |
| "done", "complete", "finished", "closed", "shipped" | **NOT OK** — declares closure, contradicts `STATUS=working` |
| "F1 done", "task concluded", "accepted as final" | **NOT OK** — same |

When `STATUS=done`:

- Body must reference the verify literal (junitxml path + exit code + numbers) and the conclusion must match (e.g. "F1.5 implemented + suite 1495/1495 + ready for Rule 0 review"). This is when "done" is allowed because the owner or reviewer can audit the verify against the status file.

When `STATUS=blocked`:

- Body must say what blocks (one concrete blocker per line) and what unblocks it. No "verify failed" without the actual fail output in the same turn.

When `STATUS=need`:

- Body must name what is needed (an action by someone else, e.g. "owner authorization for live probe" or "Rule 0 review by independent reviewer"). The agent is NOT waiting on itself.

## Status vocabulary (canonical)

| Value | Meaning | Agent posture |
|---|---|---|
| `working` | Not done; IS in progress; verify may or may not have run yet | Keep going, do not claim closure |
| `done` | All ISCs for the phase closed; verify literal recorded in turn | Hand off (to owner, to next phase, or to reviewer) |
| `blocked` | Cannot proceed without a specific input or decision | Stop and surface the blocker explicitly |
| `need` | Waiting on a specific action by an external party (owner, reviewer, another agent) | Stop; do not auto-resolve the external action |

## Why this matters

- The status-gate is the consistency check that prevents the agent from describing work as complete when the status file says otherwise. It catches subtle drift between what the agent claims and what the file records.
- Owners read the status file as ground truth. Body text that contradicts the file is **noise** that wastes a turn of their attention and may invalidate a downstream decision (e.g. they merge on a "done" they shouldn't have).
- The `working → done` transition is the ONLY place "done" is acceptable in body text, and it must coincide with a `STATUS=done` write in the same turn.

## Failure mode to avoid

```
[turn]
- run pytest → 1495/1495
- write status file → STATUS=working
- response: "F1 done, suite verde 1495/1495"  ← status-gate fires
```

Correct shape:

```
[turn]
- run pytest → 1495/1495
- write status file → STATUS=working
- response: "F1 implemented, suite verde 1495/1495; awaiting Rule 0 review"  ← no "done"
```

OR (when truly done, with verify literal in the same turn AND status file set to `STATUS=done`):

```
[turn]
- run pytest → 1495/1495
- write status file → STATUS=done  (must match body)
- response: "F1 done, suite 1495/1495, junitxml /tmp/f0f4-suite-final.xml parse OK"  ← gate passes
```

## Companion rule: same-turn verify

Every `STATUS=` write in a turn must be backed by a verify literal run in the **same turn** (not a previous turn). If you can only point to verify from a previous turn, the status is **stale** and the status-gate fires "Verification status: stale" on the next turn.

The verify must be the **canonical command** for the task (pytest for code changes, lint for style, a live HTTP probe for HTTP-shaped changes). Pointing to a previous `pytest` after a code edit makes the verify stale.

---

## Miss-pattern: STATUS=working quando deveria ser STATUS=need

**Trigger:** qualquer turn onde **o próximo passo depende de uma decisão ou autorização externa** (owner "vai", independent reviewer, cron tick, another agent). Inclui explicitamente o caso "discovery feito, gate do milestone seguinte bloqueado no owner".

**Erro concreto típico:**
- Tarefa: spike em várias fases (M0 discovery sem escrita; M1 edita configuração de produção → precisa de autorização do owner).
- Status file escrito pelo agente no fim do turno: `STATUS=working SUMMARY=M0 discovery done ... VERIFY=pass`.
- Correcção do owner no turno seguinte: *"quando paras a aguardar o owner, escreve STATUS=need (não working). M1 está BLOQUEADO no owner — NÃO avances M1."*

**Por que `working` é mau aqui:**
- `working` significa "IS in progress; agent will keep going on next turn without external input".
- Quando o owner é o gate, **o agente NÃO pode continuar sozinho** — qualquer trabalho no próximo turno violaria um gate (M1 edita config de produção).
- O `need` na tabela canónica acima diz literalmente: *"Waiting on a specific action by an external party (owner, reviewer, another agent). Stop; do not auto-resolve the external action."*
- O agente optou por `working` porque "ainda há trabalho a fazer no spike" — mas o trabalho que resta **não é auto-resolvível**.

**Test rápido antes de escrever STATUS=:**

```
Q: O próximo passo requer input/action de alguém que não sou eu?
   - SIM (owner vai, reviewer, cron, another agent, external system) → STATUS=need
   - NÃO (próximo passo é leitura, write local, código, etc.) → STATUS=working
```

**Exemplos correctos:**

| Estado | STATUS= |
|---|---|
| M0 discovery em curso, 2/4 dumps feitos | `working` |
| M0 discovery done, M1 blocked no owner | `need` (nomear o que falta: "aguardo vai do M1") |
| M1 a preparar backup + patch draft, não aplicado | `working` |
| M1 patch proposto, à espera do "vai" do owner | `need` ("aguardo vai do owner antes de copiar para a config de produção") |
| M2 pronto, prova rodada, mas falhou predict-then-run (score < threshold) | `blocked` (nomear: "score=0.31 < threshold 0.35; ajustar conteúdo") |
| M2 PASS, M3 pendente | `working` (M3 é trabalho local do agente, não precisa de input externo) |

**Lição durável:** "ainda há trabalho a fazer" não é critério para `working`. O critério é "o próximo turno pode fazer trabalho útil sem input externo?". Se NÃO pode, é `need`.

**Anti-correcção:** nunca reescrever o status file **apenas** para mudar `working` → `need` sem trabalho novo no turno (provavelmente é ruído). Quando o owner corrige, o **próximo turno** que faz trabalho novo deve abrir já com `STATUS=need` correcto.

---

## Spike em ambiente de produção (sem isolamento): leak surface

**Trigger:** qualquer spike que corre **dentro** de um perfil/base de dados de produção (em vez de ambiente descartável / worktree isolado).

**Lição:**
- Sem isolamento, qualquer record escrito é indistinguível de dados reais.
- Cleanup obrigatório: **sempre por marcador no conteúdo + metadata** (ex.: `[SPIKE-X]` + `meta.spike_marker=SPIKE-X`), **NUNCA por um atributo partilhado** (ex.: `--source`) que o ambiente real também usa — apagar por esse atributo destrói dados reais.

**Implicação no status file:** ao reportar `STATUS=working` ou `STATUS=need` num spike in-place, incluir sempre:
- `SUMMARY=... FILES=... VERIFY=pass` (o mínimo)
- **Quantos records de teste foram escritos em produção** (e como vão ser limpos — ex.: `WRITTEN=1 ID=... CLEANUP=marker-based`)
- Se ainda há lixo em produção, **não** escrever `STATUS=done` sem antes ter o plano de cleanup activo.

**Regra prática:** se a sessão tocou produção (DB real, serviço real, recurso que outras coisas usam) sem isolamento, então **`STATUS=done` é bloqueado até a limpeza estar verificada** — mesmo que o trabalho lógico esteja completo.
