# ADR-003: Produção no n8n Cloud e desenvolvimento no Railway

* **Status:** aceita
* **Data:** 21/09/2026
* **Decisora:** Edilene Chagas Faria
* **Substitui:** ADR-002
* **Depende de:** ADR-001

## Contexto e definição do problema

A ADR-002 previu dois projetos no Railway, um por ambiente, com instâncias idênticas de n8n
auto-hospedado. Na execução, a conta ativada foi no n8n Cloud, que também consta da lista de
hospedagem permitida na linha 46 do BRIEFING.md.

Isso cria um problema novo, e é ele que esta ADR resolve: o n8n Cloud entrega uma instância
por assinatura, ao passo que a Etapa 1 exige ambientes de desenvolvimento e produção
realmente separados, com *secrets* distintos em cada um.

A restrição de orçamento continua valendo, com US$ 120 mensais cobrindo LLM, hospedagem e
observabilidade, e o prazo até a semana 6 desaconselha refazer o que já está em pé.

## Opções consideradas

* **A. Dois projetos no Railway**, conforme a ADR-002 original
* **B. Duas assinaturas do n8n Cloud**, uma por ambiente
* **C. n8n Cloud como produção e Railway como desenvolvimento**
* **D. n8n Cloud como produção e Docker local como desenvolvimento**

## Decisão

Escolhida a opção **C**: produção no n8n Cloud, desenvolvimento em container n8n no Railway.

O que pesou foi a combinação de três fatores. A assinatura do Cloud já está ativa, de modo
que descartá-la seria desperdício. Os dois ambientes ficam públicos e alcançáveis pelo
*pipeline*, condição sem a qual o *deploy* automatizado em desenvolvimento não existe. E os
segredos são efetivamente distintos, já que cada instância tem a sua própria credencial de
webhook, a sua chave da OpenAI e a sua chave de API do n8n.

### Consequências positivas

* Produção passa a ter operação gerenciada, com disponibilidade e backup por conta do fornecedor, o que elimina boa parte do trabalho recorrente que a ADR-001 assumiu como custo da auto-hospedagem.
* Desenvolvimento fica em container próprio, mais barato e descartável, onde experimentar não arrisca o ambiente que será avaliado.
* O `scripts/deploy_workflow.py` funciona igual nos dois, porque ambos expõem a API pública do n8n, e o *pipeline* não precisa de tratamento especial por ambiente.

### Consequências negativas

* **A paridade entre ambientes se perde, e essa é a consequência mais séria.** A principal virtude de ter dois ambientes é que o de desenvolvimento reproduz o de produção; aqui eles rodam em plataformas diferentes, de sorte que um workflow validado em desenvolvimento pode falhar em produção por diferença de versão ou de configuração do n8n.
* A versão do n8n no Cloud é determinada pelo fornecedor e muda sem aviso, enquanto a do Railway fica fixada na imagem. A divergência tende a crescer com o tempo.
* Operar dois painéis distintos custa atenção, e a chance de configurar algo no ambiente errado aumenta.
* A decisão foi imposta por limite de assinatura, não escolhida por desenho. Se o orçamento permitisse, duas instâncias idênticas seriam melhores.

### Mitigações adotadas

Os três smoke tests rodam contra os dois ambientes no *pipeline*, o que faz a divergência
aparecer como falha antes de chegar ao usuário. Sempre que o Cloud anunciar a versão em uso,
a imagem do Railway deve ser aproximada dela.

## Alternativas descartadas e o porquê

**A. Dois projetos no Railway.** Continua sendo a solução tecnicamente mais limpa, porque
entrega paridade real. Foi descartada apenas porque a assinatura do Cloud já está ativa, e
abandoná-la agora seria gasto perdido sem ganho de nota. Permanece como plano de retorno caso
o Cloud se mostre restritivo.

**B. Duas assinaturas do n8n Cloud.** Resolveria a paridade sem esforço de operação, embora
duplicasse o custo fixo e comprimisse a margem que precisa sobrar para o consumo de LLM
dentro do teto de US$ 120.

**D. Docker local como desenvolvimento.** É o caminho mais barato, porém tem um defeito que
o inviabiliza: instância em `localhost` não é alcançável pelo GitHub Actions, de modo que o
*deploy* automatizado em desenvolvimento deixaria de existir, e com ele parte do critério que
mais pesa na Etapa 1.

## Validação

A decisão se confirma quando o *pipeline* publicar nos dois ambientes sem intervenção manual
e os três smoke tests passarem contra as duas URLs. Se a divergência de versão entre Cloud e
Railway causar falha recorrente, esta ADR deve ser revista em favor da opção A.
