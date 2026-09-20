# Notas soltas — Téo

Coisas que eu lembro de cabeça, antes de esquecer. Não tá organizado, é despejo de cérebro mesmo.

- **API key da OpenAI precisa rotacionar URGENTE.** É a minha conta pessoal (`sk-EXEMPLO-VAZADO-...` no JSON do workflow exportado, eu sei, eu sei). Já torrei uns 30 dólares esse mês só testando. Quando alguém assumir, gera uma chave da conta corporativa, joga numa **credencial do n8n** (não no JSON!) e apaga a minha.
- **Webhook secret também tá hardcoded** no JSON (`whsec_jurisflow_teo_2025_...`). Era pra estar no `.env` e ser lido por variável. Não estava com cabeça pra mexer no header auth na hora. Desculpa.
- **CPF e nome vão sem máscara** pro Slack e pro audit. Eu sei que é dado sensível, ainda mais sendo caso jurídico (a descrição às vezes tem coisa de saúde, dívida, processo criminal...). A Dra. Heloísa do jurídico já me alertou sobre LGPD e sigilo. Não tive tempo de mascarar. Prioridade alta pra quem pegar.
- **O Switch é exact match.** Comparo a string que o GPT devolve com `Trabalhista`, `Cível`, etc., com acento e maiúscula. Se o modelo escorregar e mandar `civel` minúsculo ou `Direito Civil`, cai no fallback (que aponta pro Cível) e ninguém percebe que roteou errado. Já vi acontecer 1x num teste. Ideia: normalizar (lower, sem acento) num Code node antes do Switch, ou usar `contains`.
- **`Parse Classificação` faz `JSON.parse` cru.** Pedi pro modelo devolver JSON puro, mas LLM é LLM — uma hora ele devolve ```json ... ``` com markdown e isso quebra. Botar try/catch e um fallback (mandar pro Cível + marcar "revisar manual").
- **Urgência tá meio decorativa.** Eu classifico (`alta/média/baixa`) e só escrevo no texto do Slack. Não faz nada com isso — o ideal seria, urgência `alta`, marcar `@aqui` no canal ou abrir tarefa. Fica de evolução.
- **Audit é NoOp.** Era pra gravar num Postgres (subi um `PGHOST` no `.env.example`) ou num Airtable. Não plugei. Hoje o caso some depois de ir pro Slack, não tem histórico nem métrica.
- **Healthcheck: não tem.** A única forma de saber se o n8n tá no ar é abrindo o navegador. A Renata já perguntou "e se cair de madrugada?". Resposta honesta: ninguém vê. Pensar num ping no Slack ou UptimeRobot grátis.
- **Custo: não meço nada.** Sem dashboard de token. Com um modelo GPT pequeno da OpenAI e `maxTokens: 40` por classificação deve ser barato, mas é chute. Com 2.500 intakes/dia some.
- **Ideia de fallback com Claude (Anthropic):** se a OpenAI cair ou estourar rate limit, dava pra ter um segundo nó chamando o **Claude** (ex.: um modelo Haiku da Anthropic, barato) com o mesmo prompt de classificação. Confere os IDs de modelo e preço atuais na doc da Anthropic antes — eu não cheguei a implementar, fica como sugestão. Um nó de erro no OpenAI -> chama Claude -> segue o fluxo.
- **n8n cloud x self-host:** tô na dúvida se vale migrar pra n8n cloud (resolve uptime e backup, mas é pago e tem a questão de dado sair do Brasil). Joga essa decisão pro jurídico avaliar junto com LGPD.
- **Testes:** deixei dois scripts em `tests/` (valida o JSON e testa o roteamento com mock). É o básico do básico. Não cobre o n8n rodando de verdade.
