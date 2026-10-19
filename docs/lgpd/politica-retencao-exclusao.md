# Política de retenção e exclusão

O art. 15 da LGPD encerra o tratamento quando a finalidade é alcançada, e o art. 16 manda
eliminar o dado em seguida, salvo nas hipóteses que ele mesmo ressalva. Uma política que
diga isso e pare aí não vale nada: dado não se apaga por força de documento. Esta política
fixa prazos e aponta, para cada um, o mecanismo que executa a exclusão.

**Atualizado em:** 19/10/2026

---

## 1. Prazos

| Armazenamento | Conteúdo | Ponto do mapa | Prazo | Mecanismo |
|---|---|---|---|---|
| Memória da execução | Payload completo do intake | PC-01, PC-03 | Duração da execução, teto de 120 s | `executionTimeout: 120` no workflow. Nada é escrito em disco quando a execução tem sucesso |
| `execution_entity` (Postgres do n8n) | Payload cru de execuções **com erro**, sem máscara | PC-02, PC-08 | **72 horas** | Pruning nativo do n8n, purga SQL às 03:15 e segunda purga às 04:15, fora da plataforma |
| Canais `#juris-*` do Slack | Nome e CPF mascarados, relato íntegro | PC-04, PC-06, PC-09 | **90 dias** | Política de retenção do workspace |
| `jurisflow_trilha_auditoria` | Registro pseudonimizado | PC-07 | **12 meses** | Purga SQL às 03:15 e segunda purga às 04:15, fora da plataforma |
| `jurisflow_purga_log` | Contagens das purgas executadas | — | **Não é purgado** | É a prestação de contas da própria política |

### Por que cada prazo é esse

**72 horas para o payload de erro.** É o prazo que cobre uma falha na sexta-feira à noite
descoberta na segunda de manhã. Menos do que isso perderia o caso justamente quando ninguém
está olhando; mais do que isso manteria nome e CPF sem máscara em repouso sem necessidade
correspondente. O prazo já vinha configurado no ambiente local, em
`EXECUTIONS_DATA_MAX_AGE=72`, e esta política apenas o torna explícito e o estende aos demais
ambientes.

**90 dias no Slack.** É o tempo em que um caso de triagem ainda pode ser consultado pela
equipe para entender por que foi encaminhado àquele canal. Passado o trimestre, o caso ou
virou atendimento, e vive no sistema do escritório, ou não virou, e a cópia na triagem deixa
de ter finalidade. O prazo também delimita a exposição de dado sensível em ferramenta de
terceiro, que é o fluxo de maior risco da aplicação, conforme a seção 5 da
[transferência internacional](transferencia-internacional.md).

**12 meses na trilha de auditoria.** Como o registro é pseudonimizado e não carrega nome, CPF
nem trecho do relato, o risco é baixo e o uso é legítimo e contínuo: medir latência, custo,
volume e taxa de erro exige série histórica. Doze meses permitem comparar um mês com o mesmo
mês do ano anterior, que é o ciclo natural de um escritório.

**Sem purga no registro de purga.** `jurisflow_purga_log` guarda alvo, prazo e contagem.
Não há dado pessoal nele, e apagá-lo destruiria a evidência de que a política é executada.

---

## 2. Mecanismos

### 2.1 Pruning nativo do n8n — primeira barreira

Variáveis de ambiente, já presentes no [`docker-compose.yml`](../../docker-compose.yml) e
documentadas em [`.env.example`](../../.env.example):

```
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
EXECUTIONS_DATA_SAVE_ON_ERROR=all
EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=72
```

A primeira linha é a que mais importa, e é fácil perdê-la de vista: ela determina que a
execução bem-sucedida **não grava o payload**. Sem ela, todo intake atendido com sucesso
deixaria nome, CPF e relato no banco.

**Pendência conhecida:** essas variáveis estão configuradas no ambiente local. Precisam ser
replicadas nas variáveis da instância do Railway e na de produção, quando esta for
restabelecida. Enquanto não forem, a primeira barreira existe só na máquina de quem
desenvolve, e a purga SQL passa a ser a única em operação.

### 2.2 Purga SQL agendada no n8n — segunda barreira

* Esquema: [`db/schema/001_trilha_auditoria.sql`](../../db/schema/001_trilha_auditoria.sql)
* Purga: [`db/retencao/purga_diaria.sql`](../../db/retencao/purga_diaria.sql)
* Agendamento: [`workflows/jurisflow-retencao.json`](../../workflows/jurisflow-retencao.json)

