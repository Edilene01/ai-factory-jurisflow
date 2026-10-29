# Roteiro do vídeo da Etapa 2

Entre 3 e 5 minutos. Falar é obrigatório, câmera ligada é desejável. O roteiro abaixo cabe em
4 minutos, e a sugestão continua a mesma do [roteiro da Etapa 1](roteiro-video.md): uma tomada
só, aceitando pequenos tropeços. Vídeo polido demais soa decorado.

O enunciado pede quatro coisas, e as quatro estão aqui: **o alerta e o que o dispara**, **a
sanitização de PII antes da chamada ao LLM**, **a otimização com antes e depois**, e **as suas
observações sobre o processo**.

## Antes de gravar

**Mova os arquivos de segredo.** Na pasta acima do repositório há `.txt` com chave da OpenAI,
token do Slack, chave de API do n8n e as chaves de cifragem. Eles não estão versionados, mas
aparecem em qualquer captura da pasta. Tire da árvore do projeto antes de abrir a tela.

Deixe quatro abas prontas, na ordem de uso:

1. O editor do n8n em produção, com o workflow de intake aberto.
2. `docs/evidencias/2026-10-20-alerta-a10.md`, no GitHub ou no editor.
3. `docs/otimizacoes/001-compressao-do-system-prompt.md`.
4. O Slack, no canal `#juris-ops`.

Feche e-mail, notificações e qualquer janela com dado de terceiro.

## 0:00 a 0:25 – Quem fala, e o que mudou

Apresente-se e diga em uma frase o que é o JurisFlow: triagem de intake jurídico em n8n, 2.500
formulários por dia.

Depois, a frase que organiza o vídeo inteiro: na Etapa 1 o sistema foi para o ar, e nesta
etapa ele precisou virar produto. Segurança de credencial, conformidade com a LGPD,
observabilidade e uma otimização que dá para provar com número.

## 0:25 a 1:10 – A sanitização, antes da chamada ao LLM

Abra o nó **`Sanitizar Entrada`** no editor. Mostre o código e explique o que ele faz, nesta
ordem:

* Gera o **protocolo**, no formato `JF-AAAAMMDD-XXXXXX`, que vira o pseudônimo do caso.
* Prepara **duas versões do mesmo intake**. Este é o ponto, e vale dizer devagar: uma versão com o dado para o Slack, mascarado, e outra para o provedor de LLM, sem dado nenhum que identifique.
* Mascara **nome** e **CPF**.
* Varre a descrição do caso e troca por marcador: `[CPF]`, `[CNPJ]`, `[EMAIL]`, `[TELEFONE]`.

Diga por que isso importa neste projeto, e não em abstrato: **a descrição do caso é coberta
por sigilo profissional**, e o protótipo herdado mandava nome e CPF sem máscara direto para o
Slack. Era a dívida que você recebeu, e está no `docs/auditoria-prototipo.md`.

Se der, dispare um intake de teste e mostre a diferença entre o que chega ao Slack e o que foi
enviado ao provedor. Se não der, o código basta.

## 1:10 a 2:00 – O alerta, e o que o faz disparar

Abra a evidência do **A-10**. Explique a mecânica em três passos:

1. A política de retenção manda apagar a trilha de auditoria depois de **12 meses**.
2. A purga roda em duas vias: às 03:15 dentro do n8n, e às 04:15 no GitHub Actions, **fora da plataforma**.
3. O alerta dispara quando a segunda via **remove alguma coisa**, porque isso significa que a primeira não rodou.

Agora a parte boa, e insista nela: **zero removido é o resultado desejado.** O alerta não
observa erro, observa silêncio quebrado.

Mostre as duas execuções da evidência. Na primeira, duas linhas com `recebido_em` de treze e
catorze meses atrás foram semeadas, a purga as encontrou e o alerta saiu em `#juris-ops`, P2.
Na segunda, imediatamente depois, não havia nada vencido e **o alerta calou**.

