-- Stage 4A
-- Run while connected to the default postgres database.
-- The canonical bootstrap passes db_name with psql -v. The default preserves
-- the established local database name for direct/manual execution.

\if :{?db_name}
\else
\set db_name manufacturing_intelligence
\endif

SELECT format('CREATE DATABASE %I', :'db_name')
WHERE NOT EXISTS (
    SELECT FROM pg_database
    WHERE datname = :'db_name'
)\gexec
