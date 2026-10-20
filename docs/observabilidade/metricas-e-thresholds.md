# Métricas e thresholds

As cinco métricas que dizem se o JurisFlow está saudável, com o limite de cada uma e a razão
do limite. Nenhum número aqui é redondo por estética: cada um vem de uma restrição do caso,
de um parâmetro do próprio workflow ou de uma conta que está feita no texto.

**Atualizado em:** 19/10/2026

> **Leitura obrigatória antes de usar estes números.** Os *thresholds* abaixo são
> **provisórios**, derivados de restrições conhecidas e de cálculo, não de medição. A linha de
> base real só existe depois que a trilha de auditoria estiver gravando em Postgres e a
> instância acumular tráfego. Cada limite traz, por isso, a base de que foi derivado e o que
> precisa medir para confirmá-lo. Afirmar que foram medidos seria inventar número, que é
> justamente o que anula a etapa.

---

## De onde vem cada restrição

| Origem | Restrição |
|---|---|
| `BRIEFING.md` | SLA de **60 segundos (P95)**, do envio do formulário até a notificação no Slack, para 95% dos intakes |
| `BRIEFING.md` | Volume esperado de **2.500 intakes por dia** |
| `BRIEFING.md` | Orçamento de **US$ 120/mês** cobrindo LLM, hospedagem e observabilidade |
| `workflows/jurisflow-intake.json` | `executionTimeout: 120` segundos |
| Idem | Nó de LLM com `timeout: 30000` ms, `maxTries: 3`, `waitBetweenTries: 2000` ms |
| Idem | `model: gpt-4o-mini`, `temperature: 0`, `maxTokens: 60` |

---

## 1. Latência — p50, p95 e p99

**O que mede.** O tempo do ciclo completo: chegada do POST no webhook até a entrega da
mensagem no canal do Slack. É o que o SLA do briefing define, e não um pedaço dele.

| Percentil | Threshold | De onde sai |
|---|---|---|
| **p50** | ≤ 5 s | A chamada ao provedor domina o caminho. Com `maxTokens: 60` e `temperature: 0`, a resposta é curta e determinística, da ordem de 1 a 2 segundos, e o restante do fluxo é transformação local. Cinco segundos dão folga de 2 a 3× sobre o esperado, sem acomodar degradação |
| **p95** | ≤ 60 s | **É o SLA contratado**, literal. Não é escolha de engenharia: é o número que o cliente comprou |
| **p99** | ≤ 110 s | Precisa ficar **abaixo do `executionTimeout` de 120 s**. Acima disso a execução é abortada e vira erro, de modo que um p99 de 120 s não seria latência alta, seria taxa de erro disfarçada. Dez segundos de margem separam uma coisa da outra |

**O raciocínio do p99 é o que importa aqui.** Um limite de latência acima do *timeout* da
plataforma mede uma coisa que não pode acontecer: execuções que passariam dele já foram
mortas e contabilizadas como falha. Fixar o p99 abaixo do *timeout* mantém a métrica
medindo o que diz medir.

### Lacuna conhecida

O campo `latencia_ms`, como está hoje no nó `Parse Classificação`, é calculado assim:

```js
const latencia = Date.now() - new Date(entrada.recebido_em).getTime();
```

Isso mede **da chegada até o parse**, e para por aí. A entrega no Slack vem depois e não
entra na conta. O SLA do briefing é até a notificação no Slack, de modo que a métrica atual
**subestima a latência que o contrato mede**. Corrigir isso é o primeiro item do
[plano de instrumentação](plano-instrumentacao.md).

**O que medir para confirmar:** p50, p95 e p99 sobre `duracao_total_ms` em janela de 24 h,
depois de a trilha estar gravando.

---

## 2. Custo por classificação

**O que mede.** Dólares gastos com o provedor de LLM, por intake e por dia.

### A conta da linha de base

