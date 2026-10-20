# Plano de instrumentação

Como o JurisFlow passa a emitir *trace* e *spans* cobrindo o fluxo real, e o que precisa
mudar no workflow para que as [cinco métricas](metricas-e-thresholds.md) sejam medidas em vez
de estimadas.

**Atualizado em:** 19/10/2026

---

## 1. O que existe hoje, e o que falta

| Sinal | Hoje | Falta |
|---|---|---|
| Identificador por requisição | `protocolo`, no formato `JF-AAAAMMDD-XXXXXX`, gerado no primeiro nó | Nada. Já serve de *trace id* |
| Latência | `latencia_ms`, da chegada até o parse | Cobrir o trecho até a entrega no Slack, que é o que o SLA mede |
| Custo | — | Contagem de tokens, que o provedor devolve e o workflow descarta |
| Erro | Execuções com erro ficam no n8n por 72 h | Classificação por causa, e registro que sobreviva à purga |
| Volume | Contável por execução | Nada, uma vez que a trilha persista |
| Qualidade | `revisao_manual` e `motivo_revisao`, já no registro | Nada |
| *Spans* por etapa | — | Tudo |
| Persistência | Sink em memória | Gravação em Postgres |

A lista é curta porque a Etapa 1 já deixou o formato do registro fechado. O nó
`Registro de Auditoria` traz no próprio comentário que *"a persistência em Postgres entra na
Etapa 2, e o formato do registro já está fechado para que aquela mudança seja só a troca do
destino"*. É o que se cumpre agora.

---

## 2. O trace id já existe, e é o protocolo

Nenhum identificador novo será criado. O `protocolo` já é único por intake, já atravessa
todos os nós, já volta ao cliente na resposta e **já é pseudônimo**: não carrega nome, CPF
nem trecho do relato.

Isso tem duas vantagens que não são de conveniência. A primeira é que o *trace* fica
correlacionável com o que o cliente tem em mãos: a pessoa liga citando o protocolo e a equipe
recupera o caminho inteiro da requisição. A segunda é de conformidade: adotar um
identificador novo exigiria avaliar se ele cria vínculo com o titular, e reaproveitar o
protocolo mantém o [mapa de dados pessoais](../lgpd/mapa-dados-pessoais.md) válido como está.

**Regra firme:** nenhum atributo de *span* recebe dado identificável. O esquema é fechado
por coluna e por chave conhecida, e não aceita texto livre do caso. É a mesma disciplina do
nó de auditoria, que monta o objeto campo a campo.

---

## 3. Os spans

Sete etapas, cobrindo o caminho inteiro do briefing: formulário até Slack.

Este plano previa sete spans. Na implementação ficaram **quatro**, e a diferença merece
explicação, porque é a diferença entre granularidade real e aparência de granularidade.

O n8n não expõe, em expressão, o instante de início e fim de cada nó. O que dá para carimbar
é o relógio dentro dos nós de código que controlamos, e há três deles no caminho. Três
carimbos mais o início e o fim delimitam quatro trechos, não sete. Emitir sete exigiria
inventar fronteiras, e span com duração fabricada é pior do que span ausente.

| Span | Delimitado por | Por que medir separado |
|---|---|---|
| `sanitizacao` | `recebido_em` → `t_sanitizacao_fim` | É barato; se aparecer no perfil de latência, algo está errado |
| `classificacao_llm` | `t_sanitizacao_fim` → `t_parse_inicio` | **É o trecho que domina a latência e é onde o custo acontece.** Carrega os tokens |
| `parse` | `t_parse_inicio` → `t_parse_fim` | Isola falha de interpretação de falha do provedor |
| `entrega_slack` | `t_parse_fim` → fim da execução | **Fecha o SLA.** Engloba o roteamento, que é barato e não tem carimbo próprio |

O que se perdeu: `recepcao` fica embutido no início de `sanitizacao`, e `roteamento` em
`entrega_slack`. Nenhum dos dois faz chamada externa, de modo que a latência deles é
desprezível perto da do provedor, e separá-los renderia dois números perto de zero.

