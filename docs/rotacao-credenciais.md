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

| Data | Credencial | Motivo | Responsável |
|---|---|---|---|
| `<preencher>` | `OPENAI_API_KEY` | Adoção do projeto, chave herdada exposta no JSON e no histórico | Edilene Chagas Faria |
| `<preencher>` | `JURISFLOW_WEBHOOK_SECRET` | Adoção do projeto, segredo exposto no JSON e no histórico | Edilene Chagas Faria |

## Verificação permanente

Duas barreiras impedem a reincidência. O `tests/validate_workflow.py` falha se qualquer padrão
de chave voltar ao JSON, e o `gitleaks` roda no *pipeline* a cada *push*, de modo que um
segredo commitado quebra a entrega antes de chegar a produção.
