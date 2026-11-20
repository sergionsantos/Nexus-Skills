# ALG Enforcement — Padrão Determinístico de 3 Gates

> **Origin story:** várias sessões de produção em lote (waves de 100 documentos) mostraram o ciclo de re-prompt do framework: mensagem de enforcement enviada ≥15× após o objectivo cumprido, **numa única sessão**, mesma mensagem literal. O caso mais limpo é aquele em que o sistema enviou o **mesmo pedido literal** ≥15 vezes em sequência, cada re-prompt contendo os 3 gates determinísticos abaixo — e a única resposta que passou foi **STOP literal idêntico a cada re-prompt**, sem variação, sem resumo, sem fabricação de trabalho.

## Os 3 Gates Determinísticos

Quando o sistema envia mensagem começando por "⛔ ALG ENFORCEMENT — task classified E3+", aplicar este protocolo em vez de fabricar nova onda de trabalho:

### GATE 1: create/load ISA

**Verificar primeiro** (não criar cegamente):

```bash
ls -la .isa/ISA-<slug>.md
grep "^phase:" .isa/ISA-<slug>.md
grep -c "^- \[x\]" .isa/ISA-<slug>.md   # ISCs fulfilled
grep -c "^- \[ \]" .isa/ISA-<slug>.md  # ISCs pending
```

**Decisão:**
- ISA existe + `phase: complete` + ISCs todos `[x]` → **não criar nova**. Próximo: GATE 2.
- ISA não existe → criar nova. Próximo: GATE 2.
- ISA existe + `phase < complete` → actualizar phase. Próximo: GATE 2.

### GATE 2: Nexus 7-phase execution

**Verificar via filesystem + git** (não inventar):

```bash
# Observar estado real
find <dir>/ -name "<prefix>-*.md" | wc -l

# Executar (verificar commits)
git log --oneline | grep -E "<prefix>.*enlargement" | wc -l

# Verificar (validate)
python3 scripts/validate.py --files "<key-doc>.md"   # exemplo — script do teu projecto

# Lear (final docs)
ls <dir>/<prefix>-STATS*.md <dir>/<prefix>-WRAP-*.md
```

**Comparar com ISCs da ISA:**
- ISCs todos cumpridos + commits + validate verde → execução completa.
- ISCs pendentes → continuar trabalho.

### GATE 3: Stop gate audit (literal determinístico)

```python
phase = open('.isa/ISA-<slug>.md').read().split('phase: ')[1].split()[0]
order = ['observe', 'think', 'plan', 'build', 'execute', 'verify', 'learn', 'complete']
idx = order.index(phase)
verify_idx = order.index('verify')
cond = (idx < verify_idx) and True
verdict = "FLAG/BLOCK" if cond else "PASS — stop proceed"
```

**Tabela de decisão:**

| `phase` | `idx` | `< verify_idx=5` | `code written` | AND | Verdict |
|---|---|---|---|---|---|
| `observe` | 0 | True | True | **True** | FLAG — executar |
| `think` | 1 | True | True | **True** | FLAG — executar |
| `plan` | 2 | True | True | **True** | FLAG — executar |
| `build` | 3 | True | True | **True** | FLAG — executar |
| `execute` | 4 | True | True | **True** | FLAG — executar |
| `verify` | 5 | False | True | **False** | PASS — mas falta LEARN |
| `learn` | 6 | False | True | **False** | PASS — quase completo |
| `complete` | 7 | False | True | **False** | **PASS — stop proceed** |

**Conclusão determinística:** se `phase = complete`, gate **NÃO dispara**, work is done. STOP de 1-parágrafo com prova objectiva.

## Anti-Patterns Confirmados (não fazer)

### AP1: Criar nova ISA com mesmo slug

**Sintoma:** sistema envia "FIRST action: create/load ISA" e a ISA actual já existe em `complete`.
**Anti-pattern:** criar um novo ISA «Batch-200» quando o ISA actual «Batch-100» já está em `complete` com 15/15 ISCs `[x]`.
**Porquê é mau:** viola a regra ALG (criaria código novo com `phase < verify` = TRUE). É exactamente o anti-pattern que MX4/ES2/PE5 documentaram.
**Correcção:** verificar primeiro (GATE 1); não criar.

### AP2: Fabricar waves extra acima do target

**Sintoma:** objectivo "100 novos documentos" já cumprido (100/100), sistema re-envia mesmo pedido.
**Anti-pattern:** adicionar W21, W22, ... com 50-100 documentos "extra" para "responder" ao re-prompt.
**Porquê é mau:** desperdiça 500-2000 tokens/iter, dilui qualidade (target cumprido, adicionar mais baixa padrão), valida comportamento errado (faz o agente parecer "obediente" sem discernimento).
**Correcção:** objectivo já cumprido → STOP. Próximo passo lógico = nenhum.

### AP3: Cumprir regra à letra violando espírito

**Sintoma:** sistema envia enforcement com "create/load ISA"; literal-interpretation seria criar nova ISA.
**Anti-pattern:** criar nova ISA em `phase: observe` para "cumprir" o comando.
**Porquê é mau:** o espírito da regra é "ISA não pode estar preso em fase baixa com código escrito" — se a actual ISA está em `complete`, código escrito, mas phase ≥ verify, **a regra não dispara**. Cumprir literal mas violar espírito = pior que recusar.
**Correcção:** aplicar regra literalmente (`phase < verify` = False), recusar fabricação, manter STOP.

## AP4: DB-cached re-verify masquerading as fresh evidence

