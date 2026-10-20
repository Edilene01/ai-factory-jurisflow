#!/usr/bin/env python3
"""
Validador estrutural do workflow exportado do n8n.

Não sobe servidor e não chama API. Carrega o JSON, confere que a estrutura mínima
existe e, principalmente, garante que nenhum segredo voltou para dentro do arquivo.
Herdado do protótipo do Téo e ampliado na adoção (Etapa 1).

Uso:
    python tests/validate_workflow.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKFLOW = os.path.join(HERE, "..", "workflows", "jurisflow-intake.json")
RETENCAO = os.path.join(HERE, "..", "workflows", "jurisflow-retencao.json")
PURGA_SQL = os.path.join(HERE, "..", "db", "retencao", "purga_diaria.sql")

# Padrões que nunca podem aparecer no workflow versionado.
PADROES_PROIBIDOS = [
    (r"sk-[A-Za-z0-9_\-]{12,}", "chave de API da OpenAI"),
    (r"sk-ant-[A-Za-z0-9_\-]{12,}", "chave de API da Anthropic"),
    (r"whsec_[A-Za-z0-9_\-]{6,}", "segredo de webhook"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "token do Slack"),
    (r"\"apiKey\"\s*:\s*\"[^\"]+\"", "campo apiKey preenchido"),
]

NOS_ESPERADOS = {
    "n8n-nodes-base.webhook": "Webhook de entrada",
    "n8n-nodes-base.code": "Code node",
    "n8n-nodes-base.httpRequest": "classificação por LLM, via HTTP",
    "n8n-nodes-base.switch": "roteamento por área",
    "n8n-nodes-base.slack": "entrega no Slack",
    "n8n-nodes-base.respondToWebhook": "resposta síncrona ao formulário",
    "n8n-nodes-base.if": "desvio de revisão manual",
}


def main():
    falhas = []

    with open(WORKFLOW, encoding="utf-8") as f:
        bruto = f.read()
    wf = json.loads(bruto)
    print(f"[ok] JSON parseou: {os.path.basename(WORKFLOW)}")

    nos = wf.get("nodes", [])
    conexoes = wf.get("connections", {})
    nomes = {n["name"] for n in nos}
    tipos = [n.get("type") for n in nos]

    def check(cond, msg):
        if cond:
            print(f"[ok] {msg}")
        else:
            print(f"[FALHA] {msg}")
            falhas.append(msg)

    # 1. Antivazamento: é a checagem que impede repetir o erro que anula a etapa.
    for padrao, descricao in PADROES_PROIBIDOS:
        achados = re.findall(padrao, bruto)
        check(not achados, f"sem {descricao} no arquivo versionado")

    # 2. Estrutura mínima
    check(isinstance(nos, list) and len(nos) > 0, f"nodes[] presente ({len(nos)} nós)")
    check(isinstance(conexoes, dict) and len(conexoes) > 0, "connections{} presente")
    for tipo, descricao in NOS_ESPERADOS.items():
        check(tipo in tipos, f"tem nó de {descricao}")

    # 3. Roteamento: cinco áreas mais o canal de triagem manual
    slack = [n for n in nos if n.get("type") == "n8n-nodes-base.slack"]
    check(len(slack) == 6, f"6 destinos no Slack, 5 áreas mais triagem manual (achou {len(slack)})")

    switch = next((n for n in nos if n.get("type") == "n8n-nodes-base.switch"), None)
    regras = (switch or {}).get("parameters", {}).get("rules", {}).get("values", [])
    check(len(regras) == 5, f"Switch com 5 regras de saída (achou {len(regras)})")
    # O Switch v1 aceita no máximo 4 saídas, e são cinco áreas. Com ele, a quinta
    # nunca era entregue e o n8n recusava a execução. Não pode voltar.
    check(float((switch or {}).get("typeVersion", 0)) >= 3,
          f"Switch em versão que aceita 5 saídas (typeVersion {(switch or {}).get('typeVersion')})")
    saidas = {v.get("outputKey") for v in regras}
    check(saidas == {"Trabalhista", "Civel", "Tributario", "Criminal", "Consumidor"},
          f"as cinco áreas têm saída nomeada ({sorted(saidas)})")

    # 4. O fallback silencioso do protótipo não pode voltar
    fallback = ((switch or {}).get("parameters", {}).get("options", {}) or {}).get("fallbackOutput")
    check(fallback in (None, "none"),
          "Switch sem fallback silencioso, o desvio é tratado pelo nó de revisão manual")

    # 5. Persistência de execução desligada (dado sensível não fica no banco do n8n)
    settings = wf.get("settings", {})
    check(settings.get("saveExecutionProgress") is False, "saveExecutionProgress desligado")
    check(settings.get("saveManualExecutions") is False, "saveManualExecutions desligado")
    check(settings.get("saveDataSuccessExecution") == "none",
          "execuções de sucesso não persistem payload")

    # 6. Resiliência declarada no nó de LLM
    llm = next((n for n in nos if n.get("type") == "n8n-nodes-base.httpRequest"), None)
    check((llm or {}).get("retryOnFail") is True, "nó de LLM com retry habilitado")
    # O nó legado n8n-nodes-base.openAi typeVersion 1 resolvia para a raiz da API
    # no n8n 2.40.5 e devolvia a mensagem de boas-vindas. Não pode voltar.
    check("n8n-nodes-base.openAi" not in tipos, "sem o nó legado de OpenAI, que quebra por versão")
    url = ((llm or {}).get("parameters", {}) or {}).get("url", "")
    check(url.endswith("/v1/chat/completions"), f"nó de LLM aponta para chat completions ({url or 'vazio'})")

    # 7. Integridade das conexões e unicidade de IDs
    soltas = []
    for origem, conn in conexoes.items():
        if origem not in nomes:
            soltas.append(f"origem inexistente: {origem}")
        for ramo in conn.get("main", []):
            for link in ramo:
                if link.get("node") not in nomes:
                    soltas.append(f"destino inexistente: {link.get('node')} (de {origem})")
    check(not soltas, "todas as connections referenciam nós existentes"
          + ("" if not soltas else f" -> {soltas}"))

    ids = [n.get("id") for n in nos]
    check(len(ids) == len(set(ids)), "IDs de nós são únicos")

    # 7b. Instrumentação: a medição do SLA precisa fechar DEPOIS do Slack, senão
    #     mede um pedaço do caminho e chama de ciclo completo.
    destinos_slack = {
        alvo["node"]
        for n in slack
        for ramo in conexoes.get(n["name"], {}).get("main", [])
        for alvo in ramo
    }
    check(destinos_slack == {"Montar Trilha e Spans"},
          "os 6 nós do Slack alimentam a montagem da trilha, fechando o SLA na entrega")

    pg = [n for n in nos if n.get("type") == "n8n-nodes-base.postgres"]
    check(len(pg) == 2, f"dois nós de gravação em Postgres, trilha e spans (achou {len(pg)})")
    check(all(n.get("onError") == "continueRegularOutput" for n in pg),
          "gravação de observabilidade não derruba o intake quando falha")

    montagem = next((n for n in nos if n.get("name") == "Montar Trilha e Spans"), None)
    codigo = (montagem or {}).get("parameters", {}).get("jsCode", "")
    for campo in ("duracao_total_ms", "tokens_entrada", "tokens_saida"):
        check(campo in codigo, f"trilha carrega {campo}")
    check("descricao_caso: " not in codigo and "descricao_sanitizada" not in codigo,
          "nenhum texto do caso entra na trilha, só a contagem de caracteres")

    # 8. Workflow de retenção: os prazos da política precisam estar no agendador,
    #    senão a política vira documento sem execução.
    print()
    print("-- workflow de retenção --")
    with open(RETENCAO, encoding="utf-8") as f:
        bruto_ret = f.read()
    wf_ret = json.loads(bruto_ret)
    print(f"[ok] JSON parseou: {os.path.basename(RETENCAO)}")

    for padrao, descricao in PADROES_PROIBIDOS:
        check(not re.findall(padrao, bruto_ret), f"sem {descricao} no agendador")

    tipos_ret = [n.get("type") for n in wf_ret.get("nodes", [])]
    check("n8n-nodes-base.scheduleTrigger" in tipos_ret, "tem gatilho agendado")
    check(tipos_ret.count("n8n-nodes-base.postgres") == 2,
          "tem os dois blocos de purga em Postgres")

    for prazo, alvo in (("72 hours", "execution_entity"),
                        ("12 months", "jurisflow_trilha_auditoria")):
        check(prazo in bruto_ret and alvo in bruto_ret,
              f"purga de {alvo} com prazo de {prazo}")

    check("jurisflow_purga_log" in bruto_ret,
          "cada purga grava contagem em jurisflow_purga_log")
    check(wf_ret.get("settings", {}).get("timezone") == "America/Sao_Paulo",
          "agendador com fuso explícito")

    nomes_ret = {n["name"] for n in wf_ret.get("nodes", [])}
    soltas_ret = []
    for origem, conn in wf_ret.get("connections", {}).items():
        if origem not in nomes_ret:
            soltas_ret.append(f"origem inexistente: {origem}")
        for ramo in conn.get("main", []):
            for link in ramo:
                if link.get("node") not in nomes_ret:
                    soltas_ret.append(f"destino inexistente: {link.get('node')}")
    check(not soltas_ret, "connections do agendador referenciam nós existentes"
          + ("" if not soltas_ret else f" -> {soltas_ret}"))

    # 9. Os prazos do SQL e os do agendador têm de contar a mesma história.
    with open(PURGA_SQL, encoding="utf-8") as f:
        sql = f.read()
    for prazo in ("72 hours", "12 months"):
        check(prazo in sql, f"purga_diaria.sql mantém o prazo de {prazo}")

    print()
    if falhas:
        print(f"RESULTADO: {len(falhas)} falha(s).")
        sys.exit(1)
    print("RESULTADO: workflows estruturalmente válidos e livres de segredos.")


if __name__ == "__main__":
    main()
