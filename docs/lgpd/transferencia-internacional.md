# Transferência internacional de dados

Toda chamada ao provedor de LLM é transferência internacional. Toda mensagem entregue no
Slack também é. Nenhum dos dois serviços processa no Brasil, e o fato de a chamada sair de um
container hospedado em São Paulo não muda nada: o que define a transferência é onde o dado é
tratado, não de onde ele parte.

Este documento identifica cada fluxo que cruza a fronteira, a hipótese do art. 33 da LGPD que
o autoriza e o que ainda falta formalizar.

**Atualizado em:** 19/10/2026

---

## 1. Fluxos que saem do Brasil

| # | Destinatário | País | Papel | O que recebe | Hipótese do art. 33 |
|---|---|---|---|---|---|
| **TI-01** | OpenAI, L.L.C. | Estados Unidos | Suboperador | `descricao_sanitizada`, sem CPF, CNPJ, e-mail, telefone nem chave de ligação com o titular | **Inciso IX**, c/c art. 7º, V |
| **TI-02** | Slack Technologies (Salesforce) | Estados Unidos | Suboperador | `nome_mascarado`, `cpf_mascarado`, `descricao_caso` íntegra, `protocolo`, área, urgência | **Inciso IX**, c/c art. 7º, V |
| **TI-03** | Railway Corp. | Estados Unidos | Suboperador | Hospeda a instância e o banco. Em repouso, apenas execuções com erro contêm dado pessoal | **Inciso IX**, c/c art. 7º, V |
| **TI-04** | GitHub, Inc. | Estados Unidos | — | Código, workflow versionado e execução dos *smoke tests* | **Não se aplica**: só trafega dado sintético |

O TI-04 está na tabela justamente para registrar que foi examinado e descartado. Os *smoke
tests* usam o CPF `111.444.777-35`, que é um número válido pelo dígito verificador e não
pertence a ninguém, e descrições de caso fictícias. Nenhum dado de pessoa real passa pelo
*pipeline*.

---

## 2. Por que o inciso IX, e não os outros

O art. 33 lista as hipóteses em que a transferência é permitida. A leitura rápida costuma
parar no inciso VIII, o do consentimento específico e em destaque, e é a leitura errada para
este caso.

**Inciso I — país com grau de proteção adequado.** Não serve. A ANPD ainda não reconheceu os
Estados Unidos como país de proteção adequada.

**Inciso II — garantias oferecidas pelo controlador.** Serve, e é o caminho que o projeto
precisa percorrer até o fim. Ver a seção 3.

**Inciso VIII — consentimento específico.** Não serve, pela mesma razão pela qual o
consentimento não é a base do tratamento principal: quem pede atendimento jurídico não está
em posição de escolher se a triagem pode ou não usar um classificador hospedado fora do país.
Um consentimento colhido nessas condições é aparência de escolha.

**Inciso IX — transferência necessária para atender as hipóteses do art. 7º, II, V e VI.**
É a hipótese aplicável. O tratamento principal se funda no art. 7º, V, procedimentos
preliminares relacionados a contrato a pedido do titular, e a transferência é necessária para
realizá-lo: sem a chamada ao provedor não há classificação, e sem a entrega no Slack não há
caso encaminhado a ninguém.

A palavra que carrega o peso é **necessária**. Ela não dispensa a demonstração de que a
transferência é o meio adequado e minimamente invasivo, e é isso que a seção 4 registra.

---

## 3. O que falta formalizar

O inciso IX autoriza a transferência, mas não substitui o dever de garantir que o
destinatário observe o padrão da LGPD. É aqui que está a pendência real do projeto, e ela é
contratual, não técnica.

A ANPD publicou em **23 de agosto de 2024** a **Resolução CD/ANPD nº 19/2024**, que aprovou o
Regulamento de Transferência Internacional de Dados e o texto das **cláusulas-padrão
contratuais (CCPs)**, regulamentando os arts. 33 a 36 da LGPD. A norma concedeu **12 meses**
para que os contratos existentes fossem adaptados, prazo que **encerrou em 23 de agosto de
2025**.

Duas consequências práticas, ambas já vencidas no calendário:

1. **As CCPs da ANPD devem ser incorporadas na íntegra**, sem modificação do texto. Elas podem
   estar em instrumento próprio ou dentro de um contrato mais amplo.
2. **Cláusulas próprias ou estrangeiras não bastam mais.** Quem usava modelos próprios ou as
   *standard contractual clauses* europeias precisa substituí-los pelas CCPs da ANPD ou obter
   da ANPD o reconhecimento de equivalência como cláusulas específicas.

