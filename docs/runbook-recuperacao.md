# Runbook — instância vazia ou perdida

Procedimento para pôr o JurisFlow de volta no ar quando a instância de n8n
aparece sem dados. Aconteceu duas vezes: em outubro de 2026 a instância do n8n Cloud
desapareceu por fim de assinatura, e a do Railway voltou vazia depois de um redeploy.

**Tempo estimado:** 15 minutos, quase todos na interface do n8n.

---

## O que se perde e o que não se perde

| Item | Onde vive | Sobrevive? |
|---|---|---|
| Os três workflows | Git, `workflows/` | **Sim.** Republicados por script |
| Trilha, spans e registro de purga | Postgres, serviço separado | **Sim.** Outro serviço, não é tocado |
| Esquema e views | Git, `db/` | **Sim** |
| Conta de dono do n8n | Banco do n8n | Não |
| As quatro credenciais | Banco do n8n, cifradas | Não |
| Chave de API | Banco do n8n | Não |
| Histórico de execuções | Banco do n8n | Não |

A primeira linha é a que importa. A instância evaporou duas vezes e a definição do sistema
ficou íntegra as duas vezes, porque o Git é a fonte da verdade. É o que a
[ADR-001](adr/ADR-001-manter-n8n-como-orquestrador.md) comprou.

---

## Antes de reconstruir: tente recuperar

Reconstruir é o plano B. Dois caminhos valem a tentativa, nesta ordem:

**1. Ler os logs do deploy ativo.** Leitura não muda estado e decide o resto.
Procure nas **primeiras 50 linhas**:

| Padrão | Significa |
|---|---|
| `EACCES`, `permission denied`, `SQLITE_CANTOPEN` | O banco existe e o container não lê. Rollback resolve |
| `Mismatching encryption keys` | `N8N_ENCRYPTION_KEY` não bate. Banco intacto, credenciais ilegíveis |
| Criação de tabelas, sem erro antes | Banco novo. Não há o que recuperar |

**2. Rollback para o deploy anterior.** No Railway, no serviço do n8n, aba **Deployments**,
menu de três pontos do último deploy que funcionava. O rollback também restaura as variáveis
daquele deploy, então remove as que foram adicionadas depois.

Cuidado: se `N8N_ENCRYPTION_KEY` já existia antes e o rollback a remover, o n8n gera outra e
as credenciais do banco antigo ficam ilegíveis. Confira no histórico de variáveis se ela é
recente ou antiga antes de clicar.

---

## Reconstrução, passo a passo

### Passo 1 — Conta de dono

Abra a URL da instância. Se aparecer a tela de primeiro acesso, crie a conta com e-mail e
senha. Anote onde guarda: é ela que dá acesso a tudo o mais.

### Passo 2 — As quatro credenciais

Em **Credentials → Add credential**. Os **nomes precisam ser exatos**: é por nome que o n8n
casa a credencial ao publicar o workflow, e um nome diferente deixa o nó órfão.

| Nome exato | Tipo | Valor |
|---|---|---|
| `JurisFlow Webhook Signature` | Header Auth | Nome do header `X-Jurisflow-Signature`, valor igual ao `JURISFLOW_WEBHOOK_SECRET` do ambiente |
| `OpenAI JurisFlow` | OpenAI API | Chave começando com `sk-` |
| `Slack JurisFlow Bot` | Slack API | Token do bot, começando com `xoxb-` |
| `JurisFlow Postgres` | Postgres | `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` do serviço Postgres |

**Limpe o campo de senha antes de colar.** O navegador preenche sozinho formulários com campo
`password`, e o valor que ele põe não é o do banco.

No Postgres, prefira o host interno, terminado em `.railway.internal`.

### Passo 3 — Chave de API

**Settings → API → Create an API key.** Guarde o valor; ele não é exibido de novo.

Confira que o arquivo tem **um** JWT: 2 pontos e algo em torno de 290 caracteres. Já houve o
caso de a mesma chave ser colada duas vezes, resultando em 4 pontos e 401 em toda chamada.

### Passo 4 — Esquema no Postgres

Só se o banco também for novo. No console de query do Postgres no Railway, cole
[`db/migrar_tudo.sql`](../db/migrar_tudo.sql). É idempotente: rodar de novo não causa dano.

Conferir:

```sql
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'jurisflow%'
UNION ALL
SELECT table_name FROM information_schema.views WHERE table_name LIKE 'vw_%' ORDER BY 1;
```

Devem aparecer dez nomes.

### Passo 5 — Republicar e verificar

Um comando faz o resto:

```bash
N8N_PUBLIC_URL=https://sua-instancia.up.railway.app \
N8N_API_KEY=<a nova chave> \
JURISFLOW_WEBHOOK_SECRET=<o segredo do webhook> \
python scripts/restaurar_instancia.py
```

O script publica os três workflows, ativa, aponta qual credencial ficou faltando, roda os três
*smoke tests* e consulta o painel de métricas. Ao fim, diz o que passou e o que não passou.

### Passo 6 — Variáveis de retenção

No serviço do n8n, aba **Variables**:

```
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=72
```

São as duas que executam a eliminação das 72 horas. As outras três da
[política de retenção](lgpd/politica-retencao-exclusao.md) já são impostas por workflow, nas
`settings` do JSON versionado, e valem sem depender do ambiente.

---

## Lição que ficou

**Toda mudança de variável no Railway dispara um redeploy**, e redeploy é o momento em que o
volume pode não remontar. Não é operação de rotina: trate como janela de manutenção, e
confira a instância logo depois.

Se o painel estiver mostrando *"Deploys have been paused"*, **não mexa em variável nenhuma**.
A mudança entra na fila e o serviço pode ficar entre dois estados, sem meio de voltar.
