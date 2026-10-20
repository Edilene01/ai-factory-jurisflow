#!/usr/bin/env python3
"""
Carga sintética contra o endpoint de intake, para levantar a linha de base das
métricas e para medir o antes e o depois de uma otimização.

Por que existe: a Etapa 2 exige medição, e não estimativa. Esperar 2.500 intakes
reais por dia não é opção num projeto de disciplina, e inventar número é o que
anula a etapa. A saída é gerar tráfego sintético, medir de verdade e dizer com
todas as letras que o tráfego é sintético.

O corpus vem de docs/exemplos-intakes.md, é fictício e não contém pessoa real.
O CPF 111.444.777-35 é válido pelo dígito verificador e não pertence a ninguém.

A ordem dos casos é determinística, fixada por semente, de modo que duas
execuções comparam o mesmo conjunto. Sem isso, antes e depois mediriam corpora
diferentes e a comparação não valeria nada.

Uso:
    N8N_PUBLIC_URL=https://... JURISFLOW_WEBHOOK_SECRET=... \
        python scripts/carga_sintetica.py --n 200 --rotulo baseline

    # depois da otimização, mesmo corpus e mesma semente:
    ... python scripts/carga_sintetica.py --n 200 --rotulo pos-otimizacao

    # comparar as duas medições:
    python scripts/carga_sintetica.py --comparar baseline pos-otimizacao
"""
import argparse
import json
import os
import random
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

BASE = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
SEGREDO = os.environ.get("JURISFLOW_WEBHOOK_SECRET", "")
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "evidencias")

# Corpus fictício, com a área esperada. Serve de rótulo para medir qualidade:
# "esperado" aqui é o julgamento humano registrado em docs/exemplos-intakes.md,
# não a resposta do modelo.
CORPUS = [
    ("Trabalhista", "Fui demitida sem justa causa e nao recebi as verbas rescisorias nem o FGTS."),
    ("Trabalhista", "Trabalho ha 2 anos sem registro em carteira e o patrao nao paga hora extra."),
    ("Trabalhista", "Sofri assedio moral da minha chefe e tenho audios. Quero entrar com acao."),
    ("Cível", "Quero dar entrada no divorcio e tem partilha de um apartamento e guarda de filho."),
    ("Cível", "Meu vizinho construiu um muro que invadiu meu terreno, ja tentei conversar e nada."),
    ("Cível", "Preciso abrir inventario do meu pai que faleceu, sao tres herdeiros."),
    ("Tributário", "Recebi uma execucao fiscal de ICMS da minha empresa e o prazo de defesa vence em 5 dias."),
    ("Tributário", "A Receita caiu na malha fina e quero contestar uma multa de imposto de renda."),
    ("Criminal", "Meu irmao foi preso em flagrante ontem e a audiencia de custodia e amanha de manha."),
    ("Criminal", "Recebi uma intimacao para depor como investigado em um inquerito por estelionato."),
    ("Consumidor", "Comprei uma geladeira com defeito e a loja se recusa a trocar ou devolver o dinheiro."),
    ("Consumidor", "O plano de saude negou minha cirurgia que o medico disse ser urgente."),
]

CPF_SINTETICO = "111.444.777-35"
NOME_SINTETICO = "Fulana de Tal Silva"


def enviar(caso):
    esperado, descricao = caso
    corpo = json.dumps({
        "nome_cliente": NOME_SINTETICO,
        "cpf": CPF_SINTETICO,
        "descricao_caso": descricao,
        "origem": "carga-sintetica",
    }).encode("utf-8")

    req = urllib.request.Request(
        BASE + "/webhook/intake",
        data=corpo,
        headers={"Content-Type": "application/json", "X-Jurisflow-Signature": SEGREDO},
        method="POST",
    )
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode("utf-8"))
        ms = int((time.perf_counter() - inicio) * 1000)
        return {
            "esperado": esperado,
            "obtido": resp.get("area"),
            "urgencia": resp.get("urgencia"),
            "revisao_manual": bool(resp.get("revisao_manual")),
            "motivo": resp.get("motivo_revisao"),
            "protocolo": resp.get("protocolo"),
            "latencia_ms": ms,
            "erro": None,
        }
    except Exception as e:
        ms = int((time.perf_counter() - inicio) * 1000)
        return {"esperado": esperado, "obtido": None, "urgencia": None,
                "revisao_manual": False, "motivo": None, "protocolo": None,
                "latencia_ms": ms, "erro": str(e)[:120]}


def percentil(valores, p):
    if not valores:
        return None
    ordenados = sorted(valores)
    # Mesma definição do percentile_cont do Postgres, para que o número daqui
    # e o da view não divirjam por método.
    k = (len(ordenados) - 1) * p
    base = int(k)
    resto = k - base
    if base + 1 < len(ordenados):
        return ordenados[base] + resto * (ordenados[base + 1] - ordenados[base])
    return ordenados[base]


