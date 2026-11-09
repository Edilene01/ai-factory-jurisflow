# Evolução 001: JurisFlow no portal do escritório

* **Status:** proposta, fora do escopo avaliado na disciplina
* **Data:** 06/11/2026
* **Autora:** Edilene Chagas Faria
* **Relação com as ADRs:** não substitui nenhuma. As ADRs 001, 002, 005, 006 e 007 continuam
  descrevendo o sistema entregue. Este documento descreve um sistema **derivado**.

---

## Por que isto existe

A JurisFlow é uma empresa fictícia. O sistema que foi construído para ela, porém, resolve um
problema que existe em qualquer escritório pequeno: alguém lê o formulário de contato, decide
de que assunto se trata, avalia se é urgente e encaminha. Isso leva horas e acontece em
horário comercial.

A proposta é levar o sistema para atendimento real no portal
`www.edilenechagas.adv.br`, mantendo o entregável acadêmico congelado como está.

A separação entre os dois é o ponto central deste documento, e vem logo abaixo.

## O que não muda: a entrega avaliada fica onde está

O briefing restringe a hospedagem a Render, Railway, Fly.io ou n8n Cloud. Um servidor próprio
não está nessa lista. Portanto:

| Repositório | Estado | Papel |
|---|---|---|
| `ai-factory-jurisflow` | congelado na v2.0.0, no Railway | entregável da disciplina |
| versão do escritório | novo, privado | atendimento real, sob responsabilidade da autora |
| repositório do portal | recebe apenas o link e o bloco de proxy | integração, não aplicação |

A versão do escritório nasce de um espelho, `git clone --bare` seguido de `git push --mirror`,
e não de um fork nem de uma cópia de pasta. O espelho preserva branches, tags, as sete ADRs e
a matriz de decisão. Isso importa por um motivo que não é técnico: **a linhagem do Git é a
evidência da adoção**. Uma cópia de arquivos viraria um commit único chamado "adiciona
jurisflow", e a história de como o sistema chegou até aqui desapareceria.

## Onde o sistema fica no portal

O portal não é WordPress. É HTML servido por nginx, com login por Cognito, e **já serve uma
aplicação dinâmica em subdiretório por proxy reverso**. O padrão que esta proposta precisa já
está rodando em produção naquele domínio.

Duas saídas foram consideradas.

**Subdomínio.** Dez minutos de trabalho, nenhuma linha de código alterada: domínio
personalizado no provedor, um CNAME no DNS, certificado emitido sozinho. Robusta, e é a saída
que menos tem o que quebrar.

**Subdiretório `/jurisflow/`.** Um bloco `location` no nginx com `proxy_pass`, mais a
substituição de seis caminhos absolutos por relativos nas telas (`/static/estilo.css` vira
`static/estilo.css`, `fetch('/api/intake')` vira `fetch('api/intake')`, e assim por diante).
O app continua funcionando igual na raiz, então não existe versão bifurcada.

**Escolhida: subdiretório.** A diferença decisiva é a origem. Em subdiretório, o JurisFlow
compartilha origem com o portal e pode, mais adiante, ficar atrás do login que já existe lá.
Em subdomínio, seria um segundo silo de autenticação.

Dois cuidados no proxy: o header `Host` precisa ser o do serviço de destino, porque é por ele
que a borda decide o roteamento; e `X-Forwarded-For` precisa ser repassado, porque
[`app/main.py`](../../app/main.py) lê o primeiro valor da cadeia para o limite de cinco
intakes por minuto. Sem isso, o limite passaria a contar o IP do próprio servidor, e um
visitante sozinho esgotaria a cota de todos.

## Hospedagem e custo

O VPS já está contratado e roda o portal. O n8n sobe ali em Docker, com a porta publicada só
no loopback, atrás do nginx. O `docker-compose.yml` do repositório já está escrito desse jeito.
O Postgres vai para a mesma máquina, e as 1.210 linhas de SQL em `db/` migram sem alteração,
porque são Postgres puro.

| Item | Hoje | No servidor próprio |
|---|---|---|
| Licença do n8n | zero | zero, a Sustainable Use License cobre uso interno |
| Hospedagem do n8n, do Postgres e da aplicação | paga no Railway | já paga |
| Entrega da notificação | Slack | e-mail corporativo já contratado |
| Tokens do modelo | US$ 0,000046 por caso | igual |

Com `gpt-4o-mini`, 500 intakes por mês custam cerca de **US$ 0,05**. O teto de US$ 120 do
briefing foi dimensionado para 2.500 casos por dia de uma empresa que não existe. No volume de
um escritório, o modelo é ruído contábil.

O custo real não é dinheiro, é memória. O container do n8n consome de 300 a 500 MB e o Postgres
uns 200 MB, somados ao que a máquina já roda. Conferir a folga antes é obrigatório.

## As três mudanças funcionais

**1. As áreas.** Trabalhista, Cível, Tributário, Criminal e Consumidor são da empresa
fictícia. Passam a ser Direito Digital, Fundiário e Administrativo, mais o destino de não
classificados. Toca o prompt de classificação, a normalização em `Parse Classificação` e o
roteamento. O banco não resiste à mudança: `area` é TEXT livre, e só `urgencia` tem
restrição de domínio.