Preços vigentes do `gpt-4o-mini`: **US$ 0,15 por 1M de tokens de entrada** e **US$ 0,60 por
1M de tokens de saída**.

| Parcela | Tokens | Custo |
|---|---|---|
| *System prompt* | ~345 (medido: 1.172 caracteres) | US$ 0,0000518 |
| Descrição do caso | ~100 (estimado) | US$ 0,0000150 |
| Resposta | ≤ 60 (teto do `maxTokens`) | US$ 0,0000360 |
| **Total por intake** | | **≈ US$ 0,000103** |

A 2.500 intakes por dia, são 75.000 por mês, o que dá **cerca de US$ 7,70 por mês**. Cabe com
larga folga nos US$ 120 de OPEX, que ainda precisam cobrir hospedagem e observabilidade.

| Threshold | Valor | De onde sai |
|---|---|---|
| Anomalia diária | custo do dia > **2×** a mediana dos 7 dias anteriores | Detecta laço de repetição, *retry* descontrolado ou mudança de prompt que inflou a entrada. É o que pega o problema no dia em que ele nasce |
| Guarda absoluta | projeção mensal > **US$ 30** | Quase 4× a linha de base calculada. Nesse patamar não é variação de volume, é mudança estrutural: outro modelo, outro prompt ou laço |

**Por que dois limites.** O relativo pega o que é súbito; o absoluto pega o que cresce devagar
e passaria despercebido por comparação diária. Um sozinho deixa metade dos casos fora.

### Lacuna conhecida

**O custo não é mensurável hoje.** O nó `Registro de Auditoria` não guarda contagem de
tokens, e sem ela a métrica é estimativa, não medição. O provedor devolve o uso na própria
resposta, e persisti-lo é mudança pequena, descrita no plano de instrumentação.

O campo `caracteres_descricao`, que já existe, serve de aproximação enquanto isso: variação
brusca no comprimento médio dos relatos antecipa variação de custo.

**O que medir para confirmar:** custo diário real, por soma de `tokens_entrada` e
`tokens_saida`, durante 7 dias de tráfego.

---

## 3. Taxa de erro

**O que mede.** Proporção de execuções que terminam em falha sobre o total.

| Threshold | Janela | Prioridade | De onde sai |
|---|---|---|---|
| > 1% | 1 hora | P2 | A 2.500 intakes/dia o fluxo é de ~104 por hora em média, e 1% é pouco mais de um caso perdido por hora. Cada caso perdido é uma pessoa que pediu ajuda jurídica e não foi atendida, o que torna tolerância maior difícil de justificar |
| > 5% | 15 minutos | P1 | Em 15 minutos passam ~26 intakes; 5% ali é falha sistêmica em curso, não variação. A janela curta existe para o alerta chegar enquanto ainda há o que salvar |

**Separar por causa é obrigatório**, porque o dono do problema muda:

* **Falha do provedor** — o nó de LLM esgotou as 3 tentativas. Ação: acionar o *fallback* de provedor, que é candidato do Bloco 3.
* **Falha de entrega no Slack** — o caso foi classificado e não chegou ao time. É o pior tipo, porque o formulário já respondeu sucesso ao cliente.
* **Falha de validação na entrada** — campo obrigatório ausente. Normalmente é o site, não o JurisFlow.

---

## 4. Volume

**O que mede.** Intakes recebidos por hora e por dia.

Esta é a métrica que o enunciado da Etapa 2 descreve sem nomear, ao dizer que um sistema em
produção *"pode falhar em silêncio sem ninguém perceber"*. Taxa de erro não pega silêncio: se
o formulário do site parar de enviar, não há erro nenhum, há ausência. Só volume detecta isso.

