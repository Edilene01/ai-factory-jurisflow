#!/usr/bin/env python3
"""
Smoke test 1 de 3 – a instância responde.

Bate no endpoint de saúde do n8n publicado e confere status 200 em menos de 10
segundos. É o teste que responde à pergunta "o sistema está no ar?" sem depender
de nenhuma credencial de negócio.

Variáveis: N8N_PUBLIC_URL
Uso: python tests/smoke/smoke_01_saude.py
"""
import os
import sys
import time
import urllib.request

BASE = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
LIMITE_SEGUNDOS = 10


def main():
    if not BASE:
        print("[ERRO] defina N8N_PUBLIC_URL")
        return 2

    url = f"{BASE}/healthz"
    inicio = time.time()
    try:
        with urllib.request.urlopen(url, timeout=LIMITE_SEGUNDOS) as r:
            status = r.status
            corpo = r.read(200).decode("utf-8", "replace")
    except Exception as erro:
        print(f"[FALHA] {url} inacessível: {erro}")
        return 1

    decorrido = time.time() - inicio
    print(f"[info] {url} -> {status} em {decorrido:.2f}s | {corpo.strip()[:80]}")

    if status != 200:
        print(f"[FALHA] esperado 200, veio {status}")
        return 1
    if decorrido > LIMITE_SEGUNDOS:
        print(f"[FALHA] resposta acima de {LIMITE_SEGUNDOS}s")
        return 1

    print("[PASS] smoke 1: instância no ar e respondendo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
