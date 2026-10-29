# JurisFlow Case Intake Router

Triagem automática de formulários de intake jurídico: recebe o caso, classifica área e
urgência, devolve um protocolo ao cliente e entrega o caso ao time responsável no Slack,
com a identidade do solicitante mascarada.

**URL pública:** https://n8n-production-81314.up.railway.app/webhook/intake
*A instância anterior, no n8n Cloud, deixou de existir em outubro de 2026. A [ADR-005](docs/adr/ADR-005-railway-nos-dois-ambientes.md) registra por que produção passou para o Railway.*
**Estado da entrega:** ver [`docs/estado-da-entrega.md`](docs/estado-da-entrega.md), que registra o que está verificado e o que ainda não está
**README v1.0** · **Versão:** v1.0.0 · [CHANGELOG](CHANGELOG.md) · [Releases](../../releases)

---

## O problema

A JurisFlow atende cerca de 180 escritórios de médio porte em nove estados, e recebe algo
próximo de 2.500 formulários de intake por dia. A triagem era manual e consumia de três a
seis horas, de modo que casos urgentes envelheciam na fila enquanto alguém lia formulário
por formulário. Cliente que espera resposta e não recebe procura outro escritório, razão
pela qual o problema deixou de ser operacional e virou perda de receita.

O protótipo herdado atacava o problema certo, embora só funcionasse na máquina de quem o
construiu. A auditoria de adoção está em [`docs/auditoria-prototipo.md`](docs/auditoria-prototipo.md)
e lista 25 achados, seis deles críticos.

## A solução

Um workflow em n8n, versionado neste repositório e publicado automaticamente a cada *push*
na branch principal. O caminho de uma requisição:

1. O formulário do site envia um POST assinado para `/webhook/intake`.
2. O sistema gera um protocolo, mascara nome e CPF e remove CPF, CNPJ, e-mail e telefone do texto que será enviado ao modelo.
3. O provedor de LLM classifica área jurídica e urgência a partir da descrição sanitizada.
4. A resposta do modelo é interpretada com tolerância a markdown e a texto extra, e a área é normalizada, de modo que variação de acento ou de caixa não quebra o roteamento.
5. O site recebe de volta o protocolo, a área e a urgência.
6. O caso segue para o canal da área. O que o sistema não conseguir classificar vai para `#juris-triagem-manual`, com o motivo explícito, em vez de ser empurrado para um canal qualquer.

| Área | Canal |
|---|---|
| Trabalhista | `#juris-trabalhista` |
| Cível | `#juris-civel` |
| Tributário | `#juris-tributario` |
| Criminal | `#juris-criminal` (aciona o plantão penal) |
| Consumidor | `#juris-consumidor` |
| Não classificado | `#juris-triagem-manual` |

## Arquitetura

Os diagramas C4 estão em [`docs/architecture/`](docs/architecture/), nos níveis de contexto
e de containers. As decisões que levaram a esse desenho estão registradas em
[`docs/adr/`](docs/adr/), e a matriz que sustenta a escolha de stack em
[`docs/matriz-decisao-stack.md`](docs/matriz-decisao-stack.md).

Em resumo: produção e desenvolvimento em instâncias Railway distintas, com a mesma imagem
fixada, secrets próprios em cada ambiente, workflow versionado em Git como fonte da verdade e
publicação por API. A [ADR-005](docs/adr/ADR-005-railway-nos-dois-ambientes.md) registra por
que os dois ambientes voltaram para a mesma plataforma, o que isso recupera em paridade e o
que custa em operação. As ADR-002 a ADR-004 ficam no repositório como histórico da decisão,
e não como descrição do que está no ar.

## Como rodar localmente

Pré-requisitos: Docker, Docker Compose e Python 3.12.

```bash
git clone <url-do-repositorio>
cd ai-factory-jurisflow
cp .env.example .env          # preencha com credenciais próprias, nunca com as de produção
docker compose up -d
```

O editor abre em `http://localhost:5678`. No primeiro acesso o n8n pede para criar uma conta
de dono, com e-mail e senha locais. Em seguida:

