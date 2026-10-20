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
