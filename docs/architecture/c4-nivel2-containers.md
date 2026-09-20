# C4 nível 2 – Containers

Como o JurisFlow Case Intake está montado por dentro, e onde cada responsabilidade mora.

```mermaid
C4Container
    title Nível 2 – Containers do JurisFlow Case Intake

    Person(cliente, "Pessoa que procura o escritório")
    Person(advogado, "Time jurídico")

    System_Ext(site, "Site do escritório", "Formulário de intake")
    System_Ext(llm, "Provedor de LLM", "Classificação de área e urgência")
    System_Ext(slack, "Slack da JurisFlow", "6 canais de destino")
    System_Ext(gha, "GitHub Actions", "Pipeline de qualidade e entrega")

    Container_Boundary(prod, "Ambiente de produção (Railway)") {
        Container(n8n, "Instância n8n", "Docker, imagem fixada", "Executa o workflow Case Intake Router v1.0")
        Container(wf, "Workflow Case Intake Router", "JSON versionado no Git", "Webhook, sanitização, classificação, parse, resposta, roteamento e auditoria")
        ContainerDb(db, "Banco do n8n", "Postgres gerenciado", "Credenciais e metadados. Payload de execução com sucesso não é persistido")
    }

    Container_Boundary(dev, "Ambiente de desenvolvimento (Railway)") {
        Container(n8ndev, "Instância n8n de desenvolvimento", "Docker", "Mesmo workflow, secrets próprios, sem tráfego real")
    }

    Rel(cliente, site, "Preenche o formulário")
    Rel(site, n8n, "POST /webhook/intake com X-Jurisflow-Signature", "HTTPS")
    Rel(n8n, wf, "Carrega e executa")
    Rel(wf, llm, "Descrição sanitizada, sem CPF, e-mail ou telefone", "HTTPS")
    Rel(wf, slack, "Caso com nome e CPF mascarados, mais protocolo", "HTTPS")
    Rel(advogado, slack, "Assume o caso pelo protocolo")
    Rel(n8n, db, "Credenciais e metadados", "TLS")
    Rel(gha, n8n, "Publica o workflow e ativa", "API do n8n")
    Rel(gha, n8ndev, "Publica em develop", "API do n8n")
```

## Caminho de uma requisição

```mermaid
flowchart LR
    A[Webhook Site Form<br/>header auth] --> B[Sanitizar Entrada<br/>protocolo, máscara, scrub de PII]
    B --> C[OpenAI Classificar<br/>retry 3x, timeout 30s]
    C --> D[Parse Classificação<br/>try/catch, normalização]
    D --> E[Responder Intake<br/>protocolo e área]
    D --> F{Precisa de<br/>revisão manual?}
    D --> G[Registro de Auditoria<br/>sem dado identificável]
    F -- sim --> H[#juris-triagem-manual]
    F -- não --> I[Switch Área]
    I --> J[#juris-trabalhista]
    I --> K[#juris-civel]
    I --> L[#juris-tributario]
    I --> M[#juris-criminal]
    I --> N[#juris-consumidor]
```

## Decisões de desenho visíveis no diagrama

A sanitização vem antes da chamada ao modelo, e não depois, porque o objetivo é que o dado
identificável simplesmente não chegue ao provedor.

A resposta ao formulário sai logo após o parse, em paralelo ao roteamento, de modo que o site
recebe o protocolo e a área sem esperar a entrega no Slack. Isso corrige o achado CONF-04,
em que o formulário recebia sucesso mesmo quando o processamento falhava adiante.

O desvio de revisão manual existe para tornar visível o que antes era silencioso. Toda
classificação que o sistema não reconhece vai para um canal próprio, em vez de ser empurrada
para o Cível como acontecia no protótipo.
