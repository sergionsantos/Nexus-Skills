# Spike READ-ONLY dry-run pattern — reusar o contrato real + input sintético + chain discipline

> Trigger class: qualquer milestone de spike/planning que precise **provar um contrato** (round-trip schema → write → read) **sem tocar produção**, OU executar uma cadeia de milestones com **gates de owner explícitos**.

## Princípio

**Importar o contrato real (read-only), não reescrevê-lo.** Fonte única de verdade.

Se o spike precisa de validar que um candidato produzido pelo componente A passa pelo validador B antes de ser persistido em C:

1. Importa o validador B real (ex.: `parse_reply` do módulo de extracção).
2. Importa os enums/constantes reais (facetas, níveis de sensibilidade, etc.).
3. Constrói um **input sintético curto** (3-5 turnos) com ≥1 facto extraível.
4. Constrói uma **resposta de provider escrita à mão** — o JSON que o LLM devolveria.
5. Chama o validador real com a resposta + input. Se OK: o candidato é o que seria persistido.
6. Faz o **mapping de metadata** que o write-path usaria, mas **não escreve**.
7. **Negative control**: resposta com citação inventada (não ancorada no input) → erro de validação → fail-closed.

## Porque reusar, não reescrever

- A spec evolui (enums, regex, facetas). Re-implementar diverge silenciosamente.
- O validador real incorpora lições acumuladas (canonicalização, normalização Unicode, retry-once). Reescrever = perdê-las.
- O owner/review já validaram o contrato real. Reescrever = re-validar.

## Verificações (predict-then-run + negative control)

**Caso positivo (prevê: 1 candidato válido):** citação ancorada verbatim no input; topic/facet/enums válidos; confiança ∈ [0,1]; exit 0, 1 candidato.

**Negative control (prevê: erro de validação por citação):** citação inventada, não ancorada → exit 1 com razão explícita («unanchored candidate»).

## Checklist read-only (literal)

Antes de reportar o milestone como done:

```bash
# 1. Script corre sem erro
python spike_extract.py --transcript ... --provider-reply ... 2>&1 | head -3
echo "EXIT=$?"

# 2. Nenhum write em produção: consulta o armazém real com uma query read-only
#    e confirma que não há records novos desde o início do spike.

# 3. Negative control devolve exit 1 com a razão prevista
```

## Anti-patterns

| Anti-pattern | Por que morde |
|---|---|
| **Reescrever o validador** no script do spike | Diverge silenciosamente; perde as lições incorporadas |
| **Saltar o negative control** | Sem ele, «0 candidatos» pode ser bug silencioso ou design OK |
| **Usar input real (PII)** | Spike é descartável; dados reais vão parar a logs. Usa sintético |
| **Chamar o provider real no dry-run** | Gasta budget; não-determinístico; a resposta escrita à mão é reprodutível |
| **Escrever o candidato «para ver»** | Spikes in-place contaminam produção; o dry-run **NÃO escreve** |
| **Mapping de metadata divergente** entre dry-run e real | Gera records inconsistentes no passo real; mantém UM mapping canónico |

## Quando ESTE pattern NÃO se aplica

- **Spike com provider real:** aí chamas o LLM; mas o **validador** continua a ser o real.
- **Spike sem contrato existente** (schema novo): reescreves, marcas `# SPIKE — DISCARD` e isolas em worktree.
- **Spike que precisa de side-effects reais** (ex.: testar recall com embeddings): escreves em produção por design, mas **marca + planeia cleanup**.

---

## Padrões adicionais para cadeias de spikes

### A: source-grounding obrigatório

Qualquer bloco de «identidade» ou claims injectado num system prompt/KB tem de ter **fonte verbatim `ficheiro:linha`**. Ver `grounded-source-only.md`.

### B: contrato de status-file — `need` ≠ `working`

`working` = a executar dentro do turno · `done` = verificado com prova deste turno · `blocked` = blocker técnico · `need` = aguardar gate do owner (autorização, «vai», decisão). Reportar `working` enquanto esperas pelo owner esconde bloqueios. Ver `done-language-and-status-vocabulary.md`.

### C: chat/execução interrompida — não retryar em loop

Se um comando de chat/CLI falha (parse de args, rede, hook partido), **não** faças retries automáticos. Fallback em 3 níveis para verificar um ISC (ex.: «o conteúdo X é injectado no prompt»):

1. **Tier 1 — comando de dump dedicado** (print-prompt/prompt-size), se existir.
2. **Tier 2 — uma única execução real** + grep do log. Se falha, não repitas.
3. **Tier 3 — PASS-by-construction:** prova que o conteúdo ESTÁ no ficheiro-fonte (`grep -F`) e que o código do runtime injecta esse ficheiro (leitura directa do código).

Tier 3 é «PASS sem observação directa»: exige aprovação explícita do owner e caveats no documento de verificação.

### D: cadeia de spikes com hard owner gates

Para spikes multi-milestone onde qualquer milestone edita produção ou o cleanup é destrutivo:

- **Gate 0** (antes do 1.º write): backup dos ficheiros de produção a editar, com SHA-256 verificado. Sem backup verificável, não avanças.
- **Gate N** (cada milestone que toca produção): diff completo apresentado ao owner para «vai» ANTES de aplicar.
- **Gate final** (cleanup): lista do que vai ser apagado/restaurado, apresentada ao owner para «vai» ANTES de executar.

Mesmo que todos os milestones verificáveis tenham passado, **não** toques no cleanup sem «vai». A urgência de fechar não justifica.

### E: marca tudo o que escreves em produção

Se escreveres records de teste num armazém real, marca-os com um marcador no conteúdo **e** na metadata, e apaga só por esse marcador (nunca por um atributo partilhado como a «source»).
