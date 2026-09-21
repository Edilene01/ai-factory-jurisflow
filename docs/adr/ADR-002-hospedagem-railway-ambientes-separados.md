# ADR-002: Hospedar em Railway, com ambientes de desenvolvimento e produção separados

* **Status:** substituída pela [ADR-003](ADR-003-producao-n8n-cloud-desenvolvimento-railway.md) em 21/09/2026
* **Data:** 18/09/2026
* **Decisora:** Edilene Chagas Faria
* **Depende de:** ADR-001
* **Substitui:** nenhuma

## Contexto e definição do problema

A ADR-001 fixou o n8n auto-hospedado como orquestrador, o que deixa em aberto onde essa
instância vai rodar e como separar desenvolvimento de produção.

Hoje o sistema só existe em `localhost`, com `WEBHOOK_URL=http://localhost:5678/` e porta
publicada apenas no *loopback*, conforme o achado OPS-01 da auditoria. O formulário do site
não alcança esse endereço, e a Etapa 1 exige URL pública estável, ambientes separados com
*secrets* distintos e *deploy* disparado por *push*.

As restrições: orçamento de US$ 120 mensais cobrindo hospedagem e consumo de LLM, prazo até
a semana 6, e a necessidade de manter o dado sob controle, já que a descrição do caso é
coberta por sigilo.

## Opções consideradas

* **A. Railway**, com dois projetos, um por ambiente
* **B. Render**
* **C. Fly.io**
* **D. VPS própria**, com Docker Compose e proxy reverso

## Decisão

Escolhido o **Railway**, com dois ambientes independentes e nenhum *secret* compartilhado
entre eles.

O desenho fica assim: a branch `develop` publica no ambiente de desenvolvimento e a `main`
publica em produção, cada uma amarrada a um *GitHub Environment* com o seu próprio conjunto
de segredos. O JSON do workflow é a fonte da verdade, e o `scripts/deploy_workflow.py`
o publica na instância alvo pela API do n8n, o que dispensa qualquer importação manual.

O que pesou: a implantação por imagem Docker atende ao motor escolhido na ADR-001 sem
adaptação, o banco gerenciado nasce junto do projeto, e o custo de entrada cabe no orçamento.
Os valores vigentes devem ser conferidos na página de preços antes de contratar, porque mudam
sem aviso, e a estimativa aqui serve de ordem de grandeza, não de garantia.

### Consequências positivas

* Uma URL pública estável passa a existir, o que destrava o requisito de maior peso da etapa e permite que o formulário do site alcance o webhook.
* A separação por ambiente elimina a situação absurda em que o workflow estava marcado com a *tag* `prod` rodando em máquina pessoal, achado OPS-02.
* O banco gerenciado no mesmo projeto abre caminho para a trilha de auditoria persistente da Etapa 2, sem nova decisão de infraestrutura.
* Métricas de CPU, memória e reinício vêm do próprio painel, o que dá o ponto de partida para o requisito de observabilidade da Etapa 2.

### Consequências negativas

* O custo de hospedagem passa a competir com o custo de LLM dentro do mesmo teto de US$ 120, o que aperta a margem por classificação e torna a medição de tokens ainda mais necessária.
* Manter dois ambientes significa manter dois conjuntos de credenciais, duas instâncias de n8n e o dobro de superfície para errar. É o preço de não testar em produção.
* O dado passa a repousar fora do Brasil, já que a plataforma não oferece região nacional. A transferência internacional já existia por causa do LLM, porém agora alcança também o repouso, e isso precisa ser documentado com base legal própria na Etapa 2.
* Há aprisionamento moderado na forma de configurar o serviço, ainda que o conteúdo, sendo imagem Docker mais JSON versionado, siga portátil.

## Alternativas descartadas e o porquê

**B. Render.** Bastante equivalente em capacidade e igualmente adequado a Docker. Ficou em
segundo lugar por uma diferença operacional: a criação de ambientes paralelos é menos direta,
e o objetivo aqui é ter dev e prod isolados com o mínimo de cerimônia.

**C. Fly.io.** Tecnicamente interessante pela distribuição por região, o que ajudaria caso
surgisse exigência de proximidade geográfica. Descartado pelo custo de aprendizado, porque a
configuração é mais artesanal e o prazo até a semana 6 é curto.

**D. VPS própria.** Daria controle máximo, inclusive sobre região, e seria a opção mais barata
em escala. Descartada porque transferiria para mim a responsabilidade por sistema operacional,
TLS, proxy reverso, backup e atualização de segurança, trabalho que não cabe no prazo e que
aumentaria o risco de entregar uma URL instável, que é exatamente o que a rubrica pune.

## Validação

A decisão se confirma quando o *pipeline* publicar em produção em menos de cinco minutos, os
três smoke tests passarem contra a URL pública e um *rollback* for executado e evidenciado.
Se o custo mensal de hospedagem passar de US$ 40, ou se a exigência de dado em território
nacional aparecer, esta ADR deve ser revisada em favor de provedor nacional ou de VPS própria.
