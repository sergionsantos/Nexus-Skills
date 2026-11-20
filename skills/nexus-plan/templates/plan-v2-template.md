# PLAN — <tema> (regime PLAN-v2)

> Evidência: <análise §N — já verificada; não re-explorar>. Executor: <1 tier-médio
> sequencial | waves com ficheiros disjuntos>. **Steps de ownership ≠ executor marcados
> — NUNCA na sequência dele.**
> Recovery: <git restore / backup-antes-de-editar>. <Avisos: symlinks live, read-only paths.>
> Paths: <vars absolutas>.

## Decisões locked

- D1..DN: <formatos, alvos, mecanismos, regras de dados-em-falta (s/d), o que é juízo
  do orquestrador vs delegável>

## S1 — <título> (trivial|pequeno) [owner: executor]
**Edit/Criar:** <concreto>
**Verify:** <comando + predict + exit visível; negative control se check novo>
**If-fails:** <acção prescrita>

## S2..SN — idem

## S<X> — <título> [owner: ORQUESTRADOR — fora da sequência do executor]

## Pós-execução (orquestrador)
Verify independente (lente ≠ executor) → fix-loop até zero findings → PROMPTS-<run>.md +
TOKEN-LEDGER-<run>.md (registo do traço).
