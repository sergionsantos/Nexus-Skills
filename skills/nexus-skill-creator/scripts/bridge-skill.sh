#!/bin/bash
# bridge-skill.sh <nome> [--copy] [--dry-run] [--a DIR] [--b DIR]
# Torna um skill disponível em DOIS agentes (por omissão Claude Code e Codex):
#   A = ~/.claude/skills   B = ~/.codex/skills   (sobrepõe com --a/--b ou SKILLS_DIR_A/SKILLS_DIR_B)
# A pasta real do skill fica onde já existe; no outro lado cria-se um symlink (ou, com --copy, uma cópia).
# Idempotente em modo symlink; com --copy uma 2.ª corrida dá CONFLITO (rc 1). Casos:
#   - skill só em A (ou só em B)          -> cria symlink/cópia no outro lado
#   - já ligado (symlink para o original) -> no-op
#   - pastas reais nos dois lados         -> CONFLITO, reconcilia à mão (diff -r)
#   - não existe em nenhum                -> erro
# --dry-run só mostra o que faria. Nota (Windows/Git Bash): symlinks podem exigir Modo de Programador;
# se falhar, usa --copy (cópias têm de ser actualizadas à mão quando o original muda).
set -euo pipefail

NAME=""; COPY=0; DRY=0
H="${HOME:-${USERPROFILE:-}}"
A="${SKILLS_DIR_A:-$H/.claude/skills}"
B="${SKILLS_DIR_B:-$H/.codex/skills}"
while [ $# -gt 0 ]; do
  case "$1" in
    --copy) COPY=1 ;;
    --dry-run) DRY=1 ;;
    --a) A="${2:?--a precisa de pasta}"; shift ;;
    --b) B="${2:?--b precisa de pasta}"; shift ;;
    -*) echo "opção desconhecida: $1" >&2; exit 2 ;;
    *) NAME="$1" ;;
  esac
  shift
done
[ -n "$NAME" ] || { echo "uso: bridge-skill.sh <nome-do-skill> [--copy] [--dry-run] [--a DIR] [--b DIR]" >&2; exit 2; }

PA="$A/$NAME"; PB="$B/$NAME"
run() { if [ "$DRY" = 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }

real() { [ -d "$1" ] && [ ! -L "$1" ]; }          # pasta real (não symlink)
# compara destinos resolvidos (robusto a / vs \ no Windows)
links_to() { [ -L "$1" ] && [ -d "$2" ] && [ "$(cd "$1" 2>/dev/null && pwd -P)" = "$(cd "$2" && pwd -P)" ]; }

link() {  # link <original> <destino>
  if [ "$COPY" = 1 ]; then
    run mkdir -p "$(dirname "$2")"; run cp -R "$1" "$2"; echo "cópia criada: $2 <- $1"
  else
    run mkdir -p "$(dirname "$2")"; run ln -s "$1" "$2"; [ "${DRY:-0}" = 1 ] || echo "symlink criado: $2 -> $1"
  fi
}

if links_to "$PB" "$PA" && [ -d "$PA" ]; then
  echo "já ligado: $PB -> $PA"
elif links_to "$PA" "$PB" && [ -d "$PB" ]; then
  echo "já ligado: $PA -> $PB"
elif real "$PA" && [ ! -e "$PB" ] && [ ! -L "$PB" ]; then
  link "$PA" "$PB"
elif real "$PB" && [ ! -e "$PA" ] && [ ! -L "$PA" ]; then
  link "$PB" "$PA"
elif real "$PA" && real "$PB"; then
  echo "CONFLITO: existem pastas reais nos dois lados — reconcilia à mão (diff -r '$PA' '$PB')" >&2
  exit 1
else
  echo "skill '$NAME' não encontrado como pasta real em $PA nem $PB (ou destino ocupado)" >&2
  exit 1
fi

# verify
if [ "$DRY" = 1 ]; then echo "[dry-run] sem verificação"; exit 0; fi
[ -f "$PA/SKILL.md" ] || { echo "FAIL: $PA/SKILL.md não resolve" >&2; exit 1; }
[ -f "$PB/SKILL.md" ] || { echo "FAIL: $PB/SKILL.md não resolve" >&2; exit 1; }
echo "verify OK: SKILL.md resolve nos 2 paths (os agentes descobrem skills no arranque da sessão)"
