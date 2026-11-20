#!/usr/bin/env bash
# recover-from-failed-patch.sh — diagnostica uma edição (ferramenta de edição) que
# reporta sucesso mas não persistiu no ficheiro (skill session-resume).
#
# Uso:  bash scripts/recover-from-failed-patch.sh <path-de-files> [<marker>]
#
# Saída: o conteúdo actual do ficheiro (echo) + 1 linha de diagnóstico,
#        e sai 0 (ok / sem marcador para testar) ou 1 (bug confirmado).
#
# Se "bug confirmado", a próxima acção é: abandonar o patch e
# re-escrever o ficheiro inteiro.

set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: $0 <file> [<marker>]" >&2
  exit 2
fi

FILE="$1"
MARKER="${2:-}"

if [ ! -f "$FILE" ]; then
  echo "DIAG: $FILE does not exist on disk"
  exit 1
fi

WCL=$(wc -l < "$FILE")
echo "DIAG: $FILE has $WCL lines on disk"

if [ -n "$MARKER" ]; then
  if grep -qF -- "$MARKER" "$FILE"; then
    echo "DIAG: marker found on disk — patch DID persist"
    exit 0
  else
    echo "DIAG: marker NOT on disk — patch did NOT persist despite tool reporting success"
    exit 1
  fi
else
  echo "DIAG: no marker given — review diff vs HEAD manually"
  exit 0
fi
