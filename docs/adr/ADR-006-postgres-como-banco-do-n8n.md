# ADR-006: Postgres como banco do n8n, com papel próprio para a purga

* **Status:** aceita
* **Data:** 29/10/2026
* **Decisora:** Edilene Chagas Faria
* **Revê:** a escolha do caminho 1 registrada na seção 2.1 de [`politica-retencao-exclusao.md`](../lgpd/politica-retencao-exclusao.md)
* **Depende de:** ADR-005
* **Procedimento associado:** [`runbook-recuperacao.md`](../runbook-recuperacao.md)

## Contexto e definição do problema

Duas coisas se encontraram, e só juntas justificam esta ADR.

A primeira estava documentada desde 20/10. A política de retenção registra que o prazo de 72
horas do PC-02 e do PC-08 **não tem mecanismo em operação**, porque o n8n guarda as próprias
execuções em SQLite, e não no Postgres que o JurisFlow criou. A purga SQL encontra
`relation "execution_entity" does not exist`, e as variáveis de *pruning* nativo não estavam
definidas no Railway. É a pendência de conformidade mais séria em aberto.

A segunda foi descoberta em 29/10, e já durava dias.

### O que se perdeu

A instância de produção respondia `200` em `/healthz` e `404` em `/webhook/intake`, com a
mensagem `The requested webhook "POST intake" is not registered`. A consulta a
`/rest/settings` devolveu `userManagement.showSetupOnFirstLoad: true`, ou seja, **a instância
pedia a criação da conta de dono**. As duas chaves de API foram recusadas com `401`, embora
nenhuma estivesse vencida: a de produção vale até 17/01/2027 e a de desenvolvimento até
20/11/2026. Chave válida recusada não é prazo, é assinatura — o segredo que as assinou deixou
de existir.

Some junto o que o n8n guardava: a conta, as quatro credenciais e o histórico de execuções.
**O que vive fora dele ficou íntegro**: os três workflows, porque estão versionados em
`workflows/`, e a trilha, os *spans* e o registro de purga, porque o Postgres é outro serviço
e não foi tocado. A tabela do que se perde e do que não se perde está no
[`runbook-recuperacao.md`](../runbook-recuperacao.md).

**Quando** isso aconteceu não é o dia em que foi visto. A última prova de instância cheia é
de 20/10/2026, em
[`evidencias/2026-10-20-smoke-e-classificacao.md`](../evidencias/2026-10-20-smoke-e-classificacao.md),
com os três *smoke tests* passando. A descoberta é de 29/10. Entre as duas datas há **até
nove dias** em que o formulário de intake não atendeu ninguém, sem que nada avisasse.

A causa é o armazenamento padrão em SQLite dentro do contêiner, que depende de um volume
remontado a cada *deploy*. O runbook registra o mecanismo em uma frase: **toda mudança de
variável no Railway dispara um redeploy, e redeploy é o momento em que o volume pode não
remontar.** O mesmo runbook traz a triagem que separa, pelos logs do *deploy*, banco ilegível
de banco novo, e nesta ocorrência o padrão é o de banco novo.

Não é episódio isolado. É a **segunda vez** que uma instância volta sem dados neste projeto:
a primeira foi a do n8n Cloud, por fim de assinatura, registrada na ADR-004. Causas
diferentes, mesmo efeito, e nas duas vezes a definição do sistema sobreviveu porque vive no
Git. A apuração do intervalo de nove dias é assunto do post-mortem, não desta ADR.

### Por que isso muda a decisão de 20/10, e não apenas a adia

A política considerou dois caminhos e escolheu o primeiro, com este argumento:

> *"A segunda opção parece mais completa e cobra um preço que ela não justifica: trocar o
> banco do n8n não migra nada, de modo que as quatro credenciais, a chave de API e o
> histórico seriam perdidos e teriam de ser refeitos à mão."*

O argumento era correto e a decisão era a certa naquele dia. O que o invalida não é um
raciocínio melhor: é que **o preço foi cobrado de qualquer modo**, em 29/10, sem a
contrapartida que ele compraria. As quatro credenciais, a chave de API e o histórico já se
foram. A escolha de 20/10 evitava um custo; hoje esse custo está pago, e o que a decisão
protegia não existe mais para ser protegido.

A comparação, portanto, não é a mesma. Em 20/10 a troca custava uma reconstrução manual e
rendia redundância. Em 29/10 a reconstrução manual é obrigatória de qualquer jeito, e a troca
passa a render a redundância **de graça**. Uma decisão que depende de uma premissa deve ser
revista quando a premissa cai, e é só isso que acontece aqui.

### O efeito colateral que a troca cria

