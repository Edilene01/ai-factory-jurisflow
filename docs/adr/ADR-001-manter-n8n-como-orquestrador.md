# ADR-001: Manter o n8n como orquestrador e evoluir o protótipo herdado

* **Status:** aceita
* **Data:** 18/09/2026
* **Decisora:** Edilene Chagas Faria
* **Consultados:** `BRIEFING.md`, `docs/auditoria-prototipo.md`, `docs/matriz-decisao-stack.md`
* **Substitui:** nenhuma

## Contexto e definição do problema

O JurisFlow foi herdado como um protótipo em n8n que triava formulários de intake jurídico
e os roteava para canais do Slack. A auditoria de adoção encontrou 25 achados, sendo seis
críticos, e o sistema só funcionava na máquina de quem o construiu.

A pergunta que esta decisão responde é anterior a qualquer correção: o fluxo continua em n8n
ou migra para outra tecnologia? Tudo o que vem depois, do tratamento de erro ao *pipeline* de
entrega, muda conforme a resposta.

Três forças moldam a escolha. O enunciado da disciplina determina evoluir o protótipo, nunca
reescrevê-lo. O orçamento operacional é de US$ 120 mensais para cerca de 2.500 intakes por
dia. E o dado tratado é coberto por sigilo profissional, o que torna o controle sobre
armazenamento e transferência um requisito, não um detalhe.

## Opções consideradas

* **A. n8n auto-hospedado em plataforma como serviço**
* **B. n8n Cloud**
* **C. Make.com**
* **D. Reescrita em Python com FastAPI**

## Decisão

Escolhida a opção **A, n8n auto-hospedado em plataforma como serviço**, com o workflow
versionado em Git como fonte da verdade e publicado por API.

A justificativa central: é a única alternativa que preserva o investimento já feito no fluxo,
mantém o dado sob controle da JurisFlow e ainda permite automatizar o *deploy* de verdade. Na
matriz de decisão obteve 430 de 500 pontos, contra 365 do n8n Cloud e 360 da reescrita.

### Consequências positivas

* O workflow herdado continua valendo, de modo que o esforço vai para segurança, confiabilidade e observabilidade, e não para reconstruir o que já funciona.
* A instância própria permite desligar a persistência de execução, definir retenção e escolher a região do dado, o que endereça diretamente os achados PRIV-04 e PRIV-05 da auditoria.
* Publicar por API a partir do JSON versionado torna possível o requisito de *push* na branch principal disparando o *deploy*, e mantém o histórico de versões do fluxo dentro do Git.
* A troca de provedor de LLM vira configuração, e não reescrita, o que abre caminho para o *fallback* com Claude previsto na Etapa 2.

### Consequências negativas

* A operação passa a ser minha. Atualização de imagem, backup e disponibilidade deixam de ser problema do fornecedor, e isso é trabalho recorrente que não existiria no n8n Cloud.
* O n8n auto-hospedado não traz painel de custo de LLM pronto, logo a instrumentação de tokens precisará ser construída, o que a Etapa 2 vai cobrar.
* Manter um motor low-code significa conviver com limitações de expressividade nos *Code nodes* e com um JSON grande e pouco amigável a revisão por diferença de texto.
* Fixar a imagem do n8n em uma versão específica protege contra quebra inesperada, porém cria dívida de atualização que alguém terá de pagar.

### Consequências neutras, que vale registrar

* A chamada ao provedor de LLM continua sendo transferência internacional de dados, independentemente de onde o n8n esteja hospedado. A auto-hospedagem reduz a superfície do problema, embora não o elimine, e a base legal dessa transferência precisa ser documentada na Etapa 2.

## Alternativas descartadas e o porquê

**B. n8n Cloud.** Resolveria disponibilidade e backup sem esforço, e é a opção mais rápida
para chegar ao ar. Foi descartada por dois motivos: reduz o controle sobre onde o dado
sigiloso repousa, e dificulta o *deploy* automatizado, porque a publicação do fluxo tende a
depender da interface. Perdeu justamente nos critérios de maior peso.

**C. Make.com.** Plataforma competente, mas migrar para ela significaria reconstruir o
cenário do zero em outro paradigma, o que contraria a regra do exercício. Some-se o
versionamento em Git menos natural e o aprisionamento mais forte. Foi a pior pontuação.

**D. Reescrita em Python com FastAPI.** Seria a melhor engenharia se o projeto começasse
agora, com controle total sobre dado, teste e observabilidade. Descartada porque o enunciado
veda a reescrita e porque consumiria até a semana 6 o tempo que precisa ir para *hardening* e
documentação. Fica anotada como caminho natural caso o produto cresça além do que um motor
de automação comporta.

## Validação

A decisão se confirma se, ao fim da Etapa 1, o *pipeline* publicar o workflow sem intervenção
manual e os três smoke tests passarem contra a URL pública. Se o *deploy* automatizado não se
sustentar em instância própria, esta ADR deve ser revisada, e a opção B volta à mesa.
