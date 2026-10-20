-- =============================================================================
-- JurisFlow · Purga diária por prazo de retenção
--
-- Executa a política descrita em docs/lgpd/politica-retencao-exclusao.md.
-- Cada bloco apaga o que venceu e grava a contagem em jurisflow_purga_log, de
-- modo que a execução deixa rastro mesmo quando não havia nada a remover.
--
-- Chamado diariamente pelo workflow workflows/jurisflow-retencao.json.
-- Roda igual na mão:
--   psql "$DATABASE_URL" -f db/retencao/purga_diaria.sql
--
-- Escrito para PostgreSQL 14+ e para o esquema do n8n 2.28.x.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Execuções com erro do n8n (PC-02 e PC-08) · prazo 72 horas
--
-- É o único lugar onde o payload cru, com nome e CPF sem máscara, fica em
-- repouso. O n8n já faz pruning nativo por EXECUTIONS_DATA_MAX_AGE; esta purga
-- é a segunda barreira, para o caso de a variável de ambiente ser perdida em
-- uma recriação de container. Quando o pruning nativo está funcionando, o
-- resultado esperado aqui é zero linha removida, e é esse zero que prova que a
-- primeira barreira está de pé.
--
-- execution_data e execution_metadata têm chave estrangeira com ON DELETE
-- CASCADE para execution_entity, de modo que apagar o pai leva os filhos.
-- -----------------------------------------------------------------------------
WITH removidas AS (
    DELETE FROM execution_entity
     WHERE "startedAt" < now() - INTERVAL '72 hours'
    RETURNING 1
)
INSERT INTO jurisflow_purga_log (alvo, prazo, linhas_removidas, origem_execucao, observacao)
SELECT 'execution_entity',
       '72 horas',
       count(*),
       'agendada',
       'segunda barreira do pruning nativo do n8n'
  FROM removidas;

-- -----------------------------------------------------------------------------
-- 2. Trilha de auditoria (PC-07) · prazo 12 meses
--
-- O registro é pseudonimizado, e por isso o prazo é mais longo: ele sustenta a
-- série histórica de latência, custo e volume, e o registro do art. 37. Doze
-- meses cobrem a comparação ano a ano sem acumular indefinidamente.
-- -----------------------------------------------------------------------------
WITH removidas AS (
    DELETE FROM jurisflow_trilha_auditoria
     WHERE recebido_em < now() - INTERVAL '12 months'
    RETURNING 1
)
INSERT INTO jurisflow_purga_log (alvo, prazo, linhas_removidas, origem_execucao)
SELECT 'jurisflow_trilha_auditoria',
       '12 meses',
       count(*),
       'agendada'
  FROM removidas;

-- -----------------------------------------------------------------------------
-- 2b. Spans do trace (migração 002) · prazo 12 meses
--
-- Mesmo prazo e mesma razão da trilha: o span é pseudonimizado, correlacionado
-- pelo protocolo, e sustenta a série histórica de latência por etapa. Vai em
-- bloco próprio para que a contagem apareça separada no registro de purga; um
-- número agregado esconderia qual das duas tabelas parou de ser limpa.
-- -----------------------------------------------------------------------------
WITH removidas AS (
    DELETE FROM jurisflow_trace_span
     WHERE inicio < now() - INTERVAL '12 months'
    RETURNING 1
)
INSERT INTO jurisflow_purga_log (alvo, prazo, linhas_removidas, origem_execucao)
SELECT 'jurisflow_trace_span',
       '12 meses',
       count(*),
       'agendada'
  FROM removidas;

-- -----------------------------------------------------------------------------
-- 3. Relatório da execução, devolvido ao workflow
-- -----------------------------------------------------------------------------
SELECT alvo,
       prazo,
       linhas_removidas,
       executado_em
  FROM jurisflow_purga_log
 WHERE executado_em >= now() - INTERVAL '5 minutes'
 ORDER BY id;
