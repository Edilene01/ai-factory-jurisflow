# Checklist da Etapa 2

Entrega na semana 10. A etapa separa o protótipo do produto: segurança de credenciais,
conformidade com a LGPD, observabilidade e uma otimização **medida**. A palavra que organiza
tudo é essa: nesta etapa, número sem evidência não conta.

> Estado da Etapa 1: [`estado-da-entrega.md`](estado-da-entrega.md).

## Bloco 0 — Destravar o ambiente (pré-requisito de tudo)

Sem URL viva não há métrica, alerta nem medição de otimização.

| Item | Situação |
|---|---|
| Decidir a plataforma e registrar em ADR | **Feito.** [ADR-005](adr/ADR-005-railway-nos-dois-ambientes.md): Railway nos dois ambientes. A ADR-004 foi substituída no mesmo dia, ao se descobrir que o período de teste do n8n Cloud não libera a API pública |
| Instância de produção | **Promovida**: a instância Railway que servia de desenvolvimento passa a ser produção, por ser a comprovada |
| Workflow de intake | **Ativo.** Publicado e ativado pelo `deploy_workflow.py` em 19/10/2026 |
| URL pública | **Responde.** `/healthz` em 200 e `/webhook/intake` recusa chamada anônima com 403 |
| Smoke tests 1, 2 e 3 | ✅ **Os três passaram** em 20/10/2026, pela primeira vez no projeto. Evidência em [`evidencias/2026-10-20-smoke-e-classificacao.md`](evidencias/2026-10-20-smoke-e-classificacao.md) |
| Roteamento nas cinco áreas | ✅ **5/5 corretas**, mais o caso ambíguo na tendência prevista. Latências de 1,5 a 3,2 s, todas dentro do SLA de 60 s |
| Credencial da OpenAI | ✅ **Corrigida** em 20/10/2026. Antes continha valor que nem começava com `sk-` |
| Nó de LLM legado | ✅ **Substituído** por HTTP Request. O `n8n-nodes-base.openAi` typeVersion 1 resolvia para a raiz da API no n8n 2.40.5 e devolvia a mensagem de boas-vindas |
| Bug do deploy que apagava credenciais | **Corrigido.** O `deploy_workflow.py` relê os ids da versão publicada e os recoloca antes do PUT |
| **Criar a segunda instância Railway, para desenvolvimento** | **Pendente, e é o próximo passo.** Mesma imagem `n8nio/n8n:2.40.5`, que é a que produção roda hoje, e as três credenciais com os nomes exatos: `JurisFlow Webhook Signature`, `OpenAI JurisFlow` e `Slack JurisFlow Bot` |
| Separação de ambientes | ⚠️ **Transitória.** Os dois *Environments* apontam hoje para a mesma URL, porque a instância de desenvolvimento ainda não existe. Enquanto durar, um *push* em `develop` publica em produção. Não use `develop` até a segunda instância estar de pé |
| Mover os *secrets* para o *Environment* certo | Pendente. A chave de API e o segredo de webhook que hoje estão em `desenvolvimento` pertencem agora a `producao` |
| *Pipeline* de CI/CD | **Vermelho** nas seis execuções anteriores. O *job* de qualidade passa; o deploy falhava por `HTTP 401` contra a instância que não existe mais |
| Aplicar `db/schema/001_trilha_auditoria.sql` nos dois bancos | Pendente |
| Plano do Railway | **Hobby assinado em 19/10/2026.** O período de teste estava em 2 dias de saldo e teria derrubado produção |
| Registrar a situação das assinaturas | **Feito**, tabela em [`rotacao-credenciais.md`](rotacao-credenciais.md) |
| Operar o desenvolvimento sob demanda | Decidido por custo: o serviço fica **parado** e é ligado só quando preciso. Ordem: ligar → *push* em `develop` → conferir deploy e *smoke tests* → desligar |

## Bloco 1 — Credenciais e LGPD (50% da nota)

| Exigência | Onde | Status |
|---|---|---|
| Trio sagrado: `.env`, `.gitignore`, `.env.example` | Raiz | **Pronto** |
| *Secrets* separados por ambiente | *GitHub Environments* `producao` e `desenvolvimento` | **Pronto** |
| Procedimento de rotação documentado | [`rotacao-credenciais.md`](rotacao-credenciais.md) | **Pronto** |
| Histórico de rotações preenchido | Idem | **Pronto**, com datas a conferir na origem |
| Mapa de dados pessoais com base legal por ponto de coleta | [`lgpd/mapa-dados-pessoais.md`](lgpd/mapa-dados-pessoais.md) | **Pronto**: 10 pontos, 3 avaliações de legítimo interesse |
| Transferência internacional reconhecida e documentada | [`lgpd/transferencia-internacional.md`](lgpd/transferencia-internacional.md) | **Pronto**: 4 fluxos, art. 33, IX |
| Política de retenção e exclusão | [`lgpd/politica-retencao-exclusao.md`](lgpd/politica-retencao-exclusao.md) | **Pronto** |
| Mecanismo real que executa a retenção | [`db/retencao/`](../db/retencao/) e [`workflows/jurisflow-retencao.json`](../workflows/jurisflow-retencao.json) | **Publicado** na instância em 19/10/2026, `active: false`. Não ativa enquanto faltar a credencial Postgres no n8n |
| Segunda via da purga, fora da plataforma | [`.github/workflows/retencao.yml`](../.github/workflows/retencao.yml) | **Escrita e validada**, nunca executada: falta `DATABASE_URL` nos *Environments* |
| Cadastrar `DATABASE_URL` em `producao` e `desenvolvimento` | *GitHub Environments* | **Pendente** |
| Expor o Postgres ao *runner* do GitHub, ou decidir não expor | Railway | **Pendente** |
| Sanitização de PII antes da chamada ao LLM | Nó `Sanitizar Entrada` | **Pronto desde a Etapa 1** |
| Varredura de segredos no histórico | `gitleaks` no *pipeline* | **Verde** em todas as execuções |
| Variáveis de pruning em todos os ambientes | `.env.example` e `docker-compose.yml` | **Pendente** no Railway e em produção |
| Retenção de 90 dias no Slack, com evidência | `docs/evidencias/` | **Pendente** |
| Nó de auditoria gravando em Postgres | Workflow de intake | **Pendente**: hoje é sink em memória |

