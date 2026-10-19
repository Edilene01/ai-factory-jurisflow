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

COMMENT ON TABLE  jurisflow_trilha_auditoria IS
    'PC-07 do mapa de dados pessoais. Registro pseudonimizado para observabilidade e para o '
    'registro das operações de tratamento do art. 37 da LGPD. Retenção: 12 meses.';
COMMENT ON COLUMN jurisflow_trilha_auditoria.protocolo IS
    'Pseudônimo do caso. É a única chave de ligação com o titular, e ela não vive aqui: a '
    'correspondência entre protocolo e pessoa está no canal do Slack do escritório.';
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
    'Prova de execução da política de retenção. Guarda apenas contagens e o alvo; nunca o '
    'conteúdo removido. Não é purgado, porque é o registro de prestação de contas.';

CREATE INDEX IF NOT EXISTS ix_purga_executado_em
    ON jurisflow_purga_log (executado_em DESC);

COMMIT;

-- -----------------------------------------------------------------------------
-- Verificação pós-aplicação
-- -----------------------------------------------------------------------------
-- SELECT table_name FROM information_schema.tables
--  WHERE table_name IN ('jurisflow_trilha_auditoria', 'jurisflow_purga_log');
