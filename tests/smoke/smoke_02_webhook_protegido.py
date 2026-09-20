#!/usr/bin/env python3
"""
Smoke test 2 de 3 – o webhook não aceita chamada anônima.

Envia um POST sem o header de assinatura e exige que a resposta seja 401 ou 403.
Se este teste passar a devolver 200, alguém desligou a autenticação do webhook e
qualquer pessoa na internet pode injetar casos falsos nos canais dos advogados.

Variáveis: N8N_PUBLIC_URL
Uso: python tests/smoke/smoke_02_webhook_protegido.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
CAMINHO = os.environ.get("INTAKE_PATH", "/webhook/intake")

PAYLOAD = {
    "nome_cliente": "Teste Smoke",
    "cpf": "000.000.000-00",
    "descricao_caso": "Chamada sem assinatura, deve ser recusada.",
    "origem": "smoke-test",
}


def main():
    if not BASE:
        print("[ERRO] defina N8N_PUBLIC_URL")
        return 2

    url = BASE + CAMINHO
    req = urllib.request.Request(
        url,
        data=json.dumps(PAYLOAD).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[FALHA] webhook aceitou chamada sem assinatura: {r.status}")
            return 1
    except urllib.error.HTTPError as erro:
        print(f"[info] {url} recusou com {erro.code}")
        if erro.code in (401, 403):
            print("[PASS] smoke 2: webhook exige assinatura")
            return 0
        print(f"[FALHA] esperado 401 ou 403, veio {erro.code}")
        return 1
    except Exception as erro:
        print(f"[FALHA] erro de rede: {erro}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
