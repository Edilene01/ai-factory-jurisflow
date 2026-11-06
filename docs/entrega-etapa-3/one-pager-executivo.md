# JurisFlow · Triagem automática de intake jurídico

**Edilene Chagas Faria** · Novembro de 2026
**Aplicação:** https://ai-factory-jurisflow-production.up.railway.app · **Código:** https://github.com/Edilene01/ai-factory-jurisflow

---

### O problema custava receita, não só tempo

A JurisFlow atende 180 escritórios e recebe 2.500 formulários de intake por dia. A triagem era
manual, e um caso levava de **3 a 6 horas** para chegar à equipe certa. Cliente que espera
meio dia procura outro escritório.

### Agora o caso chega em 2,6 segundos

O formulário é preenchido e o cliente recebe protocolo, área e urgência. A equipe responsável
é notificada no mesmo instante, com nome e CPF mascarados.

| | Antes | Depois |
|---|---|---|
| Tempo até a equipe | 3 a 6 horas | **1,27 s** (p95) |
| Caso urgente | Mesma fila | Classificado como **alta** |
| Dado pessoal no modelo | Relato cru | CPF, CNPJ, e-mail e telefone removidos antes |
| Erro | Não medido | **0%** em 200 casos |

### O valor em dinheiro

**Operar custa quase nada.** Classificar 75.000 casos por mês consome **US$ 3,43** em chamadas
ao modelo. Com hospedagem, cerca de **US$ 18 mensais**, contra os US$ 120 autorizados. Sobram
85% da verba.

**O retorno está nas horas devolvidas.** Se a triagem ocupava uma pessoa por 4,5 horas
diárias, são **99 horas por mês** de volta ao trabalho jurídico. A R$ 35 a hora de custo
total, **R$ 3.465 por mês**, ou R$ 41,5 mil por ano, contra cerca de R$ 100 de operação.

Essa última conta é estimativa, e vai marcada como tal: o briefing informa o tempo da triagem,
não o custo da hora. Os números da tabela acima são medidos em produção, com 200 casos de
teste, e estão registrados no repositório.

**Uma otimização medida.** Comprimi o prompt enviado ao modelo, de 1.172 para 784 caracteres.
O custo por caso caiu **21,2%** e a latência p95 caiu **12,3%**, sem perda de acerto. Em
dinheiro são noventa centavos de dólar por mês: o que justifica a mudança é o conjunto, e não
a economia isolada.

### O que ainda não funciona

- **A qualidade foi medida sobre 12 descrições**, todas claras. O caso ambíguo, aquele que admite duas áreas, é onde um classificador erra, e disso ainda não há evidência.
- **A sanitização não remove nome de empregador nem endereço.** Tira CPF, CNPJ, e-mail e telefone; um relato que cite "a padaria do Seu Jorge, em Macapá" chega ao provedor com o contexto intacto.
- **Falha de entrega no Slack não reprocessa.** É registrada e alerta, porém exige alguém agir. É o pior modo de falha, porque o cliente já recebeu a confirmação.

### Próximo passo

Reconhecimento de entidades nomeadas antes da chamada, para fechar a lacuna da sanitização, e
fila de reprocessamento para a entrega. Nenhuma das duas pede aumento de orçamento.

**E a prova de que escala.** O sistema vai ser adotado em atendimento real, no portal de um
escritório de advocacia, com servidor e e-mail já contratados. Custo adicional: centavos
mensais de token. O desenho está em [`../evolucao/001-jurisflow-no-portal-do-escritorio.md`](../evolucao/001-jurisflow-no-portal-do-escritorio.md).
