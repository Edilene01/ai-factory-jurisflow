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
`f7f6cd8 feat: adota o prototipo JurisFlow e publica a versao 1.0.0`, de 21/09/2026, e são
coerentes com os horários de geração dos arquivos de credencial mantidos fora do repositório.
Confirme cada uma no painel do provedor correspondente antes de usar este quadro como prova
em avaliação externa: o histórico de rotação só tem valor se cada linha puder ser verificada
na origem.

## Prazos que vencem

Assinatura não é credencial, mas falha do mesmo jeito: vence em silêncio e derruba o sistema
sem emitir erro de aplicação. Em outubro de 2026 a instância de produção no n8n Cloud deixou
de existir por término de assinatura, e nada no repositório percebeu. A ADR-004 registra a
decisão e manda anotar o prazo aqui, ao lado das credenciais, porque é onde se olha.

| Assinatura | Ambiente | Situação | Consequência de falhar |
|---|---|---|---|
| Railway Hobby | produção | **Ativa desde 19/10/2026.** Renova mensalmente, US$ 5 mais o uso que exceder o crédito incluído | A instância hiberna ou é removida, a URL pública cai e o deploy em `main` para |
| Railway Hobby | desenvolvimento | Mesmo plano, environment próprio. Serviço mantido **parado** fora das janelas de uso | Com o serviço parado, o deploy em `develop` falha por não alcançar a instância. É esperado, não é incidente |

O período de teste chegou a 2 dias de saldo antes da assinatura, e teria derrubado produção
pela segunda vez em um mês. A lição que fica é a mesma da [ADR-004](adr/ADR-004-reconstruir-producao-no-n8n-cloud.md):
o que vence em silêncio precisa de um lugar onde alguém olhe. Cartão vencido ou cobrança
recusada produzem exatamente o mesmo efeito que o fim do período de teste.

Desde a [ADR-005](adr/ADR-005-railway-nos-dois-ambientes.md) as duas instâncias estão no
mesmo fornecedor, o que torna a plataforma um ponto único de falha. Trocar de fornecedor não
eliminou o modo de falha de outubro, apenas o moveu, e é por isso que estas duas linhas
importam mais, e não menos, do que antes.

Confira na véspera, não no dia. A reconstrução exige recriar três credenciais e reemitir a
chave de API, e isso não se faz em cima da hora.

## Verificação permanente

Duas barreiras impedem a reincidência. O `tests/validate_workflow.py` falha se qualquer padrão
de chave voltar ao JSON, e o `gitleaks` roda no *pipeline* a cada *push*, de modo que um
segredo commitado quebra a entrega antes de chegar a produção.
