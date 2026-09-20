# Exemplos de intakes — JurisFlow

Coletânea sintética (fictícia, sem cliente real) para testar o classificador e o roteamento.
Use no `curl` do `teste-manual.md` trocando o campo `descricao_caso`.
Os mesmos exemplos alimentam o teste de roteamento com LLM mockado (`tests/test_routing.py`).

## Trabalhista → `#juris-trabalhista`
1. "Fui demitida sem justa causa e não recebi as verbas rescisórias nem o FGTS." (urgência: média)
2. "Trabalho há 2 anos sem registro em carteira e o patrão não paga hora extra." (urgência: média)
3. "Sofri assédio moral da minha chefe e tenho áudios. Quero entrar com ação." (urgência: média)

## Cível → `#juris-civel`
4. "Quero dar entrada no divórcio e tem partilha de um apartamento e guarda de filho." (urgência: baixa)
5. "Meu vizinho construiu um muro que invadiu meu terreno, já tentei conversar e nada." (urgência: baixa)
6. "Preciso abrir inventário do meu pai que faleceu, são três herdeiros." (urgência: baixa)

## Tributário → `#juris-tributario`
7. "Recebi uma execução fiscal de ICMS da minha empresa e o prazo de defesa vence em 5 dias." (urgência: alta)
8. "A Receita caiu na malha fina e quero contestar uma multa de imposto de renda." (urgência: média)

## Criminal → `#juris-criminal`
9. "Meu irmão foi preso em flagrante ontem e a audiência de custódia é amanhã de manhã." (urgência: alta)
10. "Recebi uma intimação para depor como investigado em um inquérito por estelionato." (urgência: alta)

## Consumidor → `#juris-consumidor`
11. "Comprei uma geladeira com defeito e a loja se recusa a trocar ou devolver o dinheiro." (urgência: baixa)
12. "O plano de saúde negou minha cirurgia que o médico disse ser urgente." (urgência: alta)

## Ambíguos (bons pra estressar o classificador)
13. "Fui mandado embora e a empresa ainda negativou meu nome por uma dívida que eu nem reconheço."
    → Trabalhista (rescisão) **+** Consumidor (negativação indevida)? O modelo costuma escolher Trabalhista.
14. "Meu sócio sumiu com o dinheiro da empresa, acho que é crime, mas também quero desfazer a sociedade."
    → Criminal (apropriação) **+** Cível (dissolução societária)? Tende a Criminal.
15. "Comprei um carro financiado, o banco cobrou tarifas que acho ilegais e ainda me mandaram pro Serasa."
    → Consumidor (tarifas/banco) **+** Cível (revisão de contrato)? Tende a Consumidor.
