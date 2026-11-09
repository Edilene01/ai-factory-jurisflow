# Parte C: material para você escrever

> **Este arquivo não entra na entrega.** Ele existe só para você consultar enquanto escreve a
> Parte C em `analise-critica.md`, a partir da linha 89.

O enunciado determina que a Parte C seja **100% autoral, sem nenhum uso de IA**. Por isso aqui
não há frase pronta, nem rascunho, nem bullet que você possa vestir de parágrafo. O que está
aqui são **as perguntas do enunciado e os fatos do seu projeto**. Os fatos são seus. O que você
conclui deles é a Parte C, e tem de sair de você.

Uma observação prática: o avaliador lê as Partes A e B e depois a C. Se a C soar com a mesma
cadência das anteriores, ela perde justamente o que a torna valiosa. Escreva como você fala.
Frase torta é melhor do que frase perfeita e sem dono.

**Espaço: 350 a 400 palavras.** É pouco, e isso é bom. Força escolha.

---

## As quatro perguntas, e o material de cada uma

### 1. Pelo menos três propostas concretas de evolução, o roadmap v1.1

Para cada uma o enunciado pede três coisas: **o que mudaria**, **que tecnologia usaria** e
**qual o impacto esperado**. Uma proposta é "concreta" quando diz o que muda no sistema, e não
o que seria bom em geral.

Candidatas que o projeto já registrou. Não precisa usar nenhuma, e sobrar candidata é melhor
do que faltar.

| Candidata | Âncora técnica | Onde está registrada |
|---|---|---|
| Reconhecimento de entidades nomeadas antes da chamada ao modelo | biblioteca de NER sobre o texto, antes do `Sanitizar Entrada` devolver a versão que sai do país | seção 5 de `docs/lgpd/mapa-dados-pessoais.md` |
| Fila de reprocessamento para falha de entrega | hoje o caso vira `causa_falha: 'slack'` e para ali | limitações da análise crítica |
| Corpus de teste com casos ambíguos e rótulo humano | `docs/exemplos-intakes.md` já tem três casos ambíguos, fora da carga de medição | limitações da análise crítica |
| Cache de classificação | descartada por não ser mensurável com honestidade sobre corpus sintético | `docs/otimizacoes/001-compressao-do-system-prompt.md` |
| Fallback de provedor | `ANTHROPIC_API_KEY` já reservada no `.env.example` | README, seção de otimizações |
| Cláusulas-padrão da ANPD nos contratos | Resolução CD/ANPD nº 19/2024, prazo encerrado em agosto de 2025 | `docs/lgpd/transferencia-internacional.md` |
| Adoção no portal do escritório | proxy reverso em subdiretório, e-mail no lugar do Slack, link `wa.me` iniciado pelo cliente, você como controladora | `docs/evolucao/001-jurisflow-no-portal-do-escritorio.md` |

Sobre a última linha: **a ideia é sua**, saiu da conversa em que você perguntou se dava para
pôr o JurisFlow no seu portal. O documento só organiza o que foi decidido ali. Se ela entrar na
Parte C, escreva com suas palavras o motivo de ter pensado nisso, porque esse motivo é a única
coisa que nenhum documento do repositório registra.

Números que existem, caso você queira quantificar impacto: p95 de 1,27 s, 0% de erro em 200
casos, US$ 0,000046 por caso, US$ 3,43 por mês a 2.500 casos diários, 21,2% de queda de custo
e 12,3% de queda de p95 na compressão do prompt, 99 horas mensais devolvidas.

### 2. O que você aprendeu que não esperava aprender

A pergunta é sobre **surpresa**, não sobre conteúdo programático. Momentos deste projeto em
que a realidade contrariou a expectativa, para ajudar a lembrar.

**Coisas que estavam quebradas sem avisar:**

* O nó `Switch` do n8n aceita no máximo quatro saídas na versão 1, e o projeto tinha cinco áreas. A quinta, Consumidor, **nunca funcionou desde o protótipo**, e só apareceu quando o fluxo rodou com volume.
* Duas falhas graves eram invisíveis porque terminavam em "sucesso": o caso caía em triagem manual e nada acusava. Com `saveDataSuccessExecution: none`, nada ficava registrado.
* O contador de execuções de produção marcou **zero** até 20 de outubro. O caminho completo nunca havia rodado.
* Os três smoke tests existiam desde a Etapa 1 e só passaram na Etapa 2.
* O n8n estava usando SQLite, e não o Postgres, então a tabela `execution_entity` não existia e a segunda barreira das 72 horas não tinha o que purgar.
* O script de publicação apagava o vínculo das credenciais a cada `PUT`, porque o JSON guarda o id vazio por desenho. É a explicação mais provável para a confusão entre rascunho e publicado na Etapa 1.

