-- =============================================================================
-- JurisFlow · Migração completa, em um arquivo
--
-- Concatena 001 (trilha e registro de purga), 002 (observabilidade) e as views
-- de métricas, nesta ordem. Existe para colar de uma vez no console de query do
-- Postgres no Railway, quando não há psql à mão.
--
-- Tudo é idempotente: rodar de novo não causa dano.
--
-- Equivalente, com psql:
--   psql "$DATABASE_URL" -f db/schema/001_trilha_auditoria.sql
--   psql "$DATABASE_URL" -f db/schema/002_observabilidade.sql
--   psql "$DATABASE_URL" -f db/metricas/vw_metricas.sql
--
-- GERADO a partir dos três arquivos acima. Não edite aqui: edite a origem.
-- =============================================================================

-- =============================================================================
-- JurisFlow · Trilha de auditoria e registro de purga
-- Migração 001 · Etapa 2
--
-- Cria as duas tabelas que sustentam a política de retenção:
--
--   jurisflow_trilha_auditoria : o registro pseudonimizado do PC-07 do mapa de
--                                dados pessoais. Nenhuma coluna aceita nome, CPF
--                                ou trecho do relato. O que existe do texto é a
--                                contagem de caracteres.
--   jurisflow_purga_log        : a prova de que a purga rodou. Sem ela, a política
--                                de retenção seria afirmação sem evidência.
--
-- Aplicar com:
--   psql "$DATABASE_URL" -f db/schema/001_trilha_auditoria.sql
--
-- Idempotente: pode rodar novamente sem efeito colateral.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Trilha de auditoria (PC-07) · base legal art. 7º, IX · retenção 12 meses
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jurisflow_trilha_auditoria (
    id                    BIGSERIAL    PRIMARY KEY,
    protocolo             TEXT         NOT NULL UNIQUE,
    recebido_em           TIMESTAMPTZ  NOT NULL,
    latencia_ms           INTEGER,
    area                  TEXT,
    urgencia              TEXT,
    revisao_manual        BOOLEAN      NOT NULL DEFAULT FALSE,
    motivo_revisao        TEXT,
    origem                TEXT,
    caracteres_descricao  INTEGER,
    registrado_em         TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT ck_urgencia_valida
        CHECK (urgencia IS NULL OR urgencia IN ('alta', 'media', 'baixa')),
    CONSTRAINT ck_protocolo_formato
        CHECK (protocolo ~ '^JF-[0-9]{8}-[A-Z0-9]{6}$')
);

COMMENT ON TABLE jurisflow_trilha_auditoria IS
    'PC-07 do mapa de dados pessoais. Registro pseudonimizado para observabilidade e para o registro das operações de tratamento do art. 37 da LGPD. Retenção: 12 meses.';
COMMENT ON COLUMN jurisflow_trilha_auditoria.protocolo IS
    'Pseudônimo do caso. É a única chave de ligação com o titular, e ela não vive aqui: a correspondência entre protocolo e pessoa está no canal do Slack do escritório.';
COMMENT ON COLUMN jurisflow_trilha_auditoria.caracteres_descricao IS
    'Comprimento do relato. Existe para medir o custo da chamada ao LLM sem guardar o texto.';

-- A purga varre por recebido_em. Sem índice, ela faz varredura completa todo dia.
CREATE INDEX IF NOT EXISTS ix_trilha_recebido_em
    ON jurisflow_trilha_auditoria (recebido_em);

-- O dashboard da Etapa 2 agrupa por área e por dia.
CREATE INDEX IF NOT EXISTS ix_trilha_area_recebido_em
    ON jurisflow_trilha_auditoria (area, recebido_em DESC);

-- -----------------------------------------------------------------------------
-- Registro das execuções de purga · a evidência da política
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jurisflow_purga_log (
    id                BIGSERIAL    PRIMARY KEY,
    executado_em      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    alvo              TEXT         NOT NULL,
    prazo             TEXT         NOT NULL,
    linhas_removidas  INTEGER      NOT NULL,
    origem_execucao   TEXT         NOT NULL DEFAULT 'agendada',
    observacao        TEXT,

    CONSTRAINT ck_origem_execucao
        CHECK (origem_execucao IN ('agendada', 'manual', 'requisicao_titular'))
);

