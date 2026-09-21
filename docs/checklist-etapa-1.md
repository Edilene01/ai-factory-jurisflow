# Checklist da Etapa 1

Entrega na semana 6, em repositório público no perfil pessoal do GitHub. A coluna de status
separa o que já está escrito do que depende de execução em ambiente real, porque a rubrica
distingue as duas coisas com clareza.

> Estado detalhado e honesto da entrega: [`estado-da-entrega.md`](estado-da-entrega.md).

## Primeiro item: arquitetura e decisões documentadas (25%)

| Exigência | Onde | Status |
|---|---|---|
| Auditoria do protótipo | `docs/auditoria-prototipo.md` | Pronto |
| Matriz de decisão de stack, com pesos definidos antes das notas | `docs/matriz-decisao-stack.md` | Pronto |
| ADR-001 em formato MADR, com alternativas e consequências honestas | `docs/adr/ADR-001-manter-n8n-como-orquestrador.md` | Pronto |
| ADR-002 em formato MADR, sobre decisão técnica concreta | `docs/adr/ADR-002-hospedagem-railway-ambientes-separados.md` | Pronto |
| Diagrama C4 nível 1 | `docs/architecture/c4-nivel1-contexto.md` | Pronto |
| Diagrama C4 nível 2 | `docs/architecture/c4-nivel2-containers.md` | Pronto |

## Segundo item: sistema publicado e automatizado (50%)

| Exigência | Onde | Status |
|---|---|---|
| Repositório público no perfil pessoal | github.com/Edilene01/ai-factory-jurisflow | **Feito** |
| URL pública funcional, independente da sua máquina | n8n Cloud, `contatestes-01` | **Parcial**: a rota responde e recusa chamada anônima, porém o caminho completo ainda não executou |
| Três smoke tests documentados e funcionando | `tests/smoke/` e `docs/smoke-tests.md` | Código pronto, **não executados** contra a URL pública |
| Pipeline de CI/CD disparado por push na branch principal | `.github/workflows/ci-cd.yml` | **Parcial**: dispara e o job de qualidade passa; os jobs de deploy falham por falta de Environments |
| Ambientes de dev e prod separados, com secrets distintos | GitHub Environments e Railway | **Não iniciado** |
| Workflow low-code versionado em Git | `workflows/jurisflow-intake.json` | Versionado, **com divergência conhecida**: a versão publicada ainda usa Basic Auth |
| README v1 com problema, solução, como rodar, arquitetura e URL | `README.md` | **Feito**, com a URL pública registrada |
| `.env.example` e `.gitignore` | Raiz | Pronto |
| Tag SemVer, CHANGELOG e GitHub Release publicado | `CHANGELOG.md` e GitHub | **Feito** na v1.0.0 |
| Rollback testado, com evidência de execução | `docs/rollback.md` e `docs/evidencias/` | Procedimento pronto, **sem evidência de execução** |
| Post-mortem de uma página, sem apontar culpados | `docs/post-mortem-INC-001.md` | Pronto |

## Terceiro item: demonstração funcional

| Exigência | Onde | Status |
|---|---|---|
| Vídeo de 3 a 5 minutos, com a sua voz | Roteiro em `docs/roteiro-video.md` | Depende de você |
| URL pública abrindo no vídeo | | Depende de você |
| Pipeline disparando um deploy no vídeo | | Depende de você |
| Observações sobre acertos, erros e aprendizados | | Depende de você |

## Critérios de anulação, conferir antes de entregar

| Risco | Verificação |
|---|---|
| Chave de API real no histórico do Git | `gitleaks detect --source . --verbose` |
| Repositório privado ou inacessível | Abrir a URL do repositório em janela anônima |
| Troca de projeto depois da semana 2 sem autorização | JurisFlow escolhido e mantido |
| Histórico fabricado | Commits reais, com conventional commits |
| Cópia integral | Todo o conteúdo escrito a partir da auditoria do próprio repositório |

## Ordem sugerida de execução

1. Rotacionar credenciais e publicar o repositório limpo.
2. Subir as duas instâncias e configurar os ambientes.
3. Importar o workflow, validar no n8n e reexportar por cima do arquivo versionado.
4. Configurar os secrets e rodar o primeiro deploy automatizado.
5. Rodar os smoke tests contra a URL pública e guardar a evidência.
6. Executar o rollback de verdade e capturar a tela.
7. Preencher a URL no README, criar a tag e publicar a release.
8. Gravar o vídeo por último, quando tudo estiver estável.