Com o n8n sobre o mesmo Postgres da trilha, quem tiver a URL do banco alcança também
`credentials_entity`, onde o n8n guarda as credenciais cifradas. O
`.github/workflows/retencao.yml` roda em um *runner* do GitHub, fora da plataforma, com essa
URL em um *secret*. Dar ao *runner* o papel dono seria entregar o cofre a quem só precisa
esvaziar o lixo, e isso contradiria a própria seção de segurança de credenciais da entrega.

O efeito colateral não desaconselha a troca. Ele define o que precisa vir junto com ela, e é
por isso que a decisão abaixo tem duas partes, e não uma.

## Opções consideradas

* **A. Postgres como banco do n8n**, no mesmo serviço que já hospeda a trilha de auditoria, com papel de menor privilégio para a purga
* **B. Voltar ao SQLite**, agora com volume garantido, e sustentar as 72 horas apenas com o *pruning* nativo
* **C. Segundo serviço Postgres**, dedicado ao n8n, separado do banco da trilha

## Decisão

Escolhida a opção **A**, em duas partes inseparáveis.

**Primeira:** o n8n passa a usar o Postgres do projeto como banco próprio, por `DB_TYPE=postgresdb`
e as variáveis de conexão, com `N8N_ENCRYPTION_KEY` definida explicitamente no ambiente.

**Segunda:** a purga executada de fora da plataforma deixa de usar o papel dono do banco e passa
a usar `jurisflow_purga`, criado por [`db/schema/003_papel_purga.sql`](../../db/schema/003_papel_purga.sql).

A ordem importa. A primeira parte sozinha resolve a conformidade e abre um buraco de
segurança; a segunda sozinha não faz sentido. Entregar uma sem a outra seria trocar uma
pendência por outra.

### Consequências positivas

* **O prazo de 72 horas ganha mecanismo, e ganha dois.** `execution_entity` passa a existir neste banco, de modo que o ramo morto de `db/retencao/purga_diaria.sql` vira o caminho principal. As cinco variáveis de *pruning* entram no ambiente no mesmo movimento, e a primeira barreira passa a operar junto com a segunda. A afirmação da política deixa de ser intenção e vira mecanismo, que é exatamente o que a rubrica distingue.
* **O estado passa a sobreviver a uma recriação de contêiner.** É a correção direta do que aconteceu em 29/10, e vale para a conta, os workflows e as credenciais.
* **As credenciais deixam de depender do volume.** Com `N8N_ENCRYPTION_KEY` no ambiente, o segredo que as decifra não vive mais em um arquivo que some junto com o disco. Era esse acoplamento, e não o banco em si, que tornava a perda irreversível.
* **O `DATABASE_URL` que faltava nos dois *GitHub Environments* passa a existir**, e com ele a segunda via da purga, os nós `Gravar Trilha` e `Gravar Spans` e as *views* das cinco métricas saem do papel.
* Um serviço de banco a menos do que a opção C, e uma conexão a menos para configurar em cada credencial.

### Consequências negativas

* **A disponibilidade do n8n passa a depender do Postgres.** Com SQLite, o n8n subia sozinho e uma falha do banco afetava só a trilha. Agora, banco fora significa n8n que não inicia. Trocamos um modo de falha raro e catastrófico por um modo de falha mais comum e menos grave, o que é um bom negócio, mas é uma troca e não um ganho limpo.
* **O raio de alcance de um vazamento da URL aumenta.** Um único banco guarda a trilha pseudonimizada, os *spans*, os *payloads* de erro com nome e CPF sem máscara, e as credenciais cifradas do n8n. O papel de menor privilégio contém isso para o *runner* do GitHub, que é o consumidor externo, mas não para quem obtiver a credencial do papel dono.
* **A rede privada do Railway é IPv6 e não existe durante o *build*.** O primeiro *boot* depois da mudança pode falhar com erro de resolução de nome e só subir no *restart* seguinte. É comportamento esperado e não incidente, mas vai assustar quem não souber.
* **O Postgres passa a rodar continuamente**, e não sob demanda como o serviço de desenvolvimento previsto na ADR-005. O custo é pequeno no plano Hobby e é previsível, mas é recorrente.
* **A reconstrução manual continua sendo obrigatória.** Esta ADR não recupera o que se perdeu em 29/10: a conta de dono e as quatro credenciais precisam ser refeitas à mão de todo modo. A decisão evita a próxima perda, não desfaz esta.
* **Aplicar esta decisão é, ela própria, uma janela de risco.** São sete variáveis novas no serviço do n8n, e cada alteração dispara um *redeploy*, que é o momento em que o volume pode não remontar. Hoje isso é inofensivo, porque não há mais o que perder; depois de recriadas as credenciais, deixa de ser.
* Um papel a mais para rotacionar, com a sua linha própria na tabela de prazos.

### Mitigações adotadas