COMMENT ON TABLE jurisflow_purga_log IS
    'Prova de execução da política de retenção. Guarda apenas contagens e o alvo; nunca o conteúdo removido. Não é purgado, porque é o registro de prestação de contas.';

CREATE INDEX IF NOT EXISTS ix_purga_executado_em
    ON jurisflow_purga_log (executado_em DESC);

COMMIT;

-- -----------------------------------------------------------------------------
-- Verificação pós-aplicação
-- -----------------------------------------------------------------------------
-- SELECT table_name FROM information_schema.tables
--  WHERE table_name IN ('jurisflow_trilha_auditoria', 'jurisflow_purga_log');
-- =============================================================================
-- JurisFlow · Observabilidade
-- Migração 002 · Etapa 2, Bloco 2
--
-- Acrescenta à trilha de auditoria o que falta para medir custo e o SLA real,
-- e cria a tabela de spans. O trace id é o próprio protocolo: ele já é único
-- por intake, já atravessa o fluxo e já é pseudônimo, de modo que nenhum
-- identificador novo é introduzido e o mapa de dados pessoais continua válido
-- como está.
--
-- Aplicar depois de 001:
--   psql "$DATABASE_URL" -f db/schema/002_observabilidade.sql
--
-- Idempotente.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. Colunas que faltavam na trilha
-- -----------------------------------------------------------------------------

-- latencia_ms mede da chegada até o parse. O SLA do briefing é até a entrega no
-- Slack, de modo que a métrica atual subestima o que o contrato mede. As duas
-- passam a conviver: duracao_total_ms fecha o SLA, duracao_resposta_ms é o que
-- o cliente espera no formulário.
ALTER TABLE jurisflow_trilha_auditoria
    ADD COLUMN IF NOT EXISTS duracao_total_ms     INTEGER,
    ADD COLUMN IF NOT EXISTS duracao_resposta_ms  INTEGER,
    ADD COLUMN IF NOT EXISTS tokens_entrada       INTEGER,
    ADD COLUMN IF NOT EXISTS tokens_saida         INTEGER,
    ADD COLUMN IF NOT EXISTS modelo               TEXT,
    ADD COLUMN IF NOT EXISTS status               TEXT,
    ADD COLUMN IF NOT EXISTS causa_falha          TEXT;

COMMENT ON COLUMN jurisflow_trilha_auditoria.duracao_total_ms IS
    'Chegada do POST até a entrega no Slack. É o SLA de 60 s (P95) do briefing.';
COMMENT ON COLUMN jurisflow_trilha_auditoria.duracao_resposta_ms IS
    'Chegada do POST até a resposta ao formulário. É o que o cliente espera na tela.';
COMMENT ON COLUMN jurisflow_trilha_auditoria.tokens_entrada IS
    'prompt_tokens devolvido pelo provedor. Sem ele o custo é cálculo, não medição.';
COMMENT ON COLUMN jurisflow_trilha_auditoria.causa_falha IS
    'provedor | slack | validacao | parse | timeout. Agregar erro sem causa esconde o dono do problema.';

ALTER TABLE jurisflow_trilha_auditoria
    DROP CONSTRAINT IF EXISTS ck_status_valido;
ALTER TABLE jurisflow_trilha_auditoria
    ADD CONSTRAINT ck_status_valido
        CHECK (status IS NULL OR status IN ('sucesso', 'erro', 'revisao_manual'));

ALTER TABLE jurisflow_trilha_auditoria
    DROP CONSTRAINT IF EXISTS ck_causa_falha_valida;
ALTER TABLE jurisflow_trilha_auditoria
    ADD CONSTRAINT ck_causa_falha_valida
        CHECK (causa_falha IS NULL
               OR causa_falha IN ('provedor', 'slack', 'validacao', 'parse', 'timeout'));

