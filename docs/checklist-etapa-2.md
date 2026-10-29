# Checklist da Etapa 2

Entrega na semana 10. A etapa separa o protótipo do produto: segurança de credenciais,
conformidade com a LGPD, observabilidade e uma otimização **medida**. A palavra que organiza
tudo é essa: nesta etapa, número sem evidência não conta.

**Atualizado em:** 29/10/2026, depois de o sistema voltar ao ar e a v2.0.0 ser publicada.

> Estado da Etapa 1: [`estado-da-entrega.md`](estado-da-entrega.md).

## Incidente encerrado — a instância que voltou vazia

Entre 20/10 e 29/10 a instância do Railway respondeu `/healthz` em 200 com **banco vazio**:
`showSetupOnFirstLoad: True`, webhooks em 404 e API em 401. Sumiram a conta de dono, as quatro
credenciais, a chave de API e o histórico. Os dados no Postgres ficaram intactos, por serem de
outro serviço, e os workflows também, porque vivem no Git.

**Encerrado em 29/10.** A [ADR-006](adr/ADR-006-postgres-como-banco-do-n8n.md) move o n8n para
o Postgres do projeto, com `N8N_ENCRYPTION_KEY` fixada no ambiente, de modo que o estado deixa
de depender de um volume remontado a cada *deploy*. O procedimento está no
[`runbook-recuperacao.md`](runbook-recuperacao.md) e a parte automatizável no
`scripts/restaurar_instancia.py`.

Duas coisas ficam em aberto para o post-mortem, e não para este checklist: a causa raiz não
pôde ser confirmada, porque o plano Hobby guarda sete dias de log e a descoberta veio no nono;
e a demora de até nove dias para alguém perceber, que o alerta **A-02** — volume abaixo de 20%
da média da mesma hora — teria pego no mesmo dia, se estivesse implementado.

## Bloco 0 — Destravar o ambiente (pré-requisito de tudo)

Sem URL viva não há métrica, alerta nem medição de otimização.

| Item | Situação |
|---|---|
| Decidir a plataforma e registrar em ADR | **Feito.** [ADR-005](adr/ADR-005-railway-nos-dois-ambientes.md): Railway nos dois ambientes |
| Instância de produção | ✅ **No ar**, `n8n-production-81314.up.railway.app`, n8n 2.40.5 sobre Postgres |
| Workflows publicados | ✅ **Três ativos**: intake v1.3.0, retenção v1.4.1 e métricas v1.1.0 |
| URL pública | ✅ `/healthz` em 200 e `/webhook/intake` recusando chamada anônima com 403 |
| Smoke tests 1, 2 e 3 | ✅ **Passam**, e passam **dentro do próprio *pipeline***, contra a URL pública |
| Roteamento nas cinco áreas | ✅ As cinco recebem: Cível 272, Trabalhista 260, Criminal 166, Consumidor 154, Tributário 126 |
| Credenciais na instância | ✅ **As quatro**, com os nomes exatos que os workflows procuram, testadas pelo próprio n8n |
| Instância de desenvolvimento | ✅ **Existe e responde**, `n8n-development-b649.up.railway.app`, desde 19/10/2026 |
| Separação de ambientes | ✅ **Real.** Cada *Environment* aponta para a sua instância, com *secrets* próprios. A variável de `desenvolvimento` apontava para produção e foi corrigida em 29/10 |
| *Pipeline* de CI/CD | ✅ **Verde**, quatro execuções seguidas em `main`. A mais lenta levou 32 s, contra o teto de 5 min da rubrica |
| Esquema aplicado no Postgres | ✅ **Dez objetos**: 4 tabelas e 9 *views*, pelo `db/migrar_tudo.sql` |
| *Rollback* testado com evidência | ✅ **Executado em produção** nos dois sentidos, em 29/10. [`evidencias/2026-10-29-rollback.md`](evidencias/2026-10-29-rollback.md) |
| Release SemVer com CHANGELOG | ✅ **v2.0.0** publicada, com GitHub Release |
| Plano do Railway | **Hobby**, assinado em 19/10/2026 |
| Registrar a situação das assinaturas | **Feito**, tabela em [`rotacao-credenciais.md`](rotacao-credenciais.md) |
| Paridade entre os ambientes | ✅ **De plataforma, restaurada em 29/10**: os dois rodam n8n 2.40.5 sobre Postgres próprio, cada um com o seu serviço e o seu volume. ⏳ Falta repovoar o desenvolvimento — conta de dono, as quatro credenciais e os workflows —, que a troca de banco zerou, como a ADR-006 previa |
| Esquema do JurisFlow no banco de desenvolvimento | ⏳ **Pendente.** Colar [`db/migrar_tudo.sql`](../db/migrar_tudo.sql) no console de query do `Postgres-dev`, pelo passo 4 do [runbook](runbook-recuperacao.md) |

## Bloco 1 — Credenciais e LGPD (50% da nota)