**2. A entrega.** Seis nós de Slack saem, um nó de e-mail entra, por SMTP do provedor
corporativo com senha de aplicativo. O workflow **encolhe**. E a notificação passa a ter trilha
pesquisável e arquivada, coisa que mensagem instantânea não tem.

**3. O WhatsApp, do cliente para o escritório.** Na tela de resultado, ao lado do protocolo,
um botão `https://wa.me/<número do escritório>?text=...` com o protocolo já escrito no corpo
da mensagem.

A alternativa seria a Cloud API da Meta, e ela foi descartada por uma razão que não é preço:
**um número registrado na Cloud API deixa de funcionar no aplicativo do WhatsApp**. O número de
contato do escritório viraria um endpoint. O custo por mensagem é irrisório, mas o custo real
seria um segundo chip, verificação de Business Manager e aprovação de template, para economizar
nada.

O link tem ainda uma vantagem que a API não tem: quem inicia a conversa é o cliente. Isso
mantém a prática do lado seguro do Provimento 205/2021 da OAB quanto a captação de clientela.

## A mudança que pesa mais: a controladora passa a ser uma pessoa real

Hoje os documentos em `docs/lgpd/` nomeiam a JurisFlow como controladora, e isso é ficção
confortável. Com atendimento real, a controladora é a titular do escritório, e o dado é
duplamente protegido: pessoal e sensível pela Lei nº 13.709/2018, e coberto por sigilo
profissional pela Lei nº 8.906/1994.

O que precisa ser reescrito antes do primeiro caso real:

* `mapa-dados-pessoais.md`, com a controladora correta e os pontos de coleta do portal.
* `politica-retencao-exclusao.md`, incluindo o backup, que também contém dado pessoal.
* `transferencia-internacional.md`, que muda de operadores quando o Slack sai da arquitetura.

A base legal migra para o **art. 7º, V**, tratamento preliminar a contrato a pedido do próprio
titular. É fundamento mais firme do que legítimo interesse, justamente porque é a pessoa que
procura o escritório.

E aqui a decisão tomada na primeira semana se paga. A sanitização que remove CPF, CNPJ, e-mail
e telefone **antes** da chamada ao modelo deixa de ser cautela acadêmica e passa a ser o que
sustenta a afirmação de que o relato do cliente não sai íntegro para um servidor fora do país.
A limitação declarada na seção 5 do mapa de dados continua valendo e fica mais urgente: a
expressão regular não remove nome próprio, endereço nem nome de empregador. Reconhecimento de
entidades nomeadas deixa de ser melhoria desejável e vira pré-requisito.

## A lacuna que precisa ser fechada antes, e não depois

Um servidor único junta nginx, n8n, aplicação e banco no mesmo disco.

O `runbook-recuperacao.md` afirma que a trilha de auditoria sobrevive à perda da instância.
Isso era verdade no Railway, onde o Postgres era serviço gerenciado separado: quando a
instância evaporava, o banco continuava de pé. Aconteceu duas vezes e funcionou as duas. **Num
servidor só, essa frase deixa de valer**, e é exatamente a linha que dá a sensação de que está
tudo bem.

Não existe rotina de backup no repositório. Procurado: `pg_dump`, `backup`, `restore`. O
`restaurar_instancia.py` restaura a instância do n8n, não o banco.

Enquanto o conteúdo era sintético, isso não custava nada. Com caso real, muda de figura: o
art. 37 da LGPD exige o registro das operações de tratamento, e perder o banco deixa de ser
perder dados para passar a ser **perder a prova da conformidade**.

Quatro providências, em ordem de retorno:

1. `pg_dump` diário, cifrado antes de sair da máquina, guardado fora do provedor do servidor. A retenção de 12 meses vale para o backup também, senão a purga é furada.
2. Versionar a configuração do servidor: nginx, compose de produção, unidades do systemd, crontab. Transforma reconstruir a máquina em `git clone` mais um script.
3. Segredos num gerenciador de senhas, e não em `.txt` na pasta do projeto.
4. Trocar o `retencao.yml` do GitHub Actions por um timer do systemd na própria máquina. Some o consumo de minutos, some a desativação automática de workflow agendado após 60 dias sem atividade no repositório, e o Postgres deixa de precisar ser alcançável pela internet.

O item 4 é o que mais muda a postura de segurança. Hoje o runner do GitHub precisa chegar ao
banco de fora, o que obriga o banco a estar exposto. Num servidor próprio, o desejado é o
Postgres amarrado ao `localhost` e nada mais, e um agendador local é a única forma de purgar
sem abrir essa porta.

## Ordem sugerida

1. Espelhar o repositório e abrir a branch da versão do escritório.
2. Conferir a folga de memória no servidor, subir n8n e Postgres em Docker, rodar `migrar_tudo.sql`.
3. Implantar backup cifrado para fora da máquina. Antes de qualquer dado real.
4. Trocar as áreas, trocar Slack por e-mail, acrescentar o botão do WhatsApp.
5. Reescrever os três documentos de LGPD com a controladora correta.
6. Publicar em `/jurisflow/` por proxy reverso, com os caminhos relativos corrigidos.
7. Só então divulgar o endereço.

A ordem não é arbitrária. Os passos 3 e 5 vêm antes do 7 porque, depois que o endereço circula,
chega caso real, e não existe desfazer.
