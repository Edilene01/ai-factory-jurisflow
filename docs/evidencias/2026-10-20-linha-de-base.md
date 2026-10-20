# Linha de base medida

**Data:** 20/10/2026
**Ambiente:** produção, `https://n8n-production-81314.up.railway.app`
**Workflow:** v1.2.2
**Carga:** 200 intakes sintéticos, semente 42, 4 em paralelo
**Comando:** `python scripts/carga_sintetica.py --n 200 --rotulo baseline --paralelas 4 --semente 42`

Dados fictícios, de `docs/exemplos-intakes.md`. CPF `111.444.777-35`, válido pelo dígito
verificador e de ninguém. Nenhum cliente real.

---

## 1. Medição do cliente, até a resposta ao formulário

```
200/200 com sucesso em 71,0 s
latência  p50 1313 ms | p95 2034 ms | p99 2644 ms | máx 2950 ms
dentro do SLA de 60 s: 100.0%
taxa de erro: 0.0%
acerto de área: 100.0%
revisão manual: 0.0%
```

Bruto em [`carga-baseline.json`](carga-baseline.json), com as 200 amostras individuais.

## 2. Medição do servidor, até a entrega no Slack

Lida de `/webhook/metricas`, com a janela restrita à corrida.

| Métrica | Valor |
|---|---|
| Volume | 184 |
| Latência p50 | **1.002 ms** |
| Latência p95 | **1.197 ms** |
| Latência p99 | **1.680 ms** |
| p95 até a resposta ao formulário | 977 ms |
| Dentro do SLA de 60 s | **100%** |
| Taxa de erro | **0%** |
| Revisão manual | 0% |
| Tokens de entrada | 60.393 |
| Tokens de saída | 2.699 |
| Custo total | US$ 0,010678 |
| **Custo por intake** | **US$ 0,000058** |

### Latência por etapa

| Etapa | p50 | p95 | máx |
|---|---|---|---|
| `classificacao_llm` | 763 ms | 977 ms | 2.502 ms |
| `entrega_slack` | 222 ms | 291 ms | 318 ms |
| `parse` | 0 ms | 1 ms | 1 ms |
| `sanitizacao` | 0 ms | 1 ms | 6 ms |

### Distribuição por área

| Área | Intakes |
|---|---|
| Cível | 51 |
| Trabalhista | 45 |
| Consumidor | 33 |
| Criminal | 31 |
| Tributário | 24 |

---

## 3. Por que os dois números de latência diferem

O cliente mede 1.313 ms de p50 e o servidor mede 1.002 ms. Não é inconsistência: são
medições de coisas diferentes, e as duas estão no esquema de propósito.

* **`duracao_resposta_ms`**, no servidor, fecha quando o formulário recebe o protocolo.
* **`duracao_total_ms`**, no servidor, fecha na entrega ao Slack, que é onde o SLA do briefing fecha.
* A **medição do cliente** inclui ainda a rede entre a máquina de quem roda o teste e o Railway, e é por isso que vem acima das duas.

Para o SLA vale o número do servidor. Para a experiência de quem preenche o formulário, vale
o do cliente, porque a rede faz parte da espera dele.

---

## 4. Discrepância entre 200 enviados e 184 gravados

Dezesseis intakes não chegaram à trilha, e a causa é conhecida: durante a corrida o workflow
ainda rodava a versão anterior em parte das execuções, enquanto a correção do `Switch` era
publicada. Os 184 restantes cobrem as cinco áreas e sustentam as métricas.

A contagem do cliente, de 200/200 com sucesso, continua válida: o intake foi aceito,
classificado e respondido nos 200 casos. O que faltou foi registro de auditoria em 16 deles.

---

## 5. O que esta medição mudou em relação ao que estava estimado

**O custo real é 44% menor do que o calculado.** A estimativa em
[`metricas-e-thresholds.md`](../observabilidade/metricas-e-thresholds.md) era de
US$ 0,000103 por intake, derivada de contagem de caracteres dividida por 3,4. O medido é
US$ 0,000058. A 2.500 intakes por dia, a projeção cai de US$ 7,70 para **US$ 4,35 por mês**.

É o argumento concreto a favor de medir: a estimativa errou para cima por quase o dobro, e
errar para cima em custo é o lado confortável, mas ainda é errar.

**O SLA tem folga de 50 vezes.** O p95 medido é de 1.197 ms contra os 60.000 ms contratados.
O limite não está em risco, e isso reposiciona a otimização: não há problema de latência a
resolver, e o espaço de melhoria está no custo.

**A chamada ao LLM responde por 76% do tempo.** São 763 ms de 1.002 ms no p50. Qualquer
otimização de latência que não toque nessa etapa mexe nos 24% restantes, dos quais o Slack
leva 222 ms e o processamento local, zero.

**O teto de `max_tokens` não está sendo alcançado.** A saída média é de 14,7 tokens contra o
limite de 60, de modo que reduzir o teto não reduziria custo: a cobrança é por token gerado,
não por limite declarado.

**A entrada é dominada pelo prompt fixo.** São 328 tokens de entrada por intake, dos quais a
descrição do caso responde por algo em torno de 30. Os outros ~300 são o *system prompt*,
reenviado a cada requisição. É aí que está o custo, e é daí que sai a otimização do Bloco 3.

---

## 6. Limites desta medição, declarados

* **Corpus de 12 descrições**, repetidas ao longo das 200 requisições. Serve para medir custo e latência, que não dependem de variedade, mas torna o acerto de área de 100% menos impressionante do que parece: são doze casos distintos classificados certo, não duzentos.
* **Tráfego sintético**, gerado de uma máquina só, com 4 requisições simultâneas. Não reproduz o padrão real de 2.500 intakes por dia concentrados em horário comercial.
* **Janela curta**, de pouco mais de um minuto. Não captura variação ao longo do dia nem degradação do provedor.

Nada disso invalida os números para o uso que têm aqui: comparar o antes e o depois de uma
otimização sobre o mesmo corpus, com a mesma semente. Invalidaria se fossem apresentados como
retrato do comportamento em produção com tráfego real, e não são.
