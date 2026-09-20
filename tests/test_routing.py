#!/usr/bin/env python3
"""
Teste da lógica de classificação e roteamento com LLM mockado.

Nunca chama provedor de verdade. O MockClassifier simula a saída do modelo e as
funções abaixo reproduzem o que os nós `Parse Classificação`, `Precisa de Revisão
Manual?` e `Switch Área` fazem no n8n.

Diferença em relação ao teste herdado: o protótipo tratava o roteamento silencioso
para o Cível como comportamento esperado. Aqui esse caminho é considerado defeito,
e o que se espera é o desvio explícito para o canal de triagem manual.

    python tests/test_routing.py
    python -m pytest tests/test_routing.py -v
"""
import json
import re
import sys
import unicodedata

CANONICAS = {
    "trabalhista": "Trabalhista",
    "civel": "Cível",
    "tributario": "Tributário",
    "criminal": "Criminal",
    "consumidor": "Consumidor",
}

SINONIMOS = {
    "direito do trabalho": "trabalhista", "trabalho": "trabalhista",
    "direito civil": "civel", "civil": "civel", "familia": "civel",
    "direito tributario": "tributario", "tributos": "tributario", "fiscal": "tributario",
    "direito penal": "criminal", "penal": "criminal", "crime": "criminal",
    "direito do consumidor": "consumidor", "consumo": "consumidor", "cdc": "consumidor",
}

CANAL = {
    "trabalhista": "#juris-trabalhista",
    "civel": "#juris-civel",
    "tributario": "#juris-tributario",
    "criminal": "#juris-criminal",
    "consumidor": "#juris-consumidor",
}
CANAL_REVISAO = "#juris-triagem-manual"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return s.lower().strip()


class MockClassifier:
    """Finge ser o nó de LLM. Heurística de palavra-chave, só para o teste."""

    KEYWORDS = [
        ("Criminal", ["preso", "flagrante", "inquerito", "custodia", "crime", "estelionato"]),
        ("Trabalhista", ["demitid", "rescis", "fgts", "carteira", "hora extra", "assedio moral", "verbas"]),
        ("Tributário", ["icms", "iss", "receita", "imposto", "execucao fiscal", "malha fina", "tributo"]),
        ("Consumidor", ["defeito", "loja", "plano de saude", "garantia", "troca", "cobranca indevida"]),
        ("Cível", ["divorcio", "inventario", "vizinho", "partilha", "guarda", "contrato", "heranca"]),
    ]

    URGENCY = [
        ("alta", ["preso", "flagrante", "custodia", "amanha", "vence em", "prazo", "urgente"]),
        ("baixa", ["duvida", "queria saber", "gostaria de informacao"]),
    ]

    def classify(self, descricao: str, envelope: str = "puro") -> str:
        n = _norm(descricao)
        area = "Cível"
        for candidato, kws in self.KEYWORDS:
            if any(k in n for k in kws):
                area = candidato
                break
        urgencia = "media"
        for nivel, kws in self.URGENCY:
            if any(k in n for k in kws):
                urgencia = nivel
                break
        corpo = json.dumps({"area": area, "urgencia": urgencia}, ensure_ascii=False)
        if envelope == "markdown":
            return "```json\n" + corpo + "\n```"
        if envelope == "tagarela":
            return "Claro! Segue a classificação:\n" + corpo + "\nEspero ter ajudado."
        return corpo