-- -----------------------------------------------------------------------------
-- 2. Spans
--
-- Sete etapas por intake, correlacionadas pelo protocolo. O esquema é fechado
-- por coluna de propósito: não há campo de texto livre que aceite trecho do
-- relato. A disciplina é a mesma do nó de auditoria, que monta o objeto campo
-- a campo, e é o que mantém a pseudonimização verificável em vez de prometida.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jurisflow_trace_span (
    id           BIGSERIAL    PRIMARY KEY,
    protocolo    TEXT         NOT NULL,
    span         TEXT         NOT NULL,
    inicio       TIMESTAMPTZ  NOT NULL,
    fim          TIMESTAMPTZ  NOT NULL,
    duracao_ms   INTEGER      NOT NULL,
    status       TEXT         NOT NULL DEFAULT 'ok',
    tentativas   SMALLINT     NOT NULL DEFAULT 1,
    detalhe      TEXT,

    CONSTRAINT ck_span_conhecido
        CHECK (span IN ('recepcao', 'sanitizacao', 'classificacao_llm', 'parse',
                        'resposta', 'roteamento', 'entrega_slack')),
    CONSTRAINT ck_span_status
        CHECK (status IN ('ok', 'erro', 'pulado')),
    CONSTRAINT ck_span_protocolo
        CHECK (protocolo ~ '^JF-[0-9]{8}-[A-Z0-9]{6}$'),
    -- detalhe existe para mensagem de erro do provedor, e não para conteúdo do
    -- caso. O teto curto é a salvaguarda contra o relato vazar para cá.
    CONSTRAINT ck_span_detalhe_curto
        CHECK (detalhe IS NULL OR length(detalhe) <= 200),

    CONSTRAINT uq_span_por_protocolo UNIQUE (protocolo, span)
);

COMMENT ON TABLE jurisflow_trace_span IS
    'Spans do fluxo de intake. Trace id = protocolo. Retenção: 12 meses, igual à trilha.';

CREATE INDEX IF NOT EXISTS ix_span_protocolo  ON jurisflow_trace_span (protocolo);
CREATE INDEX IF NOT EXISTS ix_span_inicio     ON jurisflow_trace_span (inicio);
CREATE INDEX IF NOT EXISTS ix_span_lento      ON jurisflow_trace_span (span, duracao_ms DESC);

COMMIT;

-- -----------------------------------------------------------------------------
-- Retenção: a purga de 12 meses já alcança esta tabela. Bloco 2b de
-- db/retencao/purga_diaria.sql, e nó "Purgar Trilha e Spans (12m)" do
-- workflows/jurisflow-retencao.json. Tabela nova sem mecanismo de purga
-- contradiria a política de retenção, e por isso as duas coisas entram juntas.
-- -----------------------------------------------------------------------------
-- =============================================================================
-- JurisFlow · Views das cinco métricas
--
-- Uma fonte só para o relatório e para o dashboard. A rubrica da Etapa 2 exige
-- que os números do dashboard batam com os do relatório, e a forma de garantir
-- isso não é conferir duas fontes: é não ter duas.
--
-- Thresholds justificados em docs/observabilidade/metricas-e-thresholds.md.
-- Alertas que consomem estas views em docs/observabilidade/alertas.md.
--
-- Aplicar depois de 001 e 002:
--   psql "$DATABASE_URL" -f db/metricas/vw_metricas.sql
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- Preço do modelo em um lugar só. Mudou o preço ou o modelo, muda aqui, e as
-- views de custo acompanham sem reescrita.
-- Valores de 19/10/2026, em dólares por 1M de tokens.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS jurisflow_preco_modelo (
    modelo         TEXT PRIMARY KEY,
    usd_por_1m_in  NUMERIC(10, 4) NOT NULL,
    usd_por_1m_out NUMERIC(10, 4) NOT NULL,
    vigente_desde  DATE NOT NULL DEFAULT CURRENT_DATE
);

INSERT INTO jurisflow_preco_modelo (modelo, usd_por_1m_in, usd_por_1m_out, vigente_desde)
VALUES ('gpt-4o-mini', 0.15, 0.60, DATE '2026-10-19')
ON CONFLICT (modelo) DO NOTHING;

