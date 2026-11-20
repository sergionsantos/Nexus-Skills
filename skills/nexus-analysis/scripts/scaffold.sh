#!/usr/bin/env bash
# nexus-analysis — scaffold do arranque (fase SCOPE)
# Uso: scaffold.sh <dir-projecto> <slug-sistema> <N> [data YYYY-MM-DD]
# Cria: <dir>/.analysis/checklist-analise-<slug>.md + <dir>/Analysis/<N>-Melhorias-<data>.md (esqueleto com N secções)
set -eu
DIR="${1:?uso: scaffold.sh <dir-projecto> <slug-sistema> <N> [data]}"
SLUG="${2:?falta slug}"
N="${3:?falta N}"
DATA="${4:-$(date +%F)}"
# validação de args (calibração 2026-07-20: `scaffold.sh "Projecto" 7 .` gerou checklist-analise-7.md + .-Melhorias-*.md — slug e N trocados, sem erro)
case "$N" in (*[!0-9]*|'') echo "FAIL: N='$N' não é inteiro — ordem dos args: <dir-projecto> <slug-sistema> <N> [data]"; exit 1;; esac
case "$SLUG" in (.|..|''|*/*) echo "FAIL: slug='$SLUG' inválido"; exit 1;; esac
case "$DATA" in ([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;; (*) echo "FAIL: data='$DATA' não é YYYY-MM-DD"; exit 1;; esac
echo "interpretado: dir=$DIR slug=$SLUG N=$N data=$DATA"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$DIR/.analysis" "$DIR/Analysis"
checklist="$DIR/.analysis/checklist-analise-$SLUG.md"
REL="$DIR/Analysis/$N-Melhorias-$DATA.md"
[ -e "$checklist" ] && { echo "FAIL: já existe $checklist (pre-flight collision — não sobreescrevo)"; exit 1; }
[ -e "$REL" ] && { echo "FAIL: já existe $REL"; exit 1; }

cat > "$checklist" <<EOF
---
task: Análise nexus-analysis de $SLUG — $N melhorias
type: checklist de controlo
phase: observe
status: in-progress
date: $DATA
---

# Checklist — análise $SLUG: $N melhorias

> Actualiza \`phase:\` AO ENTRAR em cada fase (observe→explore→synthesize→structure→verify→learn) — não só no fim. Duas calibrações (2026-07-20) saltaram observe→complete de uma vez; a folha mente durante horas se a phase só muda no fecho.

## ISCs (binários)
- [ ] GROUND: secção "Estado real verificado" — cada linha com comando+resultado
- [ ] EXPLORE: 4-5 lentes, reports só-factos, spot-check 2-3 claims por report
- [ ] SYNTHESIZE: pool etiquetado P/L/T; quotas ≥1 de cada; clusters (não itens rasos); descartes registados
- [ ] STRUCTURE: $N melhorias com Problema+evidência/Acção/Impacto+esforço; tabela ordem+racional; trade-offs explícitos
- [ ] VERIFY-A: scripts/verify-report.sh $REL $N → exit 0 (predição escrita antes)
- [ ] VERIFY-B: review independente fresh → zero findings num passe completo
- [ ] Resumo ordenado no chat para o dono
EOF

sed -e "s/{Sistema}/$SLUG/g" -e "s/{N}/$N/g" -e "s/{data}/$DATA/g" \
  "$SKILL_DIR/templates/report-template.md" > "$REL"

echo "criado: $checklist"
echo "criado: $REL (esqueleto — expande as N secções conforme playbook-structure)"
