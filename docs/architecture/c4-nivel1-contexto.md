# C4 nível 1 – Contexto

Quem usa o JurisFlow Case Intake e com que sistemas ele conversa. Este nível responde à
pergunta de negócio: o que entra, o que sai e quem depende disso.

```mermaid
C4Context
    title Nível 1 – Contexto do JurisFlow Case Intake

    Person(cliente, "Pessoa que procura o escritório", "Preenche o formulário de intake no site do escritório cliente")
    Person(advogado, "Time jurídico do escritório", "Recebe o caso já triado no canal da sua área")
    Person(eng, "Engenharia de automação", "Opera, versiona e publica o sistema")

    System(jurisflow, "JurisFlow Case Intake", "Recebe o formulário, classifica área e urgência, roteia para o time responsável e registra a triagem")

    System_Ext(site, "Site do escritório", "Formulário público de contato que dispara o webhook")
    System_Ext(llm, "Provedor de LLM", "Classifica área jurídica e urgência. Processamento fora do Brasil")
    System_Ext(slack, "Slack da JurisFlow", "Canais por área jurídica, mais o canal de triagem manual")
    System_Ext(github, "GitHub", "Guarda o workflow versionado e executa o pipeline de entrega")

    Rel(cliente, site, "Descreve o caso")
    Rel(site, jurisflow, "POST assinado no webhook de intake", "HTTPS")
    Rel(jurisflow, llm, "Envia a descrição sanitizada", "HTTPS")
    Rel(jurisflow, slack, "Publica o caso com identidade mascarada", "HTTPS")
    Rel(advogado, slack, "Assume o caso")
    Rel(eng, github, "Faz push na branch")
    Rel(github, jurisflow, "Publica o workflow e roda os smoke tests", "API do n8n")
```

## Fronteiras que este diagrama deixa explícitas

O dado pessoal entra por uma única porta, que é o webhook autenticado, e sai por duas: o
provedor de LLM, que recebe a descrição sanitizada, e o Slack, que recebe a descrição íntegra
com nome e CPF mascarados. Toda discussão de conformidade da Etapa 2 acontece nessas duas
setas.

O GitHub aparece como sistema externo de propósito. Ele não participa do fluxo de negócio,
apenas publica a configuração, e essa separação é o que permite dizer que o *deploy* é
automatizado sem que a entrega dependa de quem está no teclado.
