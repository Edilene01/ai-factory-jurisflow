# Roteiro do vídeo de demonstração

Entre 3 e 5 minutos. Falar é obrigatório, e a câmera ligada é desejável. O roteiro abaixo
cabe em 4 minutos com folga, e a sugestão é gravar em uma tomada só, aceitando pequenos
tropeços, porque vídeo excessivamente polido soa decorado.

## Antes de gravar

Deixe abertas quatro abas, na ordem em que serão usadas: a URL pública do n8n, o terminal com
o repositório, a página de Actions do GitHub e o Slack com os canais de triagem. Feche tudo o
que possa exibir credencial, e-mail pessoal ou dado de terceiro.

## 0:00 a 0:30 – Quem fala e sobre o quê

Apresente-se, diga que herdou o JurisFlow, uma triagem de intake jurídico em n8n, e resuma o
problema em uma frase: 2.500 formulários por dia, triagem manual de três a seis horas, casos
urgentes envelhecendo na fila.

Diga também, já de saída, qual era o estado do que você recebeu: chave de API dentro do
código, CPF sem máscara indo para o Slack e nada rodando fora do notebook de quem saiu.

## 0:30 a 1:30 – A URL pública respondendo

Mostre a URL abrindo. Se possível, faça isso do celular ou de uma janela anônima, dizendo em
voz alta que não depende da sua máquina.

Envie um intake pelo terminal, com o `curl` de dado fictício, e mostre a resposta com o
protocolo e a área. Em seguida vá ao Slack e mostre o caso chegando no canal certo, com o
nome e o CPF mascarados.

Vale fazer o segundo envio com uma descrição propositalmente ambígua, para mostrar o caso
caindo em `#juris-triagem-manual` com o motivo explícito. É a diferença mais visível em
relação ao protótipo, que empurrava isso para o Cível sem avisar ninguém.

## 1:30 a 2:30 – O pipeline disparando

Faça uma alteração pequena e verdadeira, por exemplo um ajuste de texto no README, commite
com *conventional commit* e dê o *push* em `main`.

Vá para a aba Actions e acompanhe: varredura de segredos, validação do workflow, testes,
publicação e smoke tests. Mostre o tempo total. Enquanto roda, explique que produção e
desenvolvimento são ambientes distintos, com *secrets* separados, e que o workflow é
publicado por API a partir do JSON versionado, sem ninguém importar arquivo na mão.

## 2:30 a 3:15 – O rollback

Mostre a evidência do *rollback* executado, ou execute o nível 1 ao vivo se o tempo permitir.
Diga com todas as letras que foi executado, não apenas descrito, e mostre os smoke tests
passando depois da reversão.

## 3:15 a 4:00 – O que deu certo, o que deu errado, o que aprendi

Esta parte não é enfeite, é onde o professor enxerga a sua individualidade. Sugestões do que
dizer, adaptando ao que de fato aconteceu:

* **O que deu certo:** auditar antes de mexer deu a ordem de prioridade pronta, e a maior parte das decisões seguintes já veio justificada.
* **O que deu errado:** vale contar um tropeço real, do tipo formato de nó que mudou entre versões do n8n, ou *secret* configurado no ambiente errado. Erro admitido soa mais confiável do que percurso perfeito.
* **O que aprendi:** a lição do INC-001, a de que falha silenciosa custa mais caro que falha ruidosa, e que tratar saída de modelo de linguagem como contrato é apostar contra a própria natureza da ferramenta.

## Cuidados

Nenhuma credencial na tela, em nenhum momento, nem por meio segundo. Nenhum dado de pessoa
real, apenas os casos sintéticos do repositório. E não leia o roteiro em voz alta: use como
lembrete de ordem, falando com as suas palavras.