-- =============================================================================
-- MÉTRICA 1 · Latência (p50, p95, p99)
-- SLA do briefing: p95 <= 60 s até a entrega no Slack.
-- =============================================================================
CREATE OR REPLACE VIEW vw_latencia_hora AS
SELECT date_trunc('hour', recebido_em)                                        AS hora,
       count(*)                                                               AS intakes,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY duracao_total_ms)         AS p50_ms,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY duracao_total_ms)         AS p95_ms,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY duracao_total_ms)         AS p99_ms,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY duracao_resposta_ms)      AS p95_resposta_ms,
       -- O SLA é contratado em 95% dos intakes abaixo de 60 s. Medir a fração
       -- que cumpre é mais fiel ao contrato do que só olhar o percentil.
       round(100.0 * count(*) FILTER (WHERE duracao_total_ms <= 60000)
                   / nullif(count(*), 0), 2)                                  AS pct_dentro_sla
  FROM jurisflow_trilha_auditoria
 WHERE duracao_total_ms IS NOT NULL
 GROUP BY 1
 ORDER BY 1 DESC;

COMMENT ON VIEW vw_latencia_hora IS
    'Métrica 1. Alerta A-06 dispara quando p95_ms > 60000 em 1 h.';

-- Latência por etapa: responde "onde" o tempo foi gasto, e não só "quanto".
CREATE OR REPLACE VIEW vw_latencia_por_span AS
SELECT span,
       date_trunc('hour', inicio)                                     AS hora,
       count(*)                                                       AS execucoes,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY duracao_ms)       AS p50_ms,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY duracao_ms)       AS p95_ms,
       max(duracao_ms)                                                AS max_ms,
       count(*) FILTER (WHERE status = 'erro')                        AS erros,
       sum(tentativas - 1)                                            AS retentativas
  FROM jurisflow_trace_span
 GROUP BY 1, 2
 ORDER BY 2 DESC, 1;

-- =============================================================================
-- MÉTRICA 2 · Custo
-- =============================================================================
CREATE OR REPLACE VIEW vw_custo_dia AS
SELECT date_trunc('day', t.recebido_em)::date                         AS dia,
       count(*)                                                       AS intakes,
       sum(t.tokens_entrada)                                          AS tokens_entrada,
       sum(t.tokens_saida)                                            AS tokens_saida,
       round(sum(t.tokens_entrada * p.usd_por_1m_in / 1000000.0
               + t.tokens_saida   * p.usd_por_1m_out / 1000000.0), 4) AS usd_dia,
       round(avg(t.tokens_entrada * p.usd_por_1m_in / 1000000.0
               + t.tokens_saida   * p.usd_por_1m_out / 1000000.0), 8) AS usd_por_intake
  FROM jurisflow_trilha_auditoria t
  JOIN jurisflow_preco_modelo p ON p.modelo = t.modelo
 WHERE t.tokens_entrada IS NOT NULL
 GROUP BY 1
 ORDER BY 1 DESC;

COMMENT ON VIEW vw_custo_dia IS
    'Métrica 2. Linha de base calculada: ~US$ 0,000103 por intake, ~US$ 7,70/mês a 2.500/dia.';

-- Anomalia de custo: compara o dia com a mediana dos 7 anteriores (alerta A-08)
-- e projeta o mês sobre os últimos 7 dias (alerta A-09).
-- percentile_cont é agregado de conjunto ordenado, e o PostgreSQL não aceita
-- OVER() nessa família: a janela precisa vir de um LATERAL, que recalcula a
-- mediana dos 7 dias anteriores para cada linha.
CREATE OR REPLACE VIEW vw_custo_anomalia AS
SELECT c.dia,
       c.usd_dia,
       round(m.mediana_7d, 4)                                         AS mediana_7d,
       round(c.usd_dia / nullif(m.mediana_7d, 0), 2)                  AS razao,
       (c.usd_dia > 2 * m.mediana_7d)                                 AS dispara_a08,
       round(c.usd_dia * 30, 2)                                       AS projecao_mensal_usd,
       (c.usd_dia * 30 > 30)                                          AS dispara_a09
  FROM vw_custo_dia c
  LEFT JOIN LATERAL (
      -- O cast para numeric e obrigatorio: percentile_cont devolve double
      -- precision, e round(double precision, int) nao existe no PostgreSQL.
      SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY a.usd_dia)::numeric AS mediana_7d
        FROM vw_custo_dia a
       WHERE a.dia <  c.dia
         AND a.dia >= c.dia - 7
  ) m ON TRUE
 ORDER BY c.dia DESC;