O workflow `JurisFlow - Retenção e Expurgo v1.0` roda todo dia às **03:15**, no fuso
`America/Sao_Paulo`, pelo mesmo mecanismo de todo o resto do sistema: versionado em Git e
publicado pelo *pipeline*. Ele executa os dois blocos de purga, grava a contagem em
`jurisflow_purga_log` e só avisa o canal `#juris-ops` quando houve remoção ou quando um dos
blocos não retornou contagem.

Essa última decisão é intencional. Um relatório que chega todo dia dizendo "zero removido"
deixa de ser lido em duas semanas, e um alerta que ninguém lê é pior do que alerta nenhum,
porque cria a impressão de vigilância. Nos dias sem remoção, a execução fica registrada no
histórico do n8n, que é onde se procura quando há dúvida.

O resultado esperado do bloco de execuções é **zero linha removida**, e é esse zero que prova
que o pruning nativo está de pé. Um número diferente de zero significa que a primeira
barreira caiu, e é por isso que ele merece notificação.

Rodando à mão, quando for preciso:

```bash
psql "$DATABASE_URL" -f db/retencao/purga_diaria.sql
```

**Nota sobre a própria evidência:** a purga de 72 horas apaga também as execuções do workflow
de retenção. Isso é esperado e não destrói a prova, porque a evidência durável é a linha em
`jurisflow_purga_log`, não o registro de execução do n8n.

### 2.3 Purga agendada no GitHub Actions — terceira barreira, fora da plataforma

* Definição: [`.github/workflows/retencao.yml`](../../.github/workflows/retencao.yml)
* Horário: 07:15 UTC, que é **04:15** em `America/Sao_Paulo`, uma hora depois da via do n8n
* Secret necessário: `DATABASE_URL` no *Environment* correspondente, mais `SLACK_BOT_TOKEN`
  para o alerta

As duas barreiras anteriores vivem dentro do n8n, e por isso caem junto com ele. Não é
hipótese de manual: em outubro de 2026 a instância de produção deixou de existir no n8n
Cloud, e com ela teria parado qualquer purga agendada lá dentro, sem que nada avisasse. Um
agendador hospedado fora da plataforma não compartilha esse destino.

O desenho aproveita a defasagem de uma hora para transformar a redundância em verificação:

| Resultado da execução das 04:15 | O que significa |
|---|---|
| Zero linha removida | A via do n8n rodou às 03:15 e cumpriu a sua parte. É o resultado esperado |
| Linhas removidas | A via do n8n **não** rodou. O dado foi purgado assim mesmo, e dispara alerta P2 |
| Falha na execução | Nem a segunda nem a terceira via funcionaram. Alerta P2 |

Depois da purga, o *job* ainda confere que não restou nenhum registro vencido, com as mesmas
consultas da seção 4, e falha se restar. O resumo de cada execução fica no
*GitHub Step Summary*, com ambiente, linhas removidas, registros vencidos restantes e
*commit*, o que dá uma evidência datada e pública sem depender de captura de tela.

Rodar à mão, por ambiente, pelo botão **Run workflow** na aba Actions, ou:

```bash
gh workflow run "Retenção de dados" -f ambiente=desenvolvimento
```

**O que isso custa, declarado:** o *runner* do GitHub precisa alcançar o banco, o que exige
que o Postgres aceite conexão externa e que a `DATABASE_URL` viva nos *secrets* do
*Environment*. É uma credencial a mais sob rotação e uma porta a mais no banco. A troca é
deliberada: sem ela, a política de retenção depende inteiramente de uma plataforma que já
demonstrou que pode sumir.

### 2.4 Retenção do Slack

Os canais `#juris-*` ficam sob política de retenção do workspace, configurada para **90 dias**
em *Settings & administration → Workspace settings → Message retention & deletion*, com a
exclusão automática de mensagens mais antigas.

É configuração de administrador do workspace, e não código. Por isso a evidência exigida aqui
é a captura da tela de configuração, em
[`docs/evidencias/`](../evidencias/), e não a saída de um script.

**Pendência conhecida:** a configuração ainda não foi aplicada nem capturada.

---

## 3. Exclusão a pedido do titular

Requisição do art. 18, IV ou VI. Chega ao escritório, que é o controlador, e desce ao
JurisFlow como operador. O prazo de resposta é o do art. 19: imediato em formato simplificado,
ou **15 dias** para a declaração completa.

A exclusão tem três passos, e rodar só o primeiro deixa o trabalho pela metade.

**Passo 1 — Banco.**

```bash
psql "$DATABASE_URL" -v protocolo="'JF-20261019-A1B2C3'" \
     -f db/retencao/excluir_por_protocolo.sql
```

Remove a linha da trilha de auditoria e qualquer execução com erro que ainda contenha aquele
protocolo, e grava o comprovante em `jurisflow_purga_log` com origem `requisicao_titular`.

