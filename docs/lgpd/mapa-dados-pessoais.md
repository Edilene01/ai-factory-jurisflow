# Mapa de dados pessoais

Registro das operações de tratamento do JurisFlow Case Intake, na forma do art. 37 da Lei
nº 13.709/2018 (LGPD). Cada linha descreve um ponto real do fluxo, lido do workflow
versionado em [`workflows/jurisflow-intake.json`](../../workflows/jurisflow-intake.json), e
não uma intenção de projeto. Quando o documento afirma que um dado não é persistido, a
afirmação corresponde a uma configuração verificável, indicada na própria linha.

**Atualizado em:** 19/10/2026 · **Versão do sistema:** v1.0.0

---

## 1. Papéis

O JurisFlow é um serviço prestado a cerca de 180 escritórios. O formulário de intake vive no
site de cada escritório, e é o escritório quem mantém a relação com a pessoa que o preenche.
Daí a distribuição de papéis:

| Agente | Papel | Fundamento |
|---|---|---|
| Escritório contratante | **Controlador** | Art. 5º, VI. Define a finalidade e os meios do tratamento dos casos que recebe |
| JurisFlow | **Operador** | Art. 5º, VII. Trata os dados em nome do escritório, nos limites do contrato |
| OpenAI, Slack, Railway | **Suboperadores** | Contratados pelo JurisFlow para executar parte do tratamento, com autorização do controlador |
| JurisFlow (trilha de auditoria e logs de segurança) | **Controlador** | Art. 5º, VI. Aqui a finalidade é própria: medir a saúde do serviço e sustentar a prestação de contas do art. 37 |

Essa dupla condição do JurisFlow não é uma inconsistência. É o desenho comum de quem presta
serviço e, ao mesmo tempo, precisa operar a própria plataforma. O que separa um papel do
outro é a finalidade: tratar o caso é operação; medir a latência do próprio sistema é
controle.

**Encarregado (art. 41):** a indicação é obrigação do controlador. O contrato de prestação de
serviços deve registrar o canal do encarregado de cada escritório, para onde o JurisFlow
encaminha as requisições de titular que chegarem diretamente a ele.

---

## 2. Pontos de coleta e de tratamento

| # | Ponto | Dados pessoais | Titular | Finalidade | Base legal | Retenção |
|---|---|---|---|---|---|---|
| **PC-01** | `POST /webhook/intake`, vindo do formulário do site | `nome_cliente`, `cpf`, `descricao_caso`, `origem` | Pessoa que procura o escritório | Triagem do caso e encaminhamento ao time competente | **Art. 7º, V** – procedimentos preliminares relacionados a contrato, a pedido do titular | Não persistido. Trafega em memória durante a execução |
| **PC-02** | Metadados da requisição HTTP | Endereço IP, *user-agent* | Idem PC-01 | Segurança do endpoint e contenção de abuso | **Art. 7º, IX** – legítimo interesse (LIA-01) | 72 horas, apenas em execuções com erro |
| **PC-03** | Dados sensíveis eventualmente contidos no relato | Saúde, convicção religiosa, vida sexual, filiação sindical, dado referente a infração penal | Idem PC-01 | Idem PC-01 | **Art. 11, II, "d"** – exercício regular de direitos | Idem PC-01 |
| **PC-04** | Nó `Sanitizar Entrada`, derivados mascarados | `nome_mascarado`, `cpf_mascarado`, `protocolo` | Idem PC-01 | Identificar o caso para a equipe sem expor o titular | **Art. 7º, V** (mesma finalidade do PC-01) | 90 dias, no Slack |
| **PC-05** | Nó `OpenAI Classificar`, texto enviado ao provedor | `descricao_sanitizada`, sem CPF, CNPJ, e-mail e telefone | Idem PC-01 | Classificação automática de área e urgência | **Art. 7º, V**, c/c **art. 33, IX**, quanto à transferência internacional | Não persistido pelo JurisFlow. Ver [`transferencia-internacional.md`](transferencia-internacional.md) |
| **PC-06** | Nós `Slack #juris-*`, mensagem no canal da área | `nome_mascarado`, `cpf_mascarado`, **`descricao_caso` íntegra**, `protocolo`, área, urgência | Idem PC-01 | Entrega do caso ao time responsável | **Art. 7º, V** | 90 dias |
| **PC-07** | Nó `Registro de Auditoria` | `protocolo`, `recebido_em`, `latencia_ms`, área, urgência, `origem`, nº de caracteres do relato | Pseudonimizado | Observabilidade, métricas de serviço e prestação de contas | **Art. 7º, IX** – legítimo interesse (LIA-02) | 12 meses |
| **PC-08** | Execuções com erro gravadas pelo n8n | Todos os dados do PC-01, **sem máscara** | Idem PC-01 | Diagnóstico de falha | **Art. 7º, IX** – legítimo interesse (LIA-01) | 72 horas |
| **PC-09** | Terceiros citados no relato | Nome, qualificação e fatos sobre parte contrária, testemunhas, familiares | Terceiro, que não preencheu o formulário | Instrução do caso | **Art. 7º, IX** (LIA-03) e, para dado sensível, **art. 11, II, "d"** | Igual ao PC-06 |
| **PC-10** | Resposta ao formulário, nó `Responder Intake` | `protocolo`, área, urgência, `revisao_manual` | — | Devolver o protocolo ao site | Não há dado pessoal na resposta | Não se aplica |