**Coisas que custaram caro por motivo bobo:**

* O erro mais difícil de diagnosticar foi um `HTTP 400 Bad Request` sem corpo. A causa estava na resposta que o próprio script descartava antes de mostrar.
* O nó nativo da OpenAI resolvia para a raiz da API e devolvia a mensagem de boas-vindas do provedor, que o sistema tratava como classificação malformada.
* `percentile_cont` não aceita `OVER()` no PostgreSQL.
* No Git Bash, `python3` é um atalho da Microsoft Store que termina com sucesso sem executar nada.

**Coisas sobre medir:**

* A estimativa de custo errou para cima em quase o dobro: US$ 0,000046 medido contra US$ 0,000103 calculado por contagem de caracteres.
* A otimização que deu 21,2% de economia vale noventa centavos de dólar por mês. O que justificou a mudança não foi o dinheiro.
* O cache foi descartado porque, sobre doze descrições repetidas, ele mostraria um ganho espetacular e falso.
* O SLA contratado de 60 segundos é quarenta e sete vezes maior do que o p95 real.

**Coisas sobre consertar:**

* Ao mover a trilha de auditoria para depois do Slack, uma falha de entrega passou a apagar o registro do caso. O conserto introduziu a falha, e ela só apareceu porque havia medição.
* O LICENSE trazia o nome do professor desde o commit de adoção, enquanto o campo `owner` do workflow herdado tinha sido cuidadosamente limpo. A disciplina existia, e não alcançou o arquivo de licença.

### 3. Como a experiência se conecta com os seus objetivos profissionais ou pessoais

Aqui eu não tenho o que oferecer, e não é modéstia: é a pergunta que o avaliador usa para saber
se há uma pessoa do outro lado, e qualquer coisa que eu sugerisse apagaria isso.

Perguntas que talvez ajudem a destravar:

* Você entrou nisso esperando aprender o quê? E foi isso que aconteceu?
* Alguma coisa aqui mudou o jeito como você olha para o trabalho que já faz?
* A decisão de levar o sistema para o seu portal: ela nasceu quando?
* Há algo neste projeto que você faria de novo sem ser por nota?

### 4. Se pudesse recomeçar, o que faria diferente na condução do protótipo herdado

A pergunta é sobre **condução**: ordem, prioridade, critério de "pronto". Não sobre tecnologia.

Fatos que podem servir de âncora:

* A auditoria do protótipo encontrou 25 achados, seis críticos, e foi escrita **antes** de qualquer código.
* A Etapa 1 foi entregue com o sistema parcialmente verificado, e o `estado-da-entrega.md` registrou honestamente o que não tinha sido testado.
* A plataforma mudou três vezes: ADR-002 em 18/09 escolhe Railway nos dois ambientes, ADR-003 em 21/09 move produção para o n8n Cloud, ADR-004 em 19/10 manda reconstruir no n8n Cloud, e a ADR-005 **no mesmo dia** volta para o Railway. A ADR-004 foi substituída no dia em que nasceu.
* O impedimento que derrubou a ADR-004, a conta trial não emitir chave de API, só apareceu depois da decisão tomada.
* A instância de produção sumiu duas vezes, e o banco voltou vazio uma delas. Não havia rotina de backup, e ainda não há.
* A observabilidade foi desenhada na Etapa 2, e o primeiro bug que ela expôs existia desde o protótipo.

---

## Antes de entregar a Parte C

1. **Tem pelo menos três propostas**, cada uma com o que muda, a tecnologia e o impacto?
2. **A reflexão é específica deste projeto?** Se o parágrafo funcionaria em qualquer trabalho de qualquer disciplina, está genérico demais.
3. **Soa como você?** Leia em voz alta. Se travar em alguma frase, reescreva do jeito que você diria.
4. **Está entre 350 e 400 palavras?** Conte só no fim. Contar enquanto escreve trava a mão.

O enunciado diz que *"limitações honestas elevam a nota"*. A Parte C é onde isso pesa mais,
porque é a única em que você fala na primeira pessoa sobre o que não deu certo.