-- =============================================================================
-- MÉTRICA 3 · Taxa de erro
-- Agregar sem separar por causa esconde o dono do problema.
-- =============================================================================
CREATE OR REPLACE VIEW vw_erro_hora AS
SELECT date_trunc('hour', recebido_em)                                AS hora,
       count(*)                                                       AS total,
       count(*) FILTER (WHERE status = 'erro')                        AS erros,
       round(100.0 * count(*) FILTER (WHERE status = 'erro')
                   / nullif(count(*), 0), 2)                          AS pct_erro,
       count(*) FILTER (WHERE causa_falha = 'provedor')               AS falha_provedor,
       count(*) FILTER (WHERE causa_falha = 'slack')                  AS falha_slack,
       count(*) FILTER (WHERE causa_falha = 'validacao')              AS falha_validacao,
       count(*) FILTER (WHERE causa_falha = 'parse')                  AS falha_parse,
       count(*) FILTER (WHERE causa_falha = 'timeout')                AS falha_timeout
  FROM jurisflow_trilha_auditoria
 GROUP BY 1
 ORDER BY 1 DESC;

COMMENT ON VIEW vw_erro_hora IS
    'Métrica 3. A-05 em pct_erro > 1 em 1 h; A-04 em > 5 na janela de 15 min.';

-- =============================================================================
-- MÉTRICA 4 · Volume
-- A métrica que pega falha silenciosa: sem erro, sem log, só ausência.
-- =============================================================================
CREATE OR REPLACE VIEW vw_volume_hora AS
WITH por_hora AS (
    SELECT date_trunc('hour', recebido_em)       AS hora,
           extract(hour  FROM recebido_em)::int  AS hora_do_dia,
           extract(isodow FROM recebido_em)::int AS dia_semana,
           count(*)                              AS intakes
      FROM jurisflow_trilha_auditoria
     GROUP BY 1, 2, 3
),
historico AS (
    -- Média da MESMA hora do dia, nos 7 dias anteriores: comparar 3h da manhã
    -- com a média geral acusaria queda todo dia de madrugada.
    SELECT p.hora, p.hora_do_dia, p.dia_semana, p.intakes,
           avg(h.intakes) AS media_mesma_hora_7d
      FROM por_hora p
      LEFT JOIN por_hora h
             ON h.hora_do_dia = p.hora_do_dia
            AND h.hora <  p.hora
            AND h.hora >= p.hora - INTERVAL '7 days'
     GROUP BY 1, 2, 3, 4
)
SELECT hora,
       hora_do_dia,
       dia_semana,
       intakes,
       round(media_mesma_hora_7d, 1)                                  AS media_mesma_hora_7d,
       round(100.0 * intakes / nullif(media_mesma_hora_7d, 0), 1)     AS pct_da_media,
       -- Horário comercial: segunda a sexta, 8h às 19h.
       (dia_semana BETWEEN 1 AND 5 AND hora_do_dia BETWEEN 8 AND 19)  AS horario_comercial,
       (dia_semana BETWEEN 1 AND 5 AND hora_do_dia BETWEEN 8 AND 19
        AND media_mesma_hora_7d IS NOT NULL
        AND intakes < 0.20 * media_mesma_hora_7d)                     AS dispara_a02,
       (media_mesma_hora_7d IS NOT NULL
        AND intakes > 3 * media_mesma_hora_7d)                        AS dispara_a13
  FROM historico
 ORDER BY hora DESC;

