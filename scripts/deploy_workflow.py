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


def preservar_credenciais(payload, atual):
    """Recoloca no payload os ids de credencial que já existem na instância.

    Os ids são próprios de cada instalação, e por isso o JSON versionado os
    mantém vazios: gravá-los no Git amarraria o repositório a uma instância e
    faria o id de um ambiente viajar para o outro.

    O efeito colateral é que um PUT cru apaga o vínculo que existe na instância,
    e o workflow deixa de ativar com "Missing required credential". Foi o que
    aconteceu na Etapa 1, e o sintoma aparecia como divergência entre rascunho e
    versão publicada, sem erro que apontasse a causa.

    Devolve (preservados, pendentes). Pendente é credencial que o workflow pede
    e que não existe na instância, caso em que só a interface do n8n resolve,
    porque criar credencial exige o segredo.
    """
    por_no, por_tipo = {}, {}
    for no in atual.get("nodes", []):
        for tipo, cred in (no.get("credentials") or {}).items():
            cid = (cred or {}).get("id")
            if not cid:
                continue
            por_no[(no.get("name"), tipo)] = cid
            por_tipo.setdefault(tipo, cid)

    preservados, pendentes = [], []
    for no in payload.get("nodes", []):
        for tipo, cred in (no.get("credentials") or {}).items():
            if not isinstance(cred, dict) or cred.get("id"):
                continue
            # Casa primeiro pelo nó exato; se o nó é novo, herda uma credencial
            # do mesmo tipo já usada no workflow.
            cid = por_no.get((no.get("name"), tipo)) or por_tipo.get(tipo)
            if cid:
                cred["id"] = cid
                preservados.append(f"{no.get('name')}:{tipo}")
            else:
                pendentes.append(f"{no.get('name')}:{tipo}")
    return preservados, pendentes


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
        # A listagem já traz os nós, mas nem toda versão do n8n os inclui.
        if not alvo.get("nodes"):
            alvo = chamar("GET", f"/api/v1/workflows/{wid}")

        preservados, pendentes = preservar_credenciais(payload, alvo)
        if preservados:
            print(f"[ok] {len(preservados)} vínculo(s) de credencial preservados da instância")
        if pendentes:
            faltando = ", ".join(sorted(set(pendentes)))
            print(f"[nota] sem id na versão publicada: {faltando}")
            print("       o n8n ainda pode resolver pelo nome da credencial ao salvar.")
            print("       Se a ativação falhar logo abaixo, crie-a na interface.")

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
        # O corpo da resposta é onde o n8n diz qual nó impediu a ativação. Sem
        # ele, a mensagem vira um 400 sem causa, que é o pior tipo de log.
        detalhe = ""
        try:
            detalhe = json.loads(erro.read().decode("utf-8")).get("message", "")
        except Exception:
            pass
        print(f"[AVISO] não consegui ativar automaticamente: {erro.code}")
        if detalhe:
            print("        " + detalhe.replace("\n", "\n        "))
        print("        Ative pela interface depois de resolver o que está acima.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
