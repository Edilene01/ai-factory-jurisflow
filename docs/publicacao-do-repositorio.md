# Publicação do repositório, do zero até a release

Roteiro executável, na ordem em que precisa ser feito. A primeira parte não é opcional:
chave de API real no histórico anula a etapa inteira, e *fork* do repositório do professor
traz o histórico contaminado junto.

## Passo 1 – Rotacionar antes de qualquer coisa

O protótipo veio com a chave da OpenAI e o segredo do webhook dentro do JSON. Mesmo sendo
valores fictícios no material didático, o procedimento é o mesmo do mundo real, e é ele que
será avaliado. Siga [`rotacao-credenciais.md`](rotacao-credenciais.md), gere credenciais
próprias e registre a troca no histórico daquele documento.

```bash
openssl rand -hex 32   # novo JURISFLOW_WEBHOOK_SECRET
```

## Passo 2 – Repositório novo, histórico limpo

Não faça *fork*, e não clone o repositório de origem para publicar por cima. Comece do zero
a partir desta pasta.

```bash
cd ai-factory-jurisflow

git init -b main
git add .
git commit -m "feat: adota o protótipo JurisFlow e publica a versão 1.0.0

Rotaciona credenciais, remove segredos do workflow, adiciona tratamento de erro,
desvio de revisão manual, CI/CD, smoke tests e documentação de decisões."
```

Repare que o histórico nasce com um único commit e nenhuma credencial, de modo que não existe
nada anterior para vazar.

## Passo 3 – Varredura antes de tornar público

```bash
# instale o gitleaks (https://github.com/gitleaks/gitleaks/releases)
gitleaks detect --source . --verbose

python tests/validate_workflow.py
python -m pytest tests/test_routing.py -v
```

Só avance com os três limpos. Se o `gitleaks` acusar qualquer coisa, corrija e recomece o
commit inicial, porque emendar depois deixa rastro.

## Passo 4 – Criar o repositório e enviar

Crie no GitHub um repositório **público**, no seu perfil pessoal, com o nome
`ai-factory-jurisflow`, sem README, sem `.gitignore` e sem licença, já que tudo isso já existe
aqui.

```bash
git remote add origin https://github.com/<seu-usuario>/ai-factory-jurisflow.git
git push -u origin main

git checkout -b develop
git push -u origin develop
```

## Passo 5 – Configurar os dois ambientes

Em **Settings > Environments**, crie `producao` e `desenvolvimento`. Cada um recebe o seu
próprio conjunto, e nenhum valor se repete entre eles.

*Secrets* de cada ambiente: `N8N_API_KEY`, `JURISFLOW_WEBHOOK_SECRET`.
*Variables* de cada ambiente: `N8N_PUBLIC_URL`.

As credenciais da OpenAI e do Slack não entram aqui, porque vivem nas credenciais do
n8n de cada instância. O que o GitHub precisa é apenas do suficiente para publicar e testar.

## Passo 6 – Publicar a infraestrutura

No Railway, crie dois projetos, um por ambiente, cada um com o serviço n8n a partir da imagem
`n8nio/n8n:2.28.7` e um Postgres. Variáveis mínimas por serviço:

```
N8N_HOST=<dominio-publico>
N8N_PROTOCOL=https
WEBHOOK_URL=https://<dominio-publico>/
N8N_PUBLIC_API_DISABLED=false
GENERIC_TIMEZONE=America/Sao_Paulo
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=72
```

Em cada instância, crie a conta de dono, gere a chave da API em **Settings > API** e cadastre
as três credenciais que o workflow referencia: Header Auth, OpenAI e Slack.

## Passo 7 – Validar o workflow no n8n e reexportar

O JSON deste repositório foi escrito para ser importado, e não testado apenas no papel. Antes
de confiar nele, importe pela interface, confira que todos os nós carregaram sem aviso, rode
uma execução de teste e **exporte de volta** por cima de `workflows/jurisflow-intake.json`.

A fonte da verdade de um workflow n8n é sempre o que o próprio n8n exporta, porque o formato
varia entre versões de nó. Commite a reexportação:

```bash
git add workflows/jurisflow-intake.json
git commit -m "fix: reexporta o workflow validado na instância de desenvolvimento"
```

## Passo 8 – Primeiro deploy automatizado

```bash
git push origin develop   # publica em desenvolvimento
git push origin main      # publica em produção
```

Acompanhe a execução em **Actions** e capture a tela do *pipeline* verde, com o tempo total,
que precisa ficar abaixo de cinco minutos. Guarde em `docs/evidencias/pipeline-verde.png`.

## Passo 9 – Executar o rollback de verdade

Siga [`rollback.md`](rollback.md) e execute o nível 1 em produção, com captura de tela e log.
Rollback descrito e nunca executado não pontua, e a diferença entre a faixa Capaz e a
Autônoma está exatamente aqui.

## Passo 10 – Tag, release e URL no README

```bash
# depois de preencher a URL pública no README
git add README.md
git commit -m "docs: registra a URL pública de produção no README"

git tag -a v1.0.0 -m "v1.0.0 - adoção do protótipo, deploy automatizado e hardening inicial"
git push origin main --tags
```

No GitHub, vá em **Releases > Draft a new release**, escolha a tag `v1.0.0`, use como corpo a
seção correspondente do `CHANGELOG.md` e publique.

## Convenção de commits

Use *conventional commits* do início ao fim, porque o histórico legível é critério da rubrica
e porque facilita escrever o post-mortem depois.

```
feat:     nova funcionalidade
fix:      correção de defeito
docs:     documentação
test:     testes
chore:    infraestrutura, configuração, dependências
refactor: mudança sem alteração de comportamento
```

## Verificação final antes de considerar entregue

```bash
git log --oneline                       # histórico legível, sem commit genérico
gitleaks detect --source . --verbose    # nenhum segredo
python tests/validate_workflow.py       # estrutura e antivazamento
python -m pytest tests/ -v              # testes de roteamento
```

E, por último, abra a URL pública em uma janela anônima ou no celular, fora da sua rede. É o
teste que a rubrica descreve como "abre sem depender da máquina do estudante".
