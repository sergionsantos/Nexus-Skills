# DRAFT — wrap: migrar-exportador-csv

- **Tópico:** migração do exportador CSV do projecto fictício "Faturas" para streaming
- **Data:** 2026-11-20
- **Início do tema:** 2026-11-20 09:30 (pedido inicial do utilizador)
- **Workspace:** `~/code/faturas` (spec: `PLAN.md` [A1])

## Estado
- Exportador passou a escrever linha a linha (sem carregar tudo em memória) em `src/export.py` [A1][R1].
- Testes unitários do exportador passam; teste com ficheiro de 1 GB ainda NÃO foi corrido.

## Decisões
- Streaming em vez de paginação: o formato CSV não precisa de total antecipado; menos memória [A1].
- Manter a flag `--legacy` por 1 versão para não partir utilizadores existentes [R2].

## Pendente + limitações
- PENDENTE: teste de carga com 1 GB (planeado, não executado).
- Limitação: o cabeçalho é escrito antes de validar a 1.ª linha; erros tardios deixam CSV parcial.
- Risco: `--legacy` duplica código; remover na versão seguinte.

## Ficheiros
- `src/export.py` (alterado), `tests/test_export.py` (novo), `PLAN.md` (actualizado)

## Lições
- O `csv.writer` com `newline=""` é necessário no Windows, senão surgem linhas em branco duplicadas.

## Fontes
- [A1] `PLAN.md` (spec curada)
- [R1] commit `a1b2c3d` "export: streaming"
- [R2] commit `e4f5a6b` "export: keep --legacy"

FIDELITY NOTE: resumo montado com ajuda de uma pesquisa automática de memória (apenas índice); fonte autoritativa: `PLAN.md`.
