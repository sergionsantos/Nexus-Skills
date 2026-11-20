#!/bin/bash
# validate-plan-spec.sh — verificação mecânica canónica para outputs da skill nexus-plan-spec
# Uso: ./scripts/validate-plan-spec.sh plan/PLAN-*.md
# (ou qualquer *.md com steps no formato §6 da skill nexus-plan-spec)
#
# O que verifica:
#  1. Step IDs únicos (aceita M<N>.<M> e M-PREFIX-<N>.<M>, ex.: M-E2E-0.1)
#  2. Code fences balanced
#  3. Files blocks ≥1 (prefix-match, não bullet — bullets OU parágrafos)
#  4. Verify blocks ≥1 (idem)
#  5. Done when blocks ≥1 (idem)
#  6. If-verify-fails por step (FAIL)
#  7. Commands blocks contagem
#  8. Migrations referenced (NNNN_slug, informativo)
#  9. D-numbered decisions (D###)
#
# Saída: 0 (OK) ou 1 (fail) com diagnóstico.
# Prefix-match nos markers (aceita `**Goal:**` em parágrafo ou `- **Goal**` em bullet).
# O Step ID aceita prefixos (M-E2E-N.M). O separador do cabeçalho pode ser —, – ou -.
# Decisões D##: aceita bullets "- **D01:" ou linhas de tabela "| D01 |".

set -u

PLAN="${1:?Usage: $0 <plan-file>}"
[ -f "$PLAN" ] || { echo "FATAL: file not found: $PLAN" >&2; exit 2; }

PASS=0
WARN=0
FAIL=0

ok()  { echo "  [PASS] $1"; PASS=$((PASS+1)); }
warn(){ echo "  [WARN] $1"; WARN=$((WARN+1)); }
bad() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

# === 1. Step IDs únicos (aceita M<N>.<M> e M-E2E-N.M) ===
echo ""
echo "=== 1. Step IDs únicos ==="
STEP_HEADERS=$(grep -cE "^#{3,4} (Step )?(M[0-9]+\.[0-9]+|M-[A-Z0-9]+-[0-9]+\.[0-9]+)(\.[0-9]+)?[[:space:]]+(—|–|-)" "$PLAN")
HDR_LINES=$(grep -E "^#{3,4} (Step )?(M[0-9]+\.[0-9]+|M-[A-Z0-9]+-[0-9]+\.[0-9]+)(\.[0-9]+)?[[:space:]]+(—|–|-)" "$PLAN")
STEP_IDS=$(echo "$HDR_LINES" | grep -oE "(M[0-9]+\.[0-9]+|M-[A-Z0-9]+-[0-9]+\.[0-9]+)(\.[0-9]+)?" | sort -u)
DUP_IDS=$(echo "$HDR_LINES" | grep -oE "(M[0-9]+\.[0-9]+|M-[A-Z0-9]+-[0-9]+\.[0-9]+)(\.[0-9]+)?" | sort | uniq -d)
UNIQUE_COUNT=$(echo "$STEP_IDS" | wc -l | tr -d ' ')
echo "  step headers: $STEP_HEADERS, unique: $UNIQUE_COUNT"
if [ "$STEP_HEADERS" -eq 0 ]; then
  bad "0 step headers detectados (formato: '### Step M<N>.<M> — título'; aceita —, – ou -)"
fi
if [ -z "$DUP_IDS" ]; then
  ok "no duplicate step IDs"
else
  bad "duplicate step IDs: $(echo $DUP_IDS | tr '\n' ' ')"
fi

# === 2. Code fences balanced ===
echo ""
echo "=== 2. Code fences balanced ==="
FENCE_COUNT=$(grep -c '^```' "$PLAN")
if [ $((FENCE_COUNT % 2)) -eq 0 ]; then
  ok "$FENCE_COUNT fences (even, balanced)"
else
  bad "$FENCE_COUNT fences (odd, NOT balanced)"
fi

# === 3. Files blocks (PREFIX MATCH — aceita `**Files touched:**` parágrafo OU `- **Files**` bullet) ===
echo ""
echo "=== 3. Files blocks (prefix match) ==="
FILES_COUNT=$(grep -cE '\*\*Files[[:space:]]*(touched)?:?\*\*' "$PLAN")
if [ "$FILES_COUNT" -ge 1 ]; then
  ok "$FILES_COUNT Files blocks"