COMMENT ON VIEW vw_volume_hora IS
    'Métrica 4. A-02 (P1) em volume abaixo de 20% da média da mesma hora. A-13 (P3) acima de 3x.';

-- =============================================================================
-- MÉTRICA 5 · Qualidade
-- =============================================================================
CREATE OR REPLACE VIEW vw_qualidade_dia AS
SELECT date_trunc('day', recebido_em)::date                           AS dia,
       count(*)                                                       AS total,
       count(*) FILTER (WHERE revisao_manual)                         AS revisao_manual,
       round(100.0 * count(*) FILTER (WHERE revisao_manual)
                   / nullif(count(*), 0), 2)                          AS pct_revisao_manual,
       -- Caso difícil e provedor devolvendo lixo são problemas de donos
       -- diferentes, e por isso têm tolerâncias diferentes.
       count(*) FILTER (WHERE motivo_revisao LIKE 'area nao reconhecida%')    AS area_nao_reconhecida,
       count(*) FILTER (WHERE motivo_revisao LIKE 'falha ao interpretar%')    AS resposta_malformada,
       round(100.0 * count(*) FILTER (WHERE motivo_revisao LIKE 'falha ao interpretar%')
                   / nullif(count(*), 0), 2)                          AS pct_malformada
  FROM jurisflow_trilha_auditoria
 GROUP BY 1
 ORDER BY 1 DESC;

COMMENT ON VIEW vw_qualidade_dia IS
    'Métrica 5. A-11 em pct_revisao_manual > 15 em 24 h; A-07 em pct_malformada > 2 em 1 h.';

-- Área zerada em 24 h sugere roteamento quebrado, não ausência de demanda.
CREATE OR REPLACE VIEW vw_distribuicao_area_dia AS
SELECT d.dia, a.area,
       coalesce(count(t.id), 0)                                       AS intakes,
       (coalesce(count(t.id), 0) = 0)                                 AS dispara_a12
  FROM (SELECT DISTINCT date_trunc('day', recebido_em)::date AS dia
          FROM jurisflow_trilha_auditoria) d
 CROSS JOIN (VALUES ('Trabalhista'), ('Cível'), ('Tributário'),
                    ('Criminal'), ('Consumidor')) AS a(area)
  LEFT JOIN jurisflow_trilha_auditoria t
         ON date_trunc('day', t.recebido_em)::date = d.dia
        AND t.area = a.area
 GROUP BY d.dia, a.area
 ORDER BY d.dia DESC, a.area;

-- =============================================================================
-- Painel: uma linha com o estado das cinco métricas nas últimas 24 h.
-- É o que vai para o README e para o vídeo.
-- =============================================================================
CREATE OR REPLACE VIEW vw_painel_24h AS
SELECT count(*)                                                        AS volume_24h,
       percentile_cont(0.50) WITHIN GROUP (ORDER BY duracao_total_ms)  AS latencia_p50_ms,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY duracao_total_ms)  AS latencia_p95_ms,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY duracao_total_ms)  AS latencia_p99_ms,
       round(100.0 * count(*) FILTER (WHERE duracao_total_ms <= 60000)
                   / nullif(count(*), 0), 2)                           AS pct_dentro_sla,
       round(100.0 * count(*) FILTER (WHERE status = 'erro')
                   / nullif(count(*), 0), 2)                           AS pct_erro,
       round(100.0 * count(*) FILTER (WHERE revisao_manual)
                   / nullif(count(*), 0), 2)                           AS pct_revisao_manual,
       -- coalesce porque o LEFT JOIN pode nao casar preco: sem ele, uma linha
       -- sem modelo conhecido anularia a soma inteira em vez de somar zero.
       round(coalesce(sum(t.tokens_entrada * p.usd_por_1m_in  / 1000000.0
                        + t.tokens_saida   * p.usd_por_1m_out / 1000000.0), 0), 4) AS usd_24h
  FROM jurisflow_trilha_auditoria t
  LEFT JOIN jurisflow_preco_modelo p ON p.modelo = t.modelo
 WHERE t.recebido_em >= now() - INTERVAL '24 hours';

COMMIT;
