#!/usr/bin/env python3
"""
Restaura uma instância de n8n vazia a partir do que está versionado em Git, e
confere de ponta a ponta se ela voltou a funcionar.

Existe porque a instância ficou vazia duas vezes neste projeto: em outubro de
2026 a do n8n Cloud desapareceu por fim de assinatura, e a do Railway voltou
sem dados depois de um redeploy. Nas duas vezes a definição do sistema
sobreviveu, porque vive no repositório. Este script é o caminho de volta.

O que ele NÃO faz, e não deve fazer: criar credenciais. Credencial exige o
segredo, e segredo se digita na interface do n8n, não em script.

Pré-requisitos, todos na instância, feitos à mão:
  1. conta de dono criada
  2. as quatro credenciais, com os nomes exatos que o relatório abaixo cobra
  3. uma chave de API emitida em Settings > API

Uso:
    N8N_PUBLIC_URL=https://... N8N_API_KEY=... \
    JURISFLOW_WEBHOOK_SECRET=... python scripts/restaurar_instancia.py
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

# O console do Windows abre em cp1252, e este script reimprime a saida dos
# processos filhos, que tem acento. Sem isto, ele morre com UnicodeEncodeError
# no meio de uma restauracao, que e o pior momento possivel.
for fluxo in (sys.stdout, sys.stderr):
    if hasattr(fluxo, "reconfigure"):
        fluxo.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, ".."))


def achar_bash():
    """Caminho do bash a usar.

    No Windows, o `bash` que está no PATH costuma ser o lançador do WSL, em
    System32. Sem distribuição instalada ele falha com
    `execvpe(/bin/bash) failed`, e o que se quer aqui é o bash do Git for
    Windows, que já veio junto com o git.
    """
    achado = shutil.which("bash")
    candidatos = []
    if achado and "system32" not in achado.lower():
        candidatos.append(achado)
    candidatos += [
        r"C:\Program Files\Gitinash.exe",
        r"C:\Program Files (x86)\Gitinash.exe",
        "/bin/bash",
    ]
    for caminho in candidatos:
        if caminho and os.path.exists(caminho):
            return caminho
    return achado or "bash"


def ambiente_filho():
    """Ambiente dos subprocessos, com a saida forcada em UTF-8.

    Sem isto o filho escreve no cano com a codificacao do console, e o acento
    chega aqui como caractere de substituicao.
    """
    ambiente = dict(os.environ)
    ambiente["PYTHONIOENCODING"] = "utf-8"
    ambiente["PYTHONUTF8"] = "1"
    return ambiente

BASE = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
API_KEY = os.environ.get("N8N_API_KEY", "")
SEGREDO = os.environ.get("JURISFLOW_WEBHOOK_SECRET", "")

WORKFLOWS = [
    ("workflows/jurisflow-intake.json", "Case Intake Router", True),
    ("workflows/jurisflow-retencao.json", "Retenção e Expurgo", True),
    ("workflows/jurisflow-metricas.json", "Métricas", True),
]

CREDENCIAIS = [
    ("JurisFlow Webhook Signature", "Header Auth, nome do header X-Jurisflow-Signature"),
    ("OpenAI JurisFlow", "OpenAI API, chave começando com sk-"),
    ("Slack JurisFlow Bot", "Slack API, token do bot"),
    ("JurisFlow Postgres", "Postgres, valores do serviço Postgres no Railway"),
]


def chamar(metodo, caminho, corpo=None, timeout=30):
    req = urllib.request.Request(
        BASE + caminho,
        data=json.dumps(corpo).encode("utf-8") if corpo is not None else None,
        headers={"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"},
        method=metodo,
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        bruto = r.read().decode("utf-8")
        return json.loads(bruto) if bruto else {}


def titulo(n, texto):
    print(f"\n{'=' * 64}\n{n}. {texto}\n{'=' * 64}")


def verificar_pre_requisitos():
    titulo(1, "Pré-requisitos")
    faltando = [v for v in ("N8N_PUBLIC_URL", "N8N_API_KEY", "JURISFLOW_WEBHOOK_SECRET")
                if not os.environ.get(v)]
    if faltando:
        print(f"  [ERRO] defina: {', '.join(faltando)}")
        return False

    try:
        with urllib.request.urlopen(BASE + "/healthz", timeout=20) as r:
            print(f"  [ok] instância responde: {r.read().decode('utf-8')[:40]}")
    except Exception as e:
        print(f"  [ERRO] instância fora do ar: {str(e)[:80]}")
        return False

    try:
        chamar("GET", "/api/v1/workflows?limit=1")
        print("  [ok] chave de API aceita")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("  [ERRO] chave de API recusada (401).")
            print("         Emita uma nova em Settings > API e atualize N8N_API_KEY.")
        else:
            print(f"  [ERRO] API devolveu {e.code}")
        return False
    return True


def publicar():
    titulo(2, "Publicando os workflows versionados")
    ok = True
    for caminho, rotulo, _ in WORKFLOWS:
        destino = os.path.join(RAIZ, caminho)
        if not os.path.exists(destino):
            print(f"  [ERRO] não encontrei {caminho}")
            ok = False
            continue
        print(f"\n  -- {rotulo} --")
        r = subprocess.run(
            [sys.executable, os.path.join(AQUI, "deploy_workflow.py"), caminho],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=ambiente_filho(),
        )
        for linha in (r.stdout or "").strip().splitlines():
            print("    " + linha)
        if r.returncode != 0:
            ok = False
            erro = (r.stderr or "").strip().splitlines()
            if erro:
                print("    " + erro[-1][:200])
    return ok


def conferir_credenciais():
    """A API pública do n8n não lista credenciais. O que dá para inferir é quais
    nós ficaram sem vínculo depois da publicação, e é isso que vira a lista do
    que ainda falta criar na interface."""
    titulo(3, "Credenciais referenciadas pelos workflows")
    try:
        pub = chamar("GET", "/api/v1/workflows?limit=250").get("data", [])
    except Exception as e:
        print(f"  [aviso] não consegui listar: {str(e)[:80]}")
        return True

    pendentes = set()
    for w in pub:
        for no in w.get("nodes", []):
            for tipo, cred in (no.get("credentials") or {}).items():
                if not (cred or {}).get("id"):
                    pendentes.add((cred or {}).get("name") or tipo)

    for nome, descricao in CREDENCIAIS:
        marca = "FALTA " if nome in pendentes else "[ok]  "
        print(f"  {marca} {nome:32} {descricao}")
    if pendentes:
        print("\n  Crie as marcadas com FALTA na interface do n8n, com o nome exato,")
        print("  e rode este script de novo. Credencial exige segredo, e segredo não")
        print("  entra em script.")
    return not pendentes


def smoke():
    titulo(4, "Smoke tests contra a URL pública")
    try:
        r = subprocess.run(
            [achar_bash(), "tests/smoke/run_all.sh"],
            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
            errors="replace", env=ambiente_filho(),
        )
    except FileNotFoundError:
        print("  [ERRO] não encontrei um `bash` utilizável.")
        print("  No Windows, instale o Git for Windows ou rode pelo Git Bash.")
        return False

    linhas = (r.stdout or "").strip().splitlines()
    for linha in linhas:
        if any(m in linha for m in ("PASS", "FALHA", "RESULTADO", "info")):
            print("  " + linha)

    # Silêncio aqui já custou uma investigação: o relatório final dizia [--] e
    # a seção vinha vazia, sem dizer o que havia acontecido.
    if r.returncode != 0 or not linhas:
        print(f"  [ERRO] os smoke tests terminaram em código {r.returncode}.")
        for linha in (r.stderr or "").strip().splitlines()[-5:]:
            print("    " + linha)
        if not linhas:
            print("    (o comando não produziu saída alguma)")
    return r.returncode == 0


def painel():
    titulo(5, "Painel de métricas")
    req = urllib.request.Request(
        BASE + "/webhook/metricas",
        headers={"X-Jurisflow-Signature": SEGREDO},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            d = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  [aviso] endpoint de métricas não respondeu: {str(e)[:100]}")
        print("          Se o esquema não foi aplicado, rode db/migrar_tudo.sql.")
        return False

    p = d.get("painel") or {}
    print(f"  trilha: {d.get('total_trilha')} linhas | spans: {d.get('total_spans')}")
    print(f"  volume na janela: {p.get('volume')}")
    if p.get("p95_ms"):
        print(f"  p95: {p['p95_ms']} ms | erro: {p.get('pct_erro')}% | custo: US$ {p.get('usd')}")
    return True


def main():
    print("Restauração da instância a partir do repositório")
    print(f"  alvo: {BASE or '(não definido)'}")

    if not verificar_pre_requisitos():
        return 2

    ok_pub = publicar()
    ok_cred = conferir_credenciais()
    time.sleep(3)
    ok_smoke = smoke()
    ok_painel = painel()

    titulo(6, "Resultado")
    linhas = [
        ("workflows publicados", ok_pub),
        ("credenciais completas", ok_cred),
        ("smoke tests", ok_smoke),
        ("painel de métricas", ok_painel),
    ]
    for rotulo, estado in linhas:
        print(f"  [{'ok' if estado else '--'}] {rotulo}")

    if all(e for _, e in linhas):
        print("\n  Instância restaurada e verificada.")
        return 0
    print("\n  Restauração incompleta. Resolva o que está marcado e rode de novo.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
