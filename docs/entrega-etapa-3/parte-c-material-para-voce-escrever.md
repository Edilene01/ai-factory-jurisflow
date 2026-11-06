# Parte C: material para você escrever

> **Este arquivo não entra na entrega.** Ele existe só para você consultar enquanto escreve a
> Parte C em `analise-critica.md`.

O enunciado determina que a Parte C seja **100% autoral, sem nenhum uso de IA**. Por isso eu
não a escrevi, nem rascunhei, nem deixei frases prontas para você ajustar. O que está aqui são
as perguntas do enunciado e os fatos do projeto, que são seus. O texto tem de sair de você.

Uma observação prática: o avaliador vai ler as Partes A e B e depois a C. Se a C soar com a
mesma cadência das anteriores, ela perde justamente o que a torna valiosa. Escreva como você
fala. Frase torta é melhor do que frase perfeita e sem dono.

---

## As três perguntas

### 1. Pelo menos três propostas concretas de evolução, o roadmap v1.1

Para cada uma, o enunciado pede: **o que mudaria**, **que tecnologia usaria** e **qual o
impacto esperado**.

Candidatas que o projeto já registrou, caso queira partir delas. Não precisa usar nenhuma.

| Candidata | Onde está registrada |
|---|---|
| Reconhecimento de entidades nomeadas antes da chamada ao LLM, para remover nome próprio e endereço que a regex não pega | Seção 5 de `docs/lgpd/mapa-dados-pessoais.md` |
| Cache de classificação, que eu descartei por não ser mensurável com honestidade sobre corpus sintético | `docs/otimizacoes/001-compressao-do-system-prompt.md` |
| Fila de reprocessamento para falha de entrega no Slack | Limitações da análise crítica |
| Fallback de provedor, com `ANTHROPIC_API_KEY` já reservada no `.env.example` | README, seção de otimizações |
| Corpus de teste com casos ambíguos, para medir qualidade de verdade | Limitações da análise crítica |
| Incorporar as cláusulas-padrão da ANPD aos contratos | `docs/lgpd/transferencia-internacional.md` |
| Adoção no portal do escritório, com e-mail no lugar do Slack, áreas trocadas e você como controladora | `docs/evolucao/001-jurisflow-no-portal-do-escritorio.md` |

Sobre a última linha: a ideia é sua, saiu da conversa em que você perguntou se dava para pôr o
JurisFlow no seu portal. O documento só organiza o que foi decidido lá. Se ela entrar na Parte
C, escreva com suas palavras o motivo de ter pensado nisso, porque esse motivo é a parte que
nenhum documento registra.

O que torna uma proposta "concreta" para o avaliador: ela diz o que muda no sistema, não o que
seria bom em geral. Comparar "melhorar a qualidade da classificação" com "trocar a regex por
NER usando spaCy, o que removeria nome de empregador antes da chamada e reduziria o risco de
reidentificação" mostra a diferença.

### 2. O que você aprendeu que não esperava aprender

A pergunta é sobre surpresa, não sobre conteúdo programático. Alguns momentos deste projeto em
que a realidade contrariou a expectativa, para ajudar a lembrar:

* A instância de produção sumiu duas vezes, uma por fim de assinatura no n8n Cloud e outra quando o volume do Railway voltou vazio. Nas duas, o sistema sobreviveu porque estava versionado.
* O nó `Switch` do n8n aceita no máximo quatro saídas na versão 1, e o projeto tinha cinco áreas. A quinta, Consumidor, **nunca funcionou** desde o protótipo, e só apareceu quando o fluxo rodou com volume.
* O erro mais caro de diagnosticar foi um `HTTP 400 Bad Request` sem corpo. A causa estava na resposta que o script descartava.
* A estimativa de custo errou para cima em quase o dobro. O medido foi US$ 0,000046 por caso, contra US$ 0,000103 calculados por contagem de caracteres.
* Duas falhas graves eram invisíveis porque terminavam em "sucesso": o caso caía em triagem manual e nada acusava.

### 3. Como a experiência se conecta com os seus objetivos profissionais ou pessoais

Aqui você escreve sobre você, e eu não tenho o que acrescentar. É a pergunta que o avaliador
usa para saber se há uma pessoa do outro lado.

### 4. Se pudesse recomeçar, o que faria diferente na condução do protótipo herdado

A pergunta é sobre **condução**, não sobre tecnologia. Sobre o que você faria em outra ordem,
com outra prioridade, ou com outro critério de "pronto".

Fatos que podem servir de âncora:

* A auditoria do protótipo encontrou 25 achados, seis críticos, e foi escrita antes de qualquer código.
* A Etapa 1 foi entregue com o sistema parcialmente verificado, e o `estado-da-entrega.md` registrou honestamente o que não tinha sido testado.
* O contador de execuções de produção marcou **zero** até 20 de outubro. O caminho completo nunca havia rodado.
* Os três `smoke tests` existiam desde a Etapa 1 e só passaram na Etapa 2.

---

## Antes de entregar a Parte C

Três conferências rápidas:

1. **Tem pelo menos três propostas**, cada uma com o que muda, a tecnologia e o impacto?
2. **A reflexão é específica deste projeto?** Se o parágrafo funcionaria em qualquer trabalho de qualquer disciplina, está genérico demais.
3. **Soa como você?** Leia em voz alta. Se travar em alguma frase, reescreva do jeito que você diria.

O enunciado diz que *"limitações honestas elevam a nota"*. A Parte C é onde isso pesa mais,
porque é a única em que você fala na primeira pessoa sobre o que não deu certo.