def resumir(rotulo, resultados, segundos):
    ok = [r for r in resultados if r["erro"] is None]
    lat = [r["latencia_ms"] for r in ok]
    acertos = [r for r in ok if r["obtido"] == r["esperado"]]
    revisao = [r for r in ok if r["revisao_manual"]]

    return {
        "rotulo": rotulo,
        "momento": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": BASE,
        "total": len(resultados),
        "sucesso": len(ok),
        "erros": len(resultados) - len(ok),
        "pct_erro": round(100.0 * (len(resultados) - len(ok)) / max(len(resultados), 1), 2),
        "duracao_s": round(segundos, 1),
        "latencia_p50_ms": round(percentil(lat, 0.50) or 0),
        "latencia_p95_ms": round(percentil(lat, 0.95) or 0),
        "latencia_p99_ms": round(percentil(lat, 0.99) or 0),
        "latencia_min_ms": min(lat) if lat else None,
        "latencia_max_ms": max(lat) if lat else None,
        "latencia_media_ms": round(statistics.mean(lat)) if lat else None,
        "pct_dentro_sla_60s": round(100.0 * len([x for x in lat if x <= 60000]) / max(len(lat), 1), 2),
        "pct_acerto_area": round(100.0 * len(acertos) / max(len(ok), 1), 2),
        "pct_revisao_manual": round(100.0 * len(revisao) / max(len(ok), 1), 2),
    }


def imprimir(s):
    print(f"\n=== {s['rotulo']} ===")
    print(f"  {s['sucesso']}/{s['total']} com sucesso em {s['duracao_s']} s")
    print(f"  latência  p50 {s['latencia_p50_ms']} ms | p95 {s['latencia_p95_ms']} ms | "
          f"p99 {s['latencia_p99_ms']} ms | máx {s['latencia_max_ms']} ms")
    print(f"  dentro do SLA de 60 s: {s['pct_dentro_sla_60s']}%")
    print(f"  taxa de erro: {s['pct_erro']}%")
    print(f"  acerto de área: {s['pct_acerto_area']}%")
    print(f"  revisão manual: {s['pct_revisao_manual']}%")


def arquivo(rotulo):
    return os.path.normpath(os.path.join(SAIDA, f"carga-{rotulo}.json"))


def rodar(n, rotulo, paralelas, semente):
    if not BASE or not SEGREDO:
        print("[ERRO] defina N8N_PUBLIC_URL e JURISFLOW_WEBHOOK_SECRET")
        return 2

    rnd = random.Random(semente)
    casos = [CORPUS[rnd.randrange(len(CORPUS))] for _ in range(n)]

    print(f"Disparando {n} intakes sintéticos contra {BASE}")
    print(f"  semente {semente}, {paralelas} em paralelo")
    print("  dados fictícios: nenhum cliente real, CPF de teste\n")

    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=paralelas) as pool:
        resultados = list(pool.map(enviar, casos))
    segundos = time.perf_counter() - inicio

    s = resumir(rotulo, resultados, segundos)
    imprimir(s)

    os.makedirs(SAIDA, exist_ok=True)
    with open(arquivo(rotulo), "w", encoding="utf-8") as f:
        json.dump({"resumo": s, "amostras": resultados}, f, ensure_ascii=False, indent=2)
    print(f"\n  bruto salvo em {arquivo(rotulo)}")

    falhas = [r for r in resultados if r["erro"]]
    if falhas:
        print(f"\n  {len(falhas)} falha(s), primeira: {falhas[0]['erro']}")
    return 0


def comparar(a, b):
    try:
        da = json.load(open(arquivo(a), encoding="utf-8"))["resumo"]
        db = json.load(open(arquivo(b), encoding="utf-8"))["resumo"]
    except FileNotFoundError as e:
        print(f"[ERRO] medição não encontrada: {e.filename}")
        return 2

    campos = [
        ("latencia_p50_ms", "latência p50 (ms)", "menor"),
        ("latencia_p95_ms", "latência p95 (ms)", "menor"),
        ("latencia_p99_ms", "latência p99 (ms)", "menor"),
        ("pct_erro", "taxa de erro (%)", "menor"),
        ("pct_acerto_area", "acerto de área (%)", "maior"),
        ("pct_revisao_manual", "revisão manual (%)", "menor"),
    ]
    print(f"\n{'métrica':24} {a:>14} {b:>14} {'variação':>12}")
    print("-" * 68)
    for chave, rotulo, melhor in campos:
        va, vb = da.get(chave), db.get(chave)
        if va is None or vb is None:
            continue
        delta = vb - va
        pct = (delta / va * 100) if va else 0
        bom = (delta < 0) if melhor == "menor" else (delta > 0)
        marca = "melhor" if (delta and bom) else ("pior" if delta else "igual")
        print(f"{rotulo:24} {va:>14} {vb:>14} {pct:>+11.1f}% {marca}")
    print("-" * 68)
    print(f"amostras: {da['total']} contra {db['total']}")
    print("\nTrade-off: leia latência, custo e qualidade juntos. Melhora em uma às")
    print("custas de outra é resultado legítimo, desde que declarada.")
    return 0


def main():
    p = argparse.ArgumentParser(description="Carga sintética para medir o intake.")
    p.add_argument("--n", type=int, default=120, help="número de intakes (padrão 120)")
    p.add_argument("--rotulo", default="baseline", help="nome da medição")
    p.add_argument("--paralelas", type=int, default=4,
                   help="requisições simultâneas (padrão 4, para não saturar a instância)")
    p.add_argument("--semente", type=int, default=42,
                   help="semente do sorteio; mantenha igual entre medições")
    p.add_argument("--comparar", nargs=2, metavar=("ANTES", "DEPOIS"))
    a = p.parse_args()

    if a.comparar:
        return comparar(*a.comparar)
    return rodar(a.n, a.rotulo, a.paralelas, a.semente)


if __name__ == "__main__":
    sys.exit(main())
