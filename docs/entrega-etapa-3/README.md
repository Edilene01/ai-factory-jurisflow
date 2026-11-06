# Entrega da Etapa 3

Os artefatos finais e onde cada um é cobrado.

---

## O que entregar, e onde cada peso está

| Artefato | Peso | Arquivo | Estado |
|---|---|---|---|
| Vídeo de pitch, 4:30 a 5:30, YouTube não listado | parte dos 50% | Roteiro em [`roteiro-pitch.md`](roteiro-pitch.md) | **Você grava** |
| One-pager executivo, uma página | parte dos 50% | [`one-pager-executivo.md`](one-pager-executivo.md) | Pronto |
| URL da aplicação no ar | 20% | https://ai-factory-jurisflow-production.up.railway.app | No ar desde 06/11 |
| Demo gravada de backup | parte dos 20% | Sem arquivo, é gravação | **Você grava** |
| Análise crítica, Partes A e B | parte dos 30% | [`analise-critica.md`](analise-critica.md) | Pronto |
| Análise crítica, **Parte C** | parte dos 30% | Mesmo arquivo, bloco final | **Só você, sem IA** |
| README v1.0 com troubleshooting | parte dos 30% | [`../../README.md`](../../README.md) | Pronto |

## A ordem que eu sugiro

1. **Escrever a Parte C.** É a única peça que trava tudo, porque o documento de análise não fecha sem ela. Material de apoio em [`parte-c-material-para-voce-escrever.md`](parte-c-material-para-voce-escrever.md).
2. **Gravar a demo de backup**, que é curta e serve de ensaio para o pitch.
3. **Gravar o pitch**, com o roteiro cronometrado.
4. **Publicar no YouTube** como não listado, com o título exato.
5. **Conferir a aplicação** uma última vez antes de submeter.

## Converter para PDF, se a submissão exigir

O enunciado fala em documento de 1 a 2 páginas, e o Markdown daqui converte direto:

```bash
pandoc docs/entrega-etapa-3/analise-critica.md -o analise-critica.pdf
pandoc docs/entrega-etapa-3/one-pager-executivo.md -o one-pager.pdf
```

Confira a paginação depois de converter. O one-pager tem **451 palavras e três tabelas**,
que cabem em uma página A4 com margens padrão. Se ainda assim estourar por causa da fonte,
reduza para 10pt:

```bash
pandoc docs/entrega-etapa-3/one-pager-executivo.md -o one-pager.pdf -V fontsize=10pt -V geometry:margin=2cm
```

Se precisar cortar, o candidato é o parágrafo da otimização: os 21,2% já aparecem no vídeo e
na análise crítica.

## Antes de submeter

| Conferência | Como |
|---|---|
| Aplicação respondendo | `curl https://ai-factory-jurisflow-production.up.railway.app/healthz` deve dar `n8n_configurado: true` |
| Nenhum segredo no repositório | `gitleaks detect --source . --verbose` |
| Arquivos `.txt` com chave fora da árvore do projeto | Eles estão na pasta acima e aparecem em captura de tela |
| Título do vídeo exato | `[AI Factory] Pitch - JurisFlow - Edilene Chagas Faria` |
| Duração entre 4:30 e 5:30 | Conferir no YouTube depois de publicar |
| Legendas verificadas | O YouTube gera automático e erra nomes próprios; revise "JurisFlow" e "Edilene" |

## Links que o avaliador vai usar

| O quê | Endereço |
|---|---|
| Aplicação, formulário | https://ai-factory-jurisflow-production.up.railway.app/ |
| Aplicação, painel | https://ai-factory-jurisflow-production.up.railway.app/painel |
| Repositório | https://github.com/Edilene01/ai-factory-jurisflow |
| Evidência da publicação e janela de uptime | [`../evidencias/2026-11-06-aplicacao-publicada.md`](../evidencias/2026-11-06-aplicacao-publicada.md) |

Não há login, e portanto não há credencial de teste a fornecer. Para exercitar o sistema, use
o CPF `111.444.777-35` e as descrições de [`../exemplos-intakes.md`](../exemplos-intakes.md).
