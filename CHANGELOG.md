# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui. O formato segue
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o versionamento segue
[SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Em aberto na Etapa 1
- Publicar, no n8n, a troca de Basic Auth para Header Auth no nó Webhook, hoje presente apenas como rascunho no editor
- Criar os GitHub Environments `producao` e `desenvolvimento`, com secrets distintos
- Criar o ambiente de desenvolvimento previsto na ADR-003
- Executar os três smoke tests contra a URL pública
- Executar o rollback e registrar a evidência em `docs/evidencias/`

### A fazer na Etapa 2
- Trilha de auditoria persistente em Postgres, substituindo o sink em memória
- Métricas de latência, custo, erro, volume e qualidade, com alerta configurado
- Mapa de dados pessoais, base legal por ponto de coleta e política de retenção
- Fallback de provedor de LLM

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
