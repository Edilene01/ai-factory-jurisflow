#!/usr/bin/env bash
# Roda os três smoke tests em sequência e devolve falha se qualquer um quebrar.
# Uso: N8N_PUBLIC_URL=... JURISFLOW_WEBHOOK_SECRET=... bash tests/smoke/run_all.sh
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
falhas=0

# No runner do CI é python3; no Git Bash do Windows, python3 é o atalho da
# Microsoft Store, que não executa nada e ainda devolve sucesso. Escolher o
# interpretador aqui evita que o teste pareça quebrado quando é só o ambiente.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for cand in python3 python py; do
    if command -v "$cand" > /dev/null 2>&1 && "$cand" -c "import sys" > /dev/null 2>&1; then
      PY="$cand"
      break
    fi
  done
fi
if [ -z "$PY" ]; then
  echo "ERRO: nenhum interpretador Python utilizável. Defina PYTHON=/caminho/do/python."
  exit 2
fi
echo "Interpretador: $PY"

for teste in "$DIR"/smoke_*.py; do
  echo "=============================================="
  echo ">> $(basename "$teste")"
  "$PY" "$teste" || falhas=$((falhas + 1))
done

echo "=============================================="
if [ "$falhas" -gt 0 ]; then
  echo "RESULTADO: $falhas smoke test(s) falharam."
  exit 1
fi
echo "RESULTADO: os 3 smoke tests passaram."
