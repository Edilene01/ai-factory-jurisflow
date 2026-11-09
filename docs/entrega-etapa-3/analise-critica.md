# Análise crítica · JurisFlow

**Edilene Chagas Faria** · Novembro de 2026

---

## Parte A: revisitando o briefing

**Aplicação:** https://ai-factory-jurisflow-production.up.railway.app , formulário em `/` e
painel de operação em `/painel`. **Código:** https://github.com/Edilene01/ai-factory-jurisflow.
Não há login, e isso foi decisão, não omissão: o formulário é público por natureza, e o painel
mostra apenas agregados, sem nome, CPF ou trecho de relato.

A Renata pediu três coisas, e o resultado não é uniforme.

**SLA de triagem de 60 segundos no p95.** Cumprido, com folga grande demais para ser
confortável. O p95 medido é de 1,27 segundo, quarenta e sete vezes abaixo do contratado. Folga
assim não é mérito: é sinal de SLA negociado sem medição prévia. Cinco segundos seria
compromisso mais útil ao negócio.

**Auditoria real persistida, com área, urgência, custo e taxa de fallback humano.** Cumprido. A
`jurisflow_trilha_auditoria` guarda os quatro campos, mais latência e tokens, e tem perto de
mil registros. O custo deixou de ser estimativa quando passei a persistir a contagem de tokens
que o próprio provedor devolve.

**Pitch ao Comitê de Produto.** É o que esta entrega acompanha.

O sistema resolve o problema **de tempo**: o caso que levava de 3 a 6 horas chega à equipe em
segundos, e a urgência é reconhecida em vez de ignorada. Não resolve o **de acerto**: meu
corpus tem doze descrições, todas claras, e não sei com evidência o quanto o classificador
erra em caso difícil. Velocidade comprovada, qualidade presumida. Basta hoje, e não bastará em
três meses.

---

## Parte B: defesa das decisões

**1. Manter o n8n em vez de reescrever (ADR-001).** O prazo era de 12 semanas e o orçamento de
US$ 120 mensais cobria LLM, hospedagem e observabilidade. Reescrever em Python consumiria
metade do prazo reproduzindo o que já existia, antes de começar segurança, conformidade e
observabilidade. A decisão se pagou de um jeito que eu não previ: quando a instância de
produção desapareceu, e de novo quando o volume voltou vazio, o workflow sobreviveu porque
vive no Git. **O que custou:** o nó nativo da OpenAI, na versão 2.40.5, resolvia para a raiz da
API em vez do endpoint de chat, devolvia a mensagem de boas-vindas do provedor e o sistema
tratava aquilo como classificação malformada. Perdi quase um dia. Em código escrito por mim, o
erro teria aparecido na primeira linha de log.

**2. Sanitizar antes da chamada, e não depois (ADR-001 e mapa de dados).** O protótipo mandava
o relato inteiro ao provedor, e nome e CPF sem máscara ao Slack. O nó `Sanitizar Entrada`
separa duas versões do intake: a íntegra vai para a equipe do escritório, e a sem CPF, CNPJ,
e-mail e telefone é a única que sai do país. O dado identificável não chega ao provedor porque
não é enviado, e não porque alguém o removeu depois. O briefing já avisava que a descrição do
caso pode revelar saúde, situação financeira ou processo criminal, e o sigilo profissional
cobre a relação cliente-advogado. Fundamento nos arts. 7º, V, e 33, IX, da Lei nº 13.709/2018.
**O que custou:** a expressão regular é cega a nome próprio, endereço e nome de empregador,
limite que escolhi declarar na seção 5 do mapa de dados em vez de dar por resolvido.

**3. Aplicação com ponte, em vez de página estática (ADR-007).** O webhook exige o header
`X-Jurisflow-Signature`, e qualquer pessoa leria esse valor no código de uma página estática. É
o mesmo segredo que o GitHub Environment guarda, e publicá-lo no navegador seria o critério de
anulação da própria etapa. O backend em FastAPI o mantém no servidor, e rendeu ainda o limite
de cinco requisições por minuto por IP, a `origem` fixada no servidor e nenhum registro do
corpo em log. **O que custou:** mais um serviço para manter e mais um ponto de falha.

