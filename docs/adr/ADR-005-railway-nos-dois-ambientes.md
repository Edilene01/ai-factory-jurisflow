# ADR-005: Railway nos dois ambientes

* **Status:** aceita
* **Data:** 19/10/2026
* **Decisora:** Edilene Chagas Faria
* **Substitui:** ADR-004
* **Depende de:** ADR-001

## Contexto e definição do problema

A ADR-004 decidiu reconstruir produção no n8n Cloud e fixou, como primeiro critério de
validação, que o `scripts/deploy_workflow.py` publicasse e ativasse o workflow sem
intervenção manual. Ao executar a decisão, apareceu o impedimento: **a conta em período de
teste do n8n Cloud não libera a API pública.** O acesso começa nos planos pagos, a partir do
Starter, por volta de US$ 20 ao mês.

Sem chave de API não há `deploy_workflow.py`, não há publicação automatizada e o *job*
`deploy-producao` nunca fecha. A ADR-004 falha o seu próprio critério de validação antes de
ser implementada, e por isso é substituída em vez de ajustada.

A ADR-004 já havia nomeado esta saída: *"Permanece como plano de retorno, agora pela segunda
vez, e uma terceira interrupção do Cloud deve acioná-la em vez de gerar uma ADR-005 com o
mesmo conteúdo desta."* O conteúdo aqui não é o mesmo: a ADR-004 tratava de assinatura que
expirou, esta trata de funcionalidade que o plano não oferece. Mas a conclusão é a prevista.

### A conta que decide

Pagar o Starter não substituiria o Railway: a topologia da ADR-004 mantinha desenvolvimento
no Railway de qualquer modo. A comparação real é **US$ 20 somados ao Railway**, contra o
Railway sozinho, por algo em torno de US$ 5 a 10 ao mês. E o que se compraria não é
recompensado por nenhum dos três critérios da Etapa 2: segurança e LGPD, observabilidade e
otimização medida. Na observabilidade o Cloud é inferior, porque não expõe CPU, memória e
rede por serviço, que é justamente onde o enunciado manda procurar as métricas do
*deployment*.

### A permissão

A hospedagem no Railway é autorizada pelo cliente, na linha 46 do `BRIEFING.md`:
*"Hospedagem em Render, Railway, Fly.io ou n8n Cloud."* A exigência da disciplina é de
ambientes e *secrets* separados, não de plataformas distintas.

## Opções consideradas

* **A. Railway nos dois ambientes**, com uma instância por ambiente
* **B. Plano Starter do n8n Cloud** para produção, Railway para desenvolvimento
* **C. Railway em produção**, `docker-compose.yml` em desenvolvimento

## Decisão

Escolhida a opção **A**: produção e desenvolvimento em instâncias Railway distintas.

A instância Railway atual é **promovida a produção**, e uma instância nova é criada para
desenvolvimento. A ordem importa: produção é o ambiente avaliado, e deve ficar com a
instância já comprovada, não com a recém-criada. O que já se verificou nela, em 19/10/2026:
a chave de API funciona, o workflow foi publicado e ativado pelo script, o webhook recusa
chamada anônima com 403 e os *smoke tests* 1 e 2 passam contra a URL pública.

### Consequências positivas

* **A paridade entre ambientes é restaurada**, e esta é a consequência mais relevante, porque corrige o que a ADR-003 registrou como a sua pior: dois ambientes na mesma plataforma, com a mesma imagem fixada, deixam de divergir por versão ou configuração do n8n.
* Um único painel para operar, o que elimina o custo de atenção que a ADR-003 havia aceitado e a chance de configurar no ambiente errado.
* O painel do Railway expõe CPU, memória, rede e disco por serviço, o que dá base concreta para as cinco métricas da Etapa 2 sem instrumentação adicional.
* O `deploy_workflow.py` volta a ser o caminho único de publicação nos dois ambientes, sem tratamento especial.

### Consequências negativas

* **A operação volta a ser nossa.** A ADR-003 contabilizara como ganho a produção gerenciada, com disponibilidade e *backup* por conta do fornecedor. Isso se perde: atualização de versão, cópia de segurança e recuperação passam a ser trabalho da equipe.
* **O Railway também é assinatura, e também vence.** Trocar de fornecedor não elimina o modo de falha que derrubou a produção em outubro; apenas o move. A tabela de prazos em `rotacao-credenciais.md` continua sendo a mitigação, agora com duas linhas.
* Uma segunda instância custa, ainda que pouco. O orçamento de US$ 120 absorve, mas deixa de ser gratuito.
* Produção herda uma instância que nasceu como desenvolvimento, de modo que o nome do serviço e o histórico carregam essa origem. É ruído cosmético, e preferi aceitá-lo a entregar o ambiente avaliado a uma instância não testada.
* A promoção exige remanejar *secrets* entre os dois *GitHub Environments*, e secret trocado de lugar é oportunidade de erro.

### Mitigações adotadas

Fixar a **mesma imagem** nas duas instâncias, hoje `n8nio/n8n:2.28.7`, e tratar atualização
como mudança deliberada, nunca automática. É o que torna a paridade real em vez de nominal.

Registrar o **prazo das duas assinaturas** na tabela de prazos, pelo motivo que a ADR-004 já
havia estabelecido: assinatura vence em silêncio e derruba o sistema sem erro de aplicação.

Manter o `.github/workflows/retencao.yml` **fora da plataforma**. Ele já roda no GitHub
Actions, e agora isso vale ainda mais, porque as duas instâncias passam a ter o mesmo
fornecedor e, portanto, um ponto único de falha.

## Alternativas descartadas e o porquê

**B. Plano Starter do n8n Cloud.** Resolveria o impedimento da API e devolveria produção
gerenciada. Descartada pela relação entre custo e retorno: seria gasto recorrente somado ao
Railway, para destravar uma capacidade que a instância Railway já possui e comprovou, sem
melhorar nenhum critério de avaliação. Volta a ser defensável se o JurisFlow passar a operar
com tráfego real depois da disciplina, quando disponibilidade gerenciada deixa de ser
conforto e vira requisito.

**C. Docker local como desenvolvimento.** É a opção de custo zero e foi descartada pelo mesmo
defeito que já eliminou a opção D da ADR-003 e a opção C da ADR-004: instância em `localhost`
não é alcançável pelo GitHub Actions, de modo que o *job* `deploy-desenvolvimento` perderia
alvo. Perder metade da entrega contínua para economizar uma instância não compensa.

## Validação

A decisão se confirma quando:

1. As duas instâncias rodarem a mesma versão do n8n, com a imagem fixada.
2. O `deploy_workflow.py` publicar e ativar os dois workflows em cada ambiente, sem
   intervenção manual.
3. Os três *smoke tests* passarem contra as duas URLs, incluindo o `smoke_03`, que ainda não
   passou em lugar nenhum.
4. O *pipeline* fechar verde em um *push* na `main`.

Se a paridade prometida não se sustentar na prática, ou se o custo das duas instâncias
pressionar o orçamento de LLM, esta ADR deve ser revista em favor de uma instância única com
separação por *tag* de workflow, solução inferior que até aqui não foi necessária.
