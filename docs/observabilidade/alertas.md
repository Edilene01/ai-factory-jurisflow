# Catálogo de alertas

Alerta sem ação é ruído, e ruído treina a equipe a ignorar o painel. Cada entrada aqui
declara **prioridade, público, canal e a ação esperada**. Se uma linha não souber dizer o que
alguém deve fazer ao recebê-la, ela não deveria existir.

**Atualizado em:** 19/10/2026

---

## Escala de prioridade

| Nível | Significa | Prazo de resposta | Como chega |
|---|---|---|---|
| **P1** | Cliente afetado agora, ou caso jurídico se perdendo em silêncio | Imediato, inclusive fora do horário comercial | `#juris-ops` com menção a `@plantao-plataforma` |
| **P2** | Degradação real, sem perda imediata de caso | Mesmo dia útil | `#juris-ops`, sem menção |
| **P3** | Tendência que merece olhar, não correr | Revisão semanal | Resumo às segundas em `#juris-ops` |

O público é o mesmo nos três níveis, **quem opera a plataforma**, e o que muda é a urgência
com que a mensagem interrompe. Alerta de negócio para o time jurídico não entra neste
catálogo: a equipe já recebe os casos nos canais de área, e duplicar isso como alerta
transformaria o canal de operação em repetição do fluxo normal.

---

## Catálogo

| # | Alerta | Condição | P | Ação esperada |
|---|---|---|---|---|
| **A-01** | Instância fora do ar | `/healthz` sem resposta por 2 verificações seguidas | **P1** | Conferir o serviço no painel do Railway. É o alerta que faltava quando a instância do n8n Cloud desapareceu em outubro |
| **A-02** | Fluxo em silêncio | Volume < 20% da média da mesma hora nos 7 dias anteriores, em horário comercial | **P1** | Testar o formulário do site de ponta a ponta. Causa provável fora do JurisFlow: o site parou de enviar |
| **A-03** | Zero intakes | Nenhum intake por 2 h em horário comercial | **P1** | Mesma ação do A-02. Existe como rede de segurança enquanto não há média histórica |
| **A-04** | Erro sistêmico | Taxa de erro > 5% em 15 min | **P1** | Identificar a causa pela coluna de span que falhou e avaliar desligar o workflow, para que o formulário pare de responder sucesso ao cliente |
| **A-05** | Erro acima do tolerado | Taxa de erro > 1% em 1 h | **P2** | Agrupar por causa. Falha do provedor aciona o *fallback*; falha de entrega no Slack é mais grave, porque o cliente já recebeu confirmação |
| **A-06** | SLA em risco | p95 da duração total > 60 s em 1 h | **P2** | É o número contratado no briefing. Verificar o span `classificacao_llm`, que domina o caminho |
| **A-07** | Resposta malformada do provedor | Motivo *"falha ao interpretar a classificacao"* > 2% em 1 h | **P2** | Sintoma técnico, não caso difícil. Conferir se o provedor mudou o formato de resposta |
| **A-08** | Custo anômalo | Custo do dia > 2× a mediana dos 7 dias anteriores | **P2** | Procurar laço de repetição, *retry* descontrolado ou prompt que cresceu |
| **A-09** | Custo estrutural | Projeção mensal > US$ 30 | **P2** | Quase 4× a linha de base. Revisar modelo, prompt e volume |
| **A-10** | Purga de retenção não executou | A segunda via, no GitHub Actions, removeu alguma linha, ou falhou | **P2** | **Já implementado** em [`retencao.yml`](../../.github/workflows/retencao.yml). Significa que a via do n8n não rodou, e que há dado pessoal além do prazo declarado |
| **A-11** | Classificador degradando | Taxa de revisão manual > 15% em 24 h | **P3** | Revisar as definições de área no *system prompt* contra os casos que caíram em triagem manual |
| **A-12** | Área zerada | Qualquer área sem casos em 24 h | **P3** | Com cinco áreas e 2.500 casos diários, sugere roteamento quebrado |
| **A-13** | Volume acima do normal | Volume > 3× a média da mesma hora | **P3** | Campanha de marketing ou robô. Checar a métrica de custo |

---

## Por que o A-02 é P1 e o A-13 é P3

São os dois lados da mesma métrica, com urgências opostas, e a assimetria é deliberada.

Volume **baixo** significa que pessoas pediram ajuda jurídica e o pedido não chegou a
ninguém. Não há erro, não há log, não há reclamação: o dano é invisível e não se recupera,
porque quem não foi atendido procurou outro escritório. É exatamente o cenário que o
enunciado da Etapa 2 descreve ao dizer que um sistema em produção *"pode falhar em silêncio
sem ninguém perceber"*.

Volume **alto** custa dinheiro e aparece na métrica de custo de qualquer forma. Dá para
olhar na segunda-feira.

---

## Estado de implantação

| Alerta | Situação |
|---|---|
| A-10 | **Implementado** no `retencao.yml`, ainda não executado: falta `DATABASE_URL` nos *Environments* |
| A-01 | Implementável hoje pelos alertas nativos do Railway, incluídos no plano Hobby |
| A-02 a A-09, A-11 a A-13 | **Especificados, não implementados.** Dependem da trilha de auditoria gravando em Postgres |

Nenhum destes alertas disparou de verdade ainda. A rubrica pede alerta **funcional**, e
provocar um de propósito para capturar a evidência é o passo 6 do
[plano de instrumentação](plano-instrumentacao.md).

---

## Como provocar um alerta para a evidência

O A-10 é o mais fácil de demonstrar, e serve bem para o vídeo: inserir na
`jurisflow_trilha_auditoria` uma linha com `recebido_em` de treze meses atrás e rodar o
workflow de retenção à mão. A purga remove a linha, o contador deixa de ser zero e o alerta
dispara em `#juris-ops` dizendo que a via do n8n não rodou.

É demonstração honesta: o alerta dispara pela condição real que ele monitora, com dado
sintético, e não por um gatilho de mentira criado para a gravação.
