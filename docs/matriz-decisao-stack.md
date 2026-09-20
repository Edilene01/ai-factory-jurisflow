# Matriz de decisão de stack – JurisFlow

**Data:** 18/09/2026
**Autora:** Edilene Chagas Faria
**Etapa:** 1
**Entrada:** `docs/auditoria-prototipo.md` e `BRIEFING.md`
**Saída:** `docs/adr/ADR-001-manter-n8n-como-orquestrador.md`

---

## 1. Como esta matriz foi construída

Os pesos foram fixados antes de qualquer opção ser pontuada, e o registro dessa ordem é
proposital. Se os critérios são escolhidos depois que já se sabe o resultado desejado,
a matriz deixa de ser instrumento de decisão e vira justificativa retroativa.

Os pesos saíram das restrições reais do projeto, todas verificáveis no BRIEFING.md:
teto de US$ 120 por mês, meta de 60 segundos no percentil 95, sigilo profissional sobre
a descrição do caso e a instrução expressa da disciplina de evoluir o protótipo em vez
de reescrevê-lo.

## 2. Critérios e pesos, definidos antes da avaliação

| # | Critério | Peso | Por que pesa isso |
|---|---|---|---|
| C1 | Aderência à regra de evoluir o protótipo herdado | 20 | Reescrever do zero é vedado pelo enunciado, e a dívida técnica foi plantada para ser enfrentada |
| C2 | Custo total mensal dentro de US$ 120 | 20 | Restrição contratual dura do BRIEFING.md, com 2.500 intakes por dia |
| C3 | Controle sobre dado sensível e conformidade com a LGPD | 20 | A descrição do caso é coberta por sigilo profissional e há transferência internacional no uso do LLM |
| C4 | Capacidade de automatizar deploy e versionar em Git | 15 | Metade da nota da Etapa 1 depende de CI/CD e de workflow versionado |
| C5 | Observabilidade e operação | 10 | Hoje ninguém percebe se o sistema cai de madrugada, e a Etapa 2 cobra métricas |
| C6 | Curva de aprendizado até a semana 6 | 10 | Prazo curto e projeto individual |
| C7 | Portabilidade e risco de aprisionamento | 5 | Importa, embora nenhuma decisão desta etapa seja irreversível |
| | **Total** | **100** | |

Escala de notas: 1 para inadequado, 2 para fraco, 3 para aceitável, 4 para bom e 5 para
ótimo. A pontuação de cada opção é a soma de peso multiplicado por nota, com teto de 500.

## 3. Opções avaliadas

**A. n8n auto-hospedado em PaaS.** Manter o motor atual e publicá-lo em Railway, Render
ou Fly.io, com imagem Docker fixada e banco gerenciado.

**B. n8n Cloud.** Mesmo motor, operado pelo fornecedor, com assinatura mensal.

**C. Make.com.** Migrar o cenário para outra plataforma de automação visual.

**D. Reescrita em Python com FastAPI.** Abandonar o low-code e transformar o fluxo em
serviço próprio.

## 4. Pontuação

| Critério | Peso | A. n8n em PaaS | B. n8n Cloud | C. Make.com | D. FastAPI |
|---|---|---|---|---|---|
| C1 Evoluir o protótipo | 20 | 5 | 5 | 2 | 1 |
| C2 Custo dentro do teto | 20 | 4 | 3 | 3 | 4 |
| C3 Controle do dado e LGPD | 20 | 4 | 2 | 2 | 5 |
| C4 Deploy automatizado e Git | 15 | 5 | 3 | 2 | 5 |
| C5 Observabilidade | 10 | 4 | 5 | 4 | 4 |
| C6 Curva até a semana 6 | 10 | 3 | 5 | 3 | 2 |
| C7 Portabilidade | 5 | 5 | 4 | 2 | 5 |
| **Pontuação** | **100** | **430** | **365** | **250** | **360** |
| **Aproveitamento** | | **86%** | **73%** | **50%** | **72%** |

## 5. Leitura dos números

A opção A vence por margem confortável, e o que decide são os critérios de maior peso.

Em C1 as opções A e B empatam no topo, porque ambas preservam o workflow herdado, ao
passo que Make.com e FastAPI exigiriam reconstruir a lógica em outro paradigma, o que o
enunciado veda.

Em C3, que é onde o projeto jurídico se distingue de qualquer outro caso da lista, a
auto-hospedagem permite escolher a região do dado, desligar a persistência de execução e
manter a trilha de auditoria em banco próprio. O n8n Cloud entrega o oposto: comodidade
operacional em troca de menos controle sobre onde o dado repousa, justamente o ponto que a
Dra. Heloísa levantou segundo as notas do engenheiro anterior.

Em C4 a diferença é prática. Publicar o workflow por API, a partir de um JSON versionado,
funciona bem em instância própria, enquanto em plataformas gerenciadas a importação tende
a depender da interface, o que empurraria o *deploy* de volta para o clique manual.

A opção D merece registro honesto: ela ganha em C3 e empata em C4, e seria a escolha certa
se o projeto nascesse hoje. Perde porque contraria a regra do exercício e porque reconstruir
classificação, roteamento e entrega até a semana 6 consumiria o tempo que deveria ir para
*hardening*, testes e documentação.

## 6. Decisão

Adotada a opção A, com o desdobramento de plataforma tratado em ADR-002. O registro formal,
com alternativas e consequências, está em `docs/adr/ADR-001-manter-n8n-como-orquestrador.md`.

## 7. O que faria eu mudar de ideia

Três gatilhos derrubariam esta escolha, e vale deixá-los escritos: custo de infraestrutura
passando de US$ 40 por mês só com hospedagem, indisponibilidade recorrente que a operação
própria não consiga resolver, ou exigência jurídica de manter o dado em território nacional,
hipótese em que a discussão volta para provedor brasileiro e possivelmente para a opção D.
