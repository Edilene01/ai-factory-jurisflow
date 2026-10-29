-- =============================================================================
-- JurisFlow · Papel de menor privilégio para a purga
-- Migração 003 · Etapa 2, Bloco 1
--
-- Existe porque o n8n passou a usar este mesmo Postgres como banco próprio.
-- A decisão resolve a lacuna do prazo de 72 horas, já que o pruning nativo
-- passa a operar sobre uma tabela que a purga alcança, mas cria um efeito
-- colateral: quem tiver a URL deste banco alcança também `credentials_entity`,
-- onde o n8n guarda as credenciais cifradas.
--
-- A segunda via da purga roda em um runner do GitHub, fora da plataforma, com
-- a URL guardada em um secret. Dar ao runner o papel dono do banco seria
-- entregar o cofre inteiro para quem só precisa esvaziar o lixo. Este arquivo
-- cria o papel que faz exatamente o que a política de retenção manda fazer, e
-- nada além.
--
-- Aplicar DEPOIS de 001, de 002 e do primeiro boot do n8n sobre este banco,
-- porque `execution_entity` é criada pelo n8n e não por nós:
--   psql "$DATABASE_URL" -f db/schema/003_papel_purga.sql
--
-- A senha NÃO está aqui e nunca entra no repositório. Defina-a em seguida,
-- em uma sessão separada, com um valor gerado por `openssl rand -hex 24`:
--   ALTER ROLE jurisflow_purga WITH PASSWORD 'o-valor-gerado';
--
-- A URL que vai para o secret DATABASE_URL dos GitHub Environments é a deste
-- papel, e não a do papel dono:
--   postgresql://jurisflow_purga:SENHA@HOST:PORTA/BANCO
--
-- Idempotente: rodar de novo não causa dano.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. O papel
--
-- NOLOGIN até a senha ser definida, de modo que o papel não existe como porta
-- aberta no intervalo entre criar e configurar. O ALTER ROLE com a senha
-- habilita o login junto.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'jurisflow_purga') THEN
        CREATE ROLE jurisflow_purga NOLOGIN;
        RAISE NOTICE 'papel jurisflow_purga criado, ainda sem senha e sem login';
    ELSE
        RAISE NOTICE 'papel jurisflow_purga já existia, mantido';
    END IF;
END $$;

COMMENT ON ROLE jurisflow_purga IS
    'Segunda via da purga de retenção, executada pelo runner do GitHub. Alcança apenas o que a política de retenção manda remover. Sem acesso a credentials_entity.';

-- -----------------------------------------------------------------------------
-- 2. Conexão e esquema
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO jurisflow_purga', current_database());
END $$;

GRANT USAGE ON SCHEMA public TO jurisflow_purga;

-- -----------------------------------------------------------------------------
-- 3. O que a purga precisa tocar
--
-- A trilha e os spans vencem em 12 meses: ler para contar, apagar o vencido.
-- O registro de purga só cresce: inserir e ler, nunca apagar, porque ele é a
-- prestação de contas e não pode ser limpo por quem é auditado por ele.
-- -----------------------------------------------------------------------------
GRANT SELECT, DELETE ON jurisflow_trilha_auditoria TO jurisflow_purga;
GRANT SELECT, DELETE ON jurisflow_trace_span       TO jurisflow_purga;
GRANT SELECT, INSERT ON jurisflow_purga_log        TO jurisflow_purga;

-- BIGSERIAL precisa da sequência, senão o INSERT falha com permissão negada
-- em um objeto que ninguém lembra que existe.
GRANT USAGE ON SEQUENCE jurisflow_purga_log_id_seq TO jurisflow_purga;

-- As views das métricas, para o relatório mensal da seção 4 da política.
GRANT SELECT ON vw_painel_24h          TO jurisflow_purga;
GRANT SELECT ON vw_latencia_hora       TO jurisflow_purga;
GRANT SELECT ON vw_erro_hora           TO jurisflow_purga;
GRANT SELECT ON vw_volume_hora         TO jurisflow_purga;
GRANT SELECT ON vw_qualidade_dia       TO jurisflow_purga;
GRANT SELECT ON vw_custo_dia           TO jurisflow_purga;

-- -----------------------------------------------------------------------------
-- 4. As execuções do n8n · prazo 72 horas
--
-- Tabela do n8n, criada no primeiro boot dele sobre este banco. Se ainda não
-- existe, o bloco avisa em vez de falhar: a purga já trata a ausência, e
-- derrubar a migração inteira por causa da ordem de boot seria pior.
--
-- `execution_data` entra só com SELECT, porque a exclusão a pedido do titular
-- precisa localizar a execução pelo protocolo antes de apagar o pai. O filho
-- sai por ON DELETE CASCADE, que não exige privilégio próprio de DELETE.
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF to_regclass('execution_entity') IS NOT NULL THEN
        GRANT SELECT, DELETE ON execution_entity TO jurisflow_purga;
        IF to_regclass('execution_data') IS NOT NULL THEN
            GRANT SELECT ON execution_data TO jurisflow_purga;
        END IF;
        RAISE NOTICE 'privilégios concedidos sobre as execuções do n8n';
    ELSE
        RAISE WARNING 'execution_entity ainda não existe: o n8n não subiu sobre este banco. Rode este arquivo de novo depois do primeiro boot, senão o prazo de 72 horas segue sem a segunda via.';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 5. O que o papel NÃO alcança, dito de propósito
--
-- Nenhum GRANT sobre `credentials_entity`, `user`, `shared_credentials` ou
-- `settings`. Um papel que não recebe privilégio não tem privilégio, de modo
-- que a ausência de linha aqui é a própria restrição. Está escrito para que a
-- próxima pessoa não interprete o silêncio como esquecimento.
-- -----------------------------------------------------------------------------

COMMIT;

-- -----------------------------------------------------------------------------
-- Verificação pós-aplicação
--
-- Deve listar apenas as tabelas e views acima, e nenhuma linha com
-- credentials_entity:
--
--   SELECT table_name, privilege_type
--     FROM information_schema.table_privileges
--    WHERE grantee = 'jurisflow_purga'
--    ORDER BY table_name, privilege_type;
--
-- E a contraprova, que deve falhar com "permission denied":
--
--   SET ROLE jurisflow_purga;
--   SELECT count(*) FROM credentials_entity;
--   RESET ROLE;
-- -----------------------------------------------------------------------------
