# Evidências de execução

Esta pasta guarda a prova de que os procedimentos descritos na documentação foram
efetivamente executados, e não apenas escritos. A rubrica da Etapa 1 é explícita quanto a
isso: *rollback* descrito sem evidência não conta.

## O que precisa estar aqui

| Arquivo | Conteúdo | Status |
|---|---|---|
| `rollback-01-deploy-anterior.png` | Captura da plataforma mostrando o deploy anterior restaurado, com data e hora visíveis | `<pendente>` |
| `rollback-02-deploy-workflow.txt` | Saída do `scripts/deploy_workflow.py` durante a reversão, com a versão publicada | `<pendente>` |
| `rollback-03-smoke-tests.png` | Os três smoke tests passando depois da reversão | `<pendente>` |
| `pipeline-verde.png` | Execução do GitHub Actions concluída, com o tempo total abaixo de cinco minutos | `<pendente>` |
| `url-publica.png` | A URL pública respondendo, de preferência a partir de outro dispositivo | `<pendente>` |

## Como capturar

Deixe data e hora visíveis na captura, seja pelo relógio do sistema, seja pelo carimbo da
própria plataforma. Para o log, redirecione a saída direto para o arquivo:

```bash
N8N_PUBLIC_URL=... N8N_API_KEY=... python scripts/deploy_workflow.py \
  | tee docs/evidencias/rollback-02-deploy-workflow.txt
```

Antes de commitar qualquer captura, confira que nenhuma chave, token ou dado de pessoa real
aparece na imagem. Captura de tela é o caminho mais comum de vazamento acidental.
