# Done-language + count-based proof

## Origem

Padrão recorrente em trabalho com escritas (base de dados, HTTP, ficheiros): o agente
reporta «done» com base numa linha/registo que só o seu próprio probe viu — e que já
tinha sido limpa antes do report (count 0→1→0). O dono re-verificou e descobriu count=0
e rejeitou o «done» várias vezes. Esta reference condensa a lição.

## Pitfall #1 — Done-Language inflation

**Anti-pattern:** o agente reportou "step N done (probe real, row <evento> criada às <hora>)" referindo uma row que tinha sido *gravada* por um probe
in-process **e já tinha sido limpa** antes do report. O report não verificou
count pós-cleanup; o owner re-verificou por si próprio e descobriu count=0.

**Padrão correcto:**

1. **Probe** (in-process ou via HTTP) — executa a acção que escreve.
2. **Cleanup opcional** — se a row é de teste, decidir explicitamente: deixar
   (com `awaiting owner confirm`) ou limpar (e reportar `count: 0` no report).
3. **Verify independente** — usar uma read-path separada do write-path:
   - DB writes: `sqlite3 /path/to.db "SELECT ... FROM table WHERE ..."` (CLI
     directo, não `repo.execute()` in-process)
   - HTTP writes: `curl ...` com `Authorization: Bearer ...` (CLI,
     não `requests` in-process)
   - File writes: `cat /path | sha256sum` (CLI, não `open().read()` in-process)
4. **Show before/after** no report: `BEFORE: count=X; PROBE result=Y; AFTER:
   count=Z; DIFF: Z-X=N`. Incluir primary key + timestamp.
5. **Done** só após count 0→≥1 verificado pela read-path independente.
   "Implementado, happy-path testado, por rever" é linguagem honesta até
   review independente.

**Tabela de linguagem canónica (não negociável):**

| Estado | Linguagem | Quando |
|---|---|---|
| `completed=false` | "implementado, happy-path testado, por rever" | após probe + verify independente, **antes** de review independente |
| `completed=true` | "revisto independente + verificado limpo, done" | só após review independente (e.g. Rule 0) com zero findings |
| `blocked` | "<step> OWNER-BLOCKED: <dependency> mascarada/não-acessível" | quando o owner confirma que algo (key, secret, fixture) está fora do alcance |
| `gated-pending` | "<step> OWNER-GATED-PENDING: requer owner-side action: <concreto>" | quando o step genuinamente precisa do owner presente (ex.: clicar) |

**Nunca escrever "Done", "Concluído", "Ship-it", "Verificado" sem fresh evidence
neste turno.**

## Pitfall #2 — Probe-self-confirmation não é prova

**Anti-pattern:** o agente executou
`process_message(fixture, repo=repo)` e reportou
"row criada" como prova — mas:
- O **write-path** é a própria função (`repo.append_event(...)` chamada
  dentro do pipeline).
- A **read-path** que confirmou foi **in-process** (leu do mesmo `repo` que
  acabou de escrever). In-process self-confirmation: se a função falhou
  silenciosamente (ex.: integridade DB, except engolido), o write não aconteceu
  mas a função retornou o `result` esperado.

**Padrão correcto:** **separar write-path e read-path**:

```
write-path (in-process or HTTP) → effect on world
independent read-path (CLI: sqlite3 / curl / cat) → confirm the effect
```

Se read-path não confirmar, o probe falhou (mesmo se a função retornou sucesso).

## Pitfall #3 — In-process `cur.execute()` self-confirmation

Similar a Pitfall #2 mas para SQLite. O anti-pattern:

```python
con.execute("INSERT INTO x ...")
con.execute("SELECT COUNT(*) FROM x")  # same connection — same transaction
return count
```

Se a transacção fizer rollback (constraint violation, exception) entre o INSERT
e o SELECT, o count devolve 0 e o agente reporta "row não criada" sem fazer
**rollback explícito + novo SELECT fora do contexto da transacção**.

**Padrão correcto:** commitar a transacção (`con.commit()`) e usar uma **nova
conexão** para a read de confirmação.

## Pitfall #4 — No polling on OWNER-BLOCKED / OWNER-GATED

**Anti-pattern:** quando o agente descobriu que uma chave de serviço
está mascarada no source, continuou a tentar:
- patchar o script de provisionamento → reverter → tentar de novo
- inventar passwords → não fazer
- procurar a key em keychain/.env/configs → não fazer (custo alto)
- chamar owner para dar a key → owner confirmou que tentou também, sem sucesso

**Padrão correcto:** quando o owner confirma que um item é OWNER-BLOCKED
(secret não-acessível) ou OWNER-GATED-PENDING (requer acção concreta do owner):

1. Documentar uma vez no ISA + 00-README com:
   - status: OWNER-BLOCKED / OWNER-GATED-PENDING
   - root cause (concreto, source-traced)
   - o que foi tentado (e falhou)
   - exactamente o que owner precisa de fazer (para destrancar) ou fazer
2. Set `STATUS=blocked` no status-file.
3. **Parar** o trabalho nesse item.
4. Mover para o próximo sub-step (que não depende do bloqueado).
5. Quando owner resolver, retomar (sem patching do passado).

**Não fazer:** keep retrying, regenerating patches, trying alternative
providers in the same session. Custa tokens, tempo, e dilui a sessão.

## Reference

- `references/alg-enforcement-3-gates.md` — gates ISA + processo de 7 fases.
- `references/done-language-and-status-vocabulary.md` — vocabulário STATUS e miss-patterns.