1. Importe `workflows/jurisflow-intake.json` pelo menu **... > Import from File**.
2. Crie as credenciais que o workflow referencia, porque nenhum segredo vive dentro do JSON:
   * **Header Auth** com nome `X-Jurisflow-Signature` e o valor de `JURISFLOW_WEBHOOK_SECRET`.
   * **OpenAI API** com a chave de desenvolvimento.
   * **Slack API** com o token do bot.
3. Ative o workflow no botão **Active**, senão o webhook responde 404.

Teste rápido, com dados fictícios:

```bash
curl -X POST http://localhost:5678/webhook/intake \
  -H "Content-Type: application/json" \
  -H "X-Jurisflow-Signature: $JURISFLOW_WEBHOOK_SECRET" \
  -d '{"nome_cliente":"Fulana de Tal Silva","cpf":"111.444.777-35","descricao_caso":"Fui demitida sem justa causa e não recebi as verbas rescisórias.","origem":"teste-local"}'
```

Mais exemplos para estressar o classificador em [`docs/exemplos-intakes.md`](docs/exemplos-intakes.md).

## Testes

```bash
python tests/validate_workflow.py          # estrutura do workflow e varredura de segredos
python -m pytest tests/test_routing.py -v  # roteamento com LLM mockado, sem chamar provedor

N8N_PUBLIC_URL=https://... JURISFLOW_WEBHOOK_SECRET=... bash tests/smoke/run_all.sh
```

Os três smoke tests estão descritos em [`docs/smoke-tests.md`](docs/smoke-tests.md).

## Entrega contínua

Todo *push* em `main` roda a varredura de segredos, valida o workflow, executa os testes,
publica na instância de produção pela API do n8n e roda os smoke tests contra a URL pública.
A branch `develop` faz o mesmo contra o ambiente de desenvolvimento. Cada ambiente é um
*GitHub Environment* com o seu próprio conjunto de *secrets*, sem nenhum valor compartilhado.

Definição do *pipeline*: [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml).

Há um segundo workflow, [`retencao.yml`](.github/workflows/retencao.yml), que não participa
da entrega: ele roda em horário agendado e executa a política de retenção de dados pessoais,
descrita na seção de LGPD.

## Segurança de credenciais

Nenhum segredo entra no repositório. As credenciais vivem nos *secrets* da plataforma e nas
credenciais do n8n, e `tests/validate_workflow.py` falha se qualquer padrão de chave voltar
aos JSONs versionados. O `gitleaks` roda no *pipeline* a cada *push*, contra o histórico
completo. O procedimento e o histórico de rotação estão em
[`docs/rotacao-credenciais.md`](docs/rotacao-credenciais.md).

O trio obrigatório está no lugar: [`.env.example`](.env.example) como modelo,
[`.gitignore`](.gitignore) bloqueando `.env` e variantes, e o `.env` local fora do
versionamento. Produção e desenvolvimento são *GitHub Environments* distintos, sem nenhum
valor compartilhado entre eles.

## LGPD

A descrição do caso é comunicação coberta por sigilo profissional, e o relato pode conter
dado sensível. O tratamento está documentado em três peças:

| Documento | O que responde |
|---|---|
| [`docs/lgpd/mapa-dados-pessoais.md`](docs/lgpd/mapa-dados-pessoais.md) | Os dez pontos de coleta e tratamento, a base legal de cada um, os papéis de controlador e operador, as avaliações de legítimo interesse e os direitos do titular |
| [`docs/lgpd/transferencia-internacional.md`](docs/lgpd/transferencia-internacional.md) | Os quatro fluxos que cruzam a fronteira, a hipótese do art. 33 que os autoriza e o que falta formalizar em contrato |
| [`docs/lgpd/politica-retencao-exclusao.md`](docs/lgpd/politica-retencao-exclusao.md) | Prazos por armazenamento, o mecanismo que executa cada um e o procedimento de exclusão a pedido do titular |

Em resumo, o que o sistema faz hoje:

* **A base legal é a execução de contrato**, art. 7º, V, e não o consentimento. Quem preenche
  um intake está pedindo atendimento, e não concedendo permissão opcional. Para dado sensível,
  a base é o art. 11, II, "d", exercício regular de direitos.