| Pendência | Responsável | Situação |
|---|---|---|
| Incorporar as CCPs da ANPD ao contrato com a OpenAI (*Data Processing Addendum*) | Jurídico do escritório contratante, com apoio do JurisFlow | **Em aberto** |
| Idem, para Slack e Railway | Idem | **Em aberto** |
| Registrar a autorização do controlador para a subcontratação de cada suboperador (art. 39) | Contrato de prestação de serviços | **Em aberto** |
| Confirmar no sítio da ANPD se houve prorrogação ou alteração do prazo após julho de 2025 | Jurídico | **A verificar** |

Registrar isso como pendência é deliberado. O sistema está tecnicamente adequado e
contratualmente incompleto, e trocar uma coisa pela outra seria exatamente o tipo de
afirmação sem lastro que a Etapa 2 pede para evitar.

---

## 4. Medidas que reduzem o que atravessa a fronteira

A melhor proteção em transferência internacional é não transferir. O que o sistema já faz,
verificável no workflow:

**Minimização antes da chamada.** O nó `Sanitizar Entrada` roda **antes** do nó
`OpenAI Classificar`, e não depois. O provedor recebe a `descricao_sanitizada`, da qual foram
removidos CPF, CNPJ, e-mail e telefone. O `nome_cliente` e o `cpf` nunca entram na chamada,
em nenhuma forma.

**Ausência de chave de ligação.** A chamada ao provedor não leva protocolo, identificador de
sessão, de usuário ou de escritório. Mesmo que o provedor retivesse o texto, ele não teria
como vinculá-lo a uma pessoa a partir dos próprios registros.

**Volume mínimo.** Uma única mensagem de usuário, sem histórico de conversa, com
`temperature: 0` e `maxTokens: 60` na resposta. Não há *fine-tuning*, não há *embedding*
persistido, não há base vetorial.

**Não persistência local.** `saveDataSuccessExecution: "none"` impede que o payload de
execuções bem-sucedidas fique no banco hospedado no exterior. Só a execução com erro
persiste, e por 72 horas.

### Configurações do provedor a confirmar

Três ajustes dependem da conta contratada e precisam ser verificados no painel, não presumidos:

* **Uso para treinamento.** Confirmar que os dados enviados pela API não alimentam
  treinamento de modelo, e guardar a evidência da configuração.
* **Retenção para monitoramento de abuso.** Verificar o prazo padrão de retenção do provedor e
  avaliar a contratação de *zero data retention*, quando disponível para a conta.
* **Residência de dados.** Verificar se o plano oferece processamento em região específica.

Enquanto não houver evidência dessas três configurações, a documentação não pode afirmar que
o provedor não retém nada. O que ela pode afirmar, e afirma, é o que o JurisFlow envia.

---

## 5. Risco residual

O que ainda atravessa a fronteira, declarado sem atenuação:

* **Identificadores indiretos no texto.** A sanitização por expressão regular não remove nomes
  próprios, endereços, nome de empregador nem número de processo. Um relato suficientemente
  específico permite reidentificação por quem já conheça o contexto. O limite está descrito na
  seção 5 do [mapa de dados pessoais](mapa-dados-pessoais.md), e a mitigação por
  reconhecimento de entidades nomeadas é candidata à otimização medida da Etapa 2.
* **Relato íntegro no Slack (TI-02).** É o fluxo com mais dado pessoal cruzando a fronteira, e
  o menos discutido, porque ninguém pensa em Slack como transferência internacional. É. A
  mitigação em vigor é o mascaramento da identificação civil e a retenção de 90 dias; a
  mitigação estrutural seria um canal de entrega hospedado no Brasil, o que está fora do
  escopo da disciplina mas fica registrado como dívida.
* **Dado sensível na origem.** Um relato pode conter informação de saúde ou referente a
  infração penal, e a sanitização não os remove, porque removê-los inviabilizaria a
  classificação. A base é o art. 11, II, "d", e a salvaguarda é a mesma minimização descrita
  acima.

---

## 6. Referências

* Lei nº 13.709/2018, arts. 7º, V; 11, II, "d"; 33, IX; 37; 39; 46.
* Resolução CD/ANPD nº 19, de 23 de agosto de 2024 — Regulamento de Transferência
  Internacional de Dados e cláusulas-padrão contratuais.
* [`mapa-dados-pessoais.md`](mapa-dados-pessoais.md) — pontos de coleta e bases legais.
* [`politica-retencao-exclusao.md`](politica-retencao-exclusao.md) — prazos e mecanismos de
  purga.
