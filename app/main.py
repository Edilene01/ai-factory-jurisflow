"""
JurisFlow — aplicação web.

Serve duas telas e faz a ponte com o n8n:

    /          formulário de intake, a tela que a pessoa que procura o escritório usa
    /painel    painel de operação com as cinco métricas

Por que existe uma ponte, e não chamada direta do navegador. O webhook do n8n
exige o header `X-Jurisflow-Signature`, e segredo que chega ao navegador não é
segredo: qualquer pessoa o leria no código da página ou na aba de rede. A ponte
mantém o valor no servidor e nunca o devolve ao cliente. A decisão está em
docs/adr/ADR-007-aplicacao-web-com-ponte-para-o-n8n.md.

Nada do que trafega aqui é registrado em log. O corpo do intake carrega nome,
CPF e o relato do caso, que é comunicação sob sigilo profissional; gravá-lo no
log do contêiner criaria um ponto de vazamento que o mapa de dados pessoais não
prevê e que a sanitização do workflow existe para evitar.
"""
from __future__ import annotations

import os
import time
from collections import deque
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

N8N_URL = os.environ.get("N8N_PUBLIC_URL", "").rstrip("/")
SEGREDO = os.environ.get("JURISFLOW_WEBHOOK_SECRET", "")
TIMEOUT = float(os.environ.get("JURISFLOW_TIMEOUT_S", "90"))

# O intake custa uma chamada de LLM. Sem limite, uma aba aberta em laço esvazia
# o orçamento de tokens; o teto é por IP e por janela deslizante.
LIMITE_INTAKE = int(os.environ.get("JURISFLOW_RATE_INTAKE", "5"))
LIMITE_JANELA_S = int(os.environ.get("JURISFLOW_RATE_JANELA_S", "60"))

ESTATICOS = Path(__file__).parent / "static"

app = FastAPI(
    title="JurisFlow",
    description="Triagem automática de intake jurídico",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_acessos: dict[str, deque[float]] = {}


def _ip(request: Request) -> str:
    # O Railway entrega o IP real no X-Forwarded-For; o primeiro valor é o cliente.
    encaminhado = request.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


def _excedeu_limite(chave: str) -> bool:
    agora = time.monotonic()
    janela = _acessos.setdefault(chave, deque())
    while janela and agora - janela[0] > LIMITE_JANELA_S:
        janela.popleft()
    if len(janela) >= LIMITE_INTAKE:
        return True
    janela.append(agora)
    return False


def _configurado() -> bool:
    return bool(N8N_URL and SEGREDO)


@app.get("/healthz")
async def saude() -> JSONResponse:
    return JSONResponse({"status": "ok", "n8n_configurado": _configurado()})


@app.post("/api/intake")
async def intake(request: Request) -> JSONResponse:
    if not _configurado():
        raise HTTPException(503, "Serviço não configurado: faltam N8N_PUBLIC_URL ou o segredo.")

    if _excedeu_limite(_ip(request)):
        raise HTTPException(
            429,
            f"Muitas solicitações. Aguarde e tente de novo em até {LIMITE_JANELA_S} segundos.",
        )

    try:
        corpo = await request.json()
    except Exception:
        raise HTTPException(400, "Corpo da requisição não é JSON válido.")

    faltando = [c for c in ("nome_cliente", "cpf", "descricao_caso") if not str(corpo.get(c, "")).strip()]
    if faltando:
        raise HTTPException(400, f"Campos obrigatórios ausentes: {', '.join(faltando)}.")

    # origem é sempre definida aqui, e não aceita do cliente: ela alimenta a
    # métrica de volume por canal, e deixá-la editável permitiria poluir a série.
    corpo["origem"] = "aplicacao-web"

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            r = await cliente.post(
                f"{N8N_URL}/webhook/intake",
                json=corpo,
                headers={"X-Jurisflow-Signature": SEGREDO},
            )
    except httpx.TimeoutException:
        raise HTTPException(504, "A triagem demorou mais do que o esperado. Tente novamente.")
    except httpx.HTTPError:
        raise HTTPException(502, "Não foi possível falar com o serviço de triagem.")

    if r.status_code >= 400:
        # O corpo da resposta do n8n pode conter detalhe interno; o cliente
        # recebe apenas o fato, e o diagnóstico fica no painel de execuções.
        raise HTTPException(502, "O serviço de triagem recusou a solicitação.")

    return JSONResponse(r.json())


@app.get("/api/metricas")
async def metricas(desde: str | None = None) -> JSONResponse:
    if not _configurado():
        raise HTTPException(503, "Serviço não configurado.")

    params = {"desde": desde} if desde else None
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cliente:
            r = await cliente.get(
                f"{N8N_URL}/webhook/metricas",
                params=params,
                headers={"X-Jurisflow-Signature": SEGREDO},
            )
    except httpx.HTTPError:
        raise HTTPException(502, "Não foi possível obter as métricas.")

    if r.status_code >= 400:
        raise HTTPException(502, "O serviço de métricas recusou a solicitação.")

    return JSONResponse(r.json())


@app.get("/")
async def pagina_intake() -> FileResponse:
    return FileResponse(ESTATICOS / "index.html")


@app.get("/painel")
async def pagina_painel() -> FileResponse:
    return FileResponse(ESTATICOS / "painel.html")


app.mount("/static", StaticFiles(directory=ESTATICOS), name="static")