* **A sanitização acontece antes da chamada ao LLM**, no nó `Sanitizar Entrada`, que remove
  CPF, CNPJ, e-mail e telefone do texto e mascara nome e CPF. O provedor nunca recebe o nome,
  o CPF nem qualquer chave de ligação com o titular. O limite conhecido dessa sanitização
  está declarado na seção 5 do mapa.
* **Toda chamada ao LLM é transferência internacional**, e a entrega no Slack também. As duas
  se apoiam no art. 33, IX, c/c art. 7º, V. A incorporação das cláusulas-padrão da
  Resolução CD/ANPD nº 19/2024 é pendência contratual registrada.
* **Execução com sucesso não grava payload** (`saveDataSuccessExecution: "none"`). Só a
  execução com erro persiste, por 72 horas.
* **A retenção tem mecanismo, e não só prazo**: esquema em [`db/schema/`](db/schema/) e purga
  em [`db/retencao/`](db/retencao/), com dois agendadores independentes. Às 03:15, o workflow
  do n8n [`jurisflow-retencao.json`](workflows/jurisflow-retencao.json); às 04:15, o
  [`retencao.yml`](.github/workflows/retencao.yml) no GitHub Actions, que roda fora da
  plataforma e não cai junto com ela. Cada purga grava a contagem em `jurisflow_purga_log`,
  e a segunda via alerta em P2 quando encontra algo para remover, porque isso significa que
  a primeira não rodou.

O estado de implantação de cada item, incluindo o que ainda não roda, está na seção 5 da
política de retenção.

## Observabilidade

Duas camadas, que respondem perguntas diferentes e não se substituem.

| Camada | Onde | Retenção | Responde |
|---|---|---|---|
| Infraestrutura | Painel do Railway, plano Hobby | 7 dias de log | O container está de pé? CPU, memória, rede, reinícios |
| Aplicação | `jurisflow_trilha_auditoria` e `jurisflow_trace_span`, em Postgres | 12 meses | O fluxo de negócio está saudável? |

Um container saudável que não classifica nenhum caso passa pela primeira camada e é pego
pela segunda. É por isso que as duas existem.

### Dashboard