## Bloco 2 — Observabilidade (25% da nota)

| Exigência | Status |
|---|---|
| Instrumentação com *trace* e *spans* cobrindo o fluxo real | **Desenhada**: 7 spans, trace id = protocolo, esquema em [`db/schema/002_observabilidade.sql`](../db/schema/002_observabilidade.sql) e plano em [`observabilidade/plano-instrumentacao.md`](observabilidade/plano-instrumentacao.md). Falta aplicar ao workflow |
| Cinco métricas: latência p50, p95 e p99; custo; erro; volume; qualidade | **Definidas e materializadas** em [`db/metricas/vw_metricas.sql`](../db/metricas/vw_metricas.sql), fonte única para relatório e dashboard |
| *Thresholds* definidos e justificados para o contexto | **Definidos** em [`observabilidade/metricas-e-thresholds.md`](observabilidade/metricas-e-thresholds.md), cada um com a restrição de origem. ⚠️ **Provisórios**: derivam de cálculo e de restrição do caso, não de medição. A linha de base exige tráfego real |
| Catálogo de alertas com prioridade, público e canal | **Pronto**: 13 alertas em [`observabilidade/alertas.md`](observabilidade/alertas.md). Só o A-10 está implementado |
| Lacuna: `latencia_ms` mede até o parse, e o SLA é até o Slack | **Identificada**, correção no passo 4.2 do plano |
| Lacuna: tokens não são capturados, logo o custo é cálculo e não medição | **Identificada**, correção no passo 4.1 do plano |
| Alerta funcional, com prioridade (P1/P2/P3), público e canal | **Primeiro alerta definido**: P2 em `#juris-ops`, para quem opera a plataforma, disparado quando a purga de retenção não roda ou deixa registro vencido. Falta executá-lo de verdade e capturar a evidência |
| Dashboard curado e linkado no README | Pendente. O plano Hobby do Railway inclui métricas, logs e **alertas nativos**, com 7 dias de retenção de log. É a fonte natural das métricas de infraestrutura; a série histórica mais longa fica na trilha de auditoria em Postgres |
| Automatizar as verificações mensais da política de retenção | Pendente, descrito na seção 4 da política |

## Bloco 3 — Otimização medida (parte dos 25%)

| Exigência | Status |
|---|---|
| Medir a linha de base antes de mexer | Pendente |
| Aplicar uma melhoria: cache, *fallback* de provedor, *retry*, *hybrid search* | Pendente. `.env.example` já reserva `ANTHROPIC_API_KEY` para o *fallback* |
| Medir depois, com evidência reproduzível | Pendente |
| Explicar o *trade-off* entre latência, custo e qualidade | Pendente |

**Candidata registrada:** substituir a sanitização por expressão regular por reconhecimento de
entidades nomeadas, para remover nomes próprios e endereços antes da chamada ao provedor.
Resolve o risco residual da seção 5 do mapa de dados e tem efeito medível em qualidade de
classificação e em custo de *token*.

## Bloco 4 — README v1.0 e vídeo

| Exigência | Status |
|---|---|
| Seção de LGPD no README | **Pronta** |
| Seção de observabilidade | Pendente |
| Seção de otimizações | Pendente |
| Seção de *troubleshooting* | Pendente |
| Vídeo de 3 a 5 minutos, com a sua voz | Pendente |
| Vídeo mostrando o alerta e o que o dispara | Pendente |
| Vídeo mostrando a sanitização antes da chamada ao LLM | Pendente |
| Vídeo mostrando a otimização, antes e depois | Pendente |
| Observações sobre acertos, erros e aprendizados | Pendente |

## Critérios de anulação, conferir antes de entregar

| Risco | Verificação |
|---|---|
| Chave de API real no código ou no histórico | `gitleaks detect --source . --verbose` antes de cada entrega |
| Dado pessoal real sem anonimização | Os testes usam CPF `111.444.777-35`, válido pelo dígito verificador e de ninguém |
| Métrica inventada, sem respaldo em dashboard ou log | Toda número do relatório precisa ter origem rastreável |
| Medição de otimização sem evidência | Guardar a saída bruta das duas medições |

### Fora do repositório, mas do mesmo assunto

Há arquivos `.txt` com tokens em claro na pasta acima do repositório (`gh-token.txt`,
`n8n-api-key-*.txt`, `slack-bot-token.txt`, `webhook-secret-*.txt`). Não estão versionados e
não entram na varredura, mas aparecem em gravação de tela e em captura de pasta. Mover para
fora da árvore do projeto antes de gravar o vídeo.