| Exigência | Onde | Status |
|---|---|---|
| Trio sagrado: `.env`, `.gitignore`, `.env.example` | Raiz | **Pronto** |
| *Secrets* separados por ambiente | *GitHub Environments* `producao` e `desenvolvimento` | **Pronto** |
| Procedimento de rotação documentado | [`rotacao-credenciais.md`](rotacao-credenciais.md) | **Pronto** |
| Histórico de rotações preenchido | Idem | **Pronto** |
| Mapa de dados pessoais com base legal por ponto de coleta | [`lgpd/mapa-dados-pessoais.md`](lgpd/mapa-dados-pessoais.md) | **Pronto**: 10 pontos, 3 avaliações de legítimo interesse |
| Transferência internacional reconhecida e documentada | [`lgpd/transferencia-internacional.md`](lgpd/transferencia-internacional.md) | **Pronto**: 4 fluxos, art. 33, IX |
| Política de retenção e exclusão | [`lgpd/politica-retencao-exclusao.md`](lgpd/politica-retencao-exclusao.md) | **Pronto** |
| Mecanismo real que executa a retenção | [`db/retencao/`](../db/retencao/) e [`workflows/jurisflow-retencao.json`](../workflows/jurisflow-retencao.json) | ✅ **Ativo** na instância, agendado para 03:15 |
| Segunda via da purga, fora da plataforma | [`.github/workflows/retencao.yml`](../.github/workflows/retencao.yml) | ✅ **Executada em 29/10**, contra produção: 0 removidos, 0 vencidos restantes |
| Papel de menor privilégio para a purga | [`db/schema/003_papel_purga.sql`](../db/schema/003_papel_purga.sql) | ✅ **Criado e comprovado**: lê a trilha e leva `permission denied` em `credentials_entity` |
| `DATABASE_URL` no *Environment* `producao` | *GitHub Environments* | ✅ **Cadastrada**, apontando para o papel restrito e não para o dono do banco |
| `DATABASE_URL` no *Environment* `desenvolvimento` | *GitHub Environments* | ⏳ **Em aberto por decisão.** O `Postgres-dev` existe desde 29/10 e é privado: o *runner* do GitHub não o alcança sem um proxy TCP público. Expor um banco de desenvolvimento para rodar ali a segunda via da purga é custo sem contrapartida, já que o dev não guarda dado de ninguém — a purga nativa do n8n basta. Fica registrado como decisão, e não como esquecimento |
| Expor o Postgres ao *runner* do GitHub | Railway | ✅ **Decidido e feito**: proxy TCP público, alcançável só pelo papel `jurisflow_purga` |
| Sanitização de PII antes da chamada ao LLM | Nó `Sanitizar Entrada` | **Pronto desde a Etapa 1** |
| Varredura de segredos no histórico | `gitleaks` no *pipeline* | ✅ **Verde**, inclusive depois da reescrita do histórico |
| Variáveis de *pruning* no ambiente | Serviço `n8n` no Railway | ✅ **As cinco definidas em produção.** Com o n8n sobre Postgres, `execution_entity` existe neste banco e o prazo de 72 h ganha a segunda barreira. Em desenvolvimento falta `EXECUTIONS_DATA_SAVE_ON_ERROR` |
| Nó de auditoria gravando em Postgres | Workflow de intake | ✅ **Gravando**: 978 intakes na trilha e 3.904 *spans*, entre 20/10 e 29/10 |
| Retenção de 90 dias no Slack, com evidência | `docs/evidencias/` | ⏳ **Pendente** |

## Bloco 2 — Observabilidade (25% da nota)

| Exigência | Status |
|---|---|
| Instrumentação com *trace* e *spans* cobrindo o fluxo real | ✅ **Gravando em Postgres.** 4 *spans* por intake, *trace id* = protocolo. A escolha de medir quatro, e não os sete do desenho, está justificada na seção 3 do [plano](observabilidade/plano-instrumentacao.md): o n8n não expõe início e fim de cada nó, e *span* com duração fabricada é pior que *span* ausente |
| Cinco métricas: latência p50, p95 e p99; custo; erro; volume; qualidade | ✅ **Materializadas** em [`db/metricas/vw_metricas.sql`](../db/metricas/vw_metricas.sql), fonte única para relatório e dashboard |
| *Thresholds* definidos e justificados para o contexto | ✅ **Definidos** em [`observabilidade/metricas-e-thresholds.md`](observabilidade/metricas-e-thresholds.md). ⚠️ Vieram de cálculo e de restrição do caso; os 978 intakes que os conferem são **carga sintética**, e não demanda real |
| Catálogo de alertas com prioridade, público e canal | ✅ **13 alertas** em [`observabilidade/alertas.md`](observabilidade/alertas.md) |
| Alerta funcional, com prioridade, público e canal | ✅ **Disparou de verdade**: A-10, P2, `#juris-ops`, com a contraprova de que cala quando não há o que purgar. [`evidencias/2026-10-20-alerta-a10.md`](evidencias/2026-10-20-alerta-a10.md) |
| Dashboard curado e linkado no README | ✅ **Linkado**, com os números medidos reproduzidos no próprio README, porque o painel do Railway exige login |
| Lacuna: `latencia_ms` media até o parse, e o SLA é até o Slack | ✅ **Fechada.** `duracao_total_ms` mede até a entrega no Slack e é a que fecha o SLA |
| Lacuna: tokens não eram capturados, logo o custo era cálculo | ✅ **Fechada.** `tokens_entrada` e `tokens_saida` vêm do provedor. O custo medido ficou em US$ 0,0000529 por intake, cerca de metade dos US$ 0,000103 que a estimativa previa |
| Automatizar as verificações mensais da política de retenção | ⏳ **Pendente**, descrito na seção 4 da política |

