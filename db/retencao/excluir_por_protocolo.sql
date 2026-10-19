-- =============================================================================
-- JurisFlow · Exclusão a pedido do titular (art. 18, IV e VI, da LGPD)
--
-- Diferente da purga por prazo: aqui há uma pessoa pedindo, um prazo de
-- resposta a cumprir (art. 19) e a necessidade de provar depois que a exclusão
-- aconteceu. Por isso o registro em jurisflow_purga_log marca a origem como
-- 'requisicao_titular' e guarda o protocolo na observação.
--
-- Uso:
--   psql "$DATABASE_URL" -v protocolo="'JF-20261019-A1B2C3'" \
--        -f db/retencao/excluir_por_protocolo.sql
--
-- ATENÇÃO: este script cobre apenas o que vive no banco. A exclusão completa
-- tem três passos, descritos em docs/lgpd/politica-retencao-exclusao.md, seção
-- "Exclusão a pedido do titular". Rodar só este arquivo deixa a mensagem do
-- Slack no lugar, e a exclusão fica pela metade.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. O que será removido, para conferência antes do commit
-- -----------------------------------------------------------------------------
SELECT protocolo,
       recebido_em,
       area,
       urgencia,
       origem
  FROM jurisflow_trilha_auditoria
 WHERE protocolo = :protocolo;

-- -----------------------------------------------------------------------------
-- 2. Remoção da trilha de auditoria
--
-- O art. 16 ressalva as hipóteses em que a guarda permanece autorizada após o
-- término do tratamento. Nenhuma delas se aplica à trilha: ela não cumpre
-- obrigação legal de guarda, não é estudo de órgão de pesquisa e não foi
-- transferida a terceiro. Logo, a exclusão é devida sem ressalva.
-- -----------------------------------------------------------------------------
WITH removidas AS (
    DELETE FROM jurisflow_trilha_auditoria
     WHERE protocolo = :protocolo
    RETURNING 1
)
INSERT INTO jurisflow_purga_log (alvo, prazo, linhas_removidas, origem_execucao, observacao)
SELECT 'jurisflow_trilha_auditoria',
       'art. 18, VI',
       count(*),
       'requisicao_titular',
       'protocolo ' || :protocolo
  FROM removidas;

-- -----------------------------------------------------------------------------
-- 3. Execuções com erro que ainda guardem o payload daquele intake
--
-- A janela de 72 horas normalmente já resolveu isso sozinha. A varredura existe
-- porque uma requisição de titular pode chegar dentro da janela, e nesse caso o
-- payload cru ainda está lá.
-- -----------------------------------------------------------------------------
WITH removidas AS (
    DELETE FROM execution_entity ee
     USING execution_data ed
     WHERE ed."executionId" = ee.id
       AND ed.data LIKE '%' || trim(both '''' from :protocolo) || '%'
    RETURNING 1
)
INSERT INTO jurisflow_purga_log (alvo, prazo, linhas_removidas, origem_execucao, observacao)
SELECT 'execution_entity',
       'art. 18, VI',
       count(*),
       'requisicao_titular',
       'protocolo ' || :protocolo
  FROM removidas;

COMMIT;

-- -----------------------------------------------------------------------------
-- 4. Comprovante para o titular e para o controlador
-- -----------------------------------------------------------------------------
SELECT alvo,
       linhas_removidas,
       executado_em,
       observacao
  FROM jurisflow_purga_log
 WHERE origem_execucao = 'requisicao_titular'
   AND observacao = 'protocolo ' || :protocolo
 ORDER BY id;