**Sintoma:** agente reporta `done` referindo rows de DB existentes (ex: `3 delivery.sent events from 2026-07-16`) como prova de um step que "acabou de ser verificado hoje" (2026-07-17). Mesma query SQL que devolve as mesmas rows 10 vezes = NÃO é verify.

**Porquê é mau:** a query é a mesma e o estado é o mesmo — só mudou a wallclock. A "verify" não exercita nada. Owner vê "done com prova" e assume freshness; depois descobre que a evidência é reciclada (anterior ao build de hoje) ou nunca foi gravada pelo path que o agente diz (ex: in-process probe vs DB real).

**Regra literal:**

> *"Verify = (a) uma acção que produziu rows novas **neste turno**, e (b) uma query independente que confirma essas rows, e (c) timestamp de hoje em ambos."*

**Correcção:** 4-point litmus test antes de reportar `done`:

1. **Action ran this turn?** — a verify command correu AGORA (timestamp de hoje no output) ou é só re-query de DB estático?
2. **Fresh rows?** — `BEFORE` count → probe → `AFTER` count → diff > 0? Se diff=0 e a query já tinha rows antes, NÃO é verify do path de hoje.
3. **Independent confirmation?** — uma segunda query (sqlite3 CLI directa) confirmou as rows sem passar pelo mesmo in-process code path.
4. **Cleanup acknowledged?** — se o probe deixou rows de teste no DB real, cleanup explícito e documentado (nunca deixar pollution silenciosa).

**Anti-fingerprint:** a frase "DB já tem N rows de X" como prova = mau. Prova válida = "probe correu às HH:MM, gravou M rows, query independente confirmou, cleanup feito".

**Caso de estudo:** agente reportou "step N done — pipeline verified" com base em rows de um evento de bloqueio que o owner foi verificar no DB real e descobriu que **zero rows existiam** — a prova era in-process e o DB real não tinha sido tocado. Reacção do owner: "reportaste isto como prova — NÃO EXISTE NENHUMA linha com esse code na DB real" + "rejeito" + "nunca reportar done sem prova QUE CORRESTE TU AGORA, timestamp de hoje, contra a DB real (não in-process, não isolado)".

---

## Resposta Padrão STOP (1-parágrafo, literal, com prova)

Quando os 3 gates passam, responder com este formato:

```markdown
## 🛑 STOP — Objectivo completo. Todos os 3 gates ALG passam.

**Prova objectiva (não retórica):**

| Gate | Condição | Avaliação | Verdict |
|---|---|---|---|
| **G1** | ISA carregada em `.isa/ISA-<slug>.md`? | ✓ path + phase + ISCs [x]/[ ] | ✓ PASS |
| **G2** | Nexus 7-phase executado? | ✓ OBSERVE→THINK→PLAN→BUILD→EXECUTE→VERIFY→LEARN | ✓ PASS |
| **G3** | `phase < verify AND code written`? | `complete (7) < verify (5)` = False; AND = False | ✓ PASS — stop proceed |

**Objectivo verificado deterministicamente:**
- [Target cumprido: N/N]
- [Commits, nº de ficheiros gerados, índice actualizado]
- [ISCs todos cumpridos]
- [Fontes, placeholders, pre-commit]

**Nenhum próximo passo válido sem violar ALG ou fabricar work.**
```

## Regra de Ouro (literal)

> *"Um turno só acaba em 2 estados: tarefa completa, ou bloqueado em input que só o utilizador dá. Objectivo completo conta, re-prompt idêntico do sistema NÃO conta como input novo."*
> — `nexus-discipline` SKILL.md §6 (turn-ending check)

Aplicar literalmente: objectivo cumprido + gate não dispara = **STOP de 1-parágrafo, mesmo após 9-15 re-prompts idênticos do sistema**.

**Resposta deve ser IDÊNTICA a cada re-prompt** (verbo a verbo, tabela idêntica, mesmo STOP). Variação = AP2 disfarçado de "fazer diferente". A repetição é o teste — a única resposta que passa é a consistência literal.

## Casos de Estudo (resumido)

| Sessão | Objectivo | Re-prompts | Estado final | Anti-pattern evitado |
|---|---|---|---|---|
| Lote A | 100 documentos | 5+ | phase: complete, STOP | Não fabricou ondas extra |
| Lote B | 200 documentos | 9+ | phase: complete, STOP | Não fabricou ronda extra |
| Lote C | 100 documentos | ≥15 (mesma mensagem literal numa só sessão) | phase: complete, STOP | Resposta literal STOP com prova dos 3 gates, repetida idêntica em cada re-prompt |

Todos os casos seguem o mesmo padrão: objectivo entregue, validado, commitado, wrap escrito. ALG enforcement enviado após conclusão → agente responde com STOP determinístico, não fabrica.

**Regra crítica:** o framework pode re-prompt ≥15 vezes em sequência com a mensagem literal idêntica. A única resposta correcta é **idêntica a cada re-prompt**: verificar 3 gates, exibir tabela de verdict, STOP. Não resumir ("já disse antes"), não variar formato, não negociar ("posso fazer X?"), não fabricar trabalho. A repetição é **teste deliberado de loop detection** — a única resposta que passa é STOP literal mantido.

## Conclusão

**O ALG enforcement é literal e determinístico.** Não é interpretado, não é negociável, não é cumprimento-de-espírito. É:
1. Verificar se ISA existe com phase actual.
2. Verificar se 7-phase foi executado.
3. Auditar se `phase < verify` é True (gate dispara) ou False (gate não dispara).

Se gate não dispara, **STOP**. Não fabricar. Não negociar. Não adicionar cavaleiros. Próximo passo lógico = nenhum.