### Por que não é consentimento

Quem preenche um formulário de intake está pedindo atendimento jurídico. O tratamento é
**necessário para procedimentos preliminares relacionados a contrato**, hipótese do art. 7º,
V. Pedir consentimento aqui seria pior do que inútil: criaria a aparência de uma escolha que
não existe, já que sem os dados não há triagem possível, e um consentimento revogável a
qualquer tempo, na forma do art. 8º, § 5º, deixaria o escritório sem base para tratar um caso
que ele precisa tratar.

Os dados sensíveis do PC-03 não contam com a hipótese de execução de contrato, que o art. 11
não repete. A base correta é o art. 11, II, "d", exercício regular de direitos, que é
exatamente o que a advocacia faz. O relato de uma demissão por doença, de um crime ou de uma
negativa de plano de saúde chega sem que o sistema possa evitá-lo, e por isso a hipótese
precisa estar prevista desde já, em vez de ser descoberta no primeiro caso concreto.

---

## 3. Avaliações de legítimo interesse

O art. 10 exige que o legítimo interesse se apoie em finalidade concreta e passe pelo teste
de necessidade e de expectativa do titular. As três hipóteses usadas acima:

### LIA-01 — Logs de erro e metadados de requisição (PC-02, PC-08)

**Finalidade legítima.** Um endpoint público sem registro de falha é um endpoint que não pode
ser consertado. O art. 46 impõe medidas de segurança, e diagnosticar erro é uma delas.

**Necessidade.** O payload cru só é guardado quando a execução falha, nunca quando ela dá
certo, por efeito de `saveDataSuccessExecution: "none"` nas configurações do workflow. Sem o
dado de entrada não se reproduz a falha.

**Expectativa do titular.** Quem envia um formulário espera que ele funcione e que, quebrando,
alguém conserte. O prazo de 72 horas é o que cobre um fim de semana, e não mais do que isso.

**Salvaguarda.** Purga automática em 72 horas, descrita na
[política de retenção](politica-retencao-exclusao.md). Acesso restrito a quem opera a
instância.

### LIA-02 — Trilha de auditoria (PC-07)

**Finalidade legítima.** Medir latência, custo, volume e taxa de erro, e sustentar o registro
do art. 37.

**Necessidade.** O registro guarda o protocolo, não o titular. Nenhum nome, CPF ou trecho do
relato entra nele, apenas o número de caracteres. É o mínimo que ainda permite medir.

**Expectativa.** Não há surpresa em um serviço medir a si mesmo com dado pseudonimizado.

**Salvaguarda.** A pseudonimização está no próprio código do nó, e não em uma promessa: o
`Registro de Auditoria` monta o objeto campo a campo, de modo que um dado identificável só
entraria ali por alteração deliberada do workflow versionado, que é revisada em *pull
request*.

### LIA-03 — Terceiros citados no relato (PC-09)

**Finalidade legítima.** Não existe caso jurídico sem a outra parte. O relato de uma demissão
nomeia o empregador; o de uma agressão, o agressor.

**Necessidade.** O sistema não coleta esses dados: ele os recebe dentro de um texto livre que
o titular escreveu. A alternativa seria recusar o relato.

**Expectativa e balanceamento.** O terceiro não tem como esperar essa comunicação, o que pesa
contra. Em compensação, o destino é um canal interno restrito à equipe do escritório, sob
sigilo profissional, e o dado não chega ao provedor de LLM em formato estruturado. O
balanceamento favorece o tratamento pelo mesmo fundamento que permite ao advogado ouvir o
cliente: o exercício do direito de defesa pressupõe conhecer os fatos.

**Salvaguarda.** Retenção de 90 dias no Slack e ausência de qualquer indexação por nome de
terceiro.

