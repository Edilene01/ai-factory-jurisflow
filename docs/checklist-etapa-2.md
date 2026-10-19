# Checklist da Etapa 2

Entrega na semana 10. A etapa separa o protótipo do produto: segurança de credenciais,
conformidade com a LGPD, observabilidade e uma otimização **medida**. A palavra que organiza
tudo é essa: nesta etapa, número sem evidência não conta.

> Estado da Etapa 1: [`estado-da-entrega.md`](estado-da-entrega.md).

## Bloco 0 — Destravar o ambiente (pré-requisito de tudo)

Sem URL viva não há métrica, alerta nem medição de otimização.

| Item | Situação |
|---|---|
| Instância de produção no n8n Cloud | **Caiu.** `contatestes-01` responde "404 – No instance here". A instância não existe mais |
| Instância de desenvolvimento no Railway | **No ar**, `/healthz` responde 200 |
| Workflow de intake no Railway | **Inativo**, por isso `/webhook/intake` devolve 404 |
| *Pipeline* de CI/CD | **Vermelho** nas seis execuções. O *job* de qualidade passa; o deploy falha com `HTTP 401` na API do n8n |
| Decidir a plataforma de produção e registrar em ADR-004 | Pendente |
| Reemitir `N8N_API_KEY` e atualizar os dois *Environments* | Pendente, registrado em [`rotacao-credenciais.md`](rotacao-credenciais.md) |
| Aplicar `db/schema/001_trilha_auditoria.sql` nos dois bancos | Pendente |

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
| Mecanismo real que executa a retenção | [`db/retencao/`](../db/retencao/) e [`workflows/jurisflow-retencao.json`](../workflows/jurisflow-retencao.json) | **Escrito e validado**, não publicado: depende do Bloco 0 |
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
| Instrumentação com *trace* e *spans* cobrindo o fluxo real | Pendente |
| Cinco métricas: latência p50, p95 e p99; custo; erro; volume; qualidade | Pendente |
| *Thresholds* definidos e justificados para o contexto | Pendente |
| Alerta funcional, com prioridade (P1/P2/P3), público e canal | **Primeiro alerta definido**: P2 em `#juris-ops`, para quem opera a plataforma, disparado quando a purga de retenção não roda ou deixa registro vencido. Falta executá-lo de verdade e capturar a evidência |
| Dashboard curado e linkado no README | Pendente |
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