**Passo 2 — Slack.** Localizar a mensagem pelo protocolo, na busca do workspace, e apagá-la no
canal da área. Se o caso passou por `#juris-triagem-manual` antes de ser reclassificado,
existem duas mensagens, e as duas precisam ser apagadas.

**Passo 3 — Comprovante.** Registrar no retorno ao controlador: data, protocolo, armazenamentos
alcançados e a contagem devolvida pelo passo 1.

### O que não é excluído, e por quê

O art. 16 ressalva a guarda após o término do tratamento em hipóteses específicas. Aplicadas
a este sistema:

| Item | Excluído? | Fundamento |
|---|---|---|
| Linha da trilha de auditoria | **Sim** | Nenhuma ressalva do art. 16 se aplica |
| Mensagem do Slack | **Sim** | Idem |
| Linha em `jurisflow_purga_log` | **Não** | Não contém dado pessoal: guarda alvo, prazo e contagem. É o comprovante da própria exclusão |
| Caso já convertido em atendimento no escritório | **Fora do alcance** | Tratamento do controlador, sujeito à guarda documental da advocacia |

A última linha é a que costuma gerar confusão. Excluir o registro de triagem não apaga o
processo de quem já virou cliente: ali a guarda tem outro fundamento, e o pedido deve ser
dirigido ao escritório.

---

## 4. Verificação

A política só vale se alguém conferir que ela roda. Três checagens. As duas primeiras já
rodam todo dia, dentro do *job* de
[`retencao.yml`](../../.github/workflows/retencao.yml), que falha e alerta quando o resultado
não é o esperado; ficam registradas aqui porque também servem para conferência manual, e
porque é a consulta, e não o *job*, que é a fonte da verdade.

**Mensal — a purga está rodando?**

```sql
SELECT alvo, prazo, sum(linhas_removidas) AS removidas, count(*) AS execucoes,
       max(executado_em) AS ultima
  FROM jurisflow_purga_log
 WHERE executado_em >= now() - INTERVAL '30 days'
 GROUP BY alvo, prazo;
```

Espera-se uma execução por dia para cada alvo. Menos do que isso significa workflow desativado
ou falhando em silêncio.

**Mensal — sobrou algo vencido?**

```sql
SELECT count(*) AS execucoes_vencidas
  FROM execution_entity
 WHERE "startedAt" < now() - INTERVAL '72 hours';

SELECT count(*) AS trilha_vencida
  FROM jurisflow_trilha_auditoria
 WHERE recebido_em < now() - INTERVAL '12 months';
```

Os dois devem retornar zero.

**Trimestral — o Slack está respeitando os 90 dias?** Busca por uma mensagem conhecida com
mais de 90 dias no canal de triagem. Se ela aparecer, a política do workspace foi desligada.
Esta continua manual, porque depende de configuração de administrador do workspace e não de
consulta ao banco.

O alerta das duas primeiras é P2, endereçado a quem opera a plataforma, no canal
`#juris-ops`. Não é P1 porque não há indisponibilidade para o cliente; é P2 porque há dado
pessoal permanecendo além do prazo declarado. Os *thresholds* das demais métricas são
trabalho da etapa de observabilidade, anotado no [checklist](../checklist-etapa-2.md).

---

## 5. Estado de implantação

Ser honesto sobre o que roda e o que ainda não roda é parte da política, e não uma ressalva
constrangida.

| Item | Situação |
|---|---|
| Esquema SQL das duas tabelas | **Escrito e versionado**, não aplicado a nenhum banco |
| Purga diária em SQL | **Escrita e versionada** |
| Agendamento no n8n | **Publicado** na instância em 19/10/2026, `active: false`. A ativação falha com "Credential not configured: postgres" nos dois nós de purga, e é esse o próximo passo |
| Agendamento no GitHub Actions | **Escrito e versionado**, nunca executado: falta cadastrar `DATABASE_URL` nos dois *Environments* e expor o Postgres ao *runner* |
| Variáveis de pruning no ambiente local | **Em vigor**, no `docker-compose.yml` |
| Variáveis de pruning no Railway e em produção | **Pendente** |
| Retenção de 90 dias no Slack | **Pendente**, com evidência a capturar |
| Trilha de auditoria gravando em Postgres | **Pendente**: o nó `Registro de Auditoria` ainda devolve o registro em memória. Enquanto isso, a purga da trilha roda sobre tabela vazia, e a purga de execuções, que é a que guarda dado sem máscara, roda sobre dado real |

A última linha é a dependência que separa esta política de estar plenamente em operação, e ela
depende de o ambiente estar no ar, o que hoje não está: a instância de produção no n8n Cloud
não existe mais e a de desenvolvimento está com o workflow inativo. O destravamento é o
Bloco 0 do [checklist da Etapa 2](../checklist-etapa-2.md).