---

## 4. Sigilo profissional

A `descricao_caso` não é um campo de formulário qualquer. É comunicação entre quem procura um
advogado e o escritório, protegida pelo art. 7º, II, da Lei nº 8.906/1994 e pelas regras de
sigilo do Código de Ética e Disciplina da OAB, que alcançam os fatos conhecidos em razão da
profissão ainda que a contratação não se concretize.

Isso tem duas consequências de engenharia, e as duas já estão no sistema:

1. O relato íntegro **nunca** sai do perímetro do escritório em direção ao provedor de LLM. O
   que sai é a `descricao_sanitizada`, e a sanitização acontece no nó anterior à chamada, e
   não como filtro de saída.
2. O Slack recebe o relato íntegro porque o destinatário é a própria equipe do escritório,
   que é quem já teria acesso a ele. O que o Slack não recebe é a identificação civil do
   titular, que vai mascarada.

A escolha de mascarar nome e CPF no canal interno pode parecer excesso, já que a equipe
precisará do nome quando assumir o caso. É deliberada: o canal de triagem é lido por várias
pessoas, inclusive por quem não vai atuar naquele caso, e o protocolo basta para que o
responsável recupere a identificação no momento em que ela for necessária.

---

## 5. Limite conhecido da sanitização

A função `sanitizarTexto` remove CPF, CNPJ, e-mail e telefone por expressão regular. Ela
**não** remove nomes próprios, endereços, nome de empregador, número de processo nem datas
singulares. Um relato como *"fui demitida da Padaria do Seu Jorge, em Macapá, depois de
avisar que estava grávida"* chega ao provedor com identificadores indiretos intactos.

O risco é real e está registrado aqui porque fingir que a expressão regular resolve tudo seria
pior do que admitir o que ela não cobre. O que sustenta a adequação hoje:

* O provedor recebe o texto sem qualquer chave de ligação com o titular. Não há protocolo,
  nome, CPF ou identificador de sessão na chamada.
* O volume trafegado é mínimo: uma única mensagem de usuário, sem histórico, e `maxTokens: 60`
  na resposta.

O tratamento desse resíduo é candidato natural à otimização medida da Etapa 2, por
reconhecimento de entidades nomeadas antes da chamada, e está anotado como tal no
[checklist da Etapa 2](../checklist-etapa-2.md).

---

## 6. Direitos do titular

As requisições do art. 18 chegam ao escritório, que é o controlador. O JurisFlow, como
operador, responde ao controlador no prazo que o contrato fixar, e nunca diretamente ao
titular.

| Direito | Art. | Como o sistema atende |
|---|---|---|
| Confirmação e acesso | 18, I e II | Busca pelo protocolo. Sem protocolo, a busca é feita no canal do Slack, pelo período do caso |
| Correção | 18, III | O relato não é editável no sistema. A correção se faz por novo intake, com referência ao protocolo anterior |
| Anonimização, bloqueio ou eliminação de dado desnecessário | 18, IV | Procedimento de exclusão por protocolo, em [`politica-retencao-exclusao.md`](politica-retencao-exclusao.md) |
| Portabilidade | 18, V | Exportação do registro do Slack e da linha da trilha de auditoria, em JSON |
| Eliminação | 18, VI | Mesmo procedimento do inciso IV, com as ressalvas do art. 16 |
| Informação sobre compartilhamento | 18, VII | [`transferencia-internacional.md`](transferencia-internacional.md) lista todos os destinatários |
| Revisão de decisão automatizada | 20 | A classificação é automatizada, e por isso existe o desvio para `#juris-triagem-manual`. Nenhum caso é descartado pela máquina: o que ela não classifica, uma pessoa classifica |

O art. 20 merece destaque. A triagem automática decide para qual equipe um caso vai, o que
afeta o tempo de resposta a quem está pedindo ajuda. O desenho do workflow já responde a isso
ao tornar visível toda classificação duvidosa, em vez de empurrá-la para o canal mais
provável, que era o comportamento do protótipo herdado e consta da auditoria como achado.

---

## 7. O que este mapa não cobre

* **A base de dados do escritório depois do intake.** O JurisFlow entrega o caso no Slack e
  encerra a sua participação. O que acontece em seguida é tratamento do controlador.
* **O formulário do site.** O campo, o aviso de privacidade e o registro do aceite são
  responsabilidade do escritório. O JurisFlow recebe o POST já preenchido.
* **Dados de autenticação dos operadores do n8n.** Tratados pela plataforma, fora do fluxo de
  intake.
