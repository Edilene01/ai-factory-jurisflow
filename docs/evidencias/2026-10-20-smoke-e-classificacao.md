# Evidência — smoke tests e classificação em produção

**Data:** 20/10/2026
**Ambiente:** produção, `https://n8n-production-81314.up.railway.app`
**Versão do workflow:** v1.0.5
**Dados:** sintéticos. CPF `111.444.777-35`, válido pelo dígito verificador e de ninguém; descrições de `docs/exemplos-intakes.md`.

É a primeira vez no projeto que o caminho completo executa de ponta a ponta. Até aqui, o
contador de execuções de produção marcava zero, e o `smoke_03` nunca havia passado em
ambiente nenhum.

---

## 1. Os três smoke tests

```
[info] https://n8n-production-81314.up.railway.app/healthz -> 200 em 0.95s | {"status":"ok"}
[PASS] smoke 1: instância no ar e respondendo
[info] https://n8n-production-81314.up.railway.app/webhook/intake recusou com 403
[PASS] smoke 2: webhook exige assinatura
[info] 200 em 2.52s | {"status": "recebido", "protocolo": "JF-20261020-LRQ4CF",
       "area": "Trabalhista", "urgencia": "alta", "revisao_manual": false,
       "motivo_revisao": null}
[PASS] smoke 3: intake classificado e protocolado dentro do SLA
RESULTADO: os 3 smoke tests passaram.
```

Reproduzir:

```bash
N8N_PUBLIC_URL=https://n8n-production-81314.up.railway.app \
JURISFLOW_WEBHOOK_SECRET=... \
bash tests/smoke/run_all.sh
```

## 2. Roteamento nas cinco áreas

```
esperado      obtido         urg        ms  protocolo
--------------------------------------------------------------
Trabalhista   Trabalhista    media    1740  JF-20261020-DXO1CT ok
Cível         Cível          media    1519  JF-20261020-Y1WI7O ok
Tributário    Tributário     alta     2603  JF-20261020-KLIAC2 ok
Criminal      Criminal       alta     3195  JF-20261020-DUTG2T ok
Consumidor    Consumidor     media    2103  JF-20261020-1M7M0L ok
(ambíguo)     Consumidor     media    2373  JF-20261020-T3LBAA --
--------------------------------------------------------------
6/6 conforme esperado
```

O caso ambíguo — *"Comprei um carro financiado, o banco cobrou tarifas que acho ilegais e
ainda me mandaram pro Serasa"* — foi para Consumidor, que é o que
[`exemplos-intakes.md`](../exemplos-intakes.md) registrava como tendência esperada. Não é
acerto nem erro: é caso que admite duas áreas, e a previsão do documento se confirmou.

A urgência variou com o conteúdo, e não por acaso: execução fiscal com prazo de 5 dias e
audiência de custódia no dia seguinte vieram como **alta**; os demais, como **média**. O
critério de urgência do *system prompt* está sendo aplicado.

## 3. O que estes números são, e o que não são

Sete amostras, medidas da máquina de quem desenvolve, incluindo latência de rede até o
Railway.

| Observação | Valor |
|---|---|
| Menor latência | 1.519 ms |
| Maior latência | 3.195 ms |
| Mediana aproximada | ~2.370 ms |
| Dentro do SLA de 60 s | 7 de 7 |

**Isto não é a linha de base.** Sete amostras não sustentam p95 nem p99, e o
[documento de métricas](../observabilidade/metricas-e-thresholds.md) continua marcando os
*thresholds* como provisórios. O que estes números permitem afirmar, e só isso:

* O fluxo completo funciona, da recepção à entrega.
* A ordem de grandeza da latência é de **segundos**, e não de dezenas de segundos, o que
  torna o limite de 5 s para o p50 plausível em vez de arbitrário.
* O SLA de 60 s não está em risco no caminho feliz.

A linha de base real exige tráfego acumulado e a trilha de auditoria gravando em Postgres.

## 4. Histórico: o que estava quebrado

Dois defeitos empilhados impediam a classificação, e o segundo só apareceu depois de
corrigido o primeiro.

**O nó de LLM chamava a raiz da API.** O `n8n-nodes-base.openAi` typeVersion 1 é legado e,
no n8n 2.40.5, resolvia para `https://api.openai.com/v1/` em vez do endpoint de *chat
completions*. A resposta era a mensagem de boas-vindas da OpenAI, que o parser não conseguia
interpretar, e todo caso caía em triagem manual. Substituído por HTTP Request 4.2.

**A credencial da OpenAI tinha chave inválida.** Com o endpoint certo, o provedor respondeu
`Incorrect API key provided`. Corrigido na interface do n8n.

Nenhum dos dois era visível no histórico de execuções, porque
`saveDataSuccessExecution: "none"` não persiste execução bem-sucedida, e as duas falhas
terminavam em sucesso com desvio para triagem manual. O diagnóstico só foi possível depois de
`motivo_revisao` passar a sair na resposta do webhook.

É o argumento concreto a favor da observabilidade do Bloco 2: o sistema esteve quebrado de
forma invisível, e a correção começou por tornar a falha legível.
