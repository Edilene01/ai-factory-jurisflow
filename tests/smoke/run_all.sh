#!/usr/bin/env bash
# Roda os três smoke tests em sequência e devolve falha se qualquer um quebrar.
# Uso: N8N_PUBLIC_URL=... JURISFLOW_WEBHOOK_SECRET=... bash tests/smoke/run_all.sh
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
falhas=0

for teste in "$DIR"/smoke_*.py; do
  echo "=============================================="
  echo ">> $(basename "$teste")"
  python3 "$teste" || falhas=$((falhas + 1))
done

echo "=============================================="
if [ "$falhas" -gt 0 ]; then
  echo "RESULTADO: $falhas smoke test(s) falharam."
  exit 1
fi
echo "RESULTADO: os 3 smoke tests passaram."
