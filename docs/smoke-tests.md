# Smoke tests

Três testes, executados contra a URL pública a cada publicação. A pergunta que cada um
responde é diferente, e juntos cobrem o mínimo necessário para afirmar que o sistema está
operante: a instância responde, a porta de entrada está protegida e o caminho completo
funciona dentro do prazo.

Nenhum deles usa dado de pessoa real. O caso do terceiro teste é sintético, com CPF
matematicamente válido e domínio `.invalid`, reservado justamente para exemplos.

## 1. Saúde da instância

**Arquivo:** `tests/smoke/smoke_01_saude.py`
**Pergunta:** o sistema está no ar?

Bate em `/healthz` e exige 200 em menos de 10 segundos.

Passa quando a instância responde. Falha quando o serviço está reiniciando, o container caiu
ou a plataforma está indisponível. É o teste mais barato e o que dá o primeiro sinal.

```bash
N8N_PUBLIC_URL=https://... python tests/smoke/smoke_01_saude.py
```

## 2. Webhook protegido

**Arquivo:** `tests/smoke/smoke_02_webhook_protegido.py`
**Pergunta:** alguém consegue injetar casos sem credencial?

Envia um POST sem o header `X-Jurisflow-Signature` e exige recusa com 401 ou 403.

Este é o teste que protege contra regressão de segurança. Se um dia ele passar a receber 200,
significa que a autenticação do webhook foi desligada, e qualquer pessoa na internet pode
publicar casos falsos nos canais dos advogados ou consumir orçamento de LLM à vontade.

```bash
N8N_PUBLIC_URL=https://... python tests/smoke/smoke_02_webhook_protegido.py
```

## 3. Intake ponta a ponta

**Arquivo:** `tests/smoke/smoke_03_intake_ponta_a_ponta.py`
**Pergunta:** o caminho completo classifica, protocola e responde dentro do SLA?

Envia um caso trabalhista sintético com a assinatura correta e verifica quatro coisas: status
200, protocolo no formato `JF-AAAAMMDD-XXXXXX`, área igual a `Trabalhista` e tempo total
abaixo de 60 segundos, que é a meta de P95 fixada no BRIEFING.md. Também falha se o caso cair
em revisão manual, porque isso indica que o classificador não reconheceu uma descrição que
deveria ser óbvia.

```bash
N8N_PUBLIC_URL=https://... JURISFLOW_WEBHOOK_SECRET=... \
  python tests/smoke/smoke_03_intake_ponta_a_ponta.py
```

## Executar os três

```bash
N8N_PUBLIC_URL=https://... JURISFLOW_WEBHOOK_SECRET=... bash tests/smoke/run_all.sh
```

O `run_all.sh` roda tudo e devolve código de saída diferente de zero se qualquer um falhar,
o que é o que faz o *pipeline* parar. No GitHub Actions, os três rodam depois da publicação,
tanto em desenvolvimento quanto em produção.

## Observação sobre o terceiro teste

Ele realmente chama o provedor de LLM, logo tem custo, ainda que ínfimo, e depende de rede.
É uma escolha consciente: um smoke test que simula o modelo não prova que o sistema está
funcionando, prova apenas que o código compila. Se o custo virar problema quando a
instrumentação da Etapa 2 estiver pronta, a alternativa é restringir esse teste às
publicações em produção.