**Infraestrutura:** [painel do serviço `n8n` no Railway](https://railway.com/project/92a12c78-e8f6-43c9-ba22-029f4218931f/service/52a38610-d05a-4751-87c0-315712d0b94e?environmentId=e9389aad-f152-4874-8782-8f3bb8e88849) — CPU, memória, rede, disco do
volume e contagem de requisições HTTP por faixa de status. Exige login na conta que hospeda o
projeto, e por isso os números medidos estão reproduzidos abaixo.

**Aplicação:** as *views* de [`db/metricas/vw_metricas.sql`](db/metricas/vw_metricas.sql),
com a `vw_painel_24h` resumindo as cinco métricas em uma linha. Relatório e dashboard leem da
mesma consulta, de propósito: a forma de garantir que os números batem não é conferir duas
fontes, é não ter duas.

```sql
SELECT * FROM vw_painel_24h;
```

#### Medido em 29/10/2026

Infraestrutura, última hora, do painel do Railway:

| | atual | média | máximo | limite |
|---|---|---|---|---|
| CPU | 0 vCPU (0%) | < 0,01 vCPU | 0,08 vCPU | 8,0 vCPU |
| Memória | 520 MB (6%) | 571 MB | 632 MB | 8,00 GB |
| Disco do volume | 33 MB (7%) | 33 MB | 33 MB | 500 MB |

Requisições HTTP: **227 no total**, sendo 221 em 2xx (97,4%) e 6 em 4xx (2,6%). Nenhuma 5xx.
As 4xx são os `403` do `smoke_02`, que existe justamente para provar que o webhook recusa
chamada sem assinatura.

Aplicação, sobre **978 intakes** gravados na trilha entre 20/10 e 29/10:

| Métrica | Medido | Threshold | Situação |
|---|---|---|---|
| Latência p50 | 1.023 ms | 5 s | dentro |
| Latência p95 | 1.395 ms | 60 s (SLA do briefing) | dentro, com folga de 43× |
| Latência p99 | 2.119 ms | 110 s | dentro |
| Dentro do SLA | 100,00% | — | — |
| Custo por intake | US$ 0,0000529 | projeção > US$ 30/mês | ~US$ 3,97/mês a 2.500/dia |
| Taxa de erro | 0,20% | > 1% em 1 h | dentro |
| Volume | 978 intakes | < 20% da média da mesma hora | — |
| Qualidade | 0% de revisão manual | > 15% em 24 h | dentro |

Por etapa, o que o *trace* mostra sobre onde o tempo é gasto:

| Span | p50 | p95 |
|---|---|---|
| `classificacao_llm` | 796 ms | 1.141 ms |
| `entrega_slack` | 217 ms | 275 ms |
| `parse` | 0 ms | 1 ms |
| `sanitizacao` | 0 ms | 1 ms |

A classificação domina, como o plano de instrumentação previa, e é por isso que a otimização
atacou o *prompt* e não as outras etapas: somadas, elas não chegam a 2 ms.

Distribuição por área, que é o que o alerta A-12 vigia: Cível 272, Trabalhista 260, Criminal
166, Consumidor 154 e Tributário 126. As cinco recebem.

> **O custo medido ficou abaixo do calculado.** A linha de base estimava ~US$ 0,000103 por
> intake; a medição sobre 978 execuções deu **US$ 0,0000529**, cerca de metade. A estimativa
> era conservadora na contagem de *tokens* de saída, que o teto de 60 raramente aproxima. Fica
> registrado porque o número calculado continua no `metricas-e-thresholds.md`, e dois números
> diferentes para a mesma coisa precisam de explicação, não de escolha silenciosa.

### As cinco métricas

| Métrica | Threshold | De onde sai o número |
|---|---|---|
| **Latência** p50 / p95 / p99 | 5 s / 60 s / 110 s | O p95 é o SLA contratado no briefing. O p99 fica abaixo do `executionTimeout` de 120 s, senão mediria execuções abortadas e seria taxa de erro disfarçada |
| **Custo** | > 2× a mediana de 7 dias, ou projeção mensal > US$ 30 | Linha de base calculada: ~US$ 0,000103 por intake, ~US$ 7,70/mês a 2.500/dia |
| **Erro** | > 1% em 1 h (P2), > 5% em 15 min (P1) | A 2.500/dia, 1% é pouco mais de um caso perdido por hora, e cada caso é alguém que pediu ajuda e não foi atendido |
| **Volume** | < 20% da média da mesma hora (P1) | A única métrica que detecta falha silenciosa: se o formulário parar de enviar, não há erro, há ausência |
| **Qualidade** | revisão manual > 15% em 24 h | O workflow já separa "área não reconhecida" de "resposta malformada", que têm donos diferentes |

Detalhe e justificativa de cada limite em
[`docs/observabilidade/metricas-e-thresholds.md`](docs/observabilidade/metricas-e-thresholds.md).

> ⚠️ **Os thresholds vieram de cálculo e de restrição do caso, não de demanda real.** Os
> 978 intakes medidos são carga sintética, gerada por `scripts/carga_sintetica.py` e pelos
> *smoke tests*: provam que a instrumentação mede e que o sistema cabe no SLA com folga, e não
> provam qual é o perfil de uso de um escritório de verdade. O limite de volume, em especial,
> compara cada hora com a média da mesma hora nos sete dias anteriores, e isso só passa a
> significar alguma coisa depois de uma semana de tráfego real.

### Alertas

Treze alertas catalogados em [`docs/observabilidade/alertas.md`](docs/observabilidade/alertas.md),
cada um com prioridade, público, canal e ação esperada. O público é sempre quem opera a
plataforma, no canal `#juris-ops`; o que muda é a urgência com que interrompe.

| Nível | Significa | Prazo |
|---|---|---|
| P1 | Cliente afetado agora, ou caso se perdendo em silêncio | Imediato, com menção a `@plantao-plataforma` |
| P2 | Degradação real, sem perda imediata de caso | Mesmo dia útil |
| P3 | Tendência que merece olhar | Revisão semanal |

**Implementado hoje:** o A-10, em [`.github/workflows/retencao.yml`](.github/workflows/retencao.yml).
Dispara em P2 quando a purga de retenção removeu alguma coisa — o que significa que a via do
n8n não rodou e há dado pessoal além do prazo declarado.

### Trace e spans

O *trace id* é o próprio `protocolo`. Não foi criado identificador novo: ele já é único por
intake, já atravessa o fluxo, já volta ao cliente e já é pseudônimo, o que mantém o
[mapa de dados pessoais](docs/lgpd/mapa-dados-pessoais.md) válido sem reavaliação. São sete
spans, de `recepcao` a `entrega_slack`, no esquema de
[`db/schema/002_observabilidade.sql`](db/schema/002_observabilidade.sql).

## Otimizações

### 001 — Compressão do system prompt · **aplicada e medida**

A linha de base mostrou que **90% dos tokens de entrada eram o prompt fixo**, reenviado a cada
requisição: 328 tokens por intake, dos quais a descrição do caso respondia por ~30. O prompt
foi comprimido de 1.172 para 784 caracteres, preservando o contrato de saída e os critérios.

Duas corridas consecutivas de 200 intakes, mesma semente, mesmo corpus:

| Métrica | Antes | Depois | Variação |
|---|---|---|---|
| Custo por intake | US$ 0,00005804 | US$ 0,00004573 | **−21,2%** |
| Tokens de entrada | 65.638 | 51.638 | −21,3% |
| Latência p95 | 1.443 ms | 1.266 ms | −12,3% |
| Acerto de área | 100% | 100% | — |
| Taxa de erro | 0% | 0% | — |

**O trade-off, sem maquiagem.** Custo e latência melhoraram juntos, porque menos tokens de
entrada significam menos cobrança e menos tempo — não houve sacrifício de um pelo outro. O
risco está na qualidade, e a medição não o cobre bem: o corpus tem doze descrições
inequívocas, e o lugar onde um prompt mais curto cobraria o preço é o caso ambíguo. A medição
prova que não piorou nos casos fáceis, e nada diz sobre os difíceis.

E os 21% valem **noventa centavos por mês** a 2.500 intakes diários, de US$ 4,35 para US$ 3,43.
O que justifica a mudança é o conjunto — custo, latência e manutenibilidade — e não a economia
isolada.

Análise completa, incluindo a otimização que foi **descartada por ser mensurável de forma
desonesta**, em [`docs/otimizacoes/001-compressao-do-system-prompt.md`](docs/otimizacoes/001-compressao-do-system-prompt.md).

### Candidatas registradas, não aplicadas

**Cache de classificação.** Descartada nesta etapa por um motivo de método: sobre um corpus
sintético de doze descrições repetidas, o cache acertaria ~94% das vezes e mostraria um ganho
espetacular e falso. Em produção, cada pessoa descreve o próprio caso com as próprias
palavras. Volta à mesa quando houver tráfego real para medir a repetição de verdade.

**Reconhecimento de entidades nomeadas na sanitização**, para remover nomes próprios e
endereços que a expressão regular não alcança. Ataca o risco residual declarado na seção 5 do
[mapa de dados](docs/lgpd/mapa-dados-pessoais.md).

**Fallback de provedor**, para o qual o [`.env.example`](.env.example) já reserva
`ANTHROPIC_API_KEY`. Melhora resiliência, não custo nem latência.

## Troubleshooting

Problemas que de fato aconteceram neste projeto, com o sintoma como ele aparece.

### `/webhook/intake` devolve 404

O workflow não está ativo. Webhook de workflow inativo não existe para o n8n, e 404 é a
resposta honesta. Ative pelo botão **Active** no editor, ou publique pelo
`scripts/deploy_workflow.py`, que ativa ao final.

Se a instância inteira devolver 404 com a página *"No instance here"*, não é o workflow: a
instância deixou de existir. Foi o que aconteceu com o n8n Cloud em outubro de 2026, e está
registrado na [ADR-004](docs/adr/ADR-004-reconstruir-producao-no-n8n-cloud.md).

### O deploy roda, e o workflow para de ativar com "Missing required credential"

Era o defeito mais caro do projeto. Os ids de credencial são próprios de cada instância, e o
JSON versionado os mantém vazios para não amarrar o repositório a uma instalação. Um `PUT`
cru apagava o vínculo existente, e **todo deploy automatizado desconfigurava o workflow**.

Corrigido: o `deploy_workflow.py` relê os ids da versão publicada e os recoloca antes de
enviar. Se ainda aparecer, é credencial que não existe na instância, e aí só a interface
resolve, porque criar credencial exige o segredo.

### `/webhook/intake` devolve 403 mesmo com o header

O valor da credencial *JurisFlow Webhook Signature* na instância não bate com o
`JURISFLOW_WEBHOOK_SECRET` que o chamador envia. São dois lugares, e os dois precisam ter o
mesmo valor: a credencial no n8n e o *secret* do *GitHub Environment* correspondente.

Note que o nome engana: apesar de "Signature", não há assinatura. É comparação de segredo
compartilhado, e não HMAC do corpo.

### O deploy devolve `HTTP 401 Unauthorized`

A `N8N_API_KEY` do ambiente está inválida ou foi rotacionada. Reemita em **Settings → API**
no n8n e atualize o *secret* do *Environment* certo, lembrando que `producao` e
`desenvolvimento` têm conjuntos distintos.

Em conta de período de teste do n8n Cloud a API pública não é liberada, e a chave sequer pode
ser emitida. É o que motivou a [ADR-005](docs/adr/ADR-005-railway-nos-dois-ambientes.md).

### O classificador manda tudo para triagem manual

Veja o `motivo_revisao`, que a resposta do webhook agora devolve. Dois casos já aconteceram:

*"sem objeto JSON reconhecivel | recebido: {"message":"Welcome to the OpenAI API!..."}"* — o
nó estava chamando a **raiz da API**, e não o endpoint de *chat completions*. Era o nó legado
`n8n-nodes-base.openAi` typeVersion 1, que quebra no n8n 2.40.5. Substituído por um
HTTP Request, que não muda de forma entre versões.

*"provedor retornou erro: Incorrect API key provided"* — a credencial `OpenAI JurisFlow` na
instância tem valor inválido. Chave da OpenAI começa com `sk-`; se não começar, foi colado o
valor errado. Corrija na interface do n8n.

### O agendador de retenção não ativa

`Credential not configured: postgres`. Os dois nós de purga precisam da credencial Postgres
na instância. Crie-a no n8n apontando para o banco do próprio ambiente.

### Os smoke tests não rodam no Windows

`python3` no Git Bash é o atalho da Microsoft Store, que não executa nada e ainda devolve
sucesso. O `run_all.sh` agora escolhe um interpretador que funcione; para forçar, use
`PYTHON=/caminho/do/python bash tests/smoke/run_all.sh`.

### Não há execução nenhuma no histórico do n8n

É o comportamento esperado, não defeito. `saveDataSuccessExecution: "none"` impede que
execução bem-sucedida grave o *payload*, porque ele contém nome, CPF e o relato do caso. Só
execução com erro persiste, por 72 horas.

A consequência é que depurar um caso que teve sucesso mas saiu errado exige outro caminho: a
resposta do webhook devolve `motivo_revisao`, e a trilha de auditoria guarda o registro
pseudonimizado.

### A instância some depois de algumas semanas

Assinatura encerrada. Aconteceu com o n8n Cloud em outubro de 2026 e quase se repetiu no
Railway, que chegou a 2 dias de saldo. A tabela de prazos em
[`docs/rotacao-credenciais.md`](docs/rotacao-credenciais.md) existe por isso: o que vence em
silêncio precisa de um lugar onde alguém olhe.

## Operação

* *Rollback*: [`docs/rollback.md`](docs/rollback.md), com evidência de execução em [`docs/evidencias/`](docs/evidencias/).
* Incidentes analisados: [`INC-001`](docs/post-mortem-INC-001.md), intakes perdidos por
  resposta do modelo em markdown, e [`INC-002`](docs/post-mortem-INC-002.md), nove dias no ar
  sem atender ninguém.
* Material herdado do engenheiro anterior, preservado para rastreabilidade: [`docs/heranca/`](docs/heranca/).

## Licença

MIT. Ver [LICENSE](LICENSE).
