# ADR-007: Aplicação web própria, com ponte para o n8n

* **Status:** aceita
* **Data:** 06/11/2026
* **Decisora:** Edilene Chagas Faria
* **Depende de:** ADR-001, ADR-005
* **Não substitui nenhuma:** o n8n continua sendo o orquestrador

## Contexto e definição do problema

Até aqui o JurisFlow não tinha interface. O sistema inteiro era um webhook, e a única forma
de exercitá-lo era `curl` ou o editor do n8n. Isso bastou enquanto o que se avaliava era
arquitetura, segurança e observabilidade.

Deixou de bastar. A Etapa 3 pede, textualmente, que quem estava *"trabalhando somente com
workflows do n8n"* migre para *"uma aplicação (site) de verdade"*, e avalia *"demo funcional
e fluida"*. Mais do que a rubrica: o diagrama C4 nível 1 sempre mostrou um **formulário do
site do escritório** como sistema externo, e esse formulário nunca existiu. A aplicação fecha
um desenho que estava incompleto desde o começo, e não acrescenta uma peça decorativa.

### O problema técnico que a decisão precisa resolver

O webhook exige o header `X-Jurisflow-Signature`. Um formulário em página estática teria de
carregar esse valor no JavaScript, e **segredo que chega ao navegador não é segredo**:
qualquer pessoa o leria no código-fonte da página ou na aba de rede. Pior, o segredo é o
mesmo que o *GitHub Environment* guarda e que a rotação de credenciais trata como sensível.

Publicá-lo no navegador não seria um detalhe de implementação: seria o critério de anulação
da própria etapa, que fala em *"secret exposto na aplicação ou no repositório no momento da
avaliação"*.

## Opções consideradas

* **A. Página estática chamando o webhook direto**, com o segredo no JavaScript
* **B. Remover a autenticação do webhook** e proteger por outro meio
* **C. Aplicação com um backend próprio**, que guarda o segredo e faz a ponte

## Decisão

Escolhida a opção **C**: uma aplicação em FastAPI que serve duas telas e expõe dois
endpoints de ponte, `POST /api/intake` e `GET /api/metricas`. O segredo vive na variável de
ambiente do serviço, é acrescentado no servidor e **nunca** é devolvido ao cliente.

As duas telas:

| Rota | O que é |
|---|---|
| `/` | O formulário de intake, a tela que a pessoa que procura o escritório usa |
| `/painel` | O painel de operação com as cinco métricas, lidas da mesma view que o relatório cita |

### Consequências positivas

* **O segredo não sai do servidor.** Verificado: nenhum dos ativos servidos contém o valor, e o teste está no procedimento de verificação da aplicação.
* O backend é o lugar natural para o **limite de taxa**. Cada intake custa uma chamada de LLM, e uma página aberta em laço esvaziaria o orçamento de tokens. O teto é de 5 por minuto por IP, aplicado antes de qualquer trabalho.
* **Validação de CPF no cliente**, pelos dígitos verificadores, recusa número inventado antes de gastar chamada ao provedor e antes que dado inválido entre na trilha de auditoria.
* O painel torna a observabilidade **visível**. Até aqui as métricas existiam em SQL e em JSON; agora têm forma, e a demo pode mostrar o volume subindo em tempo real.
* A `origem` do intake é fixada no servidor como `aplicacao-web`, e não aceita do cliente. Ela alimenta a métrica de volume por canal, e deixá-la editável permitiria poluir a série.

### Consequências negativas

* **Mais um serviço para manter, e mais um ponto de falha.** A aplicação cai sem derrubar o n8n, mas o inverso não é verdade: o n8n fora do ar deixa a aplicação sem o que mostrar.
* **Mais uma assinatura exposta ao mesmo risco.** O projeto já perdeu instância duas vezes por motivo de plataforma. Um terceiro serviço no Railway é um terceiro candidato ao mesmo acidente, e entra na tabela de prazos pela mesma razão.
* **Duplicação de validação.** O CPF é validado no cliente e os campos obrigatórios no backend, e o workflow valida de novo no nó `Sanitizar Entrada`. É redundância deliberada, e redundância custa manutenção: mudar a regra exige mudar em dois lugares.
* **O painel é público.** Não há login, o que se discute abaixo.

### Sobre não haver login

O painel não expõe dado pessoal: serve contagens, percentis e custo, nunca nome, CPF ou
trecho de relato. O esquema de `jurisflow_trilha_auditoria` não tem coluna que aceite texto
do caso, e isso é verificado por teste no `validate_workflow.py`.

Acrescentar autenticação criaria uma superfície nova — sessão, senha, recuperação — para
proteger dado que não é sensível. Preferi não ter login a ter um login improvisado, que seria
pior do que nenhum. Se o painel um dia mostrar caso individual, a decisão se inverte, e aí a
autenticação vem antes do dado.

## Alternativas descartadas e o porquê

**A. Página estática com o segredo no JavaScript.** É a opção mais simples e a única
inaceitável. O segredo estaria publicado para qualquer visitante, e a rubrica da Etapa 3 trata
isso como critério de anulação.

**B. Remover a autenticação do webhook.** Resolveria o problema do segredo ao custo de abrir
o endpoint de intake à internet inteira, sem controle. Cada requisição anônima viraria uma
chamada de LLM paga. Seria trocar vazamento de segredo por conta aberta, e o *smoke test* 2,
que exige recusa de chamada sem assinatura, deixaria de passar — um teste que existe desde a
Etapa 1 justamente para garantir essa propriedade.

## Validação

A decisão se confirma quando:

1. Nenhum ativo servido contiver o segredo. **Verificado em 06/11/2026**, nas quatro rotas públicas.
2. O intake pela aplicação produzir protocolo e classificação corretos. **Verificado**: `JF-20261106-2M44FS`, área Trabalhista, urgência alta.
3. O limite de taxa recusar o excesso com 429. **Verificado**.
4. O painel refletir os mesmos números do endpoint de métricas. **Verificado**.
5. A aplicação estar publicada e funcional em URL própria. **Verificado em 06/11/2026**: https://ai-factory-jurisflow-production.up.railway.app, com intake `JF-20261106-05YYJ5` classificado como Consumidor pelo navegador.
6. A URL permanecer estável por 24 horas antes da avaliação. **Em curso**, contagem iniciada em 06/11/2026 às 15:20; ver [`evidencias/2026-11-06-aplicacao-publicada.md`](../evidencias/2026-11-06-aplicacao-publicada.md).
