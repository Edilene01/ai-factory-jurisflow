# Auditoria do protótipo herdado – JurisFlow Case Intake Router

**Projeto:** JurisFlow (legaltech). Stack herdada: n8n + LLM + Slack
**Repositório de origem:** `wmonteiro-ai/ai-factory-jurisflow`
**Commit auditado:** `30275a6` ("Hardening do mirror n8n local (docker-compose)")
**Versão do workflow:** v0.2 (`versionId: v0.2.0`, `lastUpdated: 2026-02-19`)
**Data da auditoria:** 18/09/2026
**Autora:** Edilene Chagas Faria
**Etapa:** 1 – Escolha e adoção do protótipo

---

## 1. Objetivo e escopo

Esta auditoria retrata o protótipo **como ele foi recebido**, antes de qualquer alteração. A intenção não é criticar quem construiu, e sim registrar o ponto de partida com precisão suficiente para que qualquer decisão posterior possa ser justificada e comparada.

O escopo cobre os treze arquivos versionados no repositório de origem, com atenção especial ao `workflows/jurisflow-intake-v0.json`, que concentra a lógica de negócio. Foram examinados também o histórico do Git, os dois scripts de teste e a documentação deixada pelo engenheiro anterior.

Ficaram de fora, por indisponibilidade de acesso: o workspace Slack de produção, a conta OpenAI utilizada, o formulário do site que origina os webhooks e qualquer métrica real de execução. Onde a análise depende desses elementos, o texto sinaliza a limitação.

## 2. Método

O trabalho seguiu quatro passos: leitura do README e do BRIEFING.md, que trazem respectivamente a voz de quem saiu e a de quem vai cobrar; inspeção linha a linha do JSON do workflow; varredura do histórico do Git em busca de credenciais; e execução mental do fluxo contra os casos de teste do próprio repositório.

Cada achado recebeu um identificador, uma severidade e a citação do arquivo e da linha em que se sustenta. A severidade segue quatro níveis: **Crítico** para o que anula a entrega ou expõe dado pessoal de imediato, **Alto** para o que quebra em produção ou descumpre a LGPD, **Médio** para o que degrada a operação sem interrompê-la e **Baixo** para dívida de organização.

## 3. O sistema como ele está hoje

O workflow tem dez nós e um caminho feliz bastante curto:

```
Webhook Site Form → OpenAI Classificar → Parse Classificação → Switch Área → 5 nós Slack
                                              └──────────────→ Audit (NoOp)
```

O webhook recebe `POST /intake` com os campos `nome_cliente`, `cpf`, `email` e `descricao_caso`. A descrição segue para o modelo, que devolve um JSON com área e urgência. Um *Code node* faz o parse e reanexa os dados pessoais vindos do webhook. O Switch encaminha para um dos cinco canais do Slack, ao passo que o ramo paralelo de auditoria termina em um nó que não faz absolutamente nada.

A escala declarada no BRIEFING.md é de aproximadamente 2.500 formulários por dia, com orçamento operacional de US$ 120 por mês e meta de classificação em até 60 segundos no percentil 95.

## 4. Achados

### 4.1 Segredos e gestão de credenciais

**SEC-01 – Chave de API da OpenAI commitada no repositório. Severidade: Crítico.**
A chave está escrita como parâmetro do nó de classificação, em `workflows/jurisflow-intake-v0.json`, linha 31. O nome da credencial associada, na linha 58, confirma a origem: "OpenAI Téo (pessoal - ROTACIONAR!)". A varredura do histórico mostra que o valor aparece em ambos os commits do repositório, de modo que remover a linha no *working tree* não resolve, pois o segredo permanece recuperável em qualquer clone. Vale registrar que o valor plantado é fictício, embora o padrão de vazamento seja idêntico ao de uma chave real e o critério de anulação da etapa não distinga um caso do outro.

