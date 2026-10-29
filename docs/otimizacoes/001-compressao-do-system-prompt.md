# Otimização 001 — Compressão do system prompt

**Data:** 20/10/2026
**Versões:** v1.2.3 (antes) → v1.3.0 (depois)
**Medição:** 200 intakes sintéticos, semente 42, 4 em paralelo, duas corridas consecutivas

---

## 1. De onde veio a escolha

A linha de base não apontou problema de latência. O p95 medido foi de 1.443 ms contra os
60.000 ms do SLA contratado, ou seja, **folga de 41 vezes**. Otimizar latência resolveria um
problema que não existe.

O que a medição apontou foi outra coisa. São **328 tokens de entrada por intake**, dos quais
a descrição do caso responde por cerca de 30. Os outros ~300 são o *system prompt*, idêntico
em toda requisição e reenviado a cada uma delas. Noventa por cento do custo de entrada era
instrução fixa.

### A otimização que eu descartei, e por quê

O candidato óbvio seria **cache de classificação**: guardar o resultado por descrição e
devolvê-lo sem chamar o provedor. Num corpus de doze descrições repetidas ao longo de 200
requisições, o cache acertaria em torno de 94% das vezes e mostraria uma melhora
espetacular.

E seria mentira. O ganho viria da repetição do corpus sintético, não do sistema: em produção,
cada pessoa descreve o próprio caso com as próprias palavras, e a taxa de acerto do cache
seria próxima de zero. Medir cache sobre dado repetido é fabricar resultado, e a rubrica
desta etapa chama isso pelo nome.

Fica registrado como candidato legítimo para quando houver tráfego real que permita medir a
taxa de repetição de verdade.

---

## 2. O que foi feito

O *system prompt* passou de **1.172 para 784 caracteres**, uma redução de 33%. O que mudou:

* As listas de valores permitidos viraram enumerações com `|` em vez de frases.
* As definições de área perderam o preâmbulo e mantiveram as palavras que discriminam.
* A instrução de formato encolheu, preservando a exigência de JSON sem markdown.
* Os nomes de área no prompt perderam acento, o que teve efeito colateral mensurável na saída, discutido adiante.

O que **não** mudou: o contrato de saída, os cinco rótulos de área, os três de urgência, os
critérios de urgência e a instrução de devolver `Indefinido` sem certeza. A normalização no
nó `Parse Classificação` já tolerava variação de acento e caixa, de modo que a saída continua
aceita qualquer que seja a grafia.

---

## 3. Antes e depois

Duas corridas consecutivas, no mesmo dia, mesma instância, mesma semente, 200 intakes cada.
A sequência importa: a primeira comparação que fiz tinha corridas em horários distintos e
tamanhos de amostra diferentes, e foi descartada por isso.

### Medição do servidor, da trilha de auditoria

| Métrica | Antes | Depois | Variação |
|---|---|---|---|
| Volume | 200 | 200 | — |
| **Tokens de entrada** | 65.638 | 51.638 | **−21,3%** |
| **Tokens de saída** | 2.936 | 2.335 | **−20,5%** |
| **Custo por intake** | US$ 0,00005804 | US$ 0,00004573 | **−21,2%** |
| Latência total p50 | 1.068 ms | 1.020 ms | −4,5% |
| Latência total p95 | 1.443 ms | 1.266 ms | −12,3% |
| Latência total p99 | 1.757 ms | 1.468 ms | −16,4% |
| `classificacao_llm` p50 | 844 ms | 794 ms | −5,9% |
| `classificacao_llm` p95 | 1.177 ms | 1.047 ms | −11,0% |
| Taxa de erro | 0% | 0% | — |
| Acerto de área | 100% | 100% | — |
| Revisão manual | 0% | 0% | — |
| Dentro do SLA de 60 s | 100% | 100% | — |

### Medição do cliente, até a resposta ao formulário

| Métrica | Antes | Depois | Variação |
|---|---|---|---|
| p50 | 1.512 ms | 1.479 ms | −2,2% |
| p95 | 2.002 ms | 1.895 ms | −5,3% |
| p99 | 2.264 ms | 2.181 ms | −3,7% |

Bruto em [`carga-baseline.json`](../evidencias/carga-baseline.json) e
[`carga-pos-otimizacao.json`](../evidencias/carga-pos-otimizacao.json), com as 200 amostras
individuais de cada corrida.

### Reproduzir

```bash
N8N_PUBLIC_URL=... JURISFLOW_WEBHOOK_SECRET=... \
  python scripts/carga_sintetica.py --n 200 --rotulo baseline --paralelas 4 --semente 42
# troca do prompt, publica, e:
  python scripts/carga_sintetica.py --n 200 --rotulo pos-otimizacao --paralelas 4 --semente 42
  python scripts/carga_sintetica.py --comparar baseline pos-otimizacao
```

---

## 4. O trade-off, com honestidade

**Não houve trade-off entre custo e latência.** As duas melhoraram. Era o esperado pelo
mecanismo: menos tokens de entrada significam menos trabalho para o provedor, tanto em
cobrança quanto em tempo. Alegar um sacrifício de latência onde não houve seria inventar
simetria.

**Houve um ganho que eu não previ, e que vale explicar.** Os tokens de **saída** caíram 20,5%,
embora a otimização só tenha mexido na entrada. A causa é a retirada dos acentos dos nomes de
área no prompt: o modelo passou a devolver `Civel` e `Tributario` em vez de `Cível` e
`Tributário`, e caractere acentuado custa mais tokens. O `Parse Classificação` já normalizava
acento, de modo que o roteamento não notou a diferença. Foi acidente de implementação que
deu certo, e não desenho — registrar como sorte é mais útil do que reivindicar como método.

**O risco real está na qualidade, e a medição não o cobre bem.** O acerto de área ficou em
100% nas duas corridas, mas o corpus tem **doze descrições distintas**, todas razoavelmente
inequívocas. Um prompt mais curto perdeu palavras-chave, e o lugar onde isso cobraria o preço
é precisamente o caso ambíguo — o relato que admite duas áreas, em que a nuance descartada
decidiria. O corpus não tem esses casos em volume suficiente para detectar a diferença.

Dito de outro modo: **a medição prova que não piorou nos casos fáceis, e não prova nada sobre
os difíceis.** Antes de levar isso a tráfego real, o corpus precisa receber os casos ambíguos
de [`exemplos-intakes.md`](../exemplos-intakes.md) e a taxa de revisão manual precisa ser
acompanhada por alguns dias.

**E o ganho absoluto é pequeno.** Vinte e um por cento soa bem; em dinheiro, a 2.500 intakes
por dia, são **US$ 4,35 para US$ 3,43 por mês**, ou noventa centavos. Num sistema com
orçamento de US$ 120 mensais de OPEX, isso não paga o tempo gasto se o único objetivo fosse
economizar. O que justifica a mudança é a combinação: o custo cai, a latência cai, a
qualidade se mantém nos casos medidos, e o prompt fica mais fácil de manter. Apresentar os
21% sem dizer que são noventa centavos seria escolher o número que impressiona em vez do que
informa.

---

## 5. Decisão

**Mantida em produção**, na v1.3.0.

Revisão prevista: acompanhar `pct_revisao_manual` em
[`vw_qualidade_dia`](../../db/metricas/vw_metricas.sql) por uma semana. O limite do alerta
A-11 é de 15%; a linha de base é de 0% sobre corpus fácil. Qualquer subida consistente acima
de 5% sugere que a nuance removida do prompt fazia falta, e o caminho de volta é restaurar as
definições de área mantendo o resto da compressão, que não depende delas.
