# Roteiro do pitch · Etapa 3

**Duração exigida:** entre **4:30 e 5:30**. Abaixo de 4:29 ou a partir de 5:30 a nota cai, e o
enunciado é explícito. Este roteiro cronometra em torno de **5:05** em ritmo de fala normal,
o que deixa trinta segundos de folga dos dois lados.

**Título no YouTube, não listado, exatamente assim:**

```
[AI Factory] Pitch - JurisFlow - Edilene Chagas Faria
```

**Público:** liderança e investidor. Ninguém vai ler o seu código. Se uma frase só faz sentido
para quem programa, corte.

**A mudança em relação à versão anterior deste roteiro:** o fechamento deixou de ser uma lista
de melhorias técnicas e passou a ser a adoção real do sistema no portal do seu escritório. É o
único trecho do pitch que nenhum outro aluno tem como dizer.

---

## Antes de gravar

**Mova os arquivos de segredo.** Na pasta acima do repositório há `.txt` com chave da OpenAI,
token do Slack e chaves de API. Não estão versionados, mas aparecem em qualquer captura que
mostre a pasta.

**Deixe três abas prontas**, nesta ordem:

1. https://ai-factory-jurisflow-production.up.railway.app/ , o formulário, campos vazios
2. https://ai-factory-jurisflow-production.up.railway.app/painel , o painel
3. O Slack, no canal `#juris-trabalhista`

**Grave uma demo de backup antes.** A rubrica pede demo gravada de reserva mesmo que não seja
usada, e ela pesa junto com os 20% da aplicação no ar. Dois minutos de tela bastam.

**Áudio.** Ganho entre -18 e -6 dB, algo perto de -14 LUFS. Na prática: fale a 20 centímetros
do microfone, num cômodo com cortina ou sofá, e teste trinta segundos antes. Áudio pesa mais
que imagem.

---

## 0:00 a 0:55 · O problema

Comece pelo dinheiro, não pela tecnologia.

A JurisFlow atende 180 escritórios e recebe 2.500 formulários de intake por dia. A triagem era
manual, e um caso levava de 3 a 6 horas para chegar à equipe certa.

A frase que fixa o problema: **cliente que espera meio dia por uma resposta procura outro
escritório**. Não era problema operacional, era perda de receita, e ninguém media o tamanho
dela.

Diga em seguida o que você recebeu, porque isso enquadra tudo o que vem depois: um protótipo
que rodava só na máquina de quem o escreveu, com chave de API dentro do código e com nome e
CPF indo sem máscara para o Slack.

## 0:55 a 1:55 · A solução

Em uma frase: o formulário é preenchido e, em menos de três segundos, o cliente recebe um
protocolo com a área e a urgência, enquanto a equipe responsável é notificada.

Três pontos, e só três:

1. **A urgência é reconhecida.** Prisão em flagrante e prazo vencendo em cinco dias viram alta. Antes, o caso urgente ficava na mesma fila do resto.
2. **O dado pessoal não chega ao modelo.** CPF, CNPJ, e-mail e telefone são removidos antes da chamada. A descrição de um caso jurídico é coberta por sigilo profissional, e isso não é detalhe de implementação.
3. **O que o sistema não entende, ele admite.** Em vez de chutar a área, manda para triagem humana com o motivo escrito.

Resista a falar de n8n, FastAPI ou Postgres aqui. A liderança não compra stack.

## 1:55 a 3:20 · Demo

A parte mais importante, e a que mais estoura tempo. Ensaie com cronômetro.

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

**Abra o painel.** Mostre o volume, o p95 e o custo. Uma frase: *"cada caso custa quatro
centésimos de milésimo de dólar."*

## 3:20 a 4:20 · Resultados

Números medidos, não estimados. Diga isso em voz alta, porque a rubrica anula resultado
inventado.

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

Admitir isso desarma a pergunta que o avaliador faria em seguida.

## 4:20 a 5:05 · Próximos passos, e a prova de que escala

Aqui está a mudança de peso em relação ao roteiro antigo. Não feche com uma lista de
melhorias. Feche com adoção.

**Diga os dois primeiros em dez segundos**, porque eles respondem às limitações que você
acabou de admitir:

1. Reconhecimento de entidades nomeadas antes da chamada ao modelo, para remover nome de empregador e endereço, que a expressão regular não pega.
2. Fila de reprocessamento para quando a entrega falha, que hoje depende de alguém olhar.

**E então o terceiro, que é o fechamento do pitch.** Fale devagar, é o trecho que fica na
memória de quem avalia:

> "O terceiro item do roadmap não é uma melhoria. É adoção.
>
> Eu sou advogada, e tenho um escritório com portal próprio. O JurisFlow vai sair da empresa
> fictícia e entrar no meu site, triando contato real de cliente real. O servidor eu já pago,
> o e-mail corporativo eu já pago, e o custo adicional é o token do modelo: centavos por mês
> no volume de um escritório.
>
> Muda pouca coisa no sistema. As cinco áreas fictícias viram as três em que eu atuo. Os seis
> canais de Slack viram um e-mail. E o cliente recebe, junto com o protocolo, um botão que
> abre o WhatsApp dele já com o número do protocolo escrito, sem nenhuma API de mensageria no
> caminho.
>
> Muda uma coisa grande: a controladora dos dados passo a ser eu, com responsabilidade sobre
> dado sensível de cliente real, coberto por sigilo profissional.
>
> E é aqui que a decisão da primeira semana se paga. A sanitização que remove CPF, CNPJ,
> e-mail e telefone antes de chamar o modelo deixa de ser cuidado acadêmico e passa a ser o
> que me permite dizer, com honestidade, que o relato do cliente não sai inteiro daqui.
>
> O sistema não escala apesar da privacidade. Ele escala porque a privacidade foi desenhada
> antes de existir usuário."

**Feche com a frase de valor, não com "obrigada":** o sistema devolve ao escritório cerca de
99 horas por mês de trabalho de triagem, por volta de cem reais mensais de operação.

---

## A proposta de evolução, por trás das vinte linhas acima

Isto é material de apoio, para o caso de o avaliador perguntar. **Nada daqui entra no vídeo**,
sob pena de estourar o tempo. O desenho está registrado em
[`../evolucao/001-jurisflow-no-portal-do-escritorio.md`](../evolucao/001-jurisflow-no-portal-do-escritorio.md).

**Onde fica.** O portal já serve uma aplicação dinâmica em subdiretório, por proxy reverso no
nginx. O JurisFlow entra pelo mesmo padrão, em `/jurisflow/`, na mesma origem do site. Mesma
origem significa que, no futuro, ele pode ficar atrás do login que o portal já tem. Subdomínio
resolveria em dez minutos sem tocar em código, mas criaria um silo de autenticação separado.

**Quanto custa.** Nada de novo. O VPS já está contratado e roda o portal, o e-mail corporativo
já é pago, e o Postgres sobe no mesmo servidor. Sobra o token do modelo. Com `gpt-4o-mini`, 500
intakes por mês custam algo como US$ 0,05. O teto de US$ 120 do briefing foi dimensionado para
2.500 casos por dia de uma empresa que não existe.

**Por que não a API do WhatsApp.** Um número registrado na Cloud API da Meta deixa de funcionar
no aplicativo. O número de contato do escritório viraria um endpoint. O link `wa.me` com o
protocolo pré-escrito entrega o mesmo resultado, sem chip novo, sem verificação de Business
Manager e sem template para aprovar. Tem ainda a vantagem de que quem inicia a conversa é o
cliente, o que mantém a prática do lado seguro do Provimento 205/2021 da OAB.

**O que muda de verdade.** A troca das áreas toca o prompt, a normalização e o roteamento. A
troca do Slack por e-mail **encolhe** o workflow, de seis nós de entrega para um. O trabalho
pesado não é técnico: é reescrever `mapa-dados-pessoais.md`, `politica-retencao-exclusao.md` e
`transferencia-internacional.md` com você como controladora. A base legal migra para o art. 7º,
V, da Lei nº 13.709/2018, tratamento preliminar a contrato a pedido do próprio titular, que é
fundamento mais firme do que legítimo interesse.

**O que não muda, e é por isso que a entrega está segura.** O repositório avaliado fica
congelado no Railway com n8n. O briefing restringe a hospedagem a Render, Railway, Fly.io ou
n8n Cloud, e o VPS não está nessa lista. A versão do escritório nasce de um espelho
(`git push --mirror`) que preserva histórico, tags e ADRs, em repositório separado e privado.
A linhagem do Git vira, ela mesma, a evidência da adoção.

**A lacuna que eu não escondo.** Um VPS único junta nginx, n8n, aplicação e banco no mesmo
disco. O `runbook-recuperacao.md` diz que a trilha de auditoria sobrevive à perda da instância,
e isso era verdade no Railway, onde o Postgres era serviço separado. Deixa de ser verdade num
servidor só. Antes de entrar o primeiro dado de cliente real, tem de existir `pg_dump` diário
cifrado para fora da máquina, com a política de retenção de 12 meses valendo também para o
backup, senão a purga é furada: o dado volta.

---

## Erros que custam nota

- **Estourar 5:30 ou ficar abaixo de 4:29.** Cronometre em ensaio, não na gravação.
- **Tour de código.** A rubrica trata isso como nota mínima. Nenhum segundo em editor de código ou no canvas do n8n.
- **Deixar a adoção parecer troca de hospedagem.** Se soar como "vou tirar do Railway", o avaliador ouve descumprimento do briefing. A frase que separa as duas coisas é *"o entregável fica onde está; o que vai para o meu portal é uma versão derivada"*.
- **Demo arrastada.** Se o formulário demorar, fale por cima. Silêncio de espera consome tempo caro.
- **Jargão.** "Webhook", "span", "p95" sem tradução. Diga "o tempo que 95 de cada 100 casos levam, no pior deles".
- **Número sem origem.** Diga "medido em 200 casos", não "aproximadamente".
- **Mostrar dado do escritório real na tela.** O pitch fala da adoção, não a demonstra. Nenhuma captura do portal, do servidor ou do WhatsApp.