**SEC-02 – Segredo do webhook em texto puro. Severidade: Crítico.**
O header de autenticação `X-Jurisflow-Signature` carrega o valor `whsec_jurisflow_teo_2025_TROCAR_ANTES_DA_PROD` na linha 16 do mesmo arquivo. Quem tiver o JSON consegue forjar chamadas ao endpoint de intake, o que significa injetar casos falsos nos canais dos advogados ou, pior, consumir orçamento de LLM em requisições maliciosas.

**SEC-03 – Endereço corporativo do responsável anterior exposto. Severidade: Baixo.**
O campo `meta.owner`, linha 322, traz o e-mail funcional do engenheiro que saiu. É dado de contato profissional, sem gravidade comparável aos anteriores, porém não há razão para mantê-lo em repositório público.

**SEC-04 – Ausência de procedimento de rotação. Severidade: Alto.**
O `.env.example` avisa que a chave precisa ser trocada, mas em nenhum lugar existe o passo a passo de como fazê-lo, quem autoriza e com que periodicidade. Sem isso, a rotação vira decisão individual de quem lembrar.

### 4.2 Proteção de dados pessoais e sigilo profissional

Este é o bloco mais delicado do projeto, porque o dado tratado não é apenas pessoal: a descrição do caso jurídico é comunicação protegida por sigilo profissional, e frequentemente carrega informação de saúde, dívida ou persecução penal, categorias que a Lei nº 13.709/2018 trata com rigor adicional.

**PRIV-01 – CPF e nome trafegam sem máscara para o Slack. Severidade: Crítico.**
Os cinco nós de Slack montam a mensagem com `Cliente: {{$json.nome_cliente}} | CPF: {{$json.cpf}}` seguido da descrição integral do caso, nas linhas 118, 140, 162, 184 e 206. O dado sensível fica então retido no histórico de um sistema de mensageria de terceiro, acessível a qualquer integrante do canal e sujeito à política de retenção do Slack, não à da JurisFlow.

**PRIV-02 – O nó de parse reanexa todos os dados pessoais ao fluxo. Severidade: Alto.**
O *Code node* da linha 64 recupera `nome_cliente`, `cpf`, `email` e `descricao_caso` do webhook e os propaga adiante. Não há aqui qualquer filtro, tokenização ou pseudonimização, razão pela qual toda etapa posterior passa a carregar o pacote completo de identificação.

**PRIV-03 – Descrição do caso enviada íntegra ao provedor de LLM. Severidade: Alto.**
A linha 40 injeta `{{$json.body.descricao_caso}}` diretamente no prompt do usuário. Como o processamento ocorre fora do Brasil, configura-se transferência internacional de dados, hipótese que exige base legal própria e documentação. Nada disso existe no repositório.

**PRIV-04 – Persistência silenciosa de execuções com dado sensível. Severidade: Alto.**
As configurações `saveExecutionProgress: true` e `saveManualExecutions: true`, linhas 314 e 315, fazem o n8n gravar o *payload* de cada execução no banco interno, CPF e descrição do caso inclusive. Não há política de retenção, expurgo ou anonimização associada, de sorte que o volume cresce indefinidamente em um repositório que ninguém monitora. Este achado não aparece nas notas do engenheiro anterior, e é provavelmente o vazamento mais silencioso do protótipo.

**PRIV-05 – Trilha de auditoria inexistente. Severidade: Alto.**
O nó `Audit (TODO Postgres/Airtable)`, linha 224, é um `noOp` sem parâmetro algum. Na prática, depois que a mensagem chega ao Slack o caso deixa de existir para o sistema. Não há como responder quem tratou o quê, em quanto tempo e a que custo, embora o BRIEFING.md exija justamente auditoria persistente com rastreio de custo.

### 4.3 Confiabilidade e tratamento de erro

**CONF-01 – `JSON.parse` sem tratamento. Severidade: Crítico.**
A linha 64 faz `JSON.parse(raw)` direto sobre a resposta do modelo. O próprio código traz um `FIXME` admitindo o problema. Basta o modelo devolver a resposta embrulhada em markdown, comportamento comum, para o nó lançar exceção e derrubar a execução inteira.