## Bloco 3 — Otimização medida (parte dos 25%)

| Exigência | Status |
|---|---|
| Medir a linha de base antes de mexer | ✅ **Feito**, 200 intakes, em [`evidencias/2026-10-20-linha-de-base.md`](evidencias/2026-10-20-linha-de-base.md) |
| Aplicar uma melhoria | ✅ **Compressão do system prompt**, de 1.172 para 784 caracteres |
| Medir depois, com evidência reproduzível | ✅ **−21,2% de custo por intake**, −12,3% no p95, qualidade mantida. Duas corridas consecutivas, mesma semente |
| Explicar o *trade-off* entre latência, custo e qualidade | ✅ Em [`otimizacoes/001`](otimizacoes/001-compressao-do-system-prompt.md), incluindo o que a medição **não** prova e a otimização descartada por ser mensurável de forma desonesta |

**Candidatas que ficam para depois:** cache de classificação, descartado porque sobre corpus
sintético repetido mostraria ganho falso; reconhecimento de entidades nomeadas na sanitização,
que ataca o risco residual da seção 5 do mapa de dados; e *fallback* de provedor.

## Bloco 4 — README v1.0 e vídeo

| Exigência | Status |
|---|---|
| Seção de LGPD no README | ✅ **Pronta** |
| Seção de observabilidade | ✅ **Pronta**, com dashboard e números medidos |
| Seção de otimizações | ✅ **Pronta** |
| Seção de *troubleshooting* | ✅ **Pronta**, nove cenários |
| Vídeo de 3 a 5 minutos, com a sua voz | ⏳ **Pendente** |
| Vídeo mostrando o alerta e o que o dispara | ⏳ **Pendente**. Material em [`evidencias/2026-10-20-alerta-a10.md`](evidencias/2026-10-20-alerta-a10.md) |
| Vídeo mostrando a sanitização antes da chamada ao LLM | ⏳ **Pendente**. Nó `Sanitizar Entrada`, no editor do n8n |
| Vídeo mostrando a otimização, antes e depois | ⏳ **Pendente**. Números em [`otimizacoes/001`](otimizacoes/001-compressao-do-system-prompt.md) |
| Observações sobre acertos, erros e aprendizados | ⏳ **Pendente**. O incidente de nove dias é o melhor material disponível |

## O que falta, em uma lista só

1. **O vídeo**, e tudo o que ele precisa mostrar. É o único item da rubrica que não pode ser delegado.
2. **Retenção de 90 dias no Slack**, com evidência.
3. **Automatizar as verificações mensais** da política de retenção.
4. **Repovoar o ambiente de desenvolvimento**: esquema no banco, conta de dono, credenciais e workflows. A paridade de plataforma já está feita.
5. **`DATABASE_URL` em `desenvolvimento`**, que depende de decidir se o banco de dev é exposto ao *runner* do GitHub. Hoje a decisão registrada é não expor.

## Critérios de anulação, conferir antes de entregar

| Risco | Verificação |
|---|---|
| Chave de API real no código ou no histórico | `gitleaks detect --source . --verbose` antes de cada entrega |
| Dado pessoal real sem anonimização | Os testes usam CPF `111.444.777-35`, válido pelo dígito verificador e de ninguém |
| Métrica inventada, sem respaldo em dashboard ou log | Todo número do relatório tem origem rastreável: as *views* de `vw_metricas.sql` e o painel do Railway |
| Medição de otimização sem evidência | A saída bruta das duas medições está em `docs/evidencias/` |

### Fora do repositório, mas do mesmo assunto

Há arquivos `.txt` com segredos em claro na pasta acima do repositório: `gh-token.txt`,
`n8n-api-key-*.txt`, `slack-bot-token.txt`, `webhook-secret-*.txt`, `openIA API.txt`,
`N8N_ENCRYPTION_KEY.txt` e `n8n-encryption-key-dev.txt`. Não estão versionados e não entram na
varredura, mas aparecem em gravação de tela e em captura de pasta. **Mover para fora da árvore
do projeto antes de gravar o vídeo.**

Dois podem ser apagados: `jurisflow-prod.txt`, cuja chave devolve 401, e `Edcode-railway.txt`,
que não era um token do Railway. Os dois arquivos de `N8N_ENCRYPTION_KEY` são o oposto: são a
apólice contra o acidente de 20/10 se repetir, e merecem cópia fora deste disco.
