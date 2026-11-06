# Evidência — aplicação web publicada e verificada

**Data:** 06/11/2026
**URL:** https://ai-factory-jurisflow-production.up.railway.app
**Serviço:** `ai-factory-jurisflow`, no projeto `jurisflow-dev`, ambiente `production`
**Versão:** merge do PR #9, branch `main`, imagem construída do `Dockerfile` em `app/`
**Dados:** sintéticos. CPF `111.444.777-35`, válido pelo dígito verificador e de ninguém.

---

## 1. Verificação completa

| # | Verificação | Resultado |
|---|---|---|
| 1 | `/healthz` | `{"status":"ok","n8n_configurado":true}` em 0,8 s |
| 2 | `/` e `/painel` | HTTP 200 |
| 3 | Ativos estáticos (CSS e dois JS) | HTTP 200 |
| 4 | **Segredo nos ativos servidos** | **Nenhum**, nas quatro rotas públicas |
| 5 | Intake de ponta a ponta | `JF-20261106-RKGE3V`, Trabalhista, urgência alta |
| 6 | Intake pelo navegador | `JF-20261106-05YYJ5`, Consumidor, urgência alta |
| 7 | Campos obrigatórios ausentes | HTTP 400 |
| 8 | Limite de taxa, 6ª requisição em um minuto | HTTP 429 |
| 9 | Painel contra `/api/metricas` | Números coincidem |

O caso do item 6 foi *"meu plano de saúde negou a cirurgia que o médico disse ser urgente e a
internação está marcada para a próxima semana"*. Classificado como **Consumidor** com
urgência **alta** — a área está correta e a urgência também, porque há prazo concreto.

## 2. Antes de a configuração chegar

Vale registrar o estado intermediário, porque ele mostra o comportamento desejado na falta de
configuração. Entre o deploy e a definição das variáveis, `/healthz` devolveu
`n8n_configurado: false` e as duas pontes responderam **HTTP 503** com
`"Serviço não configurado: faltam N8N_PUBLIC_URL ou o segredo"`.

A aplicação continuou servindo as telas. Falhar dizendo o que falta é melhor do que falhar
com erro obscuro, e foi uma lição cara: na Etapa 2, um `HTTP 400 Bad Request` sem corpo
custou meia tarde de diagnóstico.

## 3. Capturas

| Arquivo | Tela |
|---|---|
| [`01-intake-formulario.jpg`](../capturas/01-intake-formulario.jpg) | `/` — o formulário, com o aviso de base legal |
| [`02-intake-resultado.jpg`](../capturas/02-intake-resultado.jpg) | O cartão de protocolo, área e urgência |
| [`03-painel-operacao.jpg`](../capturas/03-painel-operacao.jpg) | `/painel` — as cinco métricas e a latência por etapa |
| [`04-limite-de-taxa.jpg`](../capturas/04-limite-de-taxa.jpg) | A mensagem de excesso de requisições |

As três primeiras foram capturadas na URL pública. A quarta é da execução local, do mesmo
*build*, porque reproduzir o 429 no navegador exigiria esgotar a cota com chamadas reais.

## 4. Janela de uptime

O enunciado da Etapa 3 é explícito: *"rode a aplicação 24h antes e deixe ligada. Documente a
janela de uptime. 'Estava no ar ontem' não conta."*

| Marco | Momento |
|---|---|
| Deploy concluído | 06/11/2026, por volta das 14:30 |
| Domínio público gerado | 06/11/2026, por volta das 15:00 |
| Variáveis definidas, serviço funcional | 06/11/2026, por volta das 15:20 |
| **Início da contagem** | **06/11/2026, 15:20** |

A contagem começa na terceira linha, e não na primeira: antes disso a aplicação servia as
telas mas não falava com o n8n, e um sistema que não faz o que promete não está no ar no
sentido que a rubrica pede.

Conferir o uptime a qualquer momento:

```bash
curl -s https://ai-factory-jurisflow-production.up.railway.app/healthz
```

## 5. O que esta evidência não cobre

* **Não houve 24 horas corridas ainda.** A janela começou hoje; a verificação de estabilidade exige voltar amanhã.
* **O limite de taxa é por processo, e não compartilhado.** Se o Railway escalar o serviço para mais de uma réplica, cada uma terá o próprio contador e o teto efetivo multiplica. Com uma réplica, que é a configuração atual, o teto vale como está.
* **Não há teste de carga sobre a aplicação.** As 200 requisições da linha de base foram disparadas direto contra o webhook do n8n, e não pela ponte.
