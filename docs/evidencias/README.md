# Evidências de execução

Esta pasta guarda a prova de que os procedimentos descritos na documentação foram
efetivamente executados, e não apenas escritos. A rubrica da Etapa 1 é explícita quanto a
isso: *rollback* descrito sem evidência não conta.

## O que precisa estar aqui

| Arquivo | Conteúdo | Status |
|---|---|---|
| [`2026-10-29-rollback.md`](2026-10-29-rollback.md) | O rollback executado em produção nos dois sentidos, com os seis passos, os protocolos e o que a execução mudou no procedimento | **Pronto** |
| [`rollback-02-deploy-workflow.txt`](rollback-02-deploy-workflow.txt) | Saída bruta do `deploy_workflow.py` e dos *smoke tests* na ida e na volta, com as versões publicadas | **Pronto** |
| `pipeline-verde.png` | Execução do GitHub Actions concluída, com o tempo total abaixo de cinco minutos | `<pendente>` |
| `url-publica.png` | A URL pública respondendo, de preferência a partir de outro dispositivo | `<pendente>` |
| [`2026-10-20-smoke-e-classificacao.md`](2026-10-20-smoke-e-classificacao.md) | Os três smoke tests passando e o roteamento nas cinco áreas, com protocolos e latências | **Pronto** |

## Como capturar

Deixe data e hora visíveis na captura, seja pelo relógio do sistema, seja pelo carimbo da
própria plataforma. Para o log, redirecione a saída direto para o arquivo:

```bash
N8N_PUBLIC_URL=... N8N_API_KEY=... python scripts/deploy_workflow.py \
  | tee docs/evidencias/rollback-02-deploy-workflow.txt
```

Antes de commitar qualquer captura, confira que nenhuma chave, token ou dado de pessoa real
aparece na imagem. Captura de tela é o caminho mais comum de vazamento acidental.
