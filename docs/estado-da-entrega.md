# Estado da entrega – Etapa 1

**Atualizado em:** 21/09/2026
**Ambiente de produção:** n8n Cloud, instância `contatestes-01`
**URL pública:** https://contatestes-01.app.n8n.cloud/webhook/intake

Este documento registra o que está efetivamente funcionando e o que ainda não está. Ele
existe porque prometer no papel o que não foi verificado na prática é o defeito que a
auditoria do protótipo apontou logo na abertura, e repeti-lo aqui seria incoerente.

## O que está verificado

**A instância responde e a rota existe.** Uma chamada POST para `/webhook/intake` retorna
403, e não 404, o que prova que o workflow está publicado e servindo aquele caminho.

**A autenticação do webhook está ativa.** Chamada sem credencial é recusada, com a mensagem
"Authorization data is wrong!". É exatamente o comportamento que o segundo smoke test exige,
ou seja, recusa com 401 ou 403.

**O repositório está limpo.** O `gitleaks` roda no *pipeline* a cada *push*, contra o
histórico completo, e passou em todas as execuções até aqui.

**O job de qualidade do CI/CD passa.** Validação estrutural do workflow, varredura de
segredos e os dez testes de roteamento com LLM simulado fecham em verde.

## O que ainda não está verificado

**O caminho completo nunca executou de ponta a ponta.** O contador de execuções de produção
na instância marca zero.

**A versão publicada diverge da versão versionada.** O JSON deste repositório define
autenticação por Header Auth, ao passo que a versão publicada no n8n ainda responde com
Basic Auth. A correção existe como rascunho no editor e não foi publicada, de modo que o
endereço de produção continua servindo a versão anterior.

**Os três smoke tests não foram executados contra a URL pública.** O código está em
`tests/smoke/` e a documentação em `docs/smoke-tests.md`, embora nenhum tenha rodado contra
o ambiente real.

**Os jobs de deploy do CI/CD falham.** Faltam os *GitHub Environments* `producao` e
`desenvolvimento`, com os respectivos *secrets* e a chave da API do n8n.

**O ambiente de desenvolvimento não existe.** A ADR-003 prevê um container n8n no Railway,
ainda não criado.

**O rollback não foi executado.** O procedimento está em `docs/rollback.md` e a pasta
`docs/evidencias/` segue vazia de capturas.

## O que destrava o resto

Um único clique: publicar, no editor do n8n, a alteração de Basic Auth para Header Auth. A
partir daí o intake passa a responder, os smoke tests podem rodar, e o *pipeline* fecha em
verde assim que os *Environments* forem configurados.

## Registro de um aprendizado

A confusão entre rascunho e versão publicada consumiu boa parte do tempo desta etapa. O
editor exibia a configuração corrigida e o endereço de produção servia outra, sem que nada
na tela indicasse a diferença. É precisamente o problema que a publicação automatizada pelo
*pipeline* elimina, porque lá o workflow versionado em Git é a única fonte da verdade, e o
que está no ar é sempre o que foi publicado pelo último *push*. A lição entrou no
post-mortem como argumento a favor da automação, e não como detalhe de ferramenta.