**CONF-02 – Truncamento provável por limite de tokens. Severidade: Alto.**
O parâmetro `maxTokens: 40`, linha 46, foi calibrado para caber o JSON de saída. A margem é estreita, e qualquer resposta ligeiramente mais longa chega truncada, o que alimenta diretamente o CONF-01. Um teste de carga com casos reais deve medir a frequência disso antes de qualquer ajuste.

**CONF-03 – Roteamento errado em silêncio. Severidade: Crítico.**
O `Switch Área` compara *strings* exatas, com acento e maiúscula, nas linhas 79 a 102, e o `fallbackOutput` é `1`, que corresponde ao canal Cível. Toda classificação que escape do formato previsto, seja "civel" sem acento, seja "Direito Civil", termina no canal Cível sem alerta nenhum. O impacto é assimétrico: um caso criminal com prazo vencendo pode aterrissar em um canal que não o trata, e o nó criminal é justamente o que aciona o *subteam* de plantão. O teste `test_switch_fragil_cai_no_fallback`, em `tests/test_routing.py`, linha 106, documenta o defeito e afirma o comportamento errado como esperado, o que o transforma em teste de regressão do *bug*, não de proteção contra ele.

**CONF-04 – Resposta ao formulário antes do processamento. Severidade: Médio.**
O webhook usa `responseMode: "onReceived"`, linha 8. O site recebe sucesso no instante em que o *payload* chega, independentemente do que aconteça depois. Falha na OpenAI, falha no parse, falha no Slack: para o cliente que preencheu o formulário, tudo correu bem. É a origem do problema de negócio descrito no BRIEFING.md, o de casos que somem na caixa de entrada.

**CONF-05 – Ausência de *retry*, fila morta e *error workflow*. Severidade: Alto.**
Nenhum nó define política de repetição, e o bloco `connections`, linhas 232 a 309, não prevê saída de erro. Uma indisponibilidade momentânea da OpenAI ou do Slack simplesmente descarta o caso.

**CONF-06 – Fallback de provedor apenas idealizado. Severidade: Médio.**
O `.env.example` reserva `ANTHROPIC_API_KEY` e as notas sugerem o Claude como segunda opção de classificação, porém o workflow tem um único caminho para a OpenAI. Hoje o provedor é ponto único de falha.

### 4.4 Deploy, operação e custo

**OPS-01 – O sistema só existe em `localhost`. Severidade: Crítico para a Etapa 1.**
O `docker-compose.yml` fixa `WEBHOOK_URL=http://localhost:5678/` e publica a porta apenas no *loopback*. A escolha faz sentido para um espelho local, no entanto significa que o formulário de produção jamais alcança o endpoint. Como a etapa vale metade da nota em deploy e automação, este é o achado que define o maior volume de trabalho.

**OPS-02 – Rótulo de produção sem produção correspondente. Severidade: Médio.**
O workflow está marcado com a *tag* `prod`, linha 328, e com `active: true`, linha 311, enquanto roda em máquina pessoal. A nomenclatura sugere um ambiente que não existe, e não há separação alguma entre desenvolvimento e produção, tampouco *secrets* distintos por ambiente.

**OPS-03 – Nenhuma automação de entrega. Severidade: Alto.**
Não existe diretório `.github/`, nem *pipeline*, nem qualquer forma de publicar o workflow sem importação manual pela interface do n8n. Todo *deploy* depende de alguém abrindo o menu e clicando em "Import from File".

**OPS-04 – Sistema sem observabilidade. Severidade: Alto.**
Não há *healthcheck*, alerta ou painel. Conforme as notas do engenheiro anterior, a única maneira de saber se o serviço está no ar é abrir o navegador, e a pergunta "e se cair de madrugada?" continua sem resposta.