A duração total, de `recebido_em` até o fim, é gravada à parte em `duracao_total_ms`, e é ela
que mede o SLA. `duracao_resposta_ms` mede até a resposta ao formulário, que é o que o cliente
espera na tela. São dois números diferentes, e os dois importam.

A resposta ao formulário e a entrega no Slack correm em paralelo depois do `parse`, como o
diagrama C4 nível 2 já mostra. O SLA do briefing fecha na entrega ao Slack, e por isso a
montagem da trilha roda **depois** dos seis nós do Slack, e não em paralelo a eles: medir
antes subestimaria justamente o número contratado.

---

## 4. Mudanças no workflow

### 4.1 Capturar os tokens no nó de classificação

O provedor devolve o uso na resposta. Hoje o `Parse Classificação` lê apenas
`$json.message.content` e descarta o resto. Passa a ler também:

```js
const uso = $json.usage || {};
// tokens_entrada: prompt_tokens | tokens_saida: completion_tokens
```

Sem isto a métrica de custo é cálculo, não medição, e a rubrica distingue as duas coisas.

### 4.2 Fechar a latência no fim do fluxo

O `latencia_ms` atual para no parse. Entra um nó de encerramento **depois** dos nós do Slack,
que calcula a duração total e grava a linha definitiva:

```js
const entrada = $('Sanitizar Entrada').first().json;
const duracao_total_ms = Date.now() - new Date(entrada.recebido_em).getTime();
```

É a correção que faz a métrica medir o SLA que o briefing contratou, e não um pedaço dele.

### 4.3 Trocar o destino do registro de auditoria

O nó `Registro de Auditoria` deixa de devolver objeto em memória e passa a inserir em
`jurisflow_trilha_auditoria`, com as colunas de token e de duração total acrescentadas pela
migração 002.

### 4.4 Emitir os spans

Cada etapa grava uma linha em `jurisflow_trace_span`, com `protocolo` como chave de
correlação. A gravação é feita em lote, no nó de encerramento, e não span a span: sete
inserções sincronizadas por intake acrescentariam latência à medição da própria latência.

---

## 5. Ordem de execução, e o que cada passo destrava

| # | Passo | Destrava |
|---|---|---|
| 1 | Criar a credencial Postgres no n8n | A ativação do agendador de retenção, hoje bloqueada |
| 2 | Aplicar `001_trilha_auditoria.sql` e `002_observabilidade.sql` | As tabelas de destino |
| 3 | Mudanças 4.1 a 4.4 no workflow | A emissão dos sinais |
| 4 | Publicar e deixar acumular tráfego | A **linha de base**, sem a qual todo *threshold* segue provisório |
| 5 | Curar o dashboard e linká-lo no README | O item da rubrica |
| 6 | Provocar um alerta de propósito e capturar a evidência | O alerta deixa de ser descrito e passa a ser funcional |

O passo 4 não tem atalho. Os *thresholds* do documento de métricas estão marcados como
provisórios justamente porque este passo ainda não aconteceu, e preencher a lacuna com número
plausível seria inventar medição.

---

## 6. O que deliberadamente não entra

**OpenTelemetry com coletor próprio.** Seria o caminho canônico e está fora de proporção
aqui: exigiria um serviço a mais no Railway, consumindo do mesmo orçamento, para instrumentar
um workflow de catorze nós cujo armazenamento de métricas já existe em Postgres. A estrutura
de `trace` e `span` adotada é a mesma; o que muda é que o transporte é um `INSERT` em vez de
um coletor.

**Métrica de acerto da classificação.** Exigiria rótulo humano sobre amostra. O limite está
declarado na seção 5 do [documento de métricas](metricas-e-thresholds.md).

**Alertas do Railway sobre os dados de negócio.** O painel do Railway enxerga CPU, memória e
rede, e não sabe o que é um intake. As duas camadas ficam separadas de propósito, cada uma
alertando sobre o que consegue ver.
