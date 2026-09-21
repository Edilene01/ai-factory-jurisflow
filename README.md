# JurisFlow Case Intake Router

Triagem automática de formulários de intake jurídico: recebe o caso, classifica área e
urgência, devolve um protocolo ao cliente e entrega o caso ao time responsável no Slack,
com a identidade do solicitante mascarada.

**URL pública:** `<preencher com a URL do ambiente de produção>`
**Status:** v1.0.0 · [CHANGELOG](CHANGELOG.md) · [Releases](../../releases)

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

Em resumo: produção no n8n Cloud e desenvolvimento em container n8n no Railway, com secrets
distintos em cada ambiente, workflow versionado em Git como fonte da verdade e publicação por
API. A ADR-003 registra por que os dois ambientes ficaram em plataformas diferentes, e o que
se perde com isso.

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

## Segurança e dado pessoal

Nenhum segredo entra no repositório. As credenciais vivem nos *secrets* da plataforma e nas
credenciais do n8n, e `tests/validate_workflow.py` falha se qualquer padrão de chave voltar
ao JSON. O procedimento de rotação está em [`docs/rotacao-credenciais.md`](docs/rotacao-credenciais.md).

A descrição do caso é comunicação coberta por sigilo profissional. Por isso o texto enviado
ao provedor de LLM passa por remoção de identificadores, o Slack recebe nome e CPF mascarados,
e a instância não persiste o *payload* de execuções bem-sucedidas. O mapa de dados pessoais,
a base legal de cada ponto de coleta e a política de retenção entram na Etapa 2.

## Operação

* *Rollback*: [`docs/rollback.md`](docs/rollback.md), com evidência de execução em [`docs/evidencias/`](docs/evidencias/).
* Incidente analisado: [`docs/post-mortem-INC-001.md`](docs/post-mortem-INC-001.md).
* Material herdado do engenheiro anterior, preservado para rastreabilidade: [`docs/heranca/`](docs/heranca/).

## Licença

MIT. Ver [LICENSE](LICENSE).