**OPS-05 – Custo não medido contra orçamento apertado. Severidade: Alto.**
Nenhum token é contabilizado. Com 2.500 intakes diários e teto de US$ 120 mensais, a margem por classificação é de aproximadamente US$ 0,0016, o que torna a medição condição para qualquer decisão de modelo. Sem instrumentação, a escolha de provedor vira palpite.

**OPS-06 – Identificador de modelo fixo no JSON. Severidade: Médio.**
O valor `gpt-5.4-mini`, linha 30, está embutido no workflow. Além de exigir verificação junto à documentação do provedor, impede trocar de modelo sem editar e reimportar o arquivo, o que atrapalha qualquer teste comparativo de custo e qualidade.

### 4.5 Qualidade, versionamento e documentação

**QUAL-01 – Cobertura de teste apenas estrutural. Severidade: Médio.**
`tests/validate_workflow.py` carrega o JSON e confere a presença dos nós esperados, sem subir servidor nem chamar API. `tests/test_routing.py` exercita a lógica de roteamento com LLM simulado. Nenhum dos dois toca o n8n em execução, razão pela qual o fluxo real nunca foi testado de ponta a ponta.

**QUAL-02 – Versionamento fora de padrão. Severidade: Médio.**
O `CHANGELOG.md` é uma lista informal por autor, sem datas nem seções de tipo de mudança. O repositório não tem *tag* SemVer nem *release* publicado, e a única marca de versão vive dentro do JSON, no campo `versionId`. O histórico tem dois commits, com mensagens descritivas, mas fora do padrão de *conventional commits*.

**QUAL-03 – README que documenta a saída, não o sistema. Severidade: Médio.**
O arquivo atual é honesto e útil como confissão de dívida técnica, embora não sirva como documentação de produto: não descreve o problema de negócio, não traz arquitetura e termina com um pedido de desculpas. Precisará ser reescrito por inteiro.

**QUAL-04 – Nenhum registro de decisão arquitetural. Severidade: Médio.**
Não existem ADRs nem diagramas. Toda escolha de stack feita até aqui é implícita, o que impede avaliar o que foi considerado e descartado.

## 5. Quadro-resumo

| ID | Achado | Severidade | Evidência |
|---|---|---|---|
| SEC-01 | Chave OpenAI commitada, presente no histórico | Crítico | workflow, l. 31 e 58 |
| SEC-02 | Segredo do webhook em texto puro | Crítico | workflow, l. 16 |
| SEC-03 | E-mail corporativo do responsável anterior exposto | Baixo | workflow, l. 322 |
| SEC-04 | Sem procedimento de rotação de credenciais | Alto | `.env.example` |
| PRIV-01 | CPF e nome sem máscara nos cinco canais do Slack | Crítico | workflow, l. 118-206 |
| PRIV-02 | Parse reanexa todos os dados pessoais ao fluxo | Alto | workflow, l. 64 |
| PRIV-03 | Descrição sigilosa enviada íntegra ao provedor | Alto | workflow, l. 40 |
| PRIV-04 | Execuções persistidas com CPF, sem retenção definida | Alto | workflow, l. 314-315 |
| PRIV-05 | Auditoria inexistente, nó `noOp` | Alto | workflow, l. 224 |
| CONF-01 | `JSON.parse` sem tratamento de erro | Crítico | workflow, l. 64 |
| CONF-02 | `maxTokens: 40` com margem de truncamento | Alto | workflow, l. 46 |
| CONF-03 | Switch exato com fallback silencioso para Cível | Crítico | workflow, l. 79-105 |
| CONF-04 | Resposta ao formulário antes do processamento | Médio | workflow, l. 8 |
| CONF-05 | Sem *retry*, fila morta ou fluxo de erro | Alto | workflow, l. 232-309 |
| CONF-06 | Provedor único, *fallback* apenas idealizado | Médio | `.env.example` |
| OPS-01 | Sistema restrito a `localhost` | Crítico | `docker-compose.yml` |
| OPS-02 | *Tag* `prod` sem ambiente correspondente | Médio | workflow, l. 311 e 328 |
| OPS-03 | Nenhuma automação de *deploy* | Alto | ausência de `.github/` |
| OPS-04 | Sem *healthcheck*, alerta ou painel | Alto | `docs/notas-teo.md` |
| OPS-05 | Custo de token não medido | Alto | `docs/notas-teo.md` |
| OPS-06 | Modelo fixado no JSON | Médio | workflow, l. 30 |
| QUAL-01 | Testes não cobrem o fluxo real | Médio | `tests/` |
| QUAL-02 | Sem SemVer, *release* ou *conventional commits* | Médio | `CHANGELOG.md`, histórico |
| QUAL-03 | README não documenta o sistema | Médio | `README.md` |
| QUAL-04 | Nenhuma ADR ou diagrama | Médio | ausência de `docs/adr/` |

