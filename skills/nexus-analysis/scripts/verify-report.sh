#!/usr/bin/env bash
# nexus-analysis — check mecânico do relatório (Parte A do playbook-verify)
# Uso: verify-report.sh <relatorio.md> <N>
#   N = número ESPERADO de melhorias (declara-o tu; inferi-lo do próprio ficheiro tornaria o check circular)
# Exit 0 = PASS; exit 1 = FAIL (com dump por campo). Corre o negative control na 1ª utilização
# (remove uma secção obrigatória e confirma exit 1) — check nunca visto a falhar não prova nada.
set -u
R="${1:?uso: verify-report.sh <relatorio.md> <N>}"
N="${2:?falta N (número esperado de melhorias)}"
[ -f "$R" ] || { echo "FAIL: ficheiro não existe: $R"; exit 1; }

secs=$(grep -c "^## " "$R")
resumo=$(grep -c "^## Resumo executivo" "$R")   # secção OPCIONAL — se presente, conta no total esperado
recon=$(grep -c "^## Reconciliação" "$R")       # secção do modo DELTA — opcional a frio, obrigatória em delta
estado=$(grep -c "^## Estado real verificado" "$R")
ordem=$(grep -c "^## Ordem" "$R")
verif=$(grep -c "^## Verificação independente" "$R")
probs=$(grep -c "^\*\*Problema:" "$R")
accs=$(grep -c "^\*\*Acção:" "$R")
imps=$(grep -c "^\*\*Impacto:" "$R")

esperado_secs=$((N+3+resumo+recon))
echo "secs=$secs (esperado $esperado_secs; resumo=$resumo recon=$recon)  estado=$estado  ordem=$ordem  verif=$verif  probs=$probs accs=$accs imps=$imps (esperado $N cada)"

fail=0
[ "$resumo" -le 1 ] || { echo "FAIL: '## Resumo executivo' duplicado ($resumo×)"; fail=1; }
[ "$recon"  -le 1 ] || { echo "FAIL: '## Reconciliação' duplicado ($recon×)"; fail=1; }
[ "$secs"   -eq "$esperado_secs" ] || { echo "FAIL: secções ## = $secs, esperado $esperado_secs (N+3, +1 por Resumo executivo, +1 por Reconciliação em delta)"; fail=1; }
[ "$estado" -eq 1 ]        || { echo "FAIL: falta secção '## Estado real verificado'"; fail=1; }
[ "$ordem"  -eq 1 ]        || { echo "FAIL: falta secção '## Ordem...'"; fail=1; }
[ "$verif"  -eq 1 ]        || { echo "FAIL: falta secção '## Verificação independente' — relatório NÃO revisto"; fail=1; }
[ "$probs"  -eq "$N" ]     || { echo "FAIL: **Problema:** = $probs, esperado $N"; fail=1; }
[ "$accs"   -eq "$N" ]     || { echo "FAIL: **Acção:** = $accs, esperado $N"; fail=1; }
[ "$imps"   -eq "$N" ]     || { echo "FAIL: **Impacto:** = $imps, esperado $N"; fail=1; }

[ "$fail" -eq 0 ] && echo "PASS (exit=0)" || echo "exit=1"
exit "$fail"