| Threshold | Janela | Prioridade | De onde sai |
|---|---|---|---|
| Volume < **20%** da média da mesma hora nos 7 dias anteriores, em horário comercial | 1 hora | **P1** | Comparar com a mesma hora do dia respeita a concentração do tráfego em horário comercial. Abaixo de um quinto não é um dia fraco, é um canal quebrado |
| Zero intakes por **2 horas** em horário comercial | 2 horas | **P1** | Redundância do anterior, para o caso de a média histórica ainda não existir |
| Volume > **3×** a média da mesma hora | 1 hora | P3 | Pode ser campanha de marketing, pode ser robô. Não é urgente, mas muda a conta de custo |

**Por que P1 para volume baixo e P3 para volume alto.** Volume baixo significa clientes
perdidos em silêncio, que é o dano que não se recupera. Volume alto custa dinheiro e aparece
na métrica de custo de qualquer jeito.

---

## 5. Qualidade da classificação

**O que mede.** Proporção de intakes desviados para revisão manual, que o workflow já marca
com `revisao_manual` e qualifica com `motivo_revisao`.

| Threshold | Janela | Prioridade | De onde sai |
|---|---|---|---|
| Taxa de revisão manual > **15%** | 24 horas | P3 | Acima de um caso em cada sete o classificador deixou de ser útil, porque a triagem volta a ser humana para parcela grande do fluxo. O número é provisório: a linha de base precisa ser medida |
| Taxa com motivo *"falha ao interpretar a classificacao"* > **2%** | 1 hora | P2 | Este motivo não é caso difícil, é resposta malformada do provedor. É sintoma técnico, e a tolerância tem de ser bem menor que a do motivo anterior |
| Qualquer área com **zero** casos em 24 h | 24 horas | P3 | Com cinco áreas e 2.500 casos diários, área zerada sugere roteamento quebrado, não ausência de demanda |

**A distinção entre os dois primeiros limites é o ponto.** O workflow já separa
*"area nao reconhecida"* de *"falha ao interpretar a classificacao"*, e são problemas de
donos diferentes: o primeiro é do prompt e das definições de área, o segundo é do provedor ou
do parser. Agregar os dois numa taxa só esconde qual deles está acontecendo.

### Limite desta métrica, declarado

Taxa de revisão manual mede **quanto o sistema admite não saber**, e não se ele acerta quando
diz saber. Um classificador que erra com confiança tem taxa de revisão baixa e qualidade
ruim, e esta métrica não o pegaria.

Medir acerto de verdade exigiria rótulo humano sobre amostra, o que está fora do escopo da
etapa. O substituto honesto é acompanhar **reclassificações manuais**: caso que a equipe move
de um canal para outro é caso que o sistema errou. Registrar isso depende de ação da equipe
no Slack e fica anotado como evolução possível, não como métrica em vigor.

---

## Onde cada métrica vive

| Camada | Fonte | Retenção | O que responde |
|---|---|---|---|
| Infraestrutura | Painel do Railway, plano Hobby | 7 dias de log | O container está de pé? CPU, memória, rede e reinícios |
| Aplicação | `jurisflow_trilha_auditoria` e `jurisflow_trace_span`, em Postgres | 12 meses | O fluxo de negócio está saudável? Latência, custo, erro, volume e qualidade |

As duas camadas se complementam e nenhuma substitui a outra. O Railway responde se o
processo está vivo; o Postgres responde se o sistema está fazendo o que deveria. Um container
saudável que não classifica nenhum caso passa pela primeira camada e é pego pela segunda.

A retenção de 7 dias do log do Railway é curta para série histórica, e é exatamente por isso
que a trilha de auditoria guarda 12 meses: a política de retenção foi escrita antes destas
métricas e já previu o prazo de que elas precisam.

---

## Consultas

As cinco métricas estão materializadas em [`db/metricas/vw_metricas.sql`](../../db/metricas/vw_metricas.sql),
de modo que o número do relatório e o número do dashboard saem da mesma consulta. A rubrica
exige que eles batam; a maneira de garantir isso é não ter duas fontes.

## Alertas

O catálogo, com prioridade, público e canal de cada um, está em
[`alertas.md`](alertas.md).
