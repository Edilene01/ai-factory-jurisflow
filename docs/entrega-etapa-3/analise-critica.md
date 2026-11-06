# Análise crítica · JurisFlow

**Edilene Chagas Faria** · Novembro de 2026

---

## Parte A: revisitando o briefing

### Onde a aplicação está

| Artefato | Endereço |
|---|---|
| Aplicação | https://ai-factory-jurisflow-production.up.railway.app |
| Formulário de intake | https://ai-factory-jurisflow-production.up.railway.app/ |
| Painel de operação | https://ai-factory-jurisflow-production.up.railway.app/painel |
| Repositório | https://github.com/Edilene01/ai-factory-jurisflow |

Não há login, e isso foi decisão, não omissão: o formulário é público por natureza, e o
painel mostra apenas agregados, sem nome, CPF ou trecho de relato.

### O sistema resolve o problema que a liderança pediu?

A Renata pediu três coisas no briefing. Vale responder uma a uma, porque o resultado não é
uniforme.

**SLA de triagem de 60 segundos no P95, do formulário à notificação no Slack.** Cumprido, e
com folga grande demais para ser confortável. O p95 medido é de 1,27 segundo, cerca de
quarenta e sete vezes abaixo do contratado. Folga desse tamanho não é mérito, é sinal de que
o SLA foi negociado sem medição prévia. Seria mais útil ao negócio um compromisso de 5
segundos, que ainda cabe sem esforço e significa alguma coisa.

**Auditoria real persistida, com área, urgência, custo por classificação e taxa de fallback
humano.** Cumprido. A tabela `jurisflow_trilha_auditoria` guarda os quatro campos, mais
latência total e tokens, e hoje tem perto de mil registros. O custo por classificação deixou
de ser estimativa quando passei a persistir a contagem de tokens que o provedor devolve.

**Pitch ao Comitê de Produto.** Fora do escopo técnico, e é o que esta entrega acompanha.

Quanto ao problema de negócio em si, a resposta honesta tem duas metades. O sistema resolve o
problema **de tempo**: o caso que levava de 3 a 6 horas chega à equipe em segundos, e a
urgência é reconhecida em vez de ignorada. Não resolve o problema **de acerto**: ainda não
sei, com evidência, o quanto o classificador erra em casos difíceis, porque meu corpus de
teste tem doze descrições e todas são claras.

Dito de outro modo: entreguei velocidade comprovada e qualidade presumida. Para a liderança,
isso basta hoje e não bastará em três meses.

---

## Parte B: defesa das decisões

### Decisão 1: manter o n8n em vez de reescrever (ADR-001)

O protótipo do Téo funcionava, embora só na máquina dele. A tentação era reescrever em
Python, que eu dominaria melhor.

Não reescrevi, e a razão está no briefing: o prazo era de 12 semanas e o orçamento de US$ 120
mensais cobria LLM, hospedagem e observabilidade. Reescrever consumiria metade do prazo
reproduzindo o que já existia, para só então começar o que a disciplina pedia, ou seja,
segurança, conformidade e observabilidade.

A decisão se pagou de um jeito que eu não previ. Quando a instância de produção desapareceu
em outubro, e depois quando o volume do Railway voltou vazio, o workflow sobreviveu as duas
vezes, porque vive no Git. Reconstruir produção virou republicar um arquivo. Se o sistema
fosse código meu num servidor, seria a mesma coisa, mas o ponto é que a ADR-001 fixou o Git
como fonte da verdade antes de eu saber que precisaria disso.

**O que custou:** o n8n esconde complexidade atrás de nós visuais, e quando ele quebra, quebra
de forma opaca. Perdi quase um dia porque o nó nativo da OpenAI, na versão 2.40.5, resolvia
para a raiz da API em vez do endpoint de chat. A resposta era a mensagem de boas-vindas do
provedor, e o sistema a tratava como classificação malformada. Em código escrito por mim, o
erro teria aparecido na primeira linha de log.

### Decisão 2: a sanitização antes da chamada, e não depois (ADR-001 e mapa de dados)

O protótipo mandava nome e CPF sem máscara direto para o Slack, e o relato inteiro para o
provedor de LLM. A auditoria registrou isso como um dos seis achados críticos.

O desenho que adotei separa duas versões do mesmo intake no nó `Sanitizar Entrada`: uma com o
relato íntegro, que vai para a equipe do escritório, e outra sem CPF, CNPJ, e-mail e telefone,
que é a única que sai para o provedor. A ordem importa, e por isso a sanitização é um nó
anterior à chamada, não um filtro de saída. O dado identificável não chega ao provedor porque
ele não é enviado, e não porque alguém o removeu depois.

Isso se liga ao briefing de forma direta. A Renata escreveu que a descrição do caso "pode
revelar saúde, orientação, situação financeira ou processo criminal", e que o sigilo
profissional cobre a relação cliente-advogado. Mandar esse texto a um provedor nos Estados
Unidos sem tratamento seria transferência internacional de dado sensível sem base, e está
documentado como tal no mapa de dados pessoais, com fundamento no art. 7º, V, e no art. 33,
IX, da Lei nº 13.709/2018.

**O que custou:** a sanitização por expressão regular é cega a nome próprio, endereço e nome
de empregador. Eu sabia disso ao escrever, e escolhi declarar o limite em vez de fingir que a
regex resolvia. Está na seção 5 do mapa de dados.