Criar o papel `jurisflow_purga` e cadastrar nos *GitHub Environments* a URL **dele**, nunca a
do papel dono. O arquivo traz a contraprova no rodapé: sob `SET ROLE jurisflow_purga`, um
`SELECT` em `credentials_entity` tem de falhar com `permission denied`.

Definir `N8N_ENCRYPTION_KEY` como variável de ambiente, com valor novo e guardado fora da
árvore do projeto. Não reaproveitar a de desenvolvimento: ambientes que dividem segredo não
são ambientes separados, e a ADR-005 já paga o preço de duas instâncias justamente para que
sejam.

Fazer **todas** as alterações de variável de uma vez, antes de recriar a conta de dono e as
quatro credenciais, e só então conferir a instância. A ordem inverte o risco, porque põe o
*redeploy* perigoso no momento em que não há nada a perder. O runbook trata isso como janela
de manutenção, e não como operação de rotina.

Manter o `retencao.yml` **fora da plataforma**, pelo motivo que a ADR-005 já havia dado e que
esta decisão agrava: antes, as duas instâncias dividiam fornecedor; agora o n8n e o banco
dividem fornecedor **e projeto**. A via externa é o que impede que uma falha do Railway leve
junto a prova de que a retenção foi executada.

Registrar `jurisflow_purga` e o novo `N8N_ENCRYPTION_KEY` na tabela de
[`rotacao-credenciais.md`](../rotacao-credenciais.md), pela razão de sempre: credencial que
não está na tabela não é rotacionada, é esquecida.

## Alternativas descartadas e o porquê

**B. Voltar ao SQLite, com volume garantido.** É a opção mais barata e a mais próxima do que
já existia, e corrige a durabilidade sem tocar em arquitetura. Foi descartada porque deixa a
conformidade onde está: sem `execution_entity` neste banco, a purga SQL continua registrando
zero com observação, e o prazo de 72 horas segue apoiado em uma barreira só. A política
aceita uma barreira como suficiente para o art. 16, e isso continua verdadeiro — mas a opção
A entrega a mesma durabilidade e ainda fecha a lacuna, pelo mesmo trabalho de reconstrução
manual. Escolher B seria pagar o custo inteiro e levar metade.

**C. Segundo Postgres, dedicado ao n8n.** Resolve de forma limpa o aumento do raio de alcance,
porque as credenciais cifradas do n8n ficariam em um banco que o *runner* do GitHub jamais
alcança. Foi descartada por dois motivos. O primeiro é que ela **recria a lacuna das 72
horas**: `execution_entity` viveria no banco do n8n, e a purga externa, apontada para o banco
da trilha, não a alcançaria — exatamente o problema de hoje, com outro nome. O segundo é
custo e operação, com mais um serviço a monitorar e a rotacionar. O papel de menor privilégio
entrega a maior parte da proteção sem nenhum dos dois defeitos.

## Validação

A decisão se confirma quando:

1. `to_regclass('execution_entity')` devolver valor não nulo neste banco, e a purga diária
   gravar em `jurisflow_purga_log` pelo ramo do `IF`, e não pelo `ELSE`.
2. Um *redeploy* do serviço do n8n, depois da conta de dono e das quatro credenciais
   recriadas, **mantiver tudo no lugar**. É o teste que a configuração anterior falhou, e
   nenhum outro prova durabilidade.
3. `SET ROLE jurisflow_purga` seguido de `SELECT count(*) FROM credentials_entity` falhar com
   `permission denied`.
4. O `retencao.yml` concluir em verde, com `DATABASE_URL` apontando para o papel restrito.
5. Os três *smoke tests* passarem contra a URL pública, de novo.

O [`scripts/restaurar_instancia.py`](../../scripts/restaurar_instancia.py) cobre os itens 1 e
5 em uma corrida: publica os três workflows, ativa, aponta qual credencial ficou faltando,
roda os *smoke tests* e consulta o painel de métricas. Os itens 2, 3 e 4 são conferidos à
mão, e o 2 é o único que exige esperar um *redeploy* para valer.

Se a disponibilidade do n8n passar a ser refém do Postgres com frequência que atrapalhe a
operação, ou se o banco único se mostrar um risco maior do que o avaliado aqui, esta ADR deve
ser revista em favor da opção C, aceitando o custo do serviço adicional e resolvendo a lacuna
das 72 horas por outro caminho.

O motivo de a perda ter levado até nove dias para ser notada é assunto do post-mortem
INC-002, e não desta ADR. O que cabe registrar aqui é que o alerta
**A-02**, de volume abaixo de 20% da média da mesma hora, já estava catalogado como P1 em
[`observabilidade/alertas.md`](../observabilidade/alertas.md) e teria pego isto no mesmo dia,
se estivesse implementado.
