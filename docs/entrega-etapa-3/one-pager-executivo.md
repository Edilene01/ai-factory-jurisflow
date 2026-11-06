# JurisFlow · Triagem automática de intake jurídico

**Edilene Chagas Faria** · Novembro de 2026
**Aplicação:** https://ai-factory-jurisflow-production.up.railway.app
**Repositório:** https://github.com/Edilene01/ai-factory-jurisflow

---

## O problema que custava dinheiro

A JurisFlow atende 180 escritórios e recebe cerca de 2.500 formulários de intake por dia. A
triagem era feita à mão. Um caso levava de **3 a 6 horas** para chegar à equipe certa, e nesse
intervalo o cliente simplesmente procurava outro escritório.

Não era um problema operacional. Era perda de receita, com o agravante de que ninguém
conseguia medir o tamanho dela.

## O que o sistema faz agora

O formulário é preenchido, e em **2,6 segundos** o cliente recebe um número de protocolo com a
área e a urgência do caso. A equipe responsável é notificada no mesmo instante.

| Antes | Depois |
|---|---|
| 3 a 6 horas até a triagem | **2,6 segundos** (p95 medido) |
| Caso urgente na mesma fila | Urgência classificada: prazo vencendo e prisão viram **alta** |
| Classificação por leitura humana | 5 áreas, com desvio explícito quando o sistema não tem certeza |
| Dado pessoal cru indo ao modelo | CPF, CNPJ, e-mail e telefone removidos **antes** da chamada |

## Os números, e de onde vieram

Tudo abaixo foi medido em produção, com 200 intakes de teste, e está registrado no
repositório. Nada é estimativa.

| Métrica | Valor | Como foi medido |
|---|---|---|
| Latência p95, do envio à entrega no Slack | **1,27 s** | 200 intakes, trilha de auditoria |
| Dentro do SLA contratado de 60 s | **100%** | Mesma corrida |
| Taxa de erro | **0%** | Mesma corrida |
| Custo por caso classificado | **US$ 0,000046** | Contagem real de tokens |
| Custo mensal a 2.500 casos/dia | **US$ 3,43** | Projeção sobre o custo medido |

## O valor em dinheiro

**O custo de operar é irrisório.** Classificar os 75.000 casos de um mês custa US$ 3,43 em
chamadas ao modelo. Somada a hospedagem, a conta fecha em torno de **US$ 18 por mês**, contra
o orçamento de US$ 120 que a liderança autorizou. Sobram 85% da verba.

**O ganho está no tempo de resposta.** Se a triagem ocupava uma pessoa por 4,5 horas diárias,
são 99 horas por mês devolvidas ao trabalho jurídico. A R$ 35 por hora de custo total, isso
equivale a **R$ 3.465 por mês**, ou R$ 41,5 mil por ano, contra cerca de R$ 100 mensais de
operação.

Essa última conta é estimativa, e está marcada como tal: o briefing informa o tempo da
triagem, não o custo da hora nem quantas pessoas a executavam. Os números das tabelas
anteriores são medidos; este é projetado sobre premissa declarada.

**O ganho que não cabe em planilha** é o cliente que recebe resposta em segundos em vez de
meio dia. O briefing é explícito: quem espera e não recebe retorno procura outro escritório.

## Uma otimização, com antes e depois

O prompt enviado ao modelo consumia 328 tokens por caso, dos quais apenas 30 eram a descrição
do cliente. O resto era instrução fixa, reenviada a cada chamada. Comprimi o texto de 1.172
para 784 caracteres.

| | Antes | Depois |
|---|---|---|
| Custo por caso | US$ 0,0000580 | **US$ 0,0000457** (−21,2%) |
| Latência p95 | 1.443 ms | **1.266 ms** (−12,3%) |
| Acerto de área | 100% | 100% |

Duas corridas consecutivas de 200 casos, mesma semente, mesmo conjunto. Em dinheiro, os 21%
valem noventa centavos de dólar por mês. O que justifica a mudança é o conjunto, custo,
latência e um prompt mais fácil de manter, e não a economia isolada.

## O que ainda não funciona

**A qualidade foi medida sobre 12 descrições.** O acerto de 100% vale para casos claros. O
relato ambíguo, aquele que admite duas áreas, não aparece em volume suficiente para medir, e é
exatamente onde um classificador erra.

**A sanitização não remove nome de empregador nem endereço.** Ela tira CPF, CNPJ, e-mail e
telefone por expressão regular. Um relato que cite "a padaria do Seu Jorge, em Macapá" chega
ao provedor com o contexto intacto.

**A falha de entrega no Slack não tem reprocessamento.** Ela é registrada e dispara alerta,
porém alguém precisa agir. É o pior modo de falha do sistema, porque o cliente já recebeu a
confirmação.

## Próximo passo

Reconhecimento de entidades nomeadas antes da chamada ao modelo, para fechar a lacuna da
sanitização, e fila de reprocessamento para a entrega no Slack. As duas atacam as limitações
acima, e nenhuma depende de aumento de orçamento.