else
  bad "0 Files blocks (expected ≥1)"
fi

# === 4. Verify blocks — contagem total >= nº de steps (NAO verifica step a step) ===
echo ""
echo "=== 4. Verify blocks (total count >= steps) ==="
VERIFY_COUNT=$(grep -cF '**Verify' "$PLAN")
if [ "$STEP_HEADERS" -gt 0 ] && [ "$VERIFY_COUNT" -lt "$STEP_HEADERS" ]; then
  bad "$VERIFY_COUNT Verify blocks < $STEP_HEADERS steps (cada step exige Verify)"
elif [ "$VERIFY_COUNT" -ge 1 ]; then
  ok "$VERIFY_COUNT Verify blocks (steps: $STEP_HEADERS)"
else
  bad "0 Verify blocks (expected ≥1)"
fi

# === 5. Done when blocks (PREFIX MATCH) ===
echo ""
echo "=== 5. Done when blocks (prefix match) ==="
DONE_COUNT=$(grep -cF '**Done when' "$PLAN")
if [ "$DONE_COUNT" -ge 1 ]; then
  ok "$DONE_COUNT Done-when blocks"
else
  bad "0 Done-when blocks (expected ≥1)"
fi

# === 6. If-verify-fails — POR STEP, FAIL (nexus-discipline assume failure-tree garantido por
# construção — um step sem "If verify fails" faz o executor PARAR) ===
echo ""
echo "=== 6. If-verify-fails coverage (per-step, FAIL) ==="
IFFAILS_COUNT=$(grep -cF '**If verify fails' "$PLAN")
echo "  $IFFAILS_COUNT If-verify-fails / $STEP_HEADERS steps"
if [ "$STEP_HEADERS" -gt 0 ] && [ "$IFFAILS_COUNT" -lt "$STEP_HEADERS" ]; then
  bad "$IFFAILS_COUNT If-verify-fails < $STEP_HEADERS steps (obrigatório por step — contrato VERIFY-PREFLIGHT-GATE de nexus-discipline)"
elif [ "$STEP_HEADERS" -eq 0 ]; then
  echo "  (0 steps: já reportado como FAIL na secção 1)"
else
  ok "If-verify-fails por step completo"
fi

# === 6b. Placeholders proibidos (anti-padrão §6: sketches, '...', 'add logic here') ===
echo ""
echo "=== 6b. Placeholders proibidos ==="
PLACEHOLDERS=$(grep -nE '^[[:space:]]*(//|#)?[[:space:]]*\.\.\.[[:space:]]*$|add logic here|<placeholder|TODO\(fill' "$PLAN" | head -5)
if [ -z "$PLACEHOLDERS" ]; then
  ok "sem placeholders"
else
  bad "placeholders encontrados: $(echo "$PLACEHOLDERS" | tr '\n' ' ' | cut -c1-160)"
fi

# === 7. Commands blocks ===
echo ""
echo "=== 7. Commands blocks ==="
COMMANDS_COUNT=$(grep -cF '**Commands' "$PLAN")
ok "$COMMANDS_COUNT Commands blocks (informational)"

# === 8. Migrations referenced (informacional, genérico) ===
echo ""
echo "=== 8. Migrations referenced (informational) ==="
MIG_COUNT=$(grep -cE "[0-9]{4}_[a-z]" "$PLAN")
ok "$MIG_COUNT migration reference(s) NNNN_slug (informational)"

# === 9. D-numbered decisions ===
echo ""
echo "=== 9. D-numbered decisions ==="
# aceita bullets "- **D01:" e linhas de tabela "| D01 |" (também "| **D01** |" e D01-R)
D_COUNT=$(grep -cE "^- \*\*D[0-9]+(-R)?:|^\|[[:space:]]*\**D[0-9]+(-R)?\**[[:space:]]*\|" "$PLAN")
if [ "$D_COUNT" -ge 1 ]; then
  ok "$D_COUNT D-numbered decisions"
else
  warn "0 D-numbered decisions (expected ≥1 for §0.5 do SKILL.md)"
fi

# === Summary ===
echo ""
echo "=== Summary: $PASS pass / $WARN warn / $FAIL fail ==="
if [ $FAIL -eq 0 ]; then
  exit 0
else
  exit 1
fi
