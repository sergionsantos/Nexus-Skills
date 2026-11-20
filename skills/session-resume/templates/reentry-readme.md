# Template — folha de re-entrada (README-EXECUTOR generalizado)

> Copiar para `<projecto>/README-EXECUTOR.md` (ou `plan/00-README-EXECUTOR.md` em build plans). Preencher TODAS as secções — secção vazia = sessão futura vai assumir, e assumir é o modo de falha nº1.

```markdown
# <Projecto> — folha de re-entrada

> Autoridade de re-entrada deste projecto. Sessão nova: lê isto PRIMEIRO, depois segue a checklist do skill `session-resume`.

## 1. Como executar
- Ordem do trabalho: <fases/milestones/waves e onde estão definidos>
- Formato de cada passo + regra de verify: <o que conta como "done" aqui>
- Cadência de reporte: <1 marco por milestone/wave; intermédios só "verify ✅">

## 2. Precedência de decisões (em conflito, ganha o de cima)
1. <amendments/decisões pós-verificação, com data>
2. <decisões por fase/milestone>
3. <registo geral de decisões (D## / versões pinadas / configs)>

## 3. Factos do ambiente — VERIFICADOS <data> (NÃO são exemplos)
- <containers/serviços esperados + como verificar: comando exacto>
- <versões travadas: node/pnpm/etc + comando>
- <portas, paths absolutos, credenciais (onde estão, nunca inline)>
- ⚠️ Factos com >48h: re-verificar antes de confiar (passo 3 da skill session-resume).

## 4. Estado actual ← ACTUALIZAR A CADA SAÍDA DE SESSÃO
- **Último passo VERIFICADO:** <id + dump-chave + data>
- **Próximo passo:** <id + dependências>
- **Bloqueios/gates pendentes:** <⛔ o que espera decisão de quem>
- **Outras mãos no projecto:** <sessões/agentes paralelos conhecidos>

## 5. Regras não-negociáveis
- <as 3-5 proibições absolutas deste projecto (ex.: NUNCA reiniciar container X)>
- Verify falha fora do previsto → PÁRA + dump tabular + reporta (nunca improvisar).
```

## Regras de manutenção da folha

1. **Secção 4 actualiza-se a CADA saída** — é a passagem de turno; o resto muda raramente.
2. Factos da secção 3 levam **data**; a sessão que os re-verifica actualiza a data.
3. Divergência detectada na re-entrada → corrigir a folha ANTES de trabalhar (folha errada com autoridade é pior que nenhuma).
4. A folha aponta para os artefactos (ISA, plano, LOG) — não os duplica (senão diverge deles).
