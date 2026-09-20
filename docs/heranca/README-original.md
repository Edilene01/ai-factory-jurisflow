# jurisflow-intake (n8n)

Fala, pessoal. Esse é o roteador de **intake de casos** do formulário do site. Roda em n8n. Subi a v0.2 ontem (19/02), tá funcionando. Quem pegar isso depois de mim: lê as `docs/notas-teo.md`, deixei tudo que lembrava lá.

## O que faz

Pega o webhook do formulário → joga no GPT pra classificar **área jurídica + urgência** → manda pro canal certo no Slack. No fim tem um nó de "audit" que **ainda é NoOp** (era pra ser Postgres, não deu tempo).

Áreas e canais:

| Área         | Canal Slack            |
|--------------|------------------------|
| Trabalhista  | `#juris-trabalhista`   |
| Cível        | `#juris-civel`         |
| Tributário   | `#juris-tributario`    |
| Criminal     | `#juris-criminal` (prioridade) |
| Consumidor   | `#juris-consumidor`    |

Urgência: `alta`, `média`, `baixa` (vai no texto da mensagem do Slack).

Fluxo dos nós:
`Webhook Site Form` → `OpenAI Classificar` → `Parse Classificação` → `Switch Área` → 5x `Slack` (+ branch paralelo pro `Audit`).

## Rodar

```bash
cp .env.example .env   # preenche os tokens (ou não, veja a dívida técnica abaixo...)
docker compose up
```

Abre em http://localhost:5678 e importa o workflow de `workflows/jurisflow-intake-v0.json`
(menu **... > Import from File**). No 1º acesso o n8n pede pra criar uma conta de dono (email/senha local) — o antigo **admin/admin** foi removido no n8n v1/v2.

Depois de importar, clica no workflow e ativa no botão **Active** (canto superior direito), senão o webhook dá 404.

## Testar

Tem `curl` pronto em `docs/teste-manual.md`. Exemplos de caso pra estressar o classificador em `docs/exemplos-intakes.md`.

Tem também uns scripts de validação em `tests/` (Python) — valida o JSON do workflow e testa a lógica de roteamento com um LLM **mockado** (não chama a OpenAI de verdade):

```bash
python tests/validate_workflow.py
python -m pytest tests/test_routing.py -v   # ou: python tests/test_routing.py
```

## Dívida técnica herdada

Sejamos honestos, isso aqui é protótipo. O que **NÃO está resolvido** (e o time novo vai ter que atacar):

- **Chave da OpenAI VAZADA no JSON do workflow.** Tá hardcoded em `workflows/jurisflow-intake-v0.json` (`sk-EXEMPLO-VAZADO-...`). É a minha conta pessoal. **Rotaciona URGENTE** e move pra credencial do n8n / `.env`.
- **Webhook secret hardcoded** no mesmo JSON (`whsec_jurisflow_teo_2025_...`). Mesma história, tira de lá.
- **n8n sem hardening de produção.** O mirror local já usa conta de dono do n8n e porta só no loopback, mas falta o resto pra produção: TLS/HTTPS, gestão de credenciais fora do JSON e controle de acesso.
- **Sem tratamento de erro.** Se a OpenAI der timeout ou devolver algo fora do JSON esperado, o nó `Parse Classificação` faz `JSON.parse` sem try/catch e o workflow quebra. Sem retry, sem fila morta.
- **Sem monitoramento e sem controle de custo.** Ninguém mede consumo de token. Não sei quanto isso gasta por dia (chutaria uns poucos dólares, mas é chute).
- **PII em texto puro.** Nome do cliente e **CPF vão sem máscara** na mensagem do Slack e passam pelo nó de audit. Isso é dado sensível + sigilo profissional. LGPD vai pegar no pé.
- **Só localhost.** `WEBHOOK_URL=http://localhost:5678/`. Não escala, e o formulário de produção não consegue alcançar.
- **Switch frágil (exact match).** O `Switch Área` compara a string **exata** que sai do GPT (`Cível` com acento, maiúscula). Se o modelo devolver `cível`, `Civel` ou `civil`, cai no fallback (output Cível) e roteia errado em silêncio.
- **Audit é NoOp.** O nó no fim não grava nada. Era pra ser Postgres/Airtable.
- **Zero teste de verdade no workflow.** Os scripts em `tests/` que deixei são um começo bem básico, não cobrem o fluxo real no n8n.

> Pra quem vai evoluir: **não joga fora, refatora.** O esqueleto serve. O que falta é hardening, observabilidade e LGPD.

## Obs

- Se a OpenAI der timeout, aumenta o `timeout` no node (já tá em 30s).
- Se o Slack der erro de credencial, confere o `SLACK_BOT_TOKEN` no `.env` e dá `docker compose restart`.
- Pensei em usar **Claude (Anthropic)** como fallback de classificação se a OpenAI cair — anotei a ideia em `docs/notas-teo.md`, mas não cheguei a plugar.

Qualquer coisa, eu já não respondo mais o Slack daqui. Sorry. Boa sorte.

— Téo
