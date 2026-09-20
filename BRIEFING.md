# Briefing Oficial — JurisFlow Tecnologia Jurídica Ltda.

**Para:** AI Automation Engineer recém-contratado(a)
**De:** Renata Continentino, Head de Produto — JurisFlow
**Data:** início deste ano
**Assunto:** Roteador de Intake de Casos — Continuidade do projeto

---

## Quem somos

A JurisFlow é uma **legaltech brasileira** que vende software de gestão e automação para **escritórios de advocacia de médio porte** (entre 15 e 120 advogados). Hoje somos a camada de tecnologia de cerca de **180 escritórios** em 9 estados. Nossa missão cabe em uma frase, e a gente leva a sério:

> **"Nenhum caso esquecido na caixa de entrada."**

O produto que mais cresce é o **JurisFlow Intake**: o formulário de "Fale com um advogado" que os escritórios embutem no próprio site. Quando um possível cliente preenche, esse caso precisa cair na mesa da equipe certa — Trabalhista, Cível, Tributário, Criminal ou Consumidor — em minutos, não em horas. Caso parado é cliente perdido (e, às vezes, prazo perdido).

## Sua função

Você assume a posição de **AI Automation Engineer**, cargo novo, criado para profissionalizar a automação de triagem que vinha sendo tocada sozinha pelo **Téo Albuquerque**. O Téo saiu há duas semanas — foi para um concorrente — e deixou um protótipo rodando no n8n, com pouca documentação e alguns bilhetes sinceros (talvez sinceros demais) sobre o que está pela metade. A herança é sua.

## O problema

Os escritórios clientes recebem hoje, somados, cerca de **2.500 formulários de intake por dia**. Sem triagem automática, cada caso é lido e encaminhado manualmente por estagiários e pelo time de recepção dos escritórios. O tempo médio até o caso chegar no advogado responsável é de **3 a 6 horas**, e nas pontas (fim de semana, feriado) casos urgentes — uma prisão em flagrante, um prazo processual vencendo — ficam parados na caixa de entrada. Já perdemos contrato de cliente por causa disso.

## Estado do protótipo

O Téo entregou um **workflow no n8n self-host** (v0.2) que:

1. recebe o intake via **Webhook** (do formulário do site);
2. usa um **LLM (OpenAI)** para classificar **área jurídica** e **urgência** (alta/média/baixa);
3. roteia para o **canal do Slack** da equipe certa;
4. (deveria) gravar numa **tabela de auditoria** — hoje é só um nó NoOp de mentira.

**Roda**, mas: sem healthcheck, sem alerta de queda, segredos hardcoded no JSON exportado, sem mascaramento de dados pessoais, sem teste automatizado e sem nenhum controle de custo de tokens.

## O que esperamos em 12 semanas

1. **SLA de triagem automatizada de 60 segundos** (P95), do envio do formulário até a notificação no Slack, para 95% dos intakes.
2. **Auditoria real persistida** (Postgres ou Airtable) com área, urgência, custo por classificação e taxa de fallback humano.
3. **Pitch final ao Comitê de Produto** (eu, o CTO e o nosso Diretor Jurídico, que é OAB ativo) defendendo a virada para produção e o caso de negócio.

## Restrições inegociáveis

- **Orçamento de OPEX: US$ 120/mês** (inclui LLM, hosting e observabilidade).
- **Provedores permitidos:** OpenAI, Anthropic (Claude) e Google, via API. Hospedagem em Render, Railway, Fly.io ou n8n Cloud.
- **LGPD — atenção redobrada:** o payload carrega **dado pessoal e potencialmente sensível** (nome, CPF, e-mail e a *descrição do problema jurídico*, que pode revelar saúde, orientação, situação financeira ou processo criminal). Nada de PII em log externo sem mascaramento. Defina retenção e base legal com o Jurídico antes de qualquer persistência.
- **Sigilo profissional:** a relação cliente-advogado tem sigilo. Trate cada intake como confidencial — inclusive nos prompts enviados ao provedor de LLM.

Conte com o **Jurídico/DPO** (a Dra. Heloísa) e com a **Plataforma** (o Igor) como interlocutores. Estou disponível semanalmente.

Boas-vindas à JurisFlow.

— Renata
