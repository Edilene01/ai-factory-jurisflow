# Roteiro do pitch · Etapa 3

**Duração exigida:** entre **4:30 e 5:30**. Fora disso a nota cai, e o enunciado é explícito
sobre isso. O roteiro abaixo cronometra em cerca de 4:50 em ritmo de fala normal, o que deixa
margem para respirar sem estourar.

**Título no YouTube, não listado, exatamente assim:**

```
[AI Factory] Pitch - JurisFlow - Edilene Chagas Faria
```

**Público:** liderança e investidor. Ninguém vai ler o seu código. Se uma frase só faz sentido
para quem programa, corte.

---

## Antes de gravar

**Mova os arquivos de segredo.** Na pasta acima do repositório há `.txt` com chave da OpenAI,
token do Slack e chaves de API. Não estão versionados, mas aparecem em qualquer captura da
pasta.

**Deixe três abas prontas**, nesta ordem:

1. https://ai-factory-jurisflow-production.up.railway.app/ , o formulário, com os campos vazios
2. https://ai-factory-jurisflow-production.up.railway.app/painel , o painel
3. O Slack, no canal `#juris-trabalhista`

**Grave uma demo de backup antes.** A rubrica pede demo gravada de reserva mesmo que não seja
usada, e vale 20% junto com a aplicação no ar. Dois minutos de tela mostrando o fluxo bastam.

**Áudio.** O enunciado pede ganho entre -18 e -6 dB e algo perto de -14 LUFS. Na prática: fale
a 20 centímetros do microfone, num cômodo com cortina ou sofá, e teste trinta segundos antes.
Áudio pesa mais que imagem.

---

## 0:00 a 1:00 · O problema

Comece pelo dinheiro, não pela tecnologia.

A JurisFlow atende 180 escritórios e recebe 2.500 formulários de intake por dia. A triagem era
manual, e um caso levava de 3 a 6 horas para chegar à equipe certa.

A frase que fixa o problema: **cliente que espera meio dia por uma resposta procura outro
escritório**. Não era problema operacional, era perda de receita, e ninguém conseguia medir o
tamanho dela.

Diga também o que você recebeu: um protótipo que funcionava só na máquina de quem o escreveu,
com chave de API dentro do código e nome e CPF indo sem máscara para o Slack.

## 1:00 a 2:00 · A solução

Em uma frase: o formulário é preenchido e, em menos de três segundos, o cliente recebe um
protocolo com a área e a urgência, enquanto a equipe responsável é notificada.

Três pontos, e só três:

1. **A urgência é reconhecida.** Prisão em flagrante e prazo vencendo em cinco dias viram alta. Antes, o caso urgente ficava na mesma fila do resto.
2. **O dado pessoal não chega ao modelo.** CPF, CNPJ, e-mail e telefone são removidos antes da chamada. A descrição de um caso jurídico é coberta por sigilo profissional, e isso não é detalhe de implementação.
3. **O que o sistema não entende, ele admite.** Em vez de chutar a área, manda para triagem humana com o motivo escrito.

Resista a falar de n8n, FastAPI ou Postgres aqui. A liderança não compra stack.

## 2:00 a 3:30 · Demo

A parte mais importante, e a que mais estoura tempo. Ensaie.

**No formulário**, preencha com o caso de plano de saúde:

> "Meu plano de saúde negou a cirurgia que o médico disse ser urgente e a internação está
> marcada para a próxima semana."

Use o CPF `111.444.777-35`, dizendo em voz alta que é número de teste, válido pelo dígito
verificador e de ninguém.

Enquanto carrega, diga a frase: *"isso aqui levava de três a seis horas."*

Mostre o resultado: protocolo, área **Consumidor**, urgência **alta**. Aponte a urgência, que
é o que um humano levaria tempo para avaliar.

**Vá ao Slack** e mostre o caso no canal, com nome e CPF mascarados. Diga: *"a equipe vê o
caso, não vê o CPF."*

**Abra o painel.** Mostre o volume subindo, o p95 e o custo. Uma frase: *"cada caso custa
quatro centésimos de milésimo de dólar."*

## 3:30 a 4:30 · Resultados

Números medidos, não estimados. Diga isso.

| O que dizer | Número |
|---|---|
| Tempo até a equipe | de 3 a 6 horas para **1,27 segundo** no p95 |
| Dentro do SLA de 60 segundos | **100%** |
| Erro | **0%** em 200 casos |
| Custo mensal a 2.500 casos por dia | **US$ 3,43** |
| Orçamento autorizado | US$ 120, dos quais sobram 85% |

Depois a otimização, em uma frase: comprimi o prompt e o custo caiu 21% com a latência caindo
12%, sem perder acerto.

E então **a limitação**, que o enunciado diz que eleva a nota. Escolha uma e seja direta:

> "Medi a qualidade sobre doze descrições, todas claras. O caso ambíguo, aquele que admite
> duas áreas, é onde um classificador erra, e disso eu ainda não tenho evidência."

Admitir isso num pitch desarma a pergunta que o avaliador faria em seguida.

## 4:30 a 5:00 · Próximos passos

Três, rápidos:

1. Remover nome de empregador e endereço antes da chamada ao modelo, fechando a lacuna que a expressão regular deixa.
2. Fila de reprocessamento para quando a entrega no Slack falha, que hoje exige alguém olhar.
3. Corpus de teste com casos ambíguos, para medir acerto de verdade.

Feche com a frase de valor, não com "obrigada": o sistema devolve ao escritório cerca de 99
horas por mês de trabalho de triagem, por volta de cem reais mensais de operação.

---

## Erros que custam nota

- **Estourar 5:30.** Cronometre em ensaio, não na gravação.
- **Tour de código.** A rubrica trata isso como nota mínima. Nenhum segundo em editor de código ou no canvas do n8n.
- **Demo arrastada.** Se o formulário demorar, fale por cima. Silêncio de espera consome tempo caro.
- **Jargão.** "Webhook", "span", "p95" sem tradução. Diga "o tempo que 95 dos 100 casos levam, no pior deles".
- **Número sem origem.** Diga "medido em 200 casos", não "aproximadamente".
