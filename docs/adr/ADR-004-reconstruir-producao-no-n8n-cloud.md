# ADR-004: Reconstruir produção no n8n Cloud, em instância nova

* **Status:** aceita
* **Data:** 19/10/2026
* **Decisora:** Edilene Chagas Faria
* **Substitui:** ADR-003
* **Depende de:** ADR-001

## Contexto e definição do problema

Em outubro de 2026 a instância de produção deixou de existir. O endereço
`contatestes-01.app.n8n.cloud` não devolve erro de aplicação: devolve a página
`404 – No instance here` do próprio n8n Cloud, que é o que o fornecedor serve quando não há
instância alguma naquele subdomínio. A assinatura terminou e a instância foi removida.

O que torna isso uma decisão arquitetural, e não um incidente de operação, é a premissa que
caiu junto. A ADR-003 escolheu o n8n Cloud para produção com três fundamentos, e o primeiro
deles era *"a assinatura do Cloud já está ativa, de modo que descartá-la seria desperdício"*.
Aquilo foi tratado como fato duradouro quando era um estado temporário. A ADR registrou com
honestidade as consequências negativas da escolha, e nenhuma delas era esta: a lista previa
perda de paridade, divergência de versão e custo de atenção, mas não previu que o ambiente
avaliado pudesse simplesmente deixar de existir.

Agravante: **a queda foi silenciosa.** Nada no repositório nem no *pipeline* percebeu que
produção havia sumido. Os *smoke tests* existiam desde a Etapa 1 e nunca chegaram a rodar
contra a URL pública, porque os *jobs* de *deploy* já falhavam antes, por outro motivo. Um
sinal que nunca foi ligado não avisa quando a coisa quebra.

Há um ponto que merece registro em sentido contrário, porque confirma uma decisão anterior:
**o workflow sobreviveu à plataforma.** A instância foi embora, e a definição do sistema
continuou íntegra em `workflows/jurisflow-intake.json`. Foi exatamente para isso que a
ADR-001 fixou o Git como fonte da verdade. Reconstruir produção é republicar um arquivo, e
não remontar um sistema de memória.

## Opções consideradas

* **A. Criar nova instância no n8n Cloud**, mantendo o desenvolvimento no Railway
* **B. Promover a instância Railway a produção** e criar uma segunda instância Railway para desenvolvimento
* **C. Promover a instância Railway a produção** e usar o `docker-compose.yml` como desenvolvimento

## Decisão

Escolhida a opção **A**: produção em instância nova do n8n Cloud, desenvolvimento no
container n8n do Railway.

A topologia é a mesma da ADR-003, mas o fundamento é outro, e é por isso que esta ADR a
substitui em vez de apenas complementá-la. Não se escolhe mais o Cloud porque a assinatura já
existe; escolhe-se porque a conta disponível é a do Cloud e porque produção gerenciada,
com disponibilidade e *backup* por conta do fornecedor, continua valendo mais do que
auto-hospedagem para o ambiente que será avaliado.

A escolha vem acompanhada de uma condição que a ADR-003 não tinha: **a assinatura precisa ter
prazo conhecido e registrado.** Produção sobre período gratuito é produção com data de
validade, e a decisão só se sustenta se essa data for tratada como item de operação.

### Consequências positivas

* O desenho validado na Etapa 1 é preservado, de modo que o `deploy_workflow.py`, os *smoke tests* e os dois *GitHub Environments* continuam valendo sem alteração estrutural.
* A reconstrução é barata em esforço: publicar o JSON versionado, recriar três credenciais e reemitir a chave de API.
* Permanece a separação real de segredos entre ambientes, já que cada instância tem credencial de webhook, chave do provedor de LLM e chave de API próprias.

### Consequências negativas

* **Repete-se a dependência que já custou a produção uma vez.** É a consequência mais séria, e aceitá-la sem dizer isso seria repetir o erro da ADR-003. A diferença é que agora ela está nomeada e tem mitigação.
* **Nada é restaurado.** O n8n Cloud não devolve instância removida. Credenciais, histórico de execuções e identificadores são novos, e o endereço público muda, o que obriga a atualizar o README, a variável `N8N_PUBLIC_URL` do ambiente `producao` e a documentação que cita a URL antiga.
* A paridade entre ambientes continua perdida, pelas mesmas razões que a ADR-003 já havia registrado, e a divergência de versão tende a aumentar, porque a imagem do Railway está fixada em `n8nio/n8n:2.28.7` e a do Cloud não.
* Todo o histórico de execuções de produção é zero outra vez, de modo que a linha de base para a otimização medida da Etapa 2 terá de ser levantada do zero.

### Mitigações adotadas

**Registrar o prazo da assinatura** no `docs/rotacao-credenciais.md`, junto das credenciais,
porque é informação da mesma natureza: algo que vence e que, vencendo em silêncio, derruba o
sistema.

**Ligar o sinal que não existia.** Os três *smoke tests* passam a rodar contra a URL pública
a cada publicação, e o `smoke_01` verifica justamente que a instância responde. Uma instância
removida falha nesse teste, em vez de ser descoberta um mês depois.

**Manter fora da plataforma o que não pode cair com ela.** O `.github/workflows/retencao.yml`
já executa a política de retenção a partir do GitHub Actions, de propósito: foi escrito
depois desta queda e por causa dela.

## Alternativas descartadas e o porquê

**B. Railway para os dois ambientes.** É a opção tecnicamente superior, e a ADR-003 já a
apontava como plano de retorno. Entrega paridade real, mantém os dois alvos alcançáveis pelo
*pipeline* e elimina a operação de dois painéis. Foi descartada por uma razão de
circunstância, e não de mérito: a conta em uso é a do n8n Cloud. Permanece como plano de
retorno, agora pela segunda vez, e uma terceira interrupção do Cloud deve acioná-la em vez de
gerar uma ADR-005 com o mesmo conteúdo desta.

**C. Railway em produção e Docker local em desenvolvimento.** É a opção de custo zero. Tem o
mesmo defeito que já inviabilizou a opção D da ADR-003: instância em `localhost` não é
alcançável pelo GitHub Actions, de modo que o *job* `deploy-desenvolvimento` perderia alvo e
passaria a rodar só validação. Perder metade da entrega contínua para economizar uma
instância não compensa numa etapa cujo critério central é o sistema estar no ar e observável.

## Validação

A decisão se confirma quando, contra a nova URL pública:

1. O `deploy_workflow.py` publicar e ativar o workflow sem intervenção manual.
2. Os três *smoke tests* passarem, incluindo o `smoke_03`, que nunca passou em produção.
3. O *pipeline* fechar verde em um *push* na `main`.

Se a nova instância também expirar antes do fim da disciplina, esta ADR é revogada e a opção
B passa a valer sem nova discussão.