def parse_classificacao(saida_llm: str) -> dict:
    """Reproduz o nó `Parse Classificação`: tolera markdown e texto extra."""
    resultado = {"area_chave": "triagem_manual", "urgencia": "media",
                 "revisao_manual": True, "motivo_revisao": ""}
    try:
        limpo = re.sub(r"```(json)?", "", str(saida_llm or "")).strip()
        inicio, fim = limpo.find("{"), limpo.rfind("}")
        if inicio == -1 or fim == -1:
            raise ValueError("resposta sem objeto JSON reconhecivel")
        dados = json.loads(limpo[inicio:fim + 1])
        area = _norm(dados.get("area"))
        chave = area if area in CANONICAS else SINONIMOS.get(area)
        urgencia = _norm(dados.get("urgencia"))
        resultado["urgencia"] = urgencia if urgencia in ("alta", "media", "baixa") else "media"
        if chave:
            resultado.update({"area_chave": chave, "revisao_manual": False})
        else:
            resultado["motivo_revisao"] = f"area nao reconhecida: {dados.get('area')}"
    except Exception as erro:
        resultado["motivo_revisao"] = f"falha ao interpretar a classificacao: {erro}"
    return resultado


def route(saida_llm: str) -> str:
    """Parse + IF de revisão + Switch, na mesma ordem do workflow."""
    d = parse_classificacao(saida_llm)
    if d["revisao_manual"]:
        return CANAL_REVISAO
    return CANAL[d["area_chave"]]


clf = MockClassifier()


def test_trabalhista():
    out = clf.classify("Fui demitida sem justa causa e não recebi as verbas rescisórias nem o FGTS.")
    assert route(out) == "#juris-trabalhista"


def test_criminal_alta():
    out = clf.classify("Meu irmão foi preso em flagrante e a audiência de custódia é amanhã.")
    d = parse_classificacao(out)
    assert d["area_chave"] == "criminal"
    assert d["urgencia"] == "alta"
    assert route(out) == "#juris-criminal"


def test_tributario():
    out = clf.classify("Recebi uma execução fiscal de ICMS e o prazo de defesa vence em 5 dias.")
    assert route(out) == "#juris-tributario"


def test_consumidor():
    out = clf.classify("Comprei uma geladeira com defeito e a loja se recusa a trocar.")
    assert route(out) == "#juris-consumidor"


def test_civel():
    out = clf.classify("Quero dar entrada no divórcio, tem partilha de apartamento e guarda.")
    assert route(out) == "#juris-civel"


def test_variacao_de_caixa_e_acento_nao_quebra_o_roteamento():
    """Regressão do defeito CONF-03: antes isso caía no Cível sem ninguém notar."""
    assert route(json.dumps({"area": "civel", "urgencia": "baixa"})) == "#juris-civel"
    assert route(json.dumps({"area": "CRIMINAL", "urgencia": "alta"})) == "#juris-criminal"
    assert route(json.dumps({"area": "Direito do Trabalho", "urgencia": "media"})) == "#juris-trabalhista"


def test_resposta_em_markdown_nao_derruba_o_fluxo():
    """Regressão do defeito CONF-01: JSON.parse cru explodia aqui."""
    out = clf.classify("Recebi uma execução fiscal de ICMS.", envelope="markdown")
    assert route(out) == "#juris-tributario"


def test_resposta_tagarela_ainda_e_aproveitada():
    out = clf.classify("Comprei uma geladeira com defeito.", envelope="tagarela")
    assert route(out) == "#juris-consumidor"


def test_area_desconhecida_vai_para_triagem_manual():
    """O caso que antes era roteado errado em silêncio agora é visível."""
    d = parse_classificacao(json.dumps({"area": "Direito Espacial", "urgencia": "alta"}))
    assert d["revisao_manual"] is True
    assert route(json.dumps({"area": "Direito Espacial", "urgencia": "alta"})) == CANAL_REVISAO


def test_resposta_vazia_nao_perde_o_caso():
    assert route("") == CANAL_REVISAO
    assert route("desculpe, não consegui classificar") == CANAL_REVISAO


def _run_standalone():
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ok = 0
    for t in testes:
        try:
            t()
            print(f"[PASS] {t.__name__}")
            ok += 1
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
    print(f"\n{ok}/{len(testes)} testes passaram.")
    return 0 if ok == len(testes) else 1


if __name__ == "__main__":
    sys.exit(_run_standalone())
