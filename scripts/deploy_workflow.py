#!/usr/bin/env python3
"""
Publica o workflow versionado na instância de n8n do ambiente alvo.

É o que transforma "importei na mão pelo menu" em deploy automatizado: lê o JSON
do repositório, procura um workflow com o mesmo id lógico e cria ou atualiza,
ativando ao final. Chamado pelo GitHub Actions, mas roda igual na sua máquina.

Variáveis: N8N_PUBLIC_URL, N8N_API_KEY
Uso: python scripts/deploy_workflow.py [caminho-do-json]
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
API_KEY = os.environ.get("N8N_API_KEY", "")
ARQUIVO = sys.argv[1] if len(sys.argv) > 1 else "workflows/jurisflow-intake.json"

CAMPOS_ACEITOS = ("name", "nodes", "connections", "settings")


def chamar(metodo, caminho, corpo=None):
    req = urllib.request.Request(
        BASE + caminho,
        data=json.dumps(corpo).encode("utf-8") if corpo is not None else None,
        headers={"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"},
        method=metodo,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        bruto = r.read().decode("utf-8")
        return json.loads(bruto) if bruto else {}


def main():
    if not BASE or not API_KEY:
        print("[ERRO] defina N8N_PUBLIC_URL e N8N_API_KEY")
        return 2

    with open(ARQUIVO, encoding="utf-8") as f:
        wf = json.load(f)
    payload = {c: wf[c] for c in CAMPOS_ACEITOS if c in wf}
    nome = payload["name"]

    existentes = chamar("GET", "/api/v1/workflows?limit=250").get("data", [])
    alvo = next((w for w in existentes if w.get("name") == nome), None)

    if alvo:
        wid = alvo["id"]
        chamar("PUT", f"/api/v1/workflows/{wid}", payload)
        print(f"[ok] workflow '{nome}' atualizado (id {wid})")
    else:
        criado = chamar("POST", "/api/v1/workflows", payload)
        wid = criado.get("id")
        print(f"[ok] workflow '{nome}' criado (id {wid})")

    try:
        chamar("POST", f"/api/v1/workflows/{wid}/activate")
        print(f"[ok] workflow ativado, versão {wf.get('versionId', 'sem versionId')}")
    except urllib.error.HTTPError as erro:
        print(f"[AVISO] não consegui ativar automaticamente: {erro.code}. Ative pela interface.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
