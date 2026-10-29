# Rollback

Voltar atrás precisa ser rotina conhecida, não improviso sob pressão. Este documento descreve
os três níveis de reversão, do mais rápido ao mais completo, e onde fica a evidência de que o
procedimento foi de fato executado.

## Quando reverter

Quando qualquer uma destas condições aparecer depois de uma publicação: smoke test falhando
contra a URL pública, casos parando de chegar aos canais, latência acima do SLA de 60 segundos
de forma sustentada, ou erro de classificação em série.

A regra é reverter primeiro e investigar depois. Diagnóstico com o sistema quebrado custa
caro, e a análise de causa cabe no post-mortem.

## Nível 1 – Reverter o workflow para a versão anterior

O mais rápido, e o que resolve a maioria dos casos, porque quase toda mudança está no JSON.

O alvo é **a versão boa imediatamente anterior**, que se descobre no histórico do próprio
arquivo:

```bash
git log --oneline --follow -- workflows/jurisflow-intake.json

git checkout <sha-da-versão-anterior> -- workflows/jurisflow-intake.json

N8N_PUBLIC_URL=https://... N8N_API_KEY=... python scripts/deploy_workflow.py

N8N_PUBLIC_URL=https://... JURISFLOW_WEBHOOK_SECRET=... bash tests/smoke/run_all.sh
```

> ⚠️ **Não reverta para a `v1.0.0`.** O workflow daquela tag usa o nó
> `n8n-nodes-base.openAi` em `typeVersion 1`, que no n8n 2.40.5 resolve para a raiz da API e
> devolve a mensagem de boas-vindas em vez da classificação. Foi o defeito corrigido em
> `4deffc5`. Reverter para lá durante um incidente troca um problema por outro, no pior
> momento. O limite seguro para trás é `4deffc5`.

Tempo esperado: menos de dois minutos. O `deploy_workflow.py` atualiza o workflow existente e
o reativa, de modo que não há duplicação na instância. Ele também relê os ids das credenciais
da versão publicada e os recoloca antes do `PUT`, o que é o que impede a reversão de
desvincular os dez nós e deixar o workflow sem ativar.

## Nível 2 – Reverter o commit e deixar o pipeline republicar

Quando a mudança passou de um arquivo, ou quando a branch precisa voltar a um estado coerente.

```bash
git revert <sha-do-commit-problematico>
git push origin main
```

O *push* dispara o *pipeline*, que valida, publica e roda os smoke tests. Prefira `revert` a
`reset`, porque o histórico continua contando o que aconteceu, e é exatamente isso que o
post-mortem vai precisar.

## Nível 3 – Reverter o deploy da plataforma

Quando o problema não está no workflow, e sim na instância: imagem nova com defeito, variável
de ambiente errada, container reiniciando em laço.

No painel do Railway, abra o serviço, vá em **Deployments**, localize o último *deploy* que
estava saudável e use **Redeploy**. A instância volta ao estado anterior, com as variáveis
daquele momento.

## Evidência de execução

O procedimento foi executado em produção em **29/10/2026**, nos dois sentidos: reversão para
a versão anterior, comprovação, e volta à versão atual. A rubrica aceita *print ou log*, e o
que esta execução produziu é log.

| Item | Arquivo |
|---|---|
| Relato da execução, com os seis passos e o que se aprendeu | [`evidencias/2026-10-29-rollback.md`](evidencias/2026-10-29-rollback.md) |
| Saída bruta dos quatro comandos, íntegra | [`evidencias/rollback-02-deploy-workflow.txt`](evidencias/rollback-02-deploy-workflow.txt) |

Resumo: reverteu para `v1.2.2`, os três *smoke tests* passaram com o protocolo
`JF-20261029-HQQTUS`, voltou para `v1.3.0`, e os três passaram de novo com
`JF-20261029-8E1TM8`. Nos dois sentidos, os dez vínculos de credencial foram preservados.

## Checklist do pós-reversão

1. Os três smoke tests passam contra a URL pública.
2. Um intake de teste, com dado fictício, chega ao canal correto.
3. A versão publicada confere com a esperada, verificável na saída do `deploy_workflow.py`.
4. O incidente foi registrado, e o post-mortem agendado para as 48 horas seguintes.