### Decisão 3: a aplicação com ponte, em vez de página estática (ADR-007)

A Etapa 3 pedia uma aplicação de verdade. O caminho curto seria uma página estática chamando
o webhook do n8n direto do navegador.

Esse caminho era inaceitável por um motivo específico: o webhook exige o header
`X-Jurisflow-Signature`, e qualquer pessoa leria esse valor no código da página. É o mesmo
segredo que o GitHub Environment guarda e que o procedimento de rotação trata como sensível.
Publicá-lo no navegador seria o critério de anulação da própria etapa.

Por isso há um backend em FastAPI que guarda o segredo no servidor e faz a ponte. Verifiquei:
nas quatro rotas públicas, o valor não aparece em ativo nenhum.

Ter o backend rendeu três coisas que a página estática não teria. Limite de taxa de cinco
requisições por minuto por IP, porque cada intake custa uma chamada paga e uma aba aberta em
laço esvaziaria o orçamento. A `origem` do intake fixada no servidor, para que ninguém possa
poluir a métrica de volume por canal. E nenhum registro do corpo em log, já que ele carrega
nome, CPF e o relato sob sigilo.

**O que custou:** mais um serviço para manter, mais um ponto de falha e mais uma assinatura
sujeita ao mesmo acidente que já derrubou a instância duas vezes.

---

### O que funciona bem, e por quê

**A classificação de urgência.** Testei um caso de negativa de plano de saúde com internação
marcada, e o sistema devolveu urgência alta. Testei execução fiscal com prazo de cinco dias, e
também veio alta. Funciona porque o critério está no prompt em termos concretos, prazo legal
vencendo, prisão, audiência marcada, e não como adjetivo vago.

**O desvio para triagem manual.** O protótipo empurrava tudo que não reconhecia para o Cível,
em silêncio. Hoje, o que o sistema não classifica vai para `#juris-triagem-manual` com o motivo
escrito. Isso funciona porque o `Parse Classificação` trata a incerteza como resultado
legítimo, e não como erro a esconder.

**A observabilidade que nasceu de um incidente.** As métricas existem porque o sistema esteve
quebrado de forma invisível: duas falhas terminavam em "sucesso" com desvio para triagem
manual, e `saveDataSuccessExecution: none` não guardava nada. O conserto começou por tornar a
falha legível, e só depois virou painel.

### O que não funciona, ou funciona mal

**A medição de qualidade.** O corpus de teste tem doze descrições, todas inequívocas, e por
isso o acerto de 100% diz menos do que parece. O caso ambíguo é o que importa, e o
`exemplos-intakes.md` registra três deles sem que entrem na carga de medição. A taxa de
revisão manual acusaria o problema, e ela precisa de tráfego real para significar algo.

**A entrega no Slack falha sem reprocessar.** Quando o canal não existe ou o bot não é membro,
o caso é marcado com `causa_falha: 'slack'` e o alerta dispara, mas o caso não é reenviado.
É o pior modo de falha do sistema: o formulário já respondeu "recebido" ao cliente, e ninguém
no escritório viu o caso. Vi isso acontecer em produção, com 38 casos de Consumidor, antes de
descobrir que o nó `Switch` na versão 1 aceita no máximo quatro saídas e eu tinha cinco áreas.

**Os dois ambientes estão na mesma plataforma.** A ADR-005 recuperou a paridade que a ADR-003
havia perdido, e ao fazer isso criou um ponto único de falha. O projeto já perdeu instância
duas vezes por motivo de plataforma. Uma terceira derrubaria desenvolvimento e produção juntos.

### Limitações conhecidas

**De dados.** Todas as medições vêm de carga sintética: 200 intakes de um corpus de doze
descrições, disparados de uma máquina em uma janela de um minuto. Não reproduzem o padrão real
de 2.500 casos diários concentrados em horário comercial, nem a variedade de redação de
clientes reais.

**De tecnologia.** O limite de taxa é por processo, não compartilhado. Se o Railway escalar o
serviço para mais de uma réplica, cada uma terá o próprio contador e o teto efetivo
multiplica. Com uma réplica, que é a configuração atual, o número vale.

**De escopo.** O sistema não acompanha o caso depois da entrega no Slack. Não sabe se o
advogado assumiu, se o cliente foi respondido, nem se a área estava certa. A métrica de
qualidade mede quanto o sistema admite não saber, e não se ele acerta quando diz saber. Medir
acerto de verdade exigiria rótulo humano sobre amostra, e isso ficou fora.

**De conformidade.** As cláusulas-padrão da Resolução CD/ANPD nº 19/2024 ainda não foram
incorporadas aos contratos com OpenAI, Slack e Railway. O prazo de adequação encerrou em
agosto de 2025. A pendência é contratual, não técnica, e está registrada em
`docs/lgpd/transferencia-internacional.md`.

---

## Parte C: visão de futuro e aprendizados

> **Esta parte é sua, e só sua.** O enunciado da Etapa 3 determina que ela seja 100% autoral,
> sem nenhum uso de IA. O material de apoio, com as perguntas a responder e os fatos do
> projeto que você talvez queira usar, está em
> [`parte-c-material-para-voce-escrever.md`](parte-c-material-para-voce-escrever.md).
>
> **Apague este bloco e escreva aqui.**
