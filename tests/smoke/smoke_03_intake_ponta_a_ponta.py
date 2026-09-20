#!/usr/bin/env python3
"""
Smoke test 3 de 3 – o caminho completo classifica e devolve protocolo.

Envia um caso sintético, com dados fictícios e nenhuma informação de pessoa real,
e confere que a resposta traz protocolo, área esperada e tempo dentro do SLA de
60 segundos que o BRIEFING.md fixa como meta de P95.

Variáveis: N8N_PUBLIC_URL, JURISFLOW_WEBHOOK_SECRET
Uso: python tests/smoke/smoke_03_intake_ponta_a_ponta.py
"""
import json
import os
import sys
import time
import urllib.request

BASE = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
SEGREDO = os.environ.get("JURISFLOW_WEBHOOK_SECRET", "")
CAMINHO = os.environ.get("INTAKE_PATH", "/webhook/intake")
SLA_SEGUNDOS = 60

CASO = {
    "nome_cliente": "Fulana de Tal Silva",
    "cpf": "111.444.777-35",
    "email": "fulana@exemplo.invalid",
    "descricao_caso": (
        "Fui demitida sem justa causa em agosto, não recebi as verbas rescisórias "
        "nem o depósito do FGTS, e o prazo para reclamar está correndo."
    ),
    "origem": "smoke-test",
}
AREA_ESPERADA = "Trabalhista"


def main():
    if not BASE or not SEGREDO:
        print("[ERRO] defina N8N_PUBLIC_URL e JURISFLOW_WEBHOOK_SECRET")
        return 2

    url = BASE + CAMINHO
    req = urllib.request.Request(
        url,
        data=json.dumps(CASO).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Jurisflow-Signature": SEGREDO},
        method="POST",
    )

    inicio = time.time()
    try:
        with urllib.request.urlopen(req, timeout=SLA_SEGUNDOS + 10) as r:
            status = r.status
            corpo = json.loads(r.read().decode("utf-8"))
    except Exception as erro:
        print(f"[FALHA] intake não respondeu: {erro}")
        return 1

    decorrido = time.time() - inicio
    print(f"[info] {status} em {decorrido:.2f}s | {json.dumps(corpo, ensure_ascii=False)}")

    problemas = []
    if status != 200:
        problemas.append(f"status {status} em vez de 200")
    if not corpo.get("protocolo", "").startswith("JF-"):
        problemas.append("resposta sem protocolo no formato JF-AAAAMMDD-XXXXXX")
    if corpo.get("area") != AREA_ESPERADA:
        problemas.append(f"área {corpo.get('area')} em vez de {AREA_ESPERADA}")
    if corpo.get("revisao_manual") is True:
        problemas.append("caso caiu em revisão manual, o classificador não reconheceu a área")
    if decorrido > SLA_SEGUNDOS:
        problemas.append(f"{decorrido:.1f}s acima do SLA de {SLA_SEGUNDOS}s")

    for p in problemas:
        print(f"[FALHA] {p}")
    if problemas:
        return 1

    print("[PASS] smoke 3: intake classificado e protocolado dentro do SLA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
