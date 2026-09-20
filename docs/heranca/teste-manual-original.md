# Teste manual

Forma rápida de bater no webhook local sem precisar do formulário do site configurado.
Assume o n8n rodando (`docker compose up`) e o workflow **importado e ativado**.

> A URL do webhook em produção do n8n é `/webhook/<path>`. Aqui o path é `intake`.
> Durante o desenvolvimento, com o workflow aberto e em modo de teste, o n8n usa
> `/webhook-test/intake` (clica em "Listen for test event" antes). Em produção/ativo é `/webhook/intake`.

> ⚠️ **Pré-requisito no n8n 2.x — configure a credencial de Header Auth.**
> O node Webhook usa `Authentication: Header Auth`, e o n8n **não usa** o valor
> embutido no JSON — ele exige uma **credencial**. Sem ela, o webhook responde
> `500 "No authentication data defined on node!"`. No node Webhook →
> *Authentication* → **Create new credential** (Header Auth) com
> **Name** = `X-Jurisflow-Signature` e **Value** = `whsec_jurisflow_teo_2025_TROCAR_ANTES_DA_PROD`,
> salve e **republique/ative** o workflow. Aí os curls abaixo funcionam.

## Payload esperado

O formulário do site manda algo assim:

```json
{
  "nome_cliente": "Maria Souza",
  "cpf": "123.456.789-00",
  "email": "maria.souza@email.com",
  "telefone": "(11) 98888-7777",
  "descricao_caso": "Fui demitida sem justa causa e não recebi as verbas rescisórias.",
  "origem": "site-form"
}
```

## Exemplo 1 — Trabalhista (urgência média)

```bash
curl -X POST http://localhost:5678/webhook/intake \
  -H "Content-Type: application/json" \
  -H "X-Jurisflow-Signature: whsec_jurisflow_teo_2025_TROCAR_ANTES_DA_PROD" \
  -d '{
    "nome_cliente": "Maria Souza",
    "cpf": "123.456.789-00",
    "email": "maria.souza@email.com",
    "descricao_caso": "Fui demitida sem justa causa e não recebi as verbas rescisórias nem o FGTS."
  }'
```

**Esperado:** classifica como `Trabalhista`, posta em `#juris-trabalhista`.

## Exemplo 2 — Criminal (urgência alta)

```bash
curl -X POST http://localhost:5678/webhook/intake \
  -H "Content-Type: application/json" \
  -H "X-Jurisflow-Signature: whsec_jurisflow_teo_2025_TROCAR_ANTES_DA_PROD" \
  -d '{
    "nome_cliente": "João Pereira",
    "cpf": "987.654.321-00",
    "email": "joao.p@email.com",
    "descricao_caso": "Meu irmão foi preso em flagrante ontem à noite e a audiência de custódia é amanhã de manhã."
  }'
```

**Esperado:** classifica como `Criminal`, urgência `alta`, posta em `#juris-criminal` com cc do grupo.

## Exemplo 3 — Consumidor

```bash
curl -X POST http://localhost:5678/webhook/intake \
  -H "Content-Type: application/json" \
  -H "X-Jurisflow-Signature: whsec_jurisflow_teo_2025_TROCAR_ANTES_DA_PROD" \
  -d '{
    "nome_cliente": "Ana Lima",
    "cpf": "111.222.333-44",
    "email": "ana.lima@email.com",
    "descricao_caso": "Comprei uma geladeira que veio com defeito e a loja se recusa a trocar ou devolver meu dinheiro."
  }'
```

**Esperado:** classifica como `Consumidor`, posta em `#juris-consumidor`.

## Leitura do resultado

- Voltou `200` e apareceu a mensagem no canal correspondente do Slack → funcionando.
- Voltou `403` → o header `X-Jurisflow-Signature` não bate com o secret do node Webhook.
- Voltou `404` → ativa o workflow no painel do n8n (botão **Active**) ou você está no path errado (`/webhook-test/` vs `/webhook/`).
- Voltou `500` ou execução com erro → provavelmente a OpenAI devolveu algo fora do JSON e o `Parse Classificação` quebrou (dívida técnica conhecida, ver `notas-teo.md`).

Para outras categorias, troque o `descricao_caso` por algum exemplo de `exemplos-intakes.md`.