Diga que o gatilho não foi fabricado para a demonstração: é a condição real que o alerta
monitora, sobre dado sintético.

Se quiser um detalhe que mostra trabalho de verdade, conte o defeito que a evidência registra:
o consolidador lia a saída do último bloco de SQL, que era o dos *spans* com zero removidos,
e por isso as duas linhas da trilha eram invisíveis para ele. A purga funcionava e o alerta
não saía. Corrigido lendo o `jurisflow_purga_log`, que é a fonte de verdade.

## 2:00 a 2:50 – A otimização, com antes e depois

Abra `docs/otimizacoes/001`. Conte a descoberta primeiro, porque ela é o argumento:

**90% dos tokens de entrada eram o prompt fixo**, reenviado a cada requisição. Eram 328 tokens
por intake, dos quais a descrição do caso respondia por cerca de 30.

Depois a mudança e os números:

* *System prompt* comprimido de **1.172 para 784 caracteres**.
* **21,2% a menos de custo por intake.**
* **12,3% a menos no p95** de latência.
* Acerto de área e taxa de erro **inalterados**.

Diga como foi medido: linha de base de **200 intakes** antes de mexer, duas corridas
consecutivas com a mesma semente, saída bruta guardada em `docs/evidencias/`.

E diga o que a medição **não** prova, que é onde a honestidade aparece: corpus sintético não é
demanda real, e qualidade mantida sobre 200 casos construídos não garante qualidade mantida
sobre casos de verdade.

Se sobrar fôlego, mencione a otimização **descartada**: cache de classificação, que sobre
corpus repetido mostraria um ganho falso. Recusar uma métrica boa demais diz mais sobre método
do que entregar outra.

## 2:50 a 3:10 – Opcional: o dashboard

Se o tempo permitir, mostre a seção **Dashboard** do README, com os números medidos sobre 978
intakes: p50 de 1.023 ms, p95 de **1.395 ms** contra um SLA de 60 segundos, 100% dentro do
prazo e 0,20% de erro.

Vale citar uma linha: o custo medido ficou em **metade** do que a estimativa calculava, e os
dois números continuam no repositório com a diferença explicada.

Corte esta parte sem dó se o relógio apertar. Ela não está entre as quatro exigências.

## 3:10 a 4:00 – O que deu certo, o que deu errado, o que aprendi

É aqui que o professor enxerga você, e não o sistema. Fale com as suas palavras.

**O que deu certo.** A definição do sistema vive no Git, e isso foi testado de verdade: a
instância evaporou duas vezes e os três workflows voltaram do repositório nas duas.

**O que deu errado.** Conte o incidente, sem suavizar. Entre **20 e 29 de outubro** a produção
ficou no ar respondendo o *health check* com o banco vazio. Nove dias sem atender ninguém, e a
descoberta veio ao conferir tudo para a entrega. Pior: quando foi apurar a causa, **os logs já
tinham expirado**, porque o plano guarda sete dias e a descoberta veio no nono.

**O que aprendi.** Duas lições, e a segunda é a que importa:

* *Health check* verde não é sistema saudável. O contêiner respondia perfeitamente enquanto não atendia ninguém.
* O alerta que teria pego isso **já estava catalogado**: o A-02, volume abaixo de 20% da média da mesma hora, marcado como P1. Estava escrito e não estava implementado. Alerta no papel não acorda ninguém.

Se quiser fechar com uma frase, essa dá conta: a diferença entre protótipo e produto não é o
que o sistema faz quando funciona, é o que alguém descobre quando ele para.

## Cuidados

Nenhuma credencial na tela, em momento nenhum, nem por meio segundo. Nenhum dado de pessoa
real: use os casos sintéticos do repositório, com o CPF `111.444.777-35`, que é válido pelo
dígito verificador e não é de ninguém.

E não leia este roteiro em voz alta. Use como lembrete de ordem.