**O que funciona bem.** A classificação de urgência acerta porque o critério está no prompt em
termos concretos, prazo legal vencendo, prisão, audiência marcada, e não como adjetivo vago. O
desvio para triagem manual funciona porque o `Parse Classificação` trata a incerteza como
resultado legítimo; o protótipo mandava para o Cível, em silêncio, tudo o que não reconhecia.

**O que não funciona.** A medição de qualidade: doze descrições inequívocas fazem o acerto de
100% dizer menos do que parece. A entrega no Slack falha sem reprocessar: o caso é marcado com
`causa_falha: 'slack'` e dispara alerta, mas ninguém o reenvia, e o formulário já respondeu
"recebido" ao cliente. Vi isso em produção, com 38 casos de Consumidor, antes de descobrir que
o nó `Switch` na versão 1 aceita no máximo quatro saídas e eu tinha cinco áreas. E os dois
ambientes estão na mesma plataforma: a ADR-005 recuperou a paridade perdida pela ADR-003 e
criou, com isso, um ponto único de falha.

**Limitações conhecidas.** *De dados:* tudo foi medido com carga sintética, 200 intakes de um
corpus de doze descrições numa janela de um minuto, longe dos 2.500 casos diários
concentrados em horário comercial. *De tecnologia:* o limite de taxa é por processo, então mais
de uma réplica multiplicaria o teto efetivo. *De escopo:* o sistema não acompanha o caso depois
da entrega, e a métrica mede quanto ele admite não saber, não se acerta quando diz saber. *De
conformidade:* as cláusulas-padrão da Resolução CD/ANPD nº 19/2024 ainda não foram
incorporadas aos contratos, pendência contratual registrada em
`docs/lgpd/transferencia-internacional.md`.

---

## Parte C: visão de futuro e aprendizados

Professor, como de costume, as suas propostas de atividades das HPs são muito desafiadoras para mim! Eu esperava conseguir rodar suave as etapas 1 e 2, além de criar o meu vídeo de pitch usando alguma ferramenta de geração de vídeo com o meu avatar de IA.
Mas não saiu como o planejado: a HP1 entreguei quase no prazo fatal e perdi o prazo para postar a HP2 (enviei já no prazo da recuperação)...
Não curti muito trabalhar em um protótipo herdado (principalmente porque estava cheio de problemas e bugs, pra variar). Justamente nesse ponto, a auditoria do protótipo encontrou 25 achados, seis críticos, e foi escrita antes de qualquer código. A plataforma mudou três vezes: ADR-002 em 18/09 escolhe Railway nos dois ambientes, ADR-003 em 21/09 move produção para o n8n Cloud, ADR-004 em 19/10 manda reconstruir no n8n Cloud, e a ADR-005 no mesmo dia volta para o Railway. A ADR-004 foi substituída no dia em que nasceu. O impedimento que derrubou a ADR-004, a conta trial não emitir chave de API, só apareceu depois da decisão tomada. A instância de produção sumiu duas vezes, e o banco voltou vazio uma delas. Não havia rotina de backup, e ainda não há (a observabilidade foi desenhada na Etapa 2, e o primeiro bug que ela expôs existia desde o protótipo).
Ainda sobre essa atividade: aprendi um montão de coisas que não sabia e teve coisas que custaram caro por motivos bestas, como o `HTTP 400 Bad Request` sem corpo, o `percentile_cont` que não aceita `OVER()` no PostgreSQL e tantas outras.
A experiência nesta atividade me ajudou a evoluir no lado "mão na massa" e serviu para evoluir vários microsserviços no meu portal, inclusive levando o desse projeto (JurisFlow) pra lá, com alguns ajustes: não uso o slack, mas o whatsApp e o e-mail corporativo.
Mais detalhes, mostrarei no vídeo da atividade. Abraço!!!
