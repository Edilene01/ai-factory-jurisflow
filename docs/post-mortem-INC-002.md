# Post-mortem INC-002 – Nove dias no ar sem atender ninguém

* **Data do incidente:** entre 20/10/2026 e 29/10/2026
* **Natureza:** real, e não simulado. Diferente do [INC-001](post-mortem-INC-001.md), este não foi reproduzido de propósito
* **Duração:** 9 dias e cerca de 3 horas, do último deploy saudável até a recuperação completa
* **Detecção:** 29/10/2026, por conferência manual durante o fechamento da entrega
* **Severidade:** alta. O sistema respondia, e não atendia
* **Autora:** Edilene Chagas Faria

> Este post-mortem analisa causa, não pessoas. O projeto tem uma pessoa só, de modo que
> procurar culpado aqui seria especialmente inútil, e a causa que interessa é por que nenhum
> mecanismo avisou.

## Resumo

Em 20/10 a instância de produção foi reimplantada e subiu com o banco do n8n **vazio**.
Sumiram a conta de dono, as quatro credenciais, a chave de API e o histórico de execuções. Os
três workflows deixaram de existir na instância e, com eles, as rotas que atendiam o
formulário.

O contêiner continuou perfeitamente saudável. `/healthz` devolvia `200` e `{"status":"ok"}`
durante os nove dias inteiros. O que mudou foi invisível para quem olhasse de fora: um `POST`
em `/webhook/intake` passou a receber `404`, com a mensagem `The requested webhook "POST
intake" is not registered`.

Ninguém percebeu até 29/10, quando fui conferir o estado do sistema para fechar a entrega da
Etapa 2.

## Impacto

**Real, neste ambiente: nenhum caso perdido.** O JurisFlow ainda não recebe tráfego de
escritório; o que entra é carga sintética e *smoke test*. Nenhuma pessoa deixou de ser
atendida, e nenhum dado pessoal foi exposto ou destruído.

**Contrafactual, na escala declarada no briefing:** a 2.500 intakes por dia, nove dias sem
atender são **22.500 formulários** devolvidos com erro. Casos urgentes entre eles.

A diferença entre os dois parágrafos é só sorte de calendário. O modo de falha é idêntico, e é
isso que torna o episódio material de post-mortem e não nota de rodapé.

Dois efeitos colaterais que valem registro:

* **A janela de apuração fechou antes da apuração.** O plano Hobby do Railway guarda sete dias de log. A descoberta veio no nono. Os logs do deploy que causou o problema já não existiam.
* **O *pipeline* ficou nove dias sem ser exercitado de verdade.** As execuções verdes daquele período eram do evento `pull_request`, que roda só o *job* de qualidade. O deploy em si não rodava desde setembro.

## Linha do tempo

| Quando | O quê |
|---|---|
| 21/09/2026, 21:21 | O volume `n8n-volume` é criado e montado em `/home/node/.n8n` |
| 20/10/2026, 12:20 a 12:27 | Carga sintética de 200 intakes, duas corridas. 971 registros entram na trilha |
| 20/10/2026, ~12:51 | Evidência do alerta A-10 capturada. **Última prova de instância cheia** |
| 20/10/2026, 13:39 | Deploy `b74b40b8`. É o último antes da lacuna, e o suspeito |
| 20/10 a 29/10 | `/healthz` em 200. `/webhook/intake` em 404. Nenhum aviso |
| 27/10/2026 | Os logs do deploy de 20/10 expiram, sete dias depois |
| 29/10/2026, 13:23 | **Detecção.** Conferência manual para a entrega: `showSetupOnFirstLoad: True`, webhook em 404, as duas chaves de API em 401 |
| 29/10/2026, 13:48 | Deploy `85fd312e`, já apontando o n8n para o Postgres. As migrações iniciais rodam do zero, o que confirma que o n8n **não** estava em Postgres antes |
| 29/10/2026, ~16:00 | Conta de dono e as quatro credenciais recriadas à mão |
| 29/10/2026, 16:48 | Workflows republicados pelo repositório, três *smoke tests* passando, protocolo `JF-20261029-JT176S` classificado e entregue ao Slack |

## Causa raiz

**Não foi apurada, e a honestidade aqui vale mais que uma hipótese bem escrita.**

O que está estabelecido:

* O volume existia desde 21/09 e existe hoje, com 32 MB. Não é caso de volume ausente.
* O n8n **não** estava em Postgres antes de 29/10. Se estivesse, o boot daquele dia teria encontrado o esquema pronto em vez de rodar a cadeia inteira de migrações iniciais.
* Logo, até 29/10 o n8n usava SQLite dentro de um volume que existia e persistia.

O que não está estabelecido: **por que o banco daquele volume deixou de ser enxergado.**

