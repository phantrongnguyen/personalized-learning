-- Docker executes this only for a new, empty PostgreSQL data directory, after
-- canonical 01 schema, 02 seed and 03 integrity. Existing volumes use Alembic.
CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY);
INSERT INTO alembic_version(version_num) VALUES ('0002_normalize') ON CONFLICT DO NOTHING;
