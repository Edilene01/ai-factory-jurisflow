# Post-mortem INC-001 – Intakes perdidos por resposta do modelo em markdown

* **Data do incidente:** 18/09/2026
* **Natureza:** simulado, reproduzido de propósito em ambiente de desenvolvimento
* **Duração:** 22 minutos, do primeiro caso perdido até a contenção
* **Severidade:** alta, porque o caso desaparece sem deixar rastro
* **Autora:** Edilene Chagas Faria

> Este post-mortem analisa causa, não pessoas. O defeito descrito estava documentado no
> próprio repositório herdado, com um `FIXME` no código, o que indica falta de tempo e de
> prioridade, e não descuido de quem construiu.

## Resumo

Durante a adoção do projeto, reproduzi em ambiente controlado o achado CONF-01 da auditoria
para medir o raio de alcance antes de corrigi-lo. Configurei o classificador para devolver a
resposta embrulhada em blocos de markdown, comportamento comum em modelos de linguagem, e
enviei 20 intakes sintéticos.

Nenhum dos 20 chegou a qualquer canal. O nó `Parse Classificação` lançava exceção no
`JSON.parse`, a execução era interrompida e o formulário continuava recebendo 200, porque o
webhook respondia no recebimento. Do ponto de vista de quem preencheu o formulário, tudo
correu bem.

## Impacto

* 20 de 20 intakes de teste perdidos, ou seja, 100% do lote.
* Nenhum alerta disparou, porque não havia alerta.
* Nenhum registro sobreviveu, porque a auditoria era um nó que não fazia nada.
* Em produção, na escala declarada de 2.500 intakes por dia, um episódio de 22 minutos
  corresponderia a algo próximo de 38 casos perdidos, sem que ninguém precisasse notar.

## Linha do tempo

| Horário | Evento |
|---|---|
| 14:02 | Início do lote sintético com respostas em markdown |
| 14:03 | Primeiro caso não aparece no canal esperado. O formulário havia recebido 200 |
| 14:07 | Confirmação de que nenhum dos casos chegou. Suspeita inicial recai sobre a credencial do Slack |
| 14:12 | Credencial do Slack descartada: um envio manual ao canal funciona normalmente |
| 14:16 | Log de execução do n8n mostra a exceção no `Parse Classificação` |
| 14:19 | Causa confirmada: `JSON.parse` sobre resposta iniciada por crase tripla |
| 14:24 | Contenção: lote interrompido e defeito reproduzido de forma isolada |

Vale notar que 14 dos 22 minutos foram gastos investigando o lugar errado. Sem sinal, a
investigação começa pelo palpite.

## Causa raiz

Aplicando cinco porquês:

1. Por que os casos sumiram? Porque a execução era interrompida antes do roteamento.
2. Por que era interrompida? Porque o `JSON.parse` lançava exceção sobre a resposta do modelo.
3. Por que a resposta quebrou o parse? Porque veio embrulhada em markdown, embora o prompt pedisse JSON puro.
4. Por que isso não foi previsto? Porque o parse confiava na obediência do modelo ao formato pedido, tratando saída probabilística como se fosse contrato.
5. Por que ninguém percebeu antes? Porque não havia auditoria, alerta ou resposta síncrona ao formulário, de modo que a falha não produzia nenhum sinal observável.

A causa raiz, portanto, não é o `JSON.parse`. É a ausência de um caminho de erro: o sistema
foi construído assumindo que o caminho feliz é o único, e falha calado quando ele não se
confirma.

## O que funcionou

* O log de execução do n8n guardava o suficiente para identificar a exceção, uma vez que se soube onde procurar.
* O ambiente de desenvolvimento estava separado, de modo que nenhum dado real e nenhum canal de produção foi atingido.
* A auditoria prévia já descrevia o defeito, o que encurtou a confirmação da causa.

## O que não funcionou

* A investigação começou pelo Slack, porque não havia nada indicando onde a execução parava.
* O formulário respondia sucesso independentemente do resultado, o que tornaria o problema invisível também para o cliente.
* Não existia métrica de casos recebidos contra casos entregues, comparação que teria acusado a divergência em segundos.

## Ações

| # | Ação | Achado | Status |
|---|---|---|---|
| 1 | `try/catch` no parse, com tolerância a markdown e a texto extra | CONF-01 | Concluída na v1.0.0 |
| 2 | Desvio explícito para `#juris-triagem-manual` no que não for classificado | CONF-03 | Concluída na v1.0.0 |
| 3 | Resposta síncrona ao formulário, com protocolo e área | CONF-04 | Concluída na v1.0.0 |
| 4 | Repetição automática no nó de LLM, com três tentativas | CONF-05 | Concluída na v1.0.0 |
| 5 | Teste de regressão cobrindo markdown, texto extra e área desconhecida | QUAL-01 | Concluída na v1.0.0 |
| 6 | Trilha de auditoria persistente, com contagem de recebidos contra entregues | PRIV-05 | Etapa 2 |
| 7 | Alerta de divergência entre recebidos e entregues | OPS-04 | Etapa 2 |

## Lição que fica

Modelo de linguagem devolve texto, não estrutura, e todo ponto do sistema que trata a saída
como se fosse contrato é um ponto de falha esperando a ocasião. O aprendizado mais caro,
porém, não é esse, e sim o de que falha silenciosa é pior do que falha ruidosa: 22 minutos
foram gastos procurando o problema no lugar errado simplesmente porque o sistema não tinha
como dizer onde havia parado.