A hipótese mais consistente com as evidências é que o volume não tenha sido montado no deploy
de 20/10. Nesse caso o n8n teria criado um SQLite novo no sistema de arquivos do contêiner e
rodado ali por nove dias, sem que nenhum reinício devolvesse o volume ao lugar, porque não
houve reinício nenhum até 29/10. **Se for isso, o banco original ainda está dentro do volume,
intacto, apenas nunca mais consultado.**

Não dá para confirmar sem um *shell* dentro do contêiner, e a confirmação deixou de ser
urgente quando a ADR-006 tirou o estado do volume. Fica registrado como hipótese, com essa
palavra.

## O que funcionou

**O Git como fonte da verdade.** Os três workflows voltaram do repositório, íntegros. É a
segunda vez que a instância evapora neste projeto, e a segunda vez que a definição do sistema
sobrevive. Foi o que a [ADR-001](adr/ADR-001-manter-n8n-como-orquestrador.md) comprou.

**O Postgres em serviço separado.** A trilha de auditoria e os *spans* não foram tocados: 971
registros e 3.880 *spans* continuavam lá quando o resto sumiu.

**O runbook escrito depois da primeira perda.** O `runbook-recuperacao.md` e o
`restaurar_instancia.py` existiam porque a instância do n8n Cloud já havia desaparecido em
outubro. Da segunda vez, a reconstrução foi procedimento em vez de improviso.

## O que não funcionou

**O alerta que teria pego isso estava escrito e não estava implementado.** O **A-02**, volume
abaixo de 20% da média da mesma hora, está catalogado como **P1** em
[`observabilidade/alertas.md`](observabilidade/alertas.md) desde que o catálogo foi escrito.
Ele existe exatamente para detectar ausência, que é o modo de falha que não gera erro. Treze
alertas no papel, um implementado, e o implementado não era este.

**O *health check* mente por construção.** `/healthz` responde pelo processo do n8n, não pelo
que o n8n está servindo. Container de pé com zero workflows publicados devolve `200` com a
mesma convicção de um sistema funcionando.

**O *pipeline* verde dava falsa segurança.** As execuções do período eram de `pull_request`,
que roda apenas o *job* de qualidade. Ver verde no GitHub durante nove dias enquanto o deploy
não rodava desde setembro é o tipo de sinal que conforta sem informar.

**A retenção de log era mais curta que o intervalo de detecção.** Sete dias de log contra nove
dias de cegueira significa que, por construção, qualquer incidente não detectado em uma semana
vira inapurável.

## Ações

| # | Ação | Estado |
|---|---|---|
| 1 | Tirar o estado do n8n do volume: Postgres como banco, com `N8N_ENCRYPTION_KEY` fixada no ambiente. [ADR-006](adr/ADR-006-postgres-como-banco-do-n8n.md) | **Feito** em 29/10, nos dois ambientes |
| 2 | Procedimento de recuperação, com o que se perde e o que sobrevive | **Feito**: [`runbook-recuperacao.md`](runbook-recuperacao.md) |
| 3 | Automatizar a parte automatizável da reconstrução | **Feito**: `scripts/restaurar_instancia.py` |
| 4 | Corrigir o exemplo do `rollback.md`, que mandava reverter para uma versão incompatível com o n8n atual | **Feito** em 29/10, com a execução registrada em [`evidencias/2026-10-29-rollback.md`](evidencias/2026-10-29-rollback.md) |
| 5 | **Implementar o A-02**, volume abaixo de 20% da média da mesma hora | **Pendente.** É a ação que mais importa desta lista |
| 6 | *Health check* que reflita o estado da aplicação, e não só o do processo: verificar que as rotas esperadas estão registradas | **Pendente** |
| 7 | Reter log além dos sete dias, ou enviá-lo para fora da plataforma | **Pendente.** Decisão de custo |
| 8 | Conferir se o banco original ainda está no volume, por curiosidade e para fechar a causa raiz | **Pendente**, sem urgência |

A ordem importa: **a 5 sozinha teria transformado nove dias em algumas horas.** As outras
reduzem o dano; ela reduz o tempo até alguém saber.

## Lição que fica

O INC-001 ensinou que falha silenciosa custa mais caro que falha ruidosa. Este incidente
ensina a versão mais incômoda da mesma coisa: **um sistema pode estar perfeitamente saudável
por todas as métricas que você coleta e não estar fazendo nada.**

CPU normal, memória normal, disco normal, `/healthz` em 200, *pipeline* verde. Cinco sinais
dizendo que estava tudo bem, e nenhum deles media a única coisa que importava, que é se algum
caso estava sendo atendido.

A métrica de **volume** existia no desenho justamente para isso. Está escrita na seção de
observabilidade do README como *"a única métrica que detecta falha silenciosa: se o formulário
parar de enviar, não há erro, há ausência"*.

A frase estava certa. Faltou implementar.
