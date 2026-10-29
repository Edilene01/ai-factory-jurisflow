# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue
[SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Adicionado
- `docs/evidencias/2026-10-29-rollback.md` e `docs/evidencias/rollback-02-deploy-workflow.txt`: o *rollback* executado em produção nos dois sentidos, com os seis passos, os dois protocolos e a saída bruta dos quatro comandos. Reverteu para `v1.2.2`, os três *smoke tests* passaram, voltou para `v1.3.0`, e passaram de novo

### Corrigido
- O exemplo do nível 1 de `docs/rollback.md` mandava reverter para a `v1.0.0`, cujo workflow usa `n8n-nodes-base.openAi` em `typeVersion 1` — o nó legado que no n8n 2.40.5 devolve a mensagem de boas-vindas em vez da classificação. Seguir o procedimento ao pé da letra durante um incidente trocaria um problema por outro. Passa a apontar para a versão boa anterior, com `f61f667` nomeado como limite seguro para trás
- A seção de evidência do `rollback.md` afirmava que o procedimento havia sido executado, enquanto o `docs/evidencias/README.md` listava os três arquivos como `<pendente>`. As duas passam a descrever o que existe de fato

## [2.0.0] – 2026-10-29

A versão que separa o protótipo do produto. É mudança maior porque o estado do sistema trocou
de lugar: o n8n deixa o SQLite e passa a viver no Postgres do projeto, com a chave de cifragem
fixada no ambiente. Quem restaurasse a instância pelo procedimento da v1.0.0 não chegaria ao
mesmo sistema.

### Adicionado — Etapa 2, Bloco 1 (LGPD)
- `docs/lgpd/mapa-dados-pessoais.md`: registro do art. 37 com dez pontos de coleta e tratamento, base legal de cada um, papéis de controlador e operador, três avaliações de legítimo interesse e o mapeamento dos direitos do titular
- `docs/lgpd/transferencia-internacional.md`: os quatro fluxos que cruzam a fronteira, a fundamentação no art. 33, IX, c/c art. 7º, V, e a pendência de incorporação das cláusulas-padrão da Resolução CD/ANPD nº 19/2024
- `docs/lgpd/politica-retencao-exclusao.md`: prazos por armazenamento, mecanismo que executa cada um e procedimento de exclusão a pedido do titular em três passos
- `db/schema/001_trilha_auditoria.sql`: tabelas `jurisflow_trilha_auditoria` e `jurisflow_purga_log`, esta última como prova de execução da política
- `db/retencao/purga_diaria.sql` e `db/retencao/excluir_por_protocolo.sql`
- `workflows/jurisflow-retencao.json`: agendador diário às 03:15, que executa a purga, grava a contagem e só notifica `#juris-ops` quando houve remoção ou falha
- `.github/workflows/retencao.yml`: segunda via da purga às 04:15, hospedada fora do n8n. Usa a defasagem de uma hora como verificação, já que remover alguma coisa significa que a via do n8n não rodou, e alerta em P2 nesse caso. Confere também que não restou registro vencido e publica o resumo no *GitHub Step Summary*
- `docs/checklist-etapa-2.md`, com o estado de cada exigência da etapa
- `db/schema/003_papel_purga.sql`: papel `jurisflow_purga`, de menor privilégio, para a segunda via da purga. Alcança a trilha, os spans, as execuções vencidas e o registro de purga, e nada mais. Existe porque o n8n passa a dividir banco com a trilha, e a URL que vai para o *runner* do GitHub não pode ser a do papel dono
- [`docs/adr/ADR-006`](docs/adr/ADR-006-postgres-como-banco-do-n8n.md): aponta o n8n para o Postgres do projeto e revê a escolha do caminho 1 da seção 2.1 da política de retenção. A decisão de 20/10 recusava a troca pelo preço de refazer à mão as quatro credenciais, a chave de API e o histórico; a perda da instância em 29/10 cobrou esse preço de qualquer modo, e a premissa caiu junto. Traz `execution_entity` para este banco e dá mecanismo ao prazo de 72 horas

### Modificado
- `README.md`: seção de LGPD e separação da seção de segurança de credenciais
- `.env.example`: `DATABASE_URL` e as cinco variáveis de retenção do n8n, que antes existiam só no `docker-compose.yml`
- `docs/rotacao-credenciais.md`: histórico de rotações preenchido e registro da rotação pendente da `N8N_API_KEY`
- `tests/validate_workflow.py`: passa a validar também o agendador de retenção e a conferir que os prazos do SQL e do workflow contam a mesma história
- `.github/workflows/ci-cd.yml`: publica o agendador de retenção nos dois ambientes

### Adicionado — Etapa 2, Bloco 3 (otimização medida)
- `docs/otimizacoes/001-compressao-do-system-prompt.md`: a otimização com antes e depois, o trade-off e os limites da medição
- Compressão do *system prompt* de 1.172 para 784 caracteres: **−21,2% de custo por intake**, −21,3% de tokens de entrada, −12,3% no p95 de latência, com acerto de área e taxa de erro inalterados
- `docs/evidencias/2026-10-20-linha-de-base.md` e os JSON brutos das duas corridas de 200 intakes

### Adicionado — Etapa 2, Bloco 2 (observabilidade), desenho
- `docs/observabilidade/metricas-e-thresholds.md`: as cinco métricas com o limite de cada uma e a restrição de que ele deriva. Os thresholds estão marcados como **provisórios**, porque vêm de cálculo e de restrição do caso, e não de medição
- `docs/observabilidade/plano-instrumentacao.md`: 7 spans cobrindo formulário até Slack, com o protocolo servindo de trace id, e as quatro mudanças necessárias no workflow
- `docs/observabilidade/alertas.md`: 13 alertas com prioridade, público, canal e ação esperada
- `db/schema/002_observabilidade.sql`: colunas de token e de duração total na trilha, e a tabela `jurisflow_trace_span`
- `db/metricas/vw_metricas.sql`: as cinco métricas como views, fonte única para relatório e dashboard

### Adicionado — operação e recuperação
- `docs/runbook-recuperacao.md`: procedimento para quando a instância volta vazia, com a tabela do que se perde e do que sobrevive, a tentativa de recuperação antes da reconstrução e as armadilhas que custaram tempo
- `scripts/restaurar_instancia.py`: publica os três workflows, ativa, aponta qual credencial ficou faltando, roda os *smoke tests* e consulta o painel de métricas

### Alterado — Etapa 2, infraestrutura
- O n8n passa a usar o Postgres do projeto como banco próprio, conforme a ADR-006, com `N8N_ENCRYPTION_KEY` fixada no ambiente. `execution_entity` volta a existir neste banco, e com ela o prazo de 72 horas ganha a segunda barreira que a política previa
- Papel `jurisflow_purga` criado no banco e `DATABASE_URL` cadastrada no Environment `producao` apontando para ele, e não para o papel dono
- Proxy TCP público habilitado no serviço Postgres, que é como o *runner* do GitHub alcança o banco de fora da plataforma
- Variável `N8N_PUBLIC_URL` do Environment `desenvolvimento` corrigida para a instância de desenvolvimento, que existia desde 19/10 sem estar referenciada. Enquanto apontava para produção, um *push* em `develop` publicava no ambiente errado

### Corrigido
- A purga de 12 meses passa a alcançar `jurisflow_trace_span`, no SQL e no agendador do n8n. Tabela nova sem mecanismo de purga contradiria a política de retenção

### Alterado — Etapa 2, Bloco 0 (plataforma)
- **ADR-005**: Railway nos dois ambientes. A instância que servia de desenvolvimento é promovida a produção, por ser a comprovada, e uma segunda instância passa a ser o desenvolvimento. Restaura a paridade que a ADR-003 havia registrado como sua pior consequência
- **ADR-004 substituída no mesmo dia**: o período de teste do n8n Cloud não libera a API pública, o que torna inalcançável o seu primeiro critério de validação, a publicação sem intervenção manual
- `README.md`, `docs/architecture/c4-nivel2-containers.md` e o checklist passam a descrever a topologia Railway; as ADRs anteriores ficam como histórico da decisão, não como descrição do que está no ar
- `docs/estado-da-entrega.md` marcado como registro histórico da Etapa 1
- Variável `N8N_PUBLIC_URL` do ambiente `producao` apontada para o Railway

### Resolvido nesta versão, do que estava em aberto
- Os três *smoke tests* passaram contra a URL pública, e passam dentro do próprio *pipeline*
- O *deploy* por *push* na `main` fechou verde pela primeira vez, em 32 segundos
- A instância de produção foi restabelecida, agora sobre Postgres, e a `N8N_API_KEY` reemitida
- O ambiente de desenvolvimento existe e o Environment passou a apontar para ele
- A trilha de auditoria grava em Postgres, no lugar do sink em memória
- As cinco métricas têm *views* materializadas, alerta funcional e dados reais por trás
- A otimização foi medida, com número antes e depois

### Em aberto ao fechar a 2.0.0
- Vídeo de 3 a 5 minutos da Etapa 2
- *Rollback* executado com evidência em `docs/evidencias/`
- Postgres próprio para o ambiente de desenvolvimento, que segue em SQLite e quebra a paridade que a ADR-005 comprou
- Link do *dashboard* no README, hoje descrito mas não linkado
- Três dos sete *spans* previstos no plano de instrumentação: o workflow mede quatro
- *Fallback* de provedor de LLM

## [1.0.0] – 2026-09-18

Primeira versão sob nova responsabilidade técnica. O protótipo herdado foi adotado e
evoluído, não reescrito.

### Adicionado
- Nó `Sanitizar Entrada`: valida campos obrigatórios, gera protocolo no formato `JF-AAAAMMDD-XXXXXX`, mascara nome e CPF e remove CPF, CNPJ, e-mail e telefone do texto enviado ao provedor de LLM
- Nó `Responder Intake`: devolve protocolo, área e urgência ao formulário, de modo que o site deixa de receber sucesso quando o processamento falha adiante
- Desvio `Precisa de Revisão Manual?` e canal `#juris-triagem-manual` para casos não classificados
- Nó `Registro de Auditoria`, com o formato do registro já fechado e sem dado identificável
- Pipeline de CI/CD em GitHub Actions, com varredura de segredos, validação, testes, publicação por API e smoke tests
- Três smoke tests contra a URL pública: saúde da instância, recusa de chamada sem assinatura e intake ponta a ponta dentro do SLA de 60 segundos
- `scripts/deploy_workflow.py`, que publica e ativa o workflow sem importação manual
- Auditoria do protótipo herdado, matriz de decisão de stack, ADR-001, ADR-002 e diagramas C4 nos níveis 1 e 2
- Procedimentos de rotação de credenciais e de rollback, com evidência de execução
- Post-mortem do incidente INC-001

### Modificado
- `Parse Classificação` passou a ter tratamento de erro, tolerar markdown e texto extra na resposta do modelo e normalizar a área antes do roteamento
- `Switch Área` passou a comparar chaves canônicas sem acento e em caixa baixa, e perdeu o fallback silencioso
- Limite de tokens da classificação subiu de 40 para 60, reduzindo a chance de resposta truncada
- Nó de LLM ganhou repetição automática, três tentativas, e segue o fluxo em caso de erro, em vez de derrubar a execução
- Identificador do modelo passou a vir de variável de ambiente
- `docker-compose.yml` passou a ler do `.env`, ganhou healthcheck e desligou a persistência do payload de execuções
- `tests/validate_workflow.py` ganhou varredura antivazamento e checagens das novas garantias
- `tests/test_routing.py` deixou de tratar o roteamento silencioso como comportamento esperado e passou a cobrir markdown, texto extra, variação de caixa e área desconhecida

### Removido
- Chave de API da OpenAI e segredo do webhook que estavam escritos dentro do JSON do workflow
- E-mail corporativo do responsável anterior nos metadados
- Persistência automática do payload de execuções bem-sucedidas, que guardava CPF e descrição do caso no banco do n8n
- Tag `prod` em workflow que rodava em máquina pessoal

### Segurança
- Credenciais movidas para as credenciais do n8n e para os secrets da plataforma, separados por ambiente
- Repositório publicado a partir de histórico limpo, com `gitleaks detect` executado antes

## [0.2.0] – 2026-02-19

Última versão sob a responsabilidade anterior, preservada aqui para rastreabilidade. O
arquivo original está em `docs/heranca/`, com os segredos removidos.

### Adicionado
- Área e canal Consumidor
- Parse de urgência
- Ramo paralelo de auditoria, ainda sem persistência

### Corrigido
- Limite de tokens ajustado para 40

## [0.1.0] – 2026

### Adicionado
- Versão inicial: webhook, classificação por LLM, roteamento em quatro áreas e entrega no Slack