Totalizam-se seis achados críticos, onze altos, oito médios e um baixo.

## 6. Leitura geral

O esqueleto do protótipo é defensável, e a orientação da disciplina de evoluir em vez de reescrever me parece acertada: o desenho de webhook, classificação, roteamento e auditoria resolve o problema certo, tanto que o time de negócio já opera em cima dele.

O que falta está em três camadas bem delimitadas. A primeira é de segurança e conformidade, onde ficam os segredos versionados e o tratamento de dado coberto por sigilo, e é a camada que anula a entrega se ignorada. A segunda é de confiabilidade, porque o sistema falha calado em pelo menos três pontos distintos, sendo o roteamento silencioso para o Cível o mais perigoso deles, já que produz um erro que ninguém percebe e que atinge exatamente os casos urgentes. A terceira é de operação, que responde por metade da nota da etapa e hoje simplesmente não existe, uma vez que nada roda fora da máquina de quem construiu.

Há ainda um ponto que merece registro à parte. O teste `test_switch_fragil_cai_no_fallback` transformou um defeito conhecido em comportamento esperado, e essa é uma armadilha sutil: ao corrigir o roteamento, a suíte vai acusar falha onde houve acerto. O teste precisa ser reescrito junto com a correção, sob pena de o *bug* ser restaurado por quem confiar no verde da suíte.

## 7. Fila de trabalho derivada

A ordem abaixo segue o risco, não a facilidade.

1. Rotacionar a chave da OpenAI e o segredo do webhook, e publicar o repositório a partir de um histórico limpo, com `gitleaks detect` executado antes. Resolve SEC-01, SEC-02 e SEC-03, e afasta o critério de anulação.
2. Publicar o sistema em URL pública com ambientes separados e *secrets* distintos, atacando OPS-01 e OPS-02.
3. Blindar o caminho de erro: `try/catch` no parse, normalização antes do Switch, *retry* e destino para o que falhar. Cobre CONF-01, CONF-03 e CONF-05.
4. Mascarar CPF e nome antes de qualquer saída, seja para o LLM, seja para o Slack, endereçando PRIV-01 a PRIV-03.
5. Automatizar a entrega com GitHub Actions e cobrir o fluxo com três *smoke tests* reais, o que resolve OPS-03 e QUAL-01.
6. Reescrever README, CHANGELOG e versionamento, publicar *release* e registrar as decisões em ADR, fechando QUAL-02 a QUAL-04.

Os itens de observabilidade, custo, retenção e auditoria persistente, ou seja, PRIV-04, PRIV-05, OPS-04 e OPS-05, permanecem mapeados aqui, embora pertençam ao escopo da Etapa 2.

## 8. Limitações desta auditoria

Três pontos ficaram fora do alcance. Não foi possível medir latência, taxa de erro ou custo real, porque não há histórico de execução disponível. A verificação do identificador de modelo `gpt-5.4-mini` depende da documentação vigente do provedor no momento da adoção. Por fim, a avaliação da qualidade da classificação exigiria um conjunto rotulado de casos reais, que o repositório não fornece: `docs/exemplos-intakes.md` traz apenas exemplos para estressar o classificador manualmente.
