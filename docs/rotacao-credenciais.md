# Rotação de credenciais

O protótipo chegou com a chave da OpenAI e o segredo do webhook escritos dentro do JSON do
workflow, e presentes em todo o histórico do Git. Este documento descreve como a rotação foi
feita na adoção e como repeti-la, porque credencial vazada sem procedimento de troca é
problema que volta.

## Quando rotacionar

* Na adoção do projeto, obrigatoriamente, antes de qualquer publicação.
* A cada 90 dias, como rotina.
* Imediatamente, sempre que uma chave aparecer em log, captura de tela, ticket ou commit.
* Quando alguém com acesso deixar o projeto.

## Inventário de credenciais

| Credencial | Onde vive | Onde se rotaciona | Impacto da troca |
|---|---|---|---|
| `OPENAI_API_KEY` | Credencial do n8n, por ambiente | Painel do provedor | Classificação para até a nova chave ser salva |
| `JURISFLOW_WEBHOOK_SECRET` | Credencial Header Auth do n8n e secret do GitHub | Gerada localmente | O formulário do site precisa ser atualizado junto |
| `SLACK_BOT_TOKEN` | Credencial do n8n | Painel de apps do Slack | Entrega nos canais para |
| `N8N_API_KEY` | Secret do GitHub, por ambiente | Interface do n8n | O deploy automatizado para |
| Credenciais do banco | Variáveis da plataforma | Painel do Railway | A instância reinicia |
| `DATABASE_URL` | Secret do GitHub, por ambiente, e credencial Postgres do n8n | Painel do Railway, junto com a senha do banco | A purga de retenção para nas duas vias. Trocar o secret do GitHub e a credencial do n8n na mesma janela |

## Procedimento

**1. Gerar a nova credencial antes de revogar a antiga.** Sobrepor evita janela de
indisponibilidade, e só o webhook exige coordenação, porque o site precisa passar a enviar o
novo valor.

```bash
# segredo do webhook
openssl rand -hex 32
```

**2. Atualizar onde o valor é consumido.** No n8n, a credencial correspondente. No GitHub, o
*secret* do ambiente certo, lembrando que `producao` e `desenvolvimento` têm conjuntos
distintos e que trocar um não troca o outro.

**3. Validar antes de revogar.** Rode os smoke tests contra o ambiente afetado:

```bash
N8N_PUBLIC_URL=... JURISFLOW_WEBHOOK_SECRET=... bash tests/smoke/run_all.sh
```

**4. Revogar a credencial antiga** no painel do provedor. Enquanto ela existir, o vazamento
continua valendo.

**5. Registrar.** Anote data, credencial trocada e motivo no quadro abaixo. Sem registro, a
rotina de 90 dias não sobrevive ao terceiro mês.

## Histórico de rotações

| Data | Credencial | Ambiente | Motivo | Responsável |
|---|---|---|---|---|
| 21/09/2026 | `OPENAI_API_KEY` | dev e prod | Adoção do projeto. Chave herdada do protótipo, exposta no JSON e em todo o histórico do Git | Edilene Chagas Faria |
| 21/09/2026 | `JURISFLOW_WEBHOOK_SECRET` | dev e prod | Adoção do projeto. Segredo exposto no JSON e no histórico. Valores distintos por ambiente, gerados com `openssl rand -hex 32` | Edilene Chagas Faria |
| 21/09/2026 | `SLACK_BOT_TOKEN` | dev e prod | Adoção do projeto. Token do protótipo substituído por app próprio | Edilene Chagas Faria |
| 21/09/2026 | `N8N_API_KEY` | dev e prod | Emissão inicial, para o deploy automatizado pelo *pipeline* | Edilene Chagas Faria |

**Rotação de rotina seguinte:** 20/12/2026, pelo ciclo de 90 dias.

### Rotação pendente

| Credencial | Ambiente | Motivo | Situação |
|---|---|---|---|
| `N8N_API_KEY` | produção | O *job* de deploy devolve `HTTP 401 Unauthorized` desde 22/09/2026, e a instância de produção no n8n Cloud deixou de existir. A chave precisa ser reemitida na instância que substituir aquela | **Em aberto**, depende do Bloco 0 da Etapa 2 |

### Observação sobre as datas

As datas acima correspondem à adoção do projeto, registrada no commit
`fb1ffa3 feat: adota o prototipo JurisFlow e publica a versao 1.0.0`, de 21/09/2026, e são
coerentes com os horários de geração dos arquivos de credencial mantidos fora do repositório.
Confirme cada uma no painel do provedor correspondente antes de usar este quadro como prova
em avaliação externa: o histórico de rotação só tem valor se cada linha puder ser verificada
na origem.

## Verificação permanente

Duas barreiras impedem a reincidência. O `tests/validate_workflow.py` falha se qualquer padrão
de chave voltar ao JSON, e o `gitleaks` roda no *pipeline* a cada *push*, de modo que um
segredo commitado quebra a entrega antes de chegar a produção.